"""SQLite catalog and bounded, allowlisted imports of public resource indexes."""

from __future__ import annotations

import hashlib
import html
import os
import re
import sqlite3
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

DEFAULT_DB = Path(os.environ["RESOURCE_RADAR_DB"]) if os.environ.get("RESOURCE_RADAR_DB") else (Path(os.environ.get("LOCALAPPDATA") or os.environ.get("USERPROFILE") or os.getcwd()) / "ResourceRadar" / "index.sqlite3")
USER_AGENT = "ResourceRadar/0.1 (+https://github.com/lite-milkfrog/resource-radar; metadata indexing)"
SOURCES = {
    "fmhy": "https://fmhy.net/single-page.md",
    "awesome": "https://raw.githubusercontent.com/sindresorhus/awesome/main/readme.md",
    "awesome_selfhosted": "https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/master/README.md",
    "free_for_dev": "https://raw.githubusercontent.com/ripienaar/free-for-dev/master/README.md",
    "awesome_userscripts": "https://raw.githubusercontent.com/awesome-scripts/awesome-userscripts/master/README.md",
}
LINK = re.compile(r"(?<!!)\[([^\]\n]{2,160})\]\((https?://[^\s)<>]+)(?:\s+\"[^\"]*\")?\)")
HTML_SUMMARY = re.compile(r'<summary[^>]*>\s*<a\s+href="(https?://[^"]+)">([^<]+)</a>(.*?)</summary>', re.I)
MARKUP = re.compile(r"[`*_~#>\[\]]")
SKIP_HOSTS = {"localhost", "127.0.0.1", "::1"}


def canonicalize(url: str) -> str:
    try:
        p = urlsplit(url.strip())
        host = (p.hostname or "").lower()
        if p.scheme.lower() not in {"http", "https"} or not host or host in SKIP_HOSTS:
            return ""
        if p.username or p.password or len(url) > 2048:
            return ""
        netloc = host + ((":" + str(p.port)) if p.port and p.port not in (80, 443) else "")
        noisy = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}
        params = urlencode([(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k.lower() not in noisy])
        return urlunsplit((p.scheme.lower(), netloc, p.path.rstrip("/") or "/", params, ""))
    except ValueError:
        return ""


def parse_markdown(text: str, source: str):
    """Parse links, remembering nearest section; do not treat an index as a software endorsement."""
    section = "Userscripts" if source == "awesome_userscripts" else "General"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and not stripped.startswith("##!") and "<" not in stripped:
            section = MARKUP.sub("", stripped).strip()[:160] or section
        if not stripped or stripped.startswith("<!--"):
            continue
        for m in LINK.finditer(line):
            title, raw_url = m.groups()
            url = canonicalize(raw_url)
            if not url:
                continue
            title = MARKUP.sub("", title).strip()
            if title.lower() in {"link", "website", "source", "github", "here", "readme", "docs"}:
                continue
            surrounding = (line[:m.start()] + " " + line[m.end():]).strip(" *-|:>\t")
            desc = MARKUP.sub("", surrounding).strip()[:240]
            yield {"title": title[:160], "url": url, "description": desc, "category": section, "source": source}
        # Some curated README catalogs (notably Awesome Userscripts) use
        # HTML <summary><a> entries rather than Markdown links.
        for m in HTML_SUMMARY.finditer(line):
            url = canonicalize(html.unescape(m.group(1)))
            title = html.unescape(m.group(2)).strip()[:160]
            desc = re.sub(r"<[^>]+>", "", html.unescape(m.group(3))).strip(" -:\t")[:240]
            if url and title:
                yield {"title": title, "url": url, "description": desc,
                       "category": section, "source": source}


def fetch_text(url: str, max_bytes: int = 12_000_000, timeout: int = 25) -> str:
    """Only fetch hardcoded catalog origins, not arbitrary user-provided URLs."""
    allowed = {urlsplit(v).hostname for v in SOURCES.values()}
    if urlsplit(url).hostname not in allowed or url not in SOURCES.values():
        raise ValueError("Catalog origin is not allowlisted")
    response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT}, stream=True, allow_redirects=False)
    response.raise_for_status()
    size = 0
    chunks = []
    for chunk in response.iter_content(65536):
        size += len(chunk)
        if size > max_bytes:
            raise ValueError("Catalog exceeds bounded download limit")
        chunks.append(chunk)
    return b"".join(chunks).decode("utf-8-sig", errors="replace")


class Catalog:
    def __init__(self, db_path: str | Path | None = None):
        self.path = Path(db_path) if db_path else DEFAULT_DB
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=15)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA busy_timeout=15000")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS resources (
                id TEXT PRIMARY KEY, url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT '', first_seen INTEGER NOT NULL,
                last_seen INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS occurrences (
                resource_id TEXT NOT NULL, source TEXT NOT NULL,
                origin TEXT NOT NULL, PRIMARY KEY (resource_id, source),
                FOREIGN KEY(resource_id) REFERENCES resources(id)
            );
            CREATE TABLE IF NOT EXISTS source_runs (
                source TEXT PRIMARY KEY, updated INTEGER, imported INTEGER DEFAULT 0,
                error TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS resources_url_idx ON resources(url);
            CREATE INDEX IF NOT EXISTS occurrences_source_idx ON occurrences(source);
        """)
        self.fts = True
        try:
            self.db.executescript("""
                CREATE VIRTUAL TABLE IF NOT EXISTS resources_fts USING fts5(
                    title, description, category, content='resources', content_rowid='rowid',
                    tokenize='unicode61 remove_diacritics 2');
                CREATE TRIGGER IF NOT EXISTS rr_ai AFTER INSERT ON resources BEGIN
                    INSERT INTO resources_fts(rowid,title,description,category)
                    VALUES (new.rowid,new.title,new.description,new.category);
                END;
                CREATE TRIGGER IF NOT EXISTS rr_ad AFTER DELETE ON resources BEGIN
                    INSERT INTO resources_fts(resources_fts,rowid,title,description,category)
                    VALUES ('delete',old.rowid,old.title,old.description,old.category);
                END;
                CREATE TRIGGER IF NOT EXISTS rr_au AFTER UPDATE ON resources BEGIN
                    INSERT INTO resources_fts(resources_fts,rowid,title,description,category)
                    VALUES ('delete',old.rowid,old.title,old.description,old.category);
                    INSERT INTO resources_fts(rowid,title,description,category)
                    VALUES (new.rowid,new.title,new.description,new.category);
                END;
            """)
            # The rebuild is idempotent and covers databases created before triggers.
            if self.db.execute("SELECT count(*) FROM resources_fts").fetchone()[0] == 0:
                self.db.execute("INSERT INTO resources_fts(resources_fts) VALUES('rebuild')")
        except sqlite3.OperationalError:
            self.fts = False
        self.db.commit()

    def close(self):
        self.db.close()

    def add(self, item: dict, origin: str = "") -> bool:
        url = canonicalize(item.get("url", ""))
        if not url:
            return False
        stamp = int(time.time())
        rid = hashlib.sha256(url.encode()).hexdigest()[:24]
        title = item.get("title", "")[:160].strip() or urlsplit(url).hostname
        desc = item.get("description", "")[:240].strip()
        section = item.get("category", "")[:160].strip()
        self.db.execute("""INSERT INTO resources(id,url,title,description,category,first_seen,last_seen)
            VALUES (?,?,?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET last_seen=excluded.last_seen,
            description=CASE WHEN length(resources.description)>length(excluded.description) THEN resources.description ELSE excluded.description END,
            category=CASE WHEN resources.category='' OR resources.category LIKE '<picture%' THEN excluded.category ELSE resources.category END""",
            (rid, url, title, desc, section, stamp, stamp))
        self.db.execute("INSERT OR IGNORE INTO occurrences(resource_id,source,origin) VALUES(?,?,?)",
                        (rid, item.get("source", "unknown"), origin))
        return True

    def import_markdown(self, source: str, text: str, origin: str = "fixture") -> dict:
        if source not in SOURCES:
            raise ValueError("Unknown catalog source")
        # Treat a sync as a unit. Do not destroy the previous index after download failure.
        records = list(parse_markdown(text, source))
        if not records:
            raise ValueError(f"No links parsed from {source}; preserving existing data")
        with self.db:
            for item in records:
                self.add(item, origin)
            self.db.execute("""INSERT INTO source_runs(source,updated,imported,error) VALUES(?,?,?,'')
                ON CONFLICT(source) DO UPDATE SET updated=excluded.updated,imported=excluded.imported,error=''""",
                (source, int(time.time()), len(records)))
        return {"source": source, "parsed": len(records), "unique_total": self.count()}

    def sync(self, names: list[str] | None = None) -> list[dict]:
        names = names or list(SOURCES)
        result = []
        for name in names:
            if name not in SOURCES:
                result.append({"source": name, "error": "Unknown source"})
                continue
            try:
                content = fetch_text(SOURCES[name])
                result.append(self.import_markdown(name, content, SOURCES[name]))
            except (requests.RequestException, ValueError, OSError) as exc:
                error = f"{type(exc).__name__}: {str(exc)[:240]}"
                with self.db:
                    self.db.execute("""INSERT INTO source_runs(source,error) VALUES(?,?)
                        ON CONFLICT(source) DO UPDATE SET error=excluded.error""", (name, error))
                result.append({"source": name, "error": error, "preserved_existing": True})
        return result

    def count(self) -> int:
        return self.db.execute("SELECT count(*) FROM resources").fetchone()[0]

    def search(self, query: str, source: str = "", limit: int = 10) -> list[dict]:
        query = query.strip()[:140]
        if not query:
            return []
        limit = min(max(1, int(limit)), 30)
        # FTS tokenization is poor for multi-character Chinese substring queries;
        # LIKE fallback is intentionally always included and de-duplicates URLs.
        fts_ids = []
        if self.fts:
            tokens = re.findall(r"[^\W_]+", query, flags=re.UNICODE)[:8]
            if tokens:
                expr = " OR ".join('"' + t.replace('"', '') + '"' for t in tokens)
                try:
                    fts_ids = [r[0] for r in self.db.execute(
                        "SELECT resources.id FROM resources_fts JOIN resources ON resources.rowid=resources_fts.rowid WHERE resources_fts MATCH ? LIMIT 120", (expr,))]
                except sqlite3.OperationalError:
                    fts_ids = []
        where = "%" + query.replace("%", "\\%").replace("_", "\\_") + "%"
        # Never interpolate SQL query content, only place-holders.
        sql = ("SELECT r.*, GROUP_CONCAT(o.source) AS sources "
               "FROM resources AS r JOIN occurrences AS o ON o.resource_id=r.id "
               "WHERE r.title LIKE ? OR r.description LIKE ? OR r.category LIKE ? "
               "GROUP BY r.id LIMIT 2000")
        rows = self.db.execute(sql, (where, where, where)).fetchall()
        ids = {r['id'] for r in rows}
        if fts_ids:
            for step in range(0,len(fts_ids),90):
                sub = fts_ids[step:step+90]
                q = ','.join('?'*len(sub))
                more = self.db.execute(f"SELECT r.*, GROUP_CONCAT(o.source) sources FROM resources r JOIN occurrences o ON o.resource_id=r.id WHERE r.id IN ({q}) GROUP BY r.id",sub).fetchall()
                for r in more:
                    if r['id'] not in ids:
                        rows.append(r)
                        ids.add(r['id'])
        words = [w.lower() for w in re.findall(r"[^\W_]+", query)][:8]
        found=[]
        for row in rows:
            sources = sorted(set(row['sources'].split(',')))
            if source and source not in sources:
                continue
            obj = {k:row[k] for k in ('title','url','description','category','last_seen')}
            obj['sources'] = sources
            target = (row['title'] + ' ' + row['description'] + ' ' + row['category']).lower()
            score = sum(4 if w in row['title'].lower() else 1 if w in target else 0 for w in words)
            if query.lower() in row['title'].lower(): score += 6
            score += min(len(sources)-1,3)
            obj['_score'] = score
            found.append(obj)
        found.sort(key=lambda x: (-x['_score'],x['title'].lower()))
        for row in found[:limit]:row.pop('_score',None)
        return found[:limit]

    def inspect(self, url: str) -> dict:
        normalized = canonicalize(url)
        row = self.db.execute("SELECT * FROM resources WHERE url=?", (normalized,)).fetchone()
        if not row:
            return {"found": False, "url": normalized, "note": "Not indexed; no safety or availability judgment"}
        sources = [dict(x) for x in self.db.execute("SELECT source,origin FROM occurrences WHERE resource_id=?", (row['id'],))]
        return {"found": True, "title": row['title'], "url": row['url'], "description": row['description'],
                "category": row['category'], "first_seen": row['first_seen'], "last_seen": row['last_seen'],
                "provenance": sources, "verified_safe": None, "open_source": None, "reachable": None}

    def status(self) -> dict:
        runs = {r['source']:dict(r) for r in self.db.execute("SELECT * FROM source_runs")}
        return {"db": str(self.path), "resources": self.count(), "available_sources": list(SOURCES),
                "sources": runs, "notes": "Indexes are descriptive; no resource safety or copyright endorsement."}
