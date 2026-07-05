from __future__ import annotations

import unittest
from pathlib import Path
from shutil import copy2, copytree

from workspace_utils import test_workspace

from gate.config import load_gate_config

ROOT = Path(__file__).resolve().parents[1]


class GateConfigTests(unittest.TestCase):
    def test_loads_expected_toggles(self) -> None:
        config = load_gate_config(ROOT)

        self.assertEqual(config.schema_version, 1)
        self.assertTrue(config.analysis.ruff.enabled)
        self.assertFalse(config.analysis.mypy.enabled)
        self.assertFalse(config.coverage.measure)
        self.assertTrue(config.size.markdown.warn_only)
        self.assertFalse(config.ci.enabled)
        self.assertFalse(config.metrics.enabled)

    def test_print_config_requires_gate_yaml(self) -> None:
        hub_root = test_workspace("gate-config") / "hub"
        hub_root.mkdir(parents=True, exist_ok=True)
        copytree(ROOT / "src", hub_root / "src", dirs_exist_ok=True)
        copytree(ROOT / "gate", hub_root / "gate", dirs_exist_ok=True)
        copytree(ROOT / "guidelines", hub_root / "guidelines", dirs_exist_ok=True)
        copytree(ROOT / "tests", hub_root / "tests", dirs_exist_ok=True)
        for name in ("README.md", "framework.yaml", "pyproject.toml"):
            copy2(ROOT / name, hub_root / name)

        config = load_gate_config(hub_root)

        self.assertEqual(config.output.report_path.name, "gate_report.json")


if __name__ == "__main__":
    unittest.main()
