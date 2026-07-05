from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import load_config
from .discovery import connection_recipe, load_service


def validate_server_path(root: Path, server_path: Path) -> dict[str, Any]:
    config = load_config(root)
    path = _resolve_input_path(config.root, server_path)
    service = load_service(path / "mcp-server.yaml")
    errors = list(service.validation.errors)
    warnings = list(service.validation.warnings)
    valid = not errors

    result: dict[str, Any] = {
        "schema_version": 1,
        "path": str(path),
        "inside_servers_dir": _is_relative_to(path, config.servers_dir),
        "valid": valid,
        "status": service.status if valid else "Invalid",
        "service": _service_summary(service.as_dict()),
        "errors": errors,
        "warnings": warnings,
        "next_actions": _next_actions(valid),
    }
    if valid:
        result["connection"] = connection_recipe(service)
    return result


def _resolve_input_path(root: Path, server_path: Path) -> Path:
    if server_path.is_absolute():
        return server_path.resolve()
    return (root / server_path).resolve()


def _service_summary(service: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": service["id"],
        "name": service["name"],
        "lifecycle": service["lifecycle"],
        "transport": service["transport"],
    }


def _next_actions(valid: bool) -> list[str]:
    if not valid:
        return ["Fix the listed errors and rerun validation."]
    return ["Run .\\scripts\\rescan-services.ps1 or use the dashboard Rescan button."]


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
