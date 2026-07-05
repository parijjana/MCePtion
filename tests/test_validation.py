from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from shutil import copytree

from workspace_utils import ROOT, test_workspace

from mcp_hub.cli import main
from mcp_hub.validation import validate_server_path

FIXTURES = Path(__file__).parent / "fixtures"


class CopyInValidationTests(unittest.TestCase):
    def test_valid_copied_server_reports_connection_recipe(self) -> None:
        hub_root = _copy_hub_minimum("validation-valid-copied")
        server = _copy_fixture(hub_root, "valid-stdio-server", "valid-copied")

        result = validate_server_path(hub_root, server)

        self.assertTrue(result["valid"])
        self.assertTrue(result["inside_servers_dir"])
        self.assertEqual(result["status"], "Ready")
        self.assertEqual(result["service"]["id"], "valid-stdio")
        self.assertEqual(result["connection"]["transport"], "stdio")
        self.assertTrue(result["connection"]["cwd"].endswith("valid-copied"))
        self.assertIn("Rescan", result["next_actions"][0])

    def test_valid_fixture_outside_servers_dir_is_allowed(self) -> None:
        result = validate_server_path(ROOT, FIXTURES / "valid-stdio-server")

        self.assertTrue(result["valid"])
        self.assertFalse(result["inside_servers_dir"])

    def test_invalid_server_has_actionable_errors_without_connection(self) -> None:
        result = validate_server_path(ROOT, FIXTURES / "invalid-missing-capabilities")

        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "Invalid")
        self.assertIn("CAPABILITIES.md is required.", result["errors"])
        self.assertNotIn("connection", result)
        self.assertEqual(result["next_actions"], ["Fix the listed errors and rerun validation."])

    def test_missing_readme_is_invalid(self) -> None:
        hub_root = _copy_hub_minimum("validation-missing-readme")
        server = _copy_fixture(hub_root, "valid-stdio-server", "missing-readme")
        (server / "README.md").unlink(missing_ok=True)

        result = validate_server_path(hub_root, server)

        self.assertIn("README.md is required.", result["errors"])

    def test_missing_script_paths_are_invalid(self) -> None:
        hub_root = _copy_hub_minimum("validation-missing-script")
        server = _copy_fixture(hub_root, "valid-stdio-server", "missing-script")
        (server / "scripts" / "test.ps1").unlink(missing_ok=True)

        result = validate_server_path(hub_root, server)

        self.assertIn("scripts.test does not exist: scripts/test.ps1", result["errors"])

    def test_absolute_manifest_paths_are_invalid(self) -> None:
        hub_root = _copy_hub_minimum("validation-absolute-paths")
        server = _copy_fixture(hub_root, "valid-stdio-server", "absolute-paths")
        manifest = server / "mcp-server.yaml"
        text = manifest.read_text(encoding="utf-8")
        text = text.replace("  start: scripts/start.ps1", "  start: C:/tools/start.ps1")
        text = text.replace("  working_directory: .", "  working_directory: C:/tools/server")
        manifest.write_text(text, encoding="utf-8")

        result = validate_server_path(hub_root, server)

        self.assertIn("scripts.start must be relative to the service root.", result["errors"])
        self.assertIn(
            "entrypoint.working_directory must be relative to the service root.",
            result["errors"],
        )

    def test_cli_exits_zero_for_valid_server(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main(
                [
                    "--root",
                    str(ROOT),
                    "validate-server",
                    str(FIXTURES / "valid-stdio-server"),
                ]
            )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["valid"])

    def test_cli_exits_one_for_invalid_server(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main(
                [
                    "--root",
                    str(ROOT),
                    "validate-server",
                    str(FIXTURES / "invalid-missing-capabilities"),
                ]
            )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertIn("CAPABILITIES.md is required.", payload["errors"])


def _copy_hub_minimum(name: str) -> Path:
    hub_root = test_workspace(name) / "hub"
    hub_root.mkdir(parents=True, exist_ok=True)
    (hub_root / "servers").mkdir(exist_ok=True)
    (hub_root / "framework.yaml").write_text(
        (ROOT / "framework.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    return hub_root


def _copy_fixture(hub_root: Path, fixture_name: str, workspace_name: str) -> Path:
    server = hub_root / "servers" / f"test-validation-{workspace_name}"
    copytree(FIXTURES / fixture_name, server, dirs_exist_ok=True)
    return server


if __name__ == "__main__":
    unittest.main()
