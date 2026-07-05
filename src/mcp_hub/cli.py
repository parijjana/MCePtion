from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .manager import HubManager, ServiceNotFoundError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mcp-hub")
    parser.add_argument("--root", default=".", help="MCP Hub root directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-services")
    subparsers.add_parser("rescan")

    describe = subparsers.add_parser("describe-service")
    describe.add_argument("service_id")

    connection = subparsers.add_parser("connection")
    connection.add_argument("service_id")

    validate = subparsers.add_parser("validate-server")
    validate.add_argument("server_path")

    guideline = subparsers.add_parser("guideline")
    guideline.add_argument("guideline_id")

    recommend = subparsers.add_parser("recommend-server-type")
    recommend.add_argument("--shared-across-projects", action="store_true")
    recommend.add_argument("--stores-durable-data", action="store_true")
    recommend.add_argument("--needs-long-running-process", action="store_true")
    recommend.add_argument("--needs-multiple-simultaneous-clients", action="store_true")
    recommend.add_argument("--needs-browser-ui", action="store_true")
    recommend.add_argument("--remote-access-required", action="store_true")

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    try:
        if args.command == "validate-server":
            return _validate_server(root, Path(args.server_path))

        manager = HubManager.from_root(root)
        if args.command == "list-services":
            return _print_json({"services": manager.list_services()})
        if args.command == "rescan":
            return _print_json(manager.rescan())
        if args.command == "describe-service":
            return _print_json(manager.describe_service(args.service_id))
        if args.command == "connection":
            return _print_json(manager.get_connection(args.service_id))
        if args.command == "guideline":
            print(manager.get_guideline(args.guideline_id), end="")
            return 0
        if args.command == "recommend-server-type":
            payload = {
                "shared_across_projects": args.shared_across_projects,
                "stores_durable_data": args.stores_durable_data,
                "needs_long_running_process": args.needs_long_running_process,
                "needs_multiple_simultaneous_clients": args.needs_multiple_simultaneous_clients,
                "needs_browser_ui": args.needs_browser_ui,
                "remote_access_required": args.remote_access_required,
            }
            return _print_json(manager.recommend_server_type(payload))
    except (ServiceNotFoundError, FileNotFoundError, KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    parser.error(f"unsupported command: {args.command}")
    return 2


def _validate_server(root: Path, server_path: Path) -> int:
    from .validation import validate_server_path

    result = validate_server_path(root, server_path)
    _print_json(result)
    return 0 if result["valid"] else 1


def _print_json(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
