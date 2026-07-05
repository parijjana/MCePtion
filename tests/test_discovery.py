from __future__ import annotations

import unittest
from pathlib import Path
from shutil import copytree

from workspace_utils import test_workspace

from mcp_hub.discovery import connection_recipe, discover_services, load_service

FIXTURES = Path(__file__).parent / "fixtures"


class DiscoveryTests(unittest.TestCase):
    def test_valid_stdio_server_is_ready(self) -> None:
        service = load_service(FIXTURES / "valid-stdio-server" / "mcp-server.yaml")

        self.assertTrue(service.valid)
        self.assertEqual(service.lifecycle, "command_per_client")
        self.assertEqual(service.transport, "stdio")
        self.assertEqual(service.status, "Ready")

    def test_connection_recipe_uses_service_root_as_cwd(self) -> None:
        service = load_service(FIXTURES / "valid-stdio-server" / "mcp-server.yaml")

        recipe = connection_recipe(service)

        self.assertEqual(recipe["transport"], "stdio")
        self.assertEqual(recipe["command"], "uv")
        self.assertEqual(recipe["args"], ["run", "python", "-m", "valid_stdio"])
        self.assertTrue(recipe["cwd"].endswith("valid-stdio-server"))

    def test_missing_capabilities_is_invalid(self) -> None:
        service = load_service(FIXTURES / "invalid-missing-capabilities" / "mcp-server.yaml")

        self.assertFalse(service.valid)
        self.assertIn("CAPABILITIES.md is required.", service.validation.errors)
        self.assertEqual(service.status, "Invalid")

    def test_duplicate_ids_are_invalid(self) -> None:
        root = test_workspace("discovery-duplicate-ids")
        copytree(FIXTURES / "valid-stdio-server", root / "one", dirs_exist_ok=True)
        copytree(FIXTURES / "valid-stdio-server", root / "two", dirs_exist_ok=True)

        services = discover_services(root)

        invalid = [service for service in services if not service.valid]
        self.assertEqual(len(invalid), 1)
        self.assertIn("Duplicate service id", invalid[0].validation.errors[0])


if __name__ == "__main__":
    unittest.main()
