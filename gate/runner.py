from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from mcp_hub.simple_yaml import SimpleYamlError, load_yaml

from .config import GateConfig, GateConfigError, load_gate_config


@dataclass
class AnalysisToolResult:
    tool: str
    errors: int
    warnings: int
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    raw_output: str = ""


@dataclass
class SizeViolation:
    kind: str
    path: str
    current: int
    limit: int
    message: str


@dataclass
class StructureViolation:
    rule_id: str
    path: str
    message: str


@dataclass
class TestFailure:
    test_name: str
    first_line: str


@dataclass
class AnalysisResult:
    enabled: bool
    errors: int = 0
    warnings: int = 0
    tool_results: list[AnalysisToolResult] = field(default_factory=list)


@dataclass
class SizeResult:
    enabled: bool
    violations: list[SizeViolation] = field(default_factory=list)
    warnings: list[SizeViolation] = field(default_factory=list)


@dataclass
class StructureResult:
    enabled: bool
    violations: list[StructureViolation] = field(default_factory=list)


@dataclass
class TestResult:
    enabled: bool
    passed: int = 0
    total: int = 0
    failures: list[TestFailure] = field(default_factory=list)
    raw_output: str = ""
    exit_code: int = 0


@dataclass
class CoverageResult:
    enabled: bool
    percent: int | None = None
    gated: bool = False
    measured: bool = False


@dataclass
class GateResult:
    schema_version: int
    passed: bool
    sha: str
    analysis: AnalysisResult
    size: SizeResult
    structure: StructureResult
    tests: TestResult
    coverage: CoverageResult
    wall_secs: float
    config_error: str | None = None

    def summary_line(self) -> str:
        cov = "n/a" if self.coverage.percent is None else str(self.coverage.percent)
        size_count = len(self.size.violations)
        return (
            f"GATE {'PASS' if self.passed else 'FAIL'}  sha={self.sha}  "
            f"tests={self.tests.passed}/{self.tests.total}  "
            f"analysis={self.analysis.errors}E/{self.analysis.warnings}W  "
            f"size={size_count}  "
            f"struct={len(self.structure.violations)}  cov={cov}%"
        )

    def failure_lines(self, limit: int) -> list[str]:
        lines = [f"GATE FAIL  sha={self.sha}"]
        lines.extend(_cap_lines(_analysis_lines(self.analysis), limit))
        lines.extend(_cap_lines(_size_lines(self.size), limit))
        lines.extend(_cap_lines(_structure_lines(self.structure), limit))
        lines.extend(_cap_test_lines(self.tests.failures, limit))
        return lines

    def to_report(self, config: GateConfig) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "pass": self.passed,
            "sha": self.sha,
            "checks": {
                "analysis": {
                    "enabled": self.analysis.enabled,
                    "errors": self.analysis.errors,
                    "warnings": self.analysis.warnings,
                    "tool_results": [
                        {
                            "tool": item.tool,
                            "errors": item.errors,
                            "warnings": item.warnings,
                            "diagnostics": item.diagnostics[:15],
                            "raw_output": _truncate(item.raw_output, 2048),
                        }
                        for item in self.analysis.tool_results
                    ],
                },
                "size": {
                    "enabled": self.size.enabled,
                    "violations": [
                        {
                            "kind": item.kind,
                            "path": item.path,
                            "current": item.current,
                            "limit": item.limit,
                            "message": item.message,
                        }
                        for item in self.size.violations[:15]
                    ],
                    "warnings": [
                        {
                            "kind": item.kind,
                            "path": item.path,
                            "current": item.current,
                            "limit": item.limit,
                            "message": item.message,
                        }
                        for item in self.size.warnings[:15]
                    ],
                },
                "structure": {
                    "enabled": self.structure.enabled,
                    "violations": [
                        {"rule_id": item.rule_id, "path": item.path, "message": item.message}
                        for item in self.structure.violations[:15]
                    ],
                },
                "tests": {
                    "enabled": self.tests.enabled,
                    "passed": self.tests.passed,
                    "total": self.tests.total,
                    "failures": [
                        {"test_name": item.test_name, "first_line": item.first_line}
                        for item in self.tests.failures[:15]
                    ],
                    "raw_output": _truncate(self.tests.raw_output, 4096),
                },
                "coverage": {
                    "enabled": self.coverage.enabled,
                    "percent": self.coverage.percent,
                    "gated": self.coverage.gated,
                    "measured": self.coverage.measured,
                },
            },
            "wall_secs": round(self.wall_secs, 3),
            "config": {
                "report_path": str(config.output.report_path),
                "summary_path": str(config.output.summary_path),
            },
        }


def load_and_run(
    root: Path, only: set[str] | None, ci: bool, print_config: bool
) -> tuple[GateConfig | None, GateResult | None, str | None]:
    try:
        config = load_gate_config(root)
    except GateConfigError as exc:
        return None, None, f"[config] {exc}"
    if print_config:
        result = _empty_result(config, root)
        _write_report(config, result)
        return config, result, f"GATE CONFIG OK  schema={config.schema_version}"
    result = run_gate(config, only=only, ci=ci)
    _write_report(config, result)
    if ci:
        _write_summary(config, result)
    return config, result, None


def run_gate(config: GateConfig, only: set[str] | None = None, ci: bool = False) -> GateResult:
    start = time.perf_counter()
    selected = only or {"analysis", "size", "structure", "tests", "coverage"}
    analysis = (
        _run_analysis(config)
        if "analysis" in selected
        else AnalysisResult(enabled=config.analysis.ruff.enabled)
    )
    size = (
        _run_size(config)
        if "size" in selected
        else SizeResult(enabled=config.size.python.enabled or config.size.markdown.enabled)
    )
    structure = (
        _run_structure(config)
        if "structure" in selected
        else StructureResult(enabled=config.structure.enabled)
    )
    tests = (
        _run_tests(config)
        if "tests" in selected
        else TestResult(enabled=config.tests.unittest.enabled)
    )
    coverage = (
        _run_coverage(config)
        if "coverage" in selected
        else CoverageResult(enabled=config.coverage.enabled)
    )
    sha = _git_sha(config.root)
    passed = (
        (
            not config.analysis.ruff.enabled
            or not config.analysis.ruff.gate
            or analysis.errors <= config.analysis.ruff.max_errors
        )
        and (
            not config.analysis.ruff.enabled
            or not config.analysis.ruff.gate
            or analysis.warnings <= config.analysis.ruff.max_warnings
        )
        and (
            not config.size.python.enabled
            or not config.size.python.gate
            or not [item for item in size.violations if item.kind == "python"]
        )
        and (
            not config.size.markdown.enabled
            or not config.size.markdown.gate
            or not [item for item in size.violations if item.kind == "markdown"]
        )
        and (not config.structure.enabled or not config.structure.gate or not structure.violations)
        and (
            not config.tests.unittest.enabled
            or not config.tests.unittest.gate
            or (tests.exit_code == 0 and not tests.failures)
        )
        and (
            not config.coverage.enabled
            or not config.coverage.gate
            or not coverage.measured
            or coverage.percent is None
            or coverage.percent >= (config.coverage.min_percent or 0)
        )
    )
    return GateResult(
        schema_version=1,
        passed=passed,
        sha=sha,
        analysis=analysis,
        size=size,
        structure=structure,
        tests=tests,
        coverage=coverage,
        wall_secs=time.perf_counter() - start,
    )


def _empty_result(config: GateConfig, root: Path) -> GateResult:
    return GateResult(
        schema_version=1,
        passed=True,
        sha=_git_sha(root),
        analysis=AnalysisResult(enabled=config.analysis.ruff.enabled),
        size=SizeResult(enabled=config.size.python.enabled or config.size.markdown.enabled),
        structure=StructureResult(enabled=config.structure.enabled),
        tests=TestResult(enabled=config.tests.unittest.enabled),
        coverage=CoverageResult(enabled=config.coverage.enabled),
        wall_secs=0.0,
    )


def _run_analysis(config: GateConfig) -> AnalysisResult:
    result = AnalysisResult(enabled=config.analysis.ruff.enabled)
    if not config.analysis.ruff.enabled:
        return result
    command = ["ruff", "check", "--no-cache", "--output-format=json", *_analysis_paths(config)]
    try:
        completed = subprocess.run(
            command, cwd=config.root, capture_output=True, text=True, check=False
        )
    except FileNotFoundError as exc:
        raise GateConfigError(
            "Ruff command is missing. Install the project dev dependency and rerun the gate."
        ) from exc
    diagnostics = _parse_json_output(completed.stdout)
    errors = 0
    warnings = 0
    normalized: list[dict[str, Any]] = []
    for item in diagnostics:
        severity = str(item.get("severity", "error")).lower()
        if severity == "warning":
            warnings += 1
        else:
            errors += 1
        normalized.append(
            {
                "code": item.get("code", ""),
                "message": item.get("message", ""),
                "filename": str(item.get("filename", "")),
                "location": item.get("location", {}),
                "severity": severity,
            }
        )
    if completed.returncode != 0 and not normalized:
        normalized.append(
            {
                "code": "RUF000",
                "message": _first_nonempty_line(
                    (completed.stderr or completed.stdout or "").splitlines()
                )
                or "ruff exited with an error.",
                "filename": "",
                "location": {},
                "severity": "error",
            }
        )
        errors = 1
    result.errors = errors
    result.warnings = warnings
    result.tool_results.append(
        AnalysisToolResult(
            tool="ruff",
            errors=errors,
            warnings=warnings,
            diagnostics=normalized[:15],
            raw_output=_truncate((completed.stdout or "") + (completed.stderr or ""), 4096),
        )
    )
    return result


def _analysis_paths(config: GateConfig) -> list[str]:
    paths = config.paths.source + config.paths.tests
    return [path for path in paths if (config.root / path).exists()]


def _run_size(config: GateConfig) -> SizeResult:
    result = SizeResult(enabled=config.size.python.enabled or config.size.markdown.enabled)
    baseline = _load_baseline(config)
    if config.size.python.enabled:
        for path in _python_files(config):
            current = len(path.read_text(encoding="utf-8").splitlines())
            rel = path.relative_to(config.root).as_posix()
            limit = baseline.get(rel, config.size.python.max_file_lines)
            if current > limit:
                result.violations.append(
                    SizeViolation("python", rel, current, limit, f"{rel} {current} > {limit}")
                )
            result.violations.extend(_function_size_violations(config, path))
    if config.size.markdown.enabled:
        for path in _markdown_files(config):
            current = len(path.read_text(encoding="utf-8").splitlines())
            rel = path.relative_to(config.root).as_posix()
            if current > config.size.markdown.max_file_lines:
                violation = SizeViolation(
                    "markdown",
                    rel,
                    current,
                    config.size.markdown.max_file_lines,
                    f"{rel} {current} > {config.size.markdown.max_file_lines}",
                )
                if config.size.markdown.gate and not config.size.markdown.warn_only:
                    result.violations.append(violation)
                else:
                    result.warnings.append(violation)
    return result


def _python_files(config: GateConfig) -> list[Path]:
    files: list[Path] = []
    for rel in config.paths.source + config.paths.tests:
        root = config.root / rel
        if root.is_file() and root.suffix == ".py" and not _excluded(root, config):
            files.append(root)
        elif root.is_dir():
            files.extend(path for path in root.rglob("*.py") if not _excluded(path, config))
    return sorted(dict.fromkeys(files))


def _markdown_files(config: GateConfig) -> list[Path]:
    files: list[Path] = []
    for rel in config.paths.docs:
        root = config.root / rel
        if root.is_file() and root.suffix.lower() == ".md" and not _excluded(root, config):
            files.append(root)
        elif root.is_dir():
            files.extend(path for path in root.rglob("*.md") if not _excluded(path, config))
    return sorted(dict.fromkeys(files))


def _load_baseline(config: GateConfig) -> dict[str, int]:
    if not config.baseline_path.exists():
        return {}
    try:
        data = json.loads(config.baseline_path.read_text(encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    baseline: dict[str, int] = {}
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, int):
            baseline[key] = value
    return baseline


def _function_size_violations(config: GateConfig, path: Path) -> list[SizeViolation]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        rel = path.relative_to(config.root).as_posix()
        return [
            SizeViolation(
                "python",
                rel,
                0,
                config.size.python.max_function_statements,
                f"{rel}: syntax error {exc.msg}",
            )
        ]
    violations: list[SizeViolation] = []
    rel = path.relative_to(config.root).as_posix()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            count = _statement_count(node.body)
            if count > config.size.python.max_function_statements:
                violations.append(
                    SizeViolation(
                        "python",
                        rel,
                        count,
                        config.size.python.max_function_statements,
                        f"{rel}:{node.name} {count} > {config.size.python.max_function_statements}",
                    )
                )
    return violations


def _statement_count(body: list[ast.stmt]) -> int:
    return len(body)


def _run_structure(config: GateConfig) -> StructureResult:
    result = StructureResult(enabled=config.structure.enabled)
    if not config.structure.enabled:
        return result
    rule = config.structure.rules.get("no_absolute_manifest_paths")
    if rule and rule.enabled:
        for manifest in _manifests(config):
            try:
                data = load_yaml(manifest)
            except (OSError, SimpleYamlError) as exc:
                rel = manifest.relative_to(config.root).as_posix()
                result.violations.append(
                    StructureViolation(
                        "no_absolute_manifest_paths", rel, f"Manifest could not be parsed: {exc}"
                    )
                )
                continue
            rel = manifest.relative_to(config.root).as_posix()
            for field in (
                ("scripts", "start"),
                ("scripts", "stop"),
                ("scripts", "test"),
                ("entrypoint", "working_directory"),
            ):
                value = _nested(data, *field)
                if isinstance(value, str) and Path(value).is_absolute():
                    result.violations.append(
                        StructureViolation(
                            "no_absolute_manifest_paths",
                            rel,
                            f"{'.'.join(field)} must be relative.",
                        )
                    )
    return result


def _manifests(config: GateConfig) -> list[Path]:
    return sorted(
        path
        for path in config.root.rglob("mcp-server.yaml")
        if not _is_generated_or_runtime_path(path, config)
    )


def _is_generated_or_runtime_path(path: Path, config: GateConfig) -> bool:
    rel = path.relative_to(config.root).as_posix()
    rule = config.structure.rules.get("no_generated_artifacts")
    if not rule or not rule.enabled or not rule.patterns:
        return False
    return any(_matches_runtime_pattern(rel, pattern) for pattern in rule.patterns)


def _matches_runtime_pattern(rel: str, pattern: str) -> bool:
    normalized = pattern.replace("\\", "/")
    if normalized.endswith("/"):
        prefix = normalized.rstrip("/") + "/"
        return rel.startswith(prefix) or f"/{prefix}" in rel
    return fnmatch(rel, normalized) or fnmatch(Path(rel).name, normalized)


def _run_tests(config: GateConfig) -> TestResult:
    result = TestResult(enabled=config.tests.unittest.enabled)
    if not config.tests.unittest.enabled:
        return result
    command = _python_command(config.tests.unittest.command)
    try:
        completed = subprocess.run(
            command, cwd=config.root, capture_output=True, text=True, check=False
        )
    except FileNotFoundError as exc:
        raise GateConfigError("Test command is missing from gate config.") from exc
    combined = (completed.stdout or "") + (completed.stderr or "")
    result.raw_output = _truncate(combined, 4096)
    result.exit_code = completed.returncode
    total = _parse_total_tests(combined)
    failures = _parse_test_failures(combined)
    if completed.returncode != 0 and not failures:
        failures.append(
            TestFailure(
                "unittest", _first_nonempty_line(combined.splitlines()) or "test command failed."
            )
        )
    result.total = total
    result.failures = failures
    result.passed = max(total - len(failures), 0)
    return result


def _python_command(command: list[str]) -> list[str]:
    if command and command[0] in {"python", "python.exe"}:
        return [sys.executable, *command[1:]]
    return command


def _run_coverage(config: GateConfig) -> CoverageResult:
    return CoverageResult(
        enabled=config.coverage.enabled, percent=None, gated=config.coverage.gate, measured=False
    )


def _parse_total_tests(text: str) -> int:
    match = re.search(r"Ran (\d+) tests?", text)
    return int(match.group(1)) if match else 0


def _parse_test_failures(text: str) -> list[TestFailure]:
    failures: list[TestFailure] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith(("FAIL:", "ERROR:")):
            name = line.split(":", 1)[1].strip()
            block: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].startswith(
                ("FAIL:", "ERROR:", "Ran ", "OK", "FAILED (", "==")
            ):
                if lines[index].strip():
                    block.append(lines[index].rstrip())
                index += 1
            failures.append(TestFailure(name, _first_meaningful_line(block)))
            continue
        index += 1
    return failures


def _first_meaningful_line(block: list[str]) -> str:
    for line in reversed(block):
        stripped = line.strip()
        if stripped and not stripped.startswith("Traceback") and not stripped.startswith("File "):
            return stripped
    return block[-1].strip() if block else "Test failed."


def _first_nonempty_line(lines: list[str]) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _analysis_lines(result: AnalysisResult) -> list[str]:
    lines: list[str] = []
    for item in result.tool_results:
        for diagnostic in item.diagnostics:
            filename = diagnostic.get("filename", "")
            code = diagnostic.get("code", "")
            message = diagnostic.get("message", "")
            lines.append(f"[G1 analysis] {filename} {code} {message}".rstrip())
    return lines


def _size_lines(result: SizeResult) -> list[str]:
    lines = [f"[G2 size] {item.message}" for item in result.violations]
    return lines


def _structure_lines(result: StructureResult) -> list[str]:
    return [f"[G3 struct] {item.path} {item.rule_id} {item.message}" for item in result.violations]


def _test_lines(failures: list[TestFailure]) -> list[str]:
    lines: list[str] = []
    for item in failures:
        lines.append(f"[G4 test] {item.test_name}")
        lines.append(f"          {item.first_line}")
    return lines


def _cap_lines(lines: list[str], limit: int) -> list[str]:
    if len(lines) <= limit:
        return lines
    return lines[:limit] + [f"(+{len(lines) - limit} more)"]


def _cap_test_lines(failures: list[TestFailure], limit: int) -> list[str]:
    if len(failures) <= limit:
        return _test_lines(failures)
    return _test_lines(failures[:limit]) + [f"(+{len(failures) - limit} more)"]


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 12] + "[truncated]"


def _excluded(path: Path, config: GateConfig) -> bool:
    rel = path.relative_to(config.root).as_posix()
    allowed = True
    for pattern in config.paths.exclude:
        negate = pattern.startswith("!")
        pattern_text = pattern[1:] if negate else pattern
        if fnmatch(rel, pattern_text):
            allowed = negate
    return not allowed


def _nested(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _git_sha(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return (
        completed.stdout.strip()
        if completed.returncode == 0 and completed.stdout.strip()
        else "none"
    )


def _parse_json_output(text: str) -> list[dict[str, Any]]:
    data = text.strip()
    if not data:
        return []
    try:
        loaded = json.loads(data)
    except json.JSONDecodeError:
        return []
    return loaded if isinstance(loaded, list) else []


def _write_report(config: GateConfig, result: GateResult) -> None:
    config.output.report_path.parent.mkdir(parents=True, exist_ok=True)
    config.output.report_path.write_text(
        json.dumps(result.to_report(config), indent=2), encoding="utf-8"
    )


def _write_summary(config: GateConfig, result: GateResult) -> None:
    config.output.summary_path.parent.mkdir(parents=True, exist_ok=True)
    config.output.summary_path.write_text(f"# {result.summary_line()}\n", encoding="utf-8")
