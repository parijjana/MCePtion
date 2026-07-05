from __future__ import annotations

import unittest
from pathlib import Path
from shutil import copytree

from workspace_utils import test_workspace

from mcp_hub.manager import HubManager

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


class ManagerTests(unittest.TestCase):
    def test_lists_copied_server(self) -> None:
        hub_root = _copy_hub_minimum(test_workspace("manager-list"))
        copytree(
            FIXTURES / "valid-stdio-server",
            hub_root / "servers" / "valid-stdio-server",
            dirs_exist_ok=True,
        )

        manager = HubManager.from_root(hub_root)
        services = manager.list_services()

        self.assertEqual(len(services), 1)
        self.assertEqual(services[0]["id"], "valid-stdio")
        self.assertEqual(services[0]["status"], "Ready")

    def test_command_per_client_start_is_not_applicable(self) -> None:
        hub_root = _copy_hub_minimum(test_workspace("manager-start"))
        copytree(
            FIXTURES / "valid-stdio-server",
            hub_root / "servers" / "valid-stdio-server",
            dirs_exist_ok=True,
        )

        manager = HubManager.from_root(hub_root)
        result = manager.start_service("valid-stdio")

        self.assertEqual(result["status"], "not_applicable")

    def test_reads_guideline_through_manager(self) -> None:
        manager = HubManager.from_root(ROOT)

        content = manager.get_guideline("server-authoring")

        self.assertIn("Default Choice", content)


def _copy_hub_minimum(root: Path) -> Path:
    hub_root = root / "hub"
    hub_root.mkdir(parents=True, exist_ok=True)
    (hub_root / "servers").mkdir(exist_ok=True)
    copytree(ROOT / "guidelines", hub_root / "guidelines", dirs_exist_ok=True)
    (hub_root / "framework.yaml").write_text(
        (ROOT / "framework.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    return hub_root


if __name__ == "__main__":
    unittest.main()
