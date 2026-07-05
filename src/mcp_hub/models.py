from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SUPPORTED_LIFECYCLES = {"command_per_client", "daemon", "external"}
SUPPORTED_TRANSPORTS = {"stdio", "streamable_http"}
CAPABILITY_HEADINGS = [
    "Purpose",
    "When To Use",
    "When Not To Use",
    "Main Capabilities",
    "Data Scope",
    "Safety Notes",
    "Typical Workflow",
]


@dataclass(frozen=True)
class HubConfig:
    root: Path
    manager_host: str
    manager_port: int
    manager_state_file: Path
    dashboard_host: str
    dashboard_port: int
    servers_dir: Path
    guidelines_dir: Path
    examples_dir: Path
    logs_dir: Path


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors


@dataclass
class ServiceRecord:
    id: str
    name: str
    version: str
    description: str
    root: Path
    manifest_path: Path
    manifest: dict[str, Any]
    lifecycle: str
    transport: str
    enabled: bool
    validation: ValidationResult
    status: str
    capabilities_path: Path
    readme_path: Path
    summary: str = ""

    @property
    def valid(self) -> bool:
        return self.validation.valid

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "lifecycle": self.lifecycle,
            "transport": self.transport,
            "status": self.status,
            "enabled": self.enabled,
            "valid": self.valid,
            "folder": str(self.root),
            "manifest_path": str(self.manifest_path),
            "capabilities_path": str(self.capabilities_path.relative_to(self.root))
            if self.capabilities_path.exists()
            else "CAPABILITIES.md",
            "readme_path": str(self.readme_path.relative_to(self.root))
            if self.readme_path.exists()
            else "README.md",
            "summary": self.summary,
            "validation_errors": list(self.validation.errors),
            "validation_warnings": list(self.validation.warnings),
        }
