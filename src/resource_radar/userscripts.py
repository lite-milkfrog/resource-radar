"""Greasy Fork read-only API; gracefully report upstream bot protections."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

import requests

from .catalog import USER_AGENT

API = "https://greasyfork.org/en/scripts.json"


def search_userscripts(query: str, limit: int = 10) -> dict:
    query = query.strip()[:120]
    if not query:
        return {"results": [], "error": "Query required"}
    limit = min(max(1, int(limit)), 30)
    try:
        response = requests.get(API, params={"q": query}, timeout=15,
                                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                                allow_redirects=False)
        if response.status_code in (401, 403, 429, 503):
            return {"results": [], "source": "greasyfork", "error": f"Upstream denied access (HTTP {response.status_code}); no bypass attempted", "browse": "https://greasyfork.org/en/scripts?q=" + requests.utils.quote(query)}
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            return {"results": [], "source": "greasyfork", "error": "Unexpected API response"}
        results = []
        for x in payload[:limit]:
            if not isinstance(x, dict):
                continue
            url = x.get("url", "")
            if urlsplit(url).hostname not in {"greasyfork.org", "www.greasyfork.org"}:
                continue
            results.append({"id": x.get("id"), "name": x.get("name"), "url": url,
                            "description": x.get("description"), "code_url": x.get("code_url"),
                            "daily_installs": x.get("daily_installs"), "total_installs": x.get("total_installs"),
                            "updated_at": x.get("code_updated_at") or x.get("created_at"),
                            "source": "greasyfork", "verified_safe": None})
        return {"results": results, "source": "greasyfork", "accessed_live": True}
    except (requests.RequestException, ValueError) as exc:
        return {"results": [], "source": "greasyfork", "error": f"{type(exc).__name__}: {str(exc)[:150]}"}


def inspect_userscript(script_id: int) -> dict:
    """Read metadata and optionally the first bounded segment of source. Never execute JS."""
    if not 1 <= int(script_id) <= 99_999_999:
        return {"error": "Invalid script ID"}
    url = f"https://greasyfork.org/en/scripts/{int(script_id)}.json"
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": USER_AGENT}, allow_redirects=False)
        if r.status_code in (401,403,429,503):
            return {"id": int(script_id), "error": f"Greasy Fork blocked metadata access (HTTP {r.status_code})"}
        r.raise_for_status()
        info = r.json()
        if not isinstance(info,dict):
            return {"error": "Unexpected API metadata response"}
        result = {"id":int(script_id), "name":info.get("name"), "url":info.get("url"),
                  "description":info.get("description"), "code_url":info.get("code_url"),
                  "verified_safe": None, "code_executed": False}
        code_url = info.get("code_url") or ""
        if urlsplit(code_url).hostname not in {"greasyfork.org", "www.greasyfork.org"}:
            result["code_note"] = "Source URL unavailable or outside Greasy Fork"
            return result
        code = requests.get(code_url, timeout=15, headers={"User-Agent": USER_AGENT}, allow_redirects=False)
        if code.status_code != 200 or len(code.content) > 300_000:
            result["code_note"] = f"Source not inspected (HTTP {code.status_code} or size limit)"
            return result
        js = code.text
        grants = re.findall(r"^\s*//\s*@grant\s+(\S+)", js, re.M)
        matches = re.findall(r"^\s*//\s*@(?:match|include)\s+(\S+)", js, re.M)
        requires = re.findall(r"^\s*//\s*@require\s+(\S+)", js, re.M)
        result["static_review"] = {"grants":grants[:100], "page_patterns":matches[:100],
                                   "remote_dependencies":requires[:30],
                                   "uses_eval":bool(re.search(r"\beval\s*\(", js)),
                                   "uses_cross_domain_api":bool(re.search(r"GM_xmlhttpRequest|GM\.xmlHttpRequest", js)),
                                   "limitations":"Heuristic static indicators only; NOT a safety certification"}
        return result
    except (requests.RequestException, ValueError) as exc:
        return {"id":int(script_id), "error": f"{type(exc).__name__}: {str(exc)[:150]}"}
