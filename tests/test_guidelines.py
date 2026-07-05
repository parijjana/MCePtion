from __future__ import annotations

import unittest
from pathlib import Path

from mcp_hub.guidelines import (
    get_example_file,
    get_guideline,
    list_example_files,
    list_guidelines,
    recommend_server_type,
)

ROOT = Path(__file__).resolve().parents[1]


class GuidelinesTests(unittest.TestCase):
    def test_lists_guidelines_and_examples(self) -> None:
        result = list_guidelines(ROOT / "guidelines", ROOT / "guidelines" / "examples")

        self.assertEqual(result["guidelines"][0]["id"], "server-authoring")
        self.assertIn("python-stdio-fastmcp", [example["id"] for example in result["examples"]])

    def test_reads_server_authoring_guideline(self) -> None:
        content = get_guideline(ROOT / "guidelines", "server-authoring")

        self.assertIn("Prefer a local stdio MCP server", content)

    def test_recommends_stdio_for_local_durable_shared_capability(self) -> None:
        result = recommend_server_type(
            {
                "shared_across_projects": True,
                "stores_durable_data": True,
                "needs_long_running_process": False,
                "needs_multiple_simultaneous_clients": False,
                "needs_browser_ui": False,
                "remote_access_required": False,
            }
        )

        self.assertEqual(result["recommendation"], "local_stdio_command_per_client")
        self.assertEqual(result["manifest"]["transport"], "stdio")

    def test_reads_example_code(self) -> None:
        files = list_example_files(ROOT / "guidelines" / "examples", "python-stdio-fastmcp")
        content = get_example_file(
            ROOT / "guidelines" / "examples",
            "python-stdio-fastmcp",
            "src/example_memory_server/__main__.py",
        )

        self.assertIn("src/example_memory_server/__main__.py", files)
        self.assertIn("FastMCP", content)


if __name__ == "__main__":
    unittest.main()
