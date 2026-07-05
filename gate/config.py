from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp_hub.simple_yaml import SimpleYamlError, load_yaml


class GateConfigError(ValueError):
    pass


@dataclass(frozen=True)
class OutputConfig:
    success_one_line: bool
    failure_limit_per_category: int
    report_path: Path
    summary_path: Path


@dataclass(frozen=True)
class ToolchainConfig:
    python: str
    uv_required: bool


@dataclass(frozen=True)
class PathsConfig:
    source: list[str]
    tests: list[str]
    docs: list[str]
    include: list[str]
    exclude: list[str]


@dataclass(frozen=True)
class RuffConfig:
    enabled: bool
    gate: bool
    max_errors: int
    max_warnings: int


@dataclass(frozen=True)
class MyPyConfig:
    enabled: bool
    gate: bool
    strict: bool
    scenario: str


@dataclass(frozen=True)
class AnalysisConfig:
    ruff: RuffConfig
    mypy: MyPyConfig


@dataclass(frozen=True)
class PythonSizeConfig:
    enabled: bool
    gate: bool
    max_file_lines: int
    max_function_statements: int
    baseline_path: Path


@dataclass(frozen=True)
class MarkdownSizeConfig:
    enabled: bool
    gate: bool
    warn_only: bool
    max_file_lines: int
    scenario: str


@dataclass(frozen=True)
class SizeConfig:
    python: PythonSizeConfig
    markdown: MarkdownSizeConfig


@dataclass(frozen=True)
class StructureRuleConfig:
    enabled: bool
    patterns: list[str] | None = None
    allowed: list[str] | None = None
    manifest_glob: str | None = None


@dataclass(frozen=True)
class StructureConfig:
    enabled: bool
    gate: bool
    rules: dict[str, StructureRuleConfig]


@dataclass(frozen=True)
class UnittestConfig:
    enabled: bool
    gate: bool
    command: list[str]


@dataclass(frozen=True)
class TestsConfig:
    unittest: UnittestConfig


@dataclass(frozen=True)
class CoverageConfig:
    enabled: bool
    measure: bool
    gate: bool
    min_percent: int | None
    scenario: str


@dataclass(frozen=True)
class CiConfig:
    enabled: bool
    workflow_enabled: bool
    scenario: str


@dataclass(frozen=True)
class MetricsConfig:
    enabled: bool
    append_history: bool
    branch: str
    scenario: str


@dataclass(frozen=True)
class GateConfig:
    root: Path
    schema_version: int
    output: OutputConfig
    toolchain: ToolchainConfig
    paths: PathsConfig
    analysis: AnalysisConfig
    size: SizeConfig
    structure: StructureConfig
    tests: TestsConfig
    coverage: CoverageConfig
    ci: CiConfig
    metrics: MetricsConfig
    source_path: Path

    @property
    def baseline_path(self) -> Path:
        return self.root / self.size.python.baseline_path


def load_gate_config(root: Path | None = None) -> GateConfig:
    hub_root = (root or Path.cwd()).resolve()
    config_path = hub_root / "gate" / "gate.yaml"
    try:
        data = load_yaml(config_path)
    except FileNotFoundError as exc:
        raise GateConfigError(f"Missing gate config: {config_path}") from exc
    except (OSError, SimpleYamlError) as exc:
        raise GateConfigError(f"Invalid gate config: {exc}") from exc
    if data.get("schema_version") != 1:
        raise GateConfigError("schema_version must be 1.")

    return GateConfig(
        root=hub_root,
        schema_version=1,
        output=OutputConfig(
            success_one_line=_bool(_section(data, "output"), "success_one_line", True),
            failure_limit_per_category=_int(
                _section(data, "output"), "failure_limit_per_category", 15
            ),
            report_path=hub_root
            / _path_text(_section(data, "output"), "report_path", "gate_report.json"),
            summary_path=hub_root
            / _path_text(_section(data, "output"), "summary_path", "gate_summary.md"),
        ),
        toolchain=ToolchainConfig(
            python=_text(_section(data, "toolchain"), "python", "3.14"),
            uv_required=_bool(_section(data, "toolchain"), "uv_required", True),
        ),
        paths=PathsConfig(
            source=_list_of_str(_section(data, "paths"), "source"),
            tests=_list_of_str(_section(data, "paths"), "tests"),
            docs=_list_of_str(_section(data, "paths"), "docs"),
            include=_list_of_str(_section(data, "paths"), "include"),
            exclude=_list_of_str(_section(data, "paths"), "exclude"),
        ),
        analysis=AnalysisConfig(
            ruff=RuffConfig(
                enabled=_bool(_section(_section(data, "analysis"), "ruff"), "enabled", True),
                gate=_bool(_section(_section(data, "analysis"), "ruff"), "gate", True),
                max_errors=_int(_section(_section(data, "analysis"), "ruff"), "max_errors", 0),
                max_warnings=_int(_section(_section(data, "analysis"), "ruff"), "max_warnings", 0),
            ),
            mypy=MyPyConfig(
                enabled=_bool(_section(_section(data, "analysis"), "mypy"), "enabled", False),
                gate=_bool(_section(_section(data, "analysis"), "mypy"), "gate", False),
                strict=_bool(_section(_section(data, "analysis"), "mypy"), "strict", False),
                scenario=_text(_section(_section(data, "analysis"), "mypy"), "scenario", ""),
            ),
        ),
        size=SizeConfig(
            python=PythonSizeConfig(
                enabled=_bool(_section(_section(data, "size"), "python"), "enabled", True),
                gate=_bool(_section(_section(data, "size"), "python"), "gate", True),
                max_file_lines=_int(
                    _section(_section(data, "size"), "python"), "max_file_lines", 300
                ),
                max_function_statements=_int(
                    _section(_section(data, "size"), "python"), "max_function_statements", 40
                ),
                baseline_path=Path(
                    _path_text(
                        _section(_section(data, "size"), "python"),
                        "baseline_path",
                        "gate/size-baseline.json",
                    )
                ),
            ),
            markdown=MarkdownSizeConfig(
                enabled=_bool(_section(_section(data, "size"), "markdown"), "enabled", True),
                gate=_bool(_section(_section(data, "size"), "markdown"), "gate", False),
                warn_only=_bool(_section(_section(data, "size"), "markdown"), "warn_only", True),
                max_file_lines=_int(
                    _section(_section(data, "size"), "markdown"), "max_file_lines", 500
                ),
                scenario=_text(_section(_section(data, "size"), "markdown"), "scenario", ""),
            ),
        ),
        structure=StructureConfig(
            enabled=_bool(_section(data, "structure"), "enabled", True),
            gate=_bool(_section(data, "structure"), "gate", True),
            rules={
                name: _structure_rule(_section(_section(data, "structure"), "rules").get(name, {}))
                for name in (
                    "no_generated_artifacts",
                    "copied_servers_not_tracked",
                    "no_absolute_manifest_paths",
                )
            },
        ),
        tests=TestsConfig(
            unittest=UnittestConfig(
                enabled=_bool(_section(_section(data, "tests"), "unittest"), "enabled", True),
                gate=_bool(_section(_section(data, "tests"), "unittest"), "gate", True),
                command=_list_of_str(_section(_section(data, "tests"), "unittest"), "command"),
            )
        ),
        coverage=CoverageConfig(
            enabled=_bool(_section(data, "coverage"), "enabled", False),
            measure=_bool(_section(data, "coverage"), "measure", False),
            gate=_bool(_section(data, "coverage"), "gate", False),
            min_percent=_nullable_int(_section(data, "coverage"), "min_percent"),
            scenario=_text(_section(data, "coverage"), "scenario", ""),
        ),
        ci=CiConfig(
            enabled=_bool(_section(data, "ci"), "enabled", False),
            workflow_enabled=_bool(_section(data, "ci"), "workflow_enabled", False),
            scenario=_text(_section(data, "ci"), "scenario", ""),
        ),
        metrics=MetricsConfig(
            enabled=_bool(_section(data, "metrics"), "enabled", False),
            append_history=_bool(_section(data, "metrics"), "append_history", False),
            branch=_text(_section(data, "metrics"), "branch", "ci-metrics"),
            scenario=_text(_section(data, "metrics"), "scenario", ""),
        ),
        source_path=config_path,
    )


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


def _text(data: dict[str, Any], key: str, default: str = "") -> str:
    value = data.get(key, default)
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _path_text(data: dict[str, Any], key: str, default: str) -> str:
    return _text(data, key, default)


def _bool(data: dict[str, Any], key: str | None, default: bool) -> bool:
    if key is None:
        return default
    value = data.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower() == "true"
    raise GateConfigError(f"Invalid boolean value for {key}: {value!r}")


def _int(data: dict[str, Any], key: str | None, default: int) -> int:
    if key is None:
        return default
    value = data.get(key, default)
    if value is None:
        return default
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise GateConfigError(f"Invalid integer value for {key}: {value!r}")


def _nullable_int(data: dict[str, Any], key: str) -> int | None:
    value = data.get(key, None)
    if value is None:
        return None
    return _int({key: value}, key, 0)


def _list_of_str(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise GateConfigError(f"{key} must be a list.")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise GateConfigError(f"{key} entries must be strings.")
        items.append(item)
    return items


def _structure_rule(data: Any) -> StructureRuleConfig:
    if not isinstance(data, dict):
        data = {}
    patterns = data.get("patterns")
    allowed = data.get("allowed")
    return StructureRuleConfig(
        enabled=_bool(data, "enabled", True),
        patterns=_list_of_str(data, "patterns") if isinstance(patterns, list) else None,
        allowed=_list_of_str(data, "allowed") if isinstance(allowed, list) else None,
        manifest_glob=_text(data, "manifest_glob", "") or None,
    )
