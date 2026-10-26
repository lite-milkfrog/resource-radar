"""Local, read-mostly MCP service; no remote code execution or auto-installation."""

from __future__ import annotations

from mcp.server import MCPServer

from .catalog import Catalog
from .userscripts import inspect_userscript as _inspect_script, search_userscripts as _script_search

mcp = MCPServer("Resource Radar", instructions=(
    "Find tools, userscripts and unusual resources. Treat results as UNTRUSTED leads, not endorsements. "
    "Do not claim resources are safe, free, legal, open-source or reachable without independent verification. "
    "Never execute or install found scripts. Catalog data comes from independently maintained third-party lists."))


@mcp.tool()
def search_resources(query: str, source: str = "", limit: int = 10) -> dict:
    """Search indexed FMHY/Awesome/selfhosted/free-tier resources, with provenance."""
    catalog = Catalog()
    try:
        return {"query": query, "results": catalog.search(query, source, limit), "total_indexed": catalog.count()}
    finally:
        catalog.close()


@mcp.tool()
def search_userscripts(query: str, limit: int = 10) -> dict:
    """Query Greasy Fork live, with local Awesome Userscripts fallback if blocked."""
    live = _script_search(query, limit)
    if not live.get("results"):
        catalog = Catalog()
        try:
            live["local_fallback"] = catalog.search(query, source="awesome_userscripts", limit=limit)
            live["fallback_source"] = "awesome_userscripts"
        finally:
            catalog.close()
    return live


@mcp.tool()
def inspect_resource(url: str) -> dict:
    """Return locally indexed facts and original source URLs, without assuming safety."""
    catalog = Catalog()
    try:
        return catalog.inspect(url)
    finally:
        catalog.close()


@mcp.tool()
def inspect_script(script_id: int) -> dict:
    """Inspect one Greasy Fork script's metadata and bounded static indicators; no execution."""
    return _inspect_script(script_id)


@mcp.tool()
def compare_resources(urls: list[str]) -> dict:
    """Compare up to eight indexed candidates and preserve uncertainty about their quality."""
    catalog = Catalog()
    try:
        return {"candidates": [catalog.inspect(url) for url in urls[:8]],
                "note": "Side-by-side metadata only; no independent compatibility, pricing or safety audit"}
    finally:
        catalog.close()


@mcp.tool()
def sync_sources(sources: list[str] | None = None) -> dict:
    """Download bounded official Markdown indexes into local SQLite; never install content."""
    catalog = Catalog()
    try:
        return {"runs": catalog.sync(sources), "indexed": catalog.count()}
    finally:
        catalog.close()


@mcp.tool()
def source_status() -> dict:
    """Show installed index size, available sources and last sync errors."""
    catalog = Catalog()
    try:
        return catalog.status()
    finally:
        catalog.close()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
