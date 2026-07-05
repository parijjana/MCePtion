from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import (
    CAPABILITY_HEADINGS,
    SUPPORTED_LIFECYCLES,
    SUPPORTED_TRANSPORTS,
    ServiceRecord,
    ValidationResult,
)
from .simple_yaml import SimpleYamlError, load_yaml


def discover_services(servers_dir: Path) -> list[ServiceRecord]:
    records: list[ServiceRecord] = []
    manifests = sorted(servers_dir.glob("*/mcp-server.yaml")) if servers_dir.exists() else []
    seen_ids: dict[str, Path] = {}

    for manifest_path in manifests:
        record = load_service(manifest_path)
        if record.id in seen_ids:
            record.validation.errors.append(
                f"Duplicate service id '{record.id}' also found at {seen_ids[record.id]}."
            )
            record.status = "Invalid"
        else:
            seen_ids[record.id] = manifest_path
        records.append(record)

    _validate_port_conflicts(records)
    return records


def load_service(manifest_path: Path) -> ServiceRecord:
    root = manifest_path.parent.resolve()
    validation = ValidationResult()
    manifest: dict[str, Any] = {}

    try:
        manifest = load_yaml(manifest_path)
    except (OSError, SimpleYamlError) as exc:
        validation.errors.append(f"Manifest could not be parsed: {exc}")

    service_id = str(manifest.get("id") or root.name)
    lifecycle = str(_nested(manifest, "lifecycle", "type") or "")
    transport = str(_nested(manifest, "transport", "type") or "")
    enabled = bool(manifest.get("enabled", True))
    capabilities_path = root / "CAPABILITIES.md"
    readme_path = root / "README.md"

    if manifest.get("schema_version") != 1:
        validation.errors.append("schema_version must be 1.")
    if not manifest.get("id"):
        validation.errors.append("id is required.")
    if lifecycle not in SUPPORTED_LIFECYCLES:
        validation.errors.append(
            "lifecycle.type must be one of: command_per_client, daemon, external."
        )
    if transport not in SUPPORTED_TRANSPORTS:
        validation.errors.append("transport.type must be one of: stdio, streamable_http.")
    if lifecycle == "daemon" and transport != "streamable_http":
        validation.errors.append("daemon lifecycle requires streamable_http transport.")
    if lifecycle == "command_per_client" and transport != "stdio":
        validation.errors.append("command_per_client lifecycle requires stdio transport.")
    if lifecycle == "external" and not _nested(manifest, "transport", "url"):
        validation.warnings.append("external services should declare transport.url.")

    _validate_required_files(root, manifest, lifecycle, validation)
    _validate_capabilities(capabilities_path, validation)
    _validate_paths(root, manifest, validation)

    status = _status_for(lifecycle, enabled, validation.valid)
    return ServiceRecord(
        id=service_id,
        name=str(manifest.get("name") or service_id),
        version=str(manifest.get("version") or ""),
        description=str(manifest.get("description") or ""),
        root=root,
        manifest_path=manifest_path.resolve(),
        manifest=manifest,
        lifecycle=lifecycle or "unknown",
        transport=transport or "unknown",
        enabled=enabled,
        validation=validation,
        status=status,
        capabilities_path=capabilities_path,
        readme_path=readme_path,
        summary=_summary(manifest, capabilities_path),
    )


def connection_recipe(service: ServiceRecord) -> dict[str, Any]:
    if service.transport == "stdio":
        entrypoint = service.manifest.get("entrypoint", {})
        return {
            "transport": "stdio",
            "command": entrypoint.get("command", ""),
            "args": entrypoint.get("args", []),
            "cwd": str((service.root / str(entrypoint.get("working_directory", "."))).resolve()),
            "env": entrypoint.get("env", {}),
        }
    if service.transport == "streamable_http":
        transport = service.manifest.get("transport", {})
        return {
            "transport": "streamable_http",
            "url": transport.get("url", ""),
            "headers": transport.get("headers", {}),
        }
    return {"transport": service.transport}


def _validate_required_files(
    root: Path, manifest: dict[str, Any], lifecycle: str, validation: ValidationResult
) -> None:
    if not (root / "CAPABILITIES.md").exists():
        validation.errors.append("CAPABILITIES.md is required.")
    if not (root / "README.md").exists():
        validation.errors.append("README.md is required.")

    scripts = manifest.get("scripts", {})
    test_script = scripts.get("test")
    if not test_script:
        validation.errors.append("scripts.test is required.")
    elif not (root / str(test_script)).exists():
        validation.errors.append(f"scripts.test does not exist: {test_script}")

    if lifecycle in {"command_per_client", "daemon"}:
        start_script = scripts.get("start")
        entrypoint = manifest.get("entrypoint", {})
        has_entrypoint = entrypoint.get("type") == "command" and entrypoint.get("command")
        if start_script and not (root / str(start_script)).exists():
            validation.errors.append(f"scripts.start does not exist: {start_script}")
        if not start_script and not has_entrypoint:
            validation.errors.append("Either scripts.start or entrypoint.command is required.")


def _validate_capabilities(path: Path, validation: ValidationResult) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    for heading in CAPABILITY_HEADINGS:
        if f"## {heading}" not in text:
            validation.warnings.append(f"CAPABILITIES.md is missing heading: {heading}")


def _validate_paths(root: Path, manifest: dict[str, Any], validation: ValidationResult) -> None:
    for section, key in [("scripts", "start"), ("scripts", "stop"), ("scripts", "test")]:
        value = _nested(manifest, section, key)
        if value and Path(str(value)).is_absolute():
            validation.errors.append(f"{section}.{key} must be relative to the service root.")
    working_directory = _nested(manifest, "entrypoint", "working_directory")
    if working_directory and Path(str(working_directory)).is_absolute():
        validation.errors.append(
            "entrypoint.working_directory must be relative to the service root."
        )


def _validate_port_conflicts(records: list[ServiceRecord]) -> None:
    ports: dict[int, str] = {}
    for record in records:
        if record.lifecycle != "daemon" or not record.enabled:
            continue
        for port in record.manifest.get("ports", []) or []:
            try:
                port_value = int(port)
            except TypeError, ValueError:
                record.validation.errors.append(f"Invalid port value: {port}")
                record.status = "Invalid"
                continue
            if port_value in ports:
                record.validation.errors.append(
                    f"Port {port_value} conflicts with service '{ports[port_value]}'."
                )
                record.status = "Invalid"
            else:
                ports[port_value] = record.id


def _status_for(lifecycle: str, enabled: bool, valid: bool) -> str:
    if not valid:
        return "Invalid"
    if not enabled:
        return "Disabled"
    if lifecycle == "command_per_client":
        return "Ready"
    if lifecycle == "daemon":
        return "Stopped"
    if lifecycle == "external":
        return "Unknown"
    return "Invalid"


def _summary(manifest: dict[str, Any], capabilities_path: Path) -> str:
    if manifest.get("description"):
        return str(manifest["description"])
    if not capabilities_path.exists():
        return ""
    for line in capabilities_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    return ""


def _nested(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
