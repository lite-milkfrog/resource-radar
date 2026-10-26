# Resource Radar

**Great tools are everywhere. Finding them shouldn't be a scavenger hunt.**

FMHY, Awesome Lists, self-hosted software, free developer services, userscript collections — some of the best finds live in curated directories that don't always surface in a normal web search.

**Resource Radar brings those directories into a searchable local index and exposes them to your AI agents through MCP.** One search, multiple sources, with links back to where every result came from.

[简体中文](README.md) · [Get started](#get-started) · [Connect your agent](#connect-your-agent)

![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-stdio-333333)
![SQLite](https://img.shields.io/badge/Local_Index-SQLite-003B57?logo=sqlite&logoColor=white)

## What can it find?

| Looking for… | Where it looks |
| --- | --- |
| Useful free tools and lesser-known websites | **FMHY** |
| Curated collections of projects | **Awesome Lists** |
| Software you can run yourself | **Awesome Selfhosted** |
| Free APIs and developer services | **Free for Dev** |
| Browser-enhancing userscripts | **Awesome Userscripts**, plus a live **Greasy Fork** API attempt |

Ask your agent: *“Find a self-hosted AI knowledge base”*, *“Look for YouTube userscripts”*, or *“Show me free developer APIs.”* Resource Radar provides relevant starting points and provenance for further research.

## How it works

`Your idea → Curated directories → Local SQLite search & deduplication → Source links → MCP agent`

- **Local-first indexing** powered by SQLite FTS5, with substring fallback.
- **Five directory inputs** with URL deduplication, source filtering, and sync history.
- **Seven MCP tools** for discovery, script lookups, comparisons, and index maintenance.
- **Practical results:** a first local sync on **2026-10-26 indexed 27,964 unique links** across five curated directories. Counts vary as sources change.

Search for **Ollama** to see results attributed to both FMHY and Awesome Selfhosted. Search for **YouTube** inside `awesome_userscripts` to discover browser scripts in the local index.

## Get started

Python 3.11+ and Git are required. Example for Windows PowerShell:

```powershell
git clone https://github.com/lite-milkfrog/resource-radar.git
cd resource-radar

py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .

$env:RESOURCE_RADAR_DB = (Join-Path (Get-Location) 'data\index.sqlite3')
.\.venv\Scripts\resource-radar.exe sync
.\.venv\Scripts\resource-radar.exe search "Ollama"
.\.venv\Scripts\resource-radar.exe search "YouTube" --source awesome_userscripts
```

Check the index or run the test suite:

```powershell
.\.venv\Scripts\resource-radar.exe status
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Without `RESOURCE_RADAR_DB`, the database defaults to `ResourceRadar/index.sqlite3` under the user's local app-data directory (or the available local fallback). Run `sync` before your first search.

## Connect your agent

Example **generic MCP client** configuration for a Windows installation (adjust paths and merge into your existing MCP configuration):

```json
{
  "mcpServers": {
    "resource-radar": {
      "command": "D:\\AgentData\\10_Workspaces\\resource-radar\\.venv\\Scripts\\python.exe",
      "args": ["-m", "resource_radar.server"],
      "env": {
        "RESOURCE_RADAR_DB": "D:\\AgentData\\10_Workspaces\\resource-radar\\data\\index.sqlite3"
      }
    }
  }
}
```

The MCP server uses local stdio. WAC-specific automatic registration is planned, not yet completed.

### MCP tools

| Tool | What it does |
| --- | --- |
| `search_resources` | Search indexed resources; filter by source |
| `search_userscripts` | Query Greasy Fork, with local curated-list fallback |
| `inspect_resource` | Look up resource details and provenance |
| `inspect_script` | Review script metadata and basic static warning signals |
| `compare_resources` | Compare indexed candidates side by side |
| `sync_sources` | Refresh selected directories |
| `source_status` | Inspect index size, sync timestamps, and errors |

The Greasy Fork API may return HTTP 403 on some networks; Resource Radar reports this and can use the locally indexed Awesome Userscripts list instead.

## What's next?

- More discovery sources: ScriptCat, OpenUserJS, HelloGitHub.
- Better Chinese search, grouping, and result ranking.
- GitHub activity, licensing, and link-status checks.
- Verified WAC integration and end-to-end agent workflows.

**Tell your agent what you want to do. Let it help you find the tools that already exist.**

## Source credits

Every resource retains its original source information. Scripts are never installed or executed by the indexer. Third-party catalogs follow their own licenses and terms; downloaded index data stays on your machine and isn't committed to this repository.

---

**Know a great directory we should index next? Open an Issue.**
