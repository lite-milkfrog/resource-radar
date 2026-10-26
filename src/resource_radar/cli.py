"""Local command-line entry point for smoke tests and syncing."""

import argparse
import json
import sys

from .catalog import Catalog, SOURCES


def main():
    # Windows consoles can use GBK; don't crash on Unicode characters from catalogs.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")

    parser = argparse.ArgumentParser(
        prog="resource-radar",
        description="Find better tools, faster — local resource discovery for AI agents",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("serve")
    sub.add_parser("status")
    sync = sub.add_parser("sync")
    sync.add_argument("sources", nargs="*", choices=list(SOURCES))
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--source", default="")
    search.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    if args.command == "serve":
        from .server import main as run_server
        run_server()
        return
    cat = Catalog()
    try:
        if args.command == "sync":
            result = cat.sync(args.sources)
        elif args.command == "search":
            result = cat.search(args.query, args.source, args.limit)
        else:
            result = cat.status()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        cat.close()


if __name__ == "__main__":
    main()
