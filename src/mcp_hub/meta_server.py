from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .manager import HubManager
from .meta_catalog import resources, tools


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mcp-hub-meta")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    server = MetaServer(HubManager.from_root(Path(args.root).resolve()))
    server.run()
    return 0


class MetaServer:
    def __init__(self, manager: HubManager) -> None:
        self.manager = manager

    def run(self) -> None:
        while True:
            message = _read_message()
            if message is None:
                break
            response = self.handle(message)
            if response is not None:
                _write_message(response)

    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = message.get("method")
        request_id = message.get("id")
        try:
            if method == "initialize":
                return _result(
                    request_id,
                    {
                        "protocolVersion": message.get("params", {}).get(
                            "protocolVersion", "2025-06-18"
                        ),
                        "capabilities": {"tools": {}, "resources": {}},
                        "serverInfo": {"name": "MCP Hub Meta Server", "version": "0.1.0"},
                    },
                )
            if method == "notifications/initialized":
                return None
            if method == "tools/list":
                return _result(request_id, {"tools": tools()})
            if method == "tools/call":
                params = message.get("params", {})
                return _result(
                    request_id,
                    _call_tool(self.manager, params.get("name", ""), params.get("arguments", {})),
                )
            if method == "resources/list":
                return _result(request_id, {"resources": resources(self.manager)})
            if method == "resources/read":
                uri = message.get("params", {}).get("uri", "")
                return _result(
                    request_id,
                    {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": "text/plain",
                                "text": _read_resource(self.manager, uri),
                            }
                        ]
                    },
                )
            return _error(request_id, -32601, f"Method not found: {method}")
        except Exception as exc:  # Keep stdio server alive and return structured MCP error.
            return _error(request_id, -32000, str(exc))


def _call_tool(manager: HubManager, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "hub.list_services":
        payload: Any = {
            "services": manager.list_services(
                include_disabled=arguments.get("include_disabled", True),
                include_invalid=arguments.get("include_invalid", True),
            )
        }
    elif name == "hub.describe_service":
        payload = manager.describe_service(arguments["id"])
    elif name == "hub.get_service_connection":
        payload = manager.get_connection(arguments["id"])
    elif name == "hub.get_service_capabilities":
        payload = {"content": manager.read_capabilities(arguments["id"])}
    elif name == "hub.get_service_readme":
        payload = {"content": manager.read_readme(arguments["id"])}
    elif name == "hub.get_service_status":
        payload = manager.get_service_status(arguments["id"])
    elif name == "hub.list_guidelines":
        payload = manager.list_guidelines()
    elif name == "hub.get_guideline":
        payload = {"content": manager.get_guideline(arguments["id"])}
    elif name == "hub.recommend_server_type":
        payload = manager.recommend_server_type(arguments)
    elif name == "hub.get_example_code":
        example_id = arguments["example_id"]
        if "path" in arguments:
            payload = {"content": manager.get_example_file(example_id, arguments["path"])}
        else:
            payload = {"files": manager.list_example_files(example_id)}
    elif name == "hub.rescan_services":
        payload = manager.rescan()
    elif name == "hub.probe_service":
        payload = manager.probe_service(arguments["id"])
    elif name == "hub.start_service":
        payload = manager.start_service(arguments["id"])
    elif name == "hub.stop_service":
        payload = manager.stop_service(arguments["id"])
    elif name == "hub.restart_service":
        payload = manager.restart_service(arguments["id"])
    elif name == "hub.tail_service_logs":
        payload = manager.tail_service_logs(arguments["id"], int(arguments.get("lines", 200)))
    else:
        raise KeyError(f"Unknown tool: {name}")
    return {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]}

def _read_resource(manager: HubManager, uri: str) -> str:
    if uri == "hub://services":
        return json.dumps({"services": manager.list_services()}, indent=2)
    if uri == "hub://guidelines/server-authoring":
        return manager.get_guideline("server-authoring")
    if uri == "hub://guidelines/examples":
        return json.dumps(manager.list_guidelines()["examples"], indent=2)
    if uri == "hub://guidelines/examples/python-stdio-fastmcp":
        return json.dumps({"files": manager.list_example_files("python-stdio-fastmcp")}, indent=2)
    example_prefix = "hub://guidelines/examples/python-stdio-fastmcp/"
    if uri.startswith(example_prefix):
        return manager.get_example_file("python-stdio-fastmcp", uri.removeprefix(example_prefix))
    parts = uri.removeprefix("hub://").split("/")
    if len(parts) >= 3 and parts[0] == "services":
        service_id = parts[1]
        if parts[2] == "capabilities":
            return manager.read_capabilities(service_id)
        if parts[2] == "readme":
            return manager.read_readme(service_id)
        if parts[2] == "connection":
            return json.dumps(manager.get_connection(service_id), indent=2)
        if parts[2] == "manifest":
            return json.dumps(manager.get_manifest(service_id), indent=2)
        if parts[2] == "status":
            return json.dumps(manager.get_service_status(service_id), indent=2)
    raise KeyError(f"Unknown resource: {uri}")


def _read_message() -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if line == b"":
            return None
        if line in {b"\r\n", b"\n"}:
            break
        key, value = line.decode("ascii").split(":", 1)
        headers[key.lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))


def _write_message(payload: dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def _result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


if __name__ == "__main__":
    raise SystemExit(main())
