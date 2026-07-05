from __future__ import annotations

import json
import unittest
from pathlib import Path
from shutil import copytree

from workspace_utils import test_workspace

from mcp_hub.manager import HubManager
from mcp_hub.meta_server import MetaServer

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


class MetaServerTests(unittest.TestCase):
    def test_lists_tools(self) -> None:
        server = MetaServer(HubManager.from_root(ROOT))

        response = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

        names = [tool["name"] for tool in response["result"]["tools"]]
        self.assertIn("hub.list_services", names)
        self.assertIn("hub.get_service_readme", names)
        self.assertIn("hub.get_service_status", names)
        self.assertIn("hub.recommend_server_type", names)

    def test_lists_and_describes_copied_service(self) -> None:
        server = _server_with_fixture("meta-list")

        listed = _call(server, "hub.list_services", {})
        described = _call(server, "hub.describe_service", {"id": "valid-stdio"})

        self.assertEqual(listed["services"][0]["id"], "valid-stdio")
        self.assertEqual(described["status"], "Ready")
        self.assertEqual(
            described["resources"]["capabilities"],
            "hub://services/valid-stdio/capabilities",
        )
        self.assertEqual(described["health"]["state"], "passing")

    def test_returns_capabilities_readme_and_connection(self) -> None:
        server = _server_with_fixture("meta-docs")

        capabilities = _call(server, "hub.get_service_capabilities", {"id": "valid-stdio"})
        readme = _call(server, "hub.get_service_readme", {"id": "valid-stdio"})
        connection = _call(server, "hub.get_service_connection", {"id": "valid-stdio"})

        self.assertIn("Fixture server", capabilities["content"])
        self.assertIn("Valid Stdio Fixture", readme["content"])
        self.assertEqual(connection["connection"]["transport"], "stdio")
        self.assertEqual(connection["connection"]["command"], "uv")
        self.assertIn("does not keep it running", connection["notes"][0])

    def test_resources_expose_service_metadata(self) -> None:
        server = _server_with_fixture("meta-resources")

        listed = server.handle({"jsonrpc": "2.0", "id": 1, "method": "resources/list"})
        uris = [item["uri"] for item in listed["result"]["resources"]]
        readme = _read_resource(server, "hub://services/valid-stdio/readme")
        status = json.loads(_read_resource(server, "hub://services/valid-stdio/status"))

        self.assertIn("hub://services/valid-stdio/capabilities", uris)
        self.assertIn("hub://services/valid-stdio/readme", uris)
        self.assertIn("hub://services/valid-stdio/status", uris)
        self.assertIn("Valid Stdio Fixture", readme)
        self.assertEqual(status["status"], "Ready")

    def test_guideline_tool_returns_content(self) -> None:
        server = MetaServer(HubManager.from_root(ROOT))

        response = server.handle(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "hub.get_guideline", "arguments": {"id": "server-authoring"}},
            }
        )

        text = response["result"]["content"][0]["text"]
        self.assertIn("Server Authoring Guidelines", text)

    def test_lists_and_reads_example_code(self) -> None:
        server = MetaServer(HubManager.from_root(ROOT))

        listing = _call(server, "hub.get_example_code", {"example_id": "python-stdio-fastmcp"})
        source = _call(
            server,
            "hub.get_example_code",
            {
                "example_id": "python-stdio-fastmcp",
                "path": "src/example_memory_server/__main__.py",
            },
        )
        resource = json.loads(
            _read_resource(server, "hub://guidelines/examples/python-stdio-fastmcp")
        )

        self.assertIn("src/example_memory_server/__main__.py", listing["files"])
        self.assertIn("FastMCP", source["content"])
        self.assertIn("README.md", resource["files"])

    def test_recommends_stdio_daemon_or_external(self) -> None:
        server = MetaServer(HubManager.from_root(ROOT))

        stdio = _call(
            server,
            "hub.recommend_server_type",
            {"shared_across_projects": True, "local_only": True, "stores_durable_data": True},
        )
        daemon = _call(
            server,
            "hub.recommend_server_type",
            {"shared_across_projects": True, "needs_long_running_process": True},
        )
        external = _call(
            server,
            "hub.recommend_server_type",
            {
                "shared_across_projects": True,
                "remote_access_required": True,
                "local_only": False,
            },
        )
        no_server = _call(server, "hub.recommend_server_type", {})

        self.assertEqual(stdio["manifest"]["lifecycle"], "command_per_client")
        self.assertEqual(stdio["manifest"]["transport"], "stdio")
        self.assertEqual(daemon["manifest"]["lifecycle"], "daemon")
        self.assertEqual(daemon["manifest"]["transport"], "streamable_http")
        self.assertEqual(external["manifest"]["lifecycle"], "external")
        self.assertEqual(external["manifest"]["transport"], "streamable_http")
        self.assertEqual(no_server["recommendation"], "no_new_server")

    def test_start_service_refuses_command_per_client(self) -> None:
        server = _server_with_fixture("meta-start")

        result = _call(server, "hub.start_service", {"id": "valid-stdio"})

        self.assertEqual(result["status"], "not_applicable")
        self.assertIn("launched by each MCP client", result["message"])


def _server_with_fixture(name: str) -> MetaServer:
    hub_root = _copy_hub_minimum(test_workspace(name))
    copytree(
        FIXTURES / "valid-stdio-server",
        hub_root / "servers" / "valid-stdio-server",
        dirs_exist_ok=True,
    )
    return MetaServer(HubManager.from_root(hub_root))


def _copy_hub_minimum(root: Path) -> Path:
    hub_root = root / "hub"
    hub_root.mkdir(parents=True, exist_ok=True)
    (hub_root / "servers").mkdir(exist_ok=True)
    copytree(ROOT / "guidelines", hub_root / "guidelines", dirs_exist_ok=True)
    (hub_root / "framework.yaml").write_text(
        (ROOT / "framework.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    return hub_root


def _call(server: MetaServer, name: str, arguments: dict[str, object]) -> dict[str, object]:
    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
    )
    return json.loads(response["result"]["content"][0]["text"])


def _read_resource(server: MetaServer, uri: str) -> str:
    response = server.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "resources/read", "params": {"uri": uri}}
    )
    return response["result"]["contents"][0]["text"]


if __name__ == "__main__":
    unittest.main()
