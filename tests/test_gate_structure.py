from __future__ import annotations

import unittest
from pathlib import Path
from shutil import copy2, copytree

from workspace_utils import test_workspace

from gate.config import load_gate_config
from gate.runner import run_gate

ROOT = Path(__file__).resolve().parents[1]


class GateStructureTests(unittest.TestCase):
    def test_absolute_manifest_paths_are_rejected_and_server_copies_are_ignored(self) -> None:
        hub_root = test_workspace("gate-structure") / "hub"
        hub_root.mkdir(parents=True, exist_ok=True)
        copytree(ROOT / "src", hub_root / "src", dirs_exist_ok=True)
        copytree(ROOT / "gate", hub_root / "gate", dirs_exist_ok=True)
        copytree(ROOT / "guidelines", hub_root / "guidelines", dirs_exist_ok=True)
        tests_dir = hub_root / "tests"
        tests_dir.mkdir(exist_ok=True)
        (tests_dir / "test_small.py").write_text(
            "import unittest\n\n\n"
            "class SmallTests(unittest.TestCase):\n"
            "    def test_small(self) -> None:\n"
            "        self.assertTrue(True)\n",
            encoding="utf-8",
        )
        for name in ("README.md", "framework.yaml", "pyproject.toml"):
            copy2(ROOT / name, hub_root / name)

        servers_dir = hub_root / "servers"
        servers_dir.mkdir(exist_ok=True)
        (servers_dir / "README.md").write_text("ok\n", encoding="utf-8")
        (servers_dir / ".gitkeep").write_text("", encoding="utf-8")
        bad_server = servers_dir / "bad"
        bad_server.mkdir(exist_ok=True)
        (bad_server / "mcp-server.yaml").write_text(
            """schema_version: 1
id: bad
name: Bad
version: 0.1.0
enabled: true
lifecycle:
  type: command_per_client
entrypoint:
  type: command
  command: uv
  args: []
  working_directory: C:/abs/path
transport:
  type: stdio
scripts:
  test: scripts/test.ps1
""",
            encoding="utf-8",
        )
        (bad_server / "CAPABILITIES.md").write_text("## Purpose\nx\n", encoding="utf-8")
        (bad_server / "README.md").write_text("x\n", encoding="utf-8")
        (bad_server / "scripts").mkdir(exist_ok=True)
        (bad_server / "scripts" / "test.ps1").write_text("exit 0\n", encoding="utf-8")

        config = load_gate_config(hub_root)
        result = run_gate(config, only={"structure"})

        self.assertFalse(result.passed)
        self.assertEqual(len(result.structure.violations), 1)
        self.assertEqual(result.structure.violations[0].rule_id, "no_absolute_manifest_paths")


if __name__ == "__main__":
    unittest.main()
