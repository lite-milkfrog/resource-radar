# Resource Radar MCP / 资源雷达

An **independent local resource discovery index** for finding under-the-radar tools, scripts and services. It complements general web search; it is **not** an unrestricted crawler, a piracy host, or an endorsement of third-party resources.

## Current implementation (v0.1)

- Bounded Markdown imports: FMHY official `single-page.md`, GitHub Awesome, Awesome Selfhosted, Free for Dev, Awesome Userscripts.
- SQLite database, FTS5 + substring fallback, canonical-URL de-duplication and multi-source provenance.
- Seven MCP tools: `search_resources`, `search_userscripts`, `inspect_resource`, `inspect_script`, `compare_resources`, `sync_sources`, `source_status`.
- Optional Greasy Fork read-only JSON API; some networks are blocked by Cloudflare. Reports HTTP 403/429 explicitly rather than bypassing protection, and searches the local Awesome Userscripts catalog as fallback.
- Local **stdio** transport; no scraping arbitrary URLs, no automatic installation or execution of JavaScript.

Other planned inputs (ScriptCat store, OpenUserJS, HelloGitHub, etc.) require independent API/access verification and are **not** implemented yet. ScriptCat separately publishes an `sctl` CLI and MCP integration, but Resource Radar has not integrated it.

## Install on Windows

```powershell
cd D:\AgentData\10_Workspaces\resource-radar
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
$env:RESOURCE_RADAR_DB = 'D:\AgentData\10_Workspaces\resource-radar\data\index.sqlite3'
.\.venv\Scripts\resource-radar.exe sync
.\.venv\Scripts\resource-radar.exe search "AI"
.\.venv\Scripts\resource-radar.exe serve
```

If `RESOURCE_RADAR_DB` is omitted, the database defaults to `%LOCALAPPDATA%\ResourceRadar\index.sqlite3` (falling back to `%USERPROFILE%` or the working directory when unavailable). **The database is excluded from Git.** `serve` communicates over stdio; start it from a compatible MCP host, not an interactive chat prompt.

### Example WAC/MCP client server configuration

```json
{
  "resource-radar": {
    "command": "D:\\AgentData\\10_Workspaces\\resource-radar\\.venv\\Scripts\\python.exe",
    "args": ["-m", "resource_radar.server"],
    "env": {"RESOURCE_RADAR_DB": "D:\\AgentData\\10_Workspaces\\resource-radar\\data\\index.sqlite3"}
  }
}
```

Place this entry **under the client application's MCP server map** (schema varies by client); do not blindly overwrite existing WAC configuration.

### Verify

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\resource-radar.exe status
```

## Safety and source licenses

Sources are independent websites; a catalog listing is **not proof** of quality, legality, safety, availability, free tier, or license. Analyze and verify a candidate before opening or installing. Index records include their original provenance and sync time. Do not redistribute imported third-party catalogs unless their licenses permit it (e.g. Awesome Selfhosted data is CC BY-SA 3.0). The repository contains **implementation source only**, not the imported data.

`inspect_script` only reads Greasy Fork metadata and optionally bounded script text for simple static warning signals; it never runs downloaded JS. Static checks are not a malware scan. A blocked source stays blocked; use the original website manually.

## Milestones

1. **v0.1:** local index + MCP + source attribution + tests (this repository).
2. **v0.2:** ScriptCat/OpenUserJS/HelloGitHub connectors, improved Chinese tokenization, per-source update/retirement and source health monitoring.
3. **v0.3:** WAC integration acceptance, resource verification pipeline (GitHub repo metadata, licensing, reachability), failure replay and ranking evaluation.
4. **v0.4:** optional dashboard, manual source review, semantic search only if benchmarked necessary.

Do not present these future milestones as completed.
