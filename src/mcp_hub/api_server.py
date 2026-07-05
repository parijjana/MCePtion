from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .config import load_config
from .dashboard import HtmlResponse, render_dashboard
from .manager import HubManager, ServiceNotFoundError


class LocalThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mcp-hub-manager")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    config = load_config(Path(args.root).resolve())
    manager = HubManager(config)
    server = LocalThreadingHTTPServer((config.manager_host, config.manager_port), _handler(manager))
    print(
        f"MCP Hub manager listening on http://{config.manager_host}:{config.manager_port}",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


def _handler(manager: HubManager) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._dispatch("GET")

        def do_POST(self) -> None:
            self._dispatch("POST")

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _dispatch(self, method: str) -> None:
            parsed = urlparse(self.path)
            parts = [unquote(part) for part in parsed.path.strip("/").split("/") if part]
            try:
                payload = self._route(method, parts)
                self._json(200, payload)
            except ServiceNotFoundError as exc:
                self._json(404, _error("SERVICE_NOT_FOUND", f"Service not found: {exc.args[0]}"))
            except KeyError as exc:
                self._json(404, _error("NOT_FOUND", str(exc)))
            except ValueError as exc:
                self._json(400, _error("BAD_REQUEST", str(exc)))

        def _route(self, method: str, parts: list[str]) -> Any:
            if method == "GET" and parts == []:
                return render_dashboard(manager)
            if method == "GET" and parts == ["health"]:
                return {"status": "ok"}
            if method == "GET" and parts == ["services"]:
                return {"services": manager.list_services()}
            if method == "POST" and parts == ["services", "rescan"]:
                return manager.rescan()
            if len(parts) >= 2 and parts[0] == "services":
                service_id = parts[1]
                if method == "GET" and len(parts) == 2:
                    return manager.describe_service(service_id)
                if method == "GET" and parts[2:] == ["connection"]:
                    return manager.get_connection(service_id)
                if method == "GET" and parts[2:] == ["capabilities"]:
                    return {"content": manager.read_capabilities(service_id)}
                if method == "GET" and parts[2:] == ["readme"]:
                    return {"content": manager.read_readme(service_id)}
                if method == "GET" and parts[2:] == ["manifest"]:
                    return manager.get_manifest(service_id)
                if method == "POST" and parts[2:] == ["probe"]:
                    return manager.probe_service(service_id)
                if method == "POST" and parts[2:] == ["start"]:
                    return manager.start_service(service_id)
                if method == "POST" and parts[2:] == ["stop"]:
                    return manager.stop_service(service_id)
                if method == "POST" and parts[2:] == ["restart"]:
                    stop = manager.stop_service(service_id)
                    start = manager.start_service(service_id)
                    return {"stop": stop, "start": start}
            if method == "GET" and parts == ["guidelines"]:
                return manager.list_guidelines()
            if method == "GET" and len(parts) == 2 and parts[0] == "guidelines":
                return {"content": manager.get_guideline(parts[1])}
            if method == "POST" and parts == ["guidelines", "recommend-server-type"]:
                return manager.recommend_server_type(self._read_json())
            if method == "GET" and parts == ["guidelines", "examples"]:
                return manager.list_guidelines().get("examples", [])
            if method == "GET" and len(parts) == 3 and parts[:2] == ["guidelines", "examples"]:
                return {"files": manager.list_example_files(parts[2])}
            if (
                method == "GET"
                and len(parts) >= 5
                and parts[:2] == ["guidelines", "examples"]
                and parts[3] == "files"
            ):
                return {"content": manager.get_example_file(parts[2], "/".join(parts[4:]))}
            raise KeyError("/" + "/".join(parts))

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if not length:
                return {}
            return json.loads(self.rfile.read(length).decode("utf-8"))

        def _json(self, status: int, payload: Any) -> None:
            if isinstance(payload, HtmlResponse):
                self._html(status, payload.content)
                return
            body = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _html(self, status: int, content: str) -> None:
            body = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def _error(code: str, message: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message}}


_html_dashboard = render_dashboard


if __name__ == "__main__":
    raise SystemExit(main())
