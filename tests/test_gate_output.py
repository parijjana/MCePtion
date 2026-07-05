from __future__ import annotations

import unittest
from pathlib import Path

from workspace_utils import test_workspace

from gate.config import load_gate_config
from gate.runner import (
    AnalysisResult,
    CoverageResult,
    GateResult,
    SizeResult,
    StructureResult,
    TestResult,
    _write_report,
    _write_summary,
)

ROOT = Path(__file__).resolve().parents[1]


class GateOutputTests(unittest.TestCase):
    def test_summary_line_matches_contract(self) -> None:
        config = load_gate_config(ROOT)
        result = GateResult(
            schema_version=1,
            passed=True,
            sha="none",
            analysis=AnalysisResult(enabled=True, errors=0, warnings=0),
            size=SizeResult(enabled=True),
            structure=StructureResult(enabled=True),
            tests=TestResult(enabled=True, passed=14, total=14),
            coverage=CoverageResult(enabled=False),
            wall_secs=0.1,
        )

        self.assertEqual(
            result.summary_line(),
            "GATE PASS  sha=none  tests=14/14  analysis=0E/0W  size=0  struct=0  cov=n/a%",
        )
        self.assertEqual(config.output.failure_limit_per_category, 15)

    def test_report_is_written_for_ci_runs(self) -> None:
        hub_root = test_workspace("gate-output") / "hub"
        hub_root.mkdir(parents=True, exist_ok=True)
        (hub_root / "gate").mkdir(exist_ok=True)
        (hub_root / "gate" / "gate.yaml").write_text(
            (ROOT / "gate" / "gate.yaml").read_text(encoding="utf-8"), encoding="utf-8"
        )
        config = load_gate_config(hub_root)
        result = GateResult(
            schema_version=1,
            passed=True,
            sha="none",
            analysis=AnalysisResult(enabled=True),
            size=SizeResult(enabled=True),
            structure=StructureResult(enabled=True),
            tests=TestResult(enabled=True, passed=1, total=1),
            coverage=CoverageResult(enabled=False),
            wall_secs=0.1,
        )
        _write_report(config, result)
        _write_summary(config, result)

        self.assertTrue((hub_root / "gate_report.json").exists())
        self.assertTrue((hub_root / "gate_summary.md").exists())
        self.assertIn("GATE PASS", (hub_root / "gate_summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
