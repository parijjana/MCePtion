from __future__ import annotations

import unittest
from pathlib import Path
from shutil import copy2, copytree

from workspace_utils import test_workspace

from gate.config import load_gate_config
from gate.runner import run_gate

ROOT = Path(__file__).resolve().parents[1]


class GateSizeTests(unittest.TestCase):
    def test_markdown_over_limit_warns_but_does_not_fail(self) -> None:
        hub_root = test_workspace("gate-size") / "hub"
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
        docs_dir = hub_root / "docs"
        docs_dir.mkdir(exist_ok=True)
        (docs_dir / "oversized.md").write_text("x\n" * 600, encoding="utf-8")

        config = load_gate_config(hub_root)
        result = run_gate(config, only={"size"})

        self.assertTrue(result.passed)
        self.assertEqual(len(result.size.violations), 0)
        self.assertEqual(len(result.size.warnings), 1)
        self.assertIn(
            "oversized.md", result.to_report(config)["checks"]["size"]["warnings"][0]["path"]
        )


if __name__ == "__main__":
    unittest.main()
