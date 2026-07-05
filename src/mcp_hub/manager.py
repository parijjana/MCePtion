from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import load_config
from .discovery import connection_recipe, discover_services
from .guidelines import (
    get_example_file,
    get_guideline,
    list_example_files,
    list_guidelines,
    recommend_server_type,
)
from .models import HubConfig, ServiceRecord


class ServiceNotFoundError(KeyError):
    pass


class HubManager:
    def __init__(self, config: HubConfig) -> None:
        self.config = config
        self._services: dict[str, ServiceRecord] = {}
        self.rescan()

    @classmethod
    def from_root(cls, root: Path | None = None) -> "HubManager":
        return cls(load_config(root))

    def rescan(self) -> dict[str, list[str]]:
        before = set(self._services)
        services = discover_services(self.config.servers_dir)
        self._services = {service.id: service for service in services}
        after = set(self._services)
        invalid = [service.id for service in services if not service.valid]
        return {
            "added": sorted(after - before),
            "changed": [],
            "removed": sorted(before - after),
            "invalid": sorted(invalid),
        }

    def list_services(
        self, include_disabled: bool = True, include_invalid: bool = True
    ) -> list[dict[str, Any]]:
        services = []
        for service in sorted(self._services.values(), key=lambda item: item.id):
            if not include_disabled and not service.enabled:
                continue
            if not include_invalid and not service.valid:
                continue
            services.append(service.as_dict())
        return services

    def get_service(self, service_id: str) -> ServiceRecord:
        try:
            return self._services[service_id]
        except KeyError as exc:
            raise ServiceNotFoundError(service_id) from exc

    def describe_service(self, service_id: str) -> dict[str, Any]:
        service = self.get_service(service_id)
        return {
            **service.as_dict(),
            "health": self.get_service_status(service_id)["health"],
            "resources": {
                "capabilities": f"hub://services/{service.id}/capabilities",
                "readme": f"hub://services/{service.id}/readme",
                "manifest": f"hub://services/{service.id}/manifest",
                "connection": f"hub://services/{service.id}/connection",
                "status": f"hub://services/{service.id}/status",
            },
        }

    def get_connection(self, service_id: str) -> dict[str, Any]:
        service = self.get_service(service_id)
        notes = []
        if service.lifecycle == "command_per_client":
            notes.append(
                "This service is launched by each MCP client. The hub does not keep it running."
            )
        if service.lifecycle == "daemon":
            notes.append("This service must be running before clients connect.")
        return {
            "id": service.id,
            "lifecycle": service.lifecycle,
            "connection": connection_recipe(service),
            "notes": notes,
        }

    def read_capabilities(self, service_id: str) -> str:
        service = self.get_service(service_id)
        return service.capabilities_path.read_text(encoding="utf-8")

    def read_readme(self, service_id: str) -> str:
        service = self.get_service(service_id)
        return service.readme_path.read_text(encoding="utf-8")

    def get_manifest(self, service_id: str) -> dict[str, Any]:
        return self.get_service(service_id).manifest

    def get_service_status(self, service_id: str) -> dict[str, Any]:
        service = self.get_service(service_id)
        health_state = "failing" if service.validation.errors else "passing"
        return {
            "id": service.id,
            "status": service.status,
            "lifecycle": service.lifecycle,
            "transport": service.transport,
            "enabled": service.enabled,
            "valid": service.valid,
            "health": {"state": health_state, "last_checked_at": None},
            "validation_errors": list(service.validation.errors),
            "validation_warnings": list(service.validation.warnings),
            "process": None,
            "events": [],
        }

    def probe_service(self, service_id: str) -> dict[str, Any]:
        service = self.get_service(service_id)
        if not service.valid:
            return {"status": "invalid", "errors": service.validation.errors}
        return {
            "status": "ready"
            if service.lifecycle == "command_per_client"
            else service.status.lower()
        }

    def start_service(self, service_id: str) -> dict[str, Any]:
        service = self.get_service(service_id)
        if service.lifecycle != "daemon":
            return {
                "status": "not_applicable",
                "message": (
                    "This service is launched by each MCP client. Use probe or connection "
                    "details instead."
                ),
            }
        return {
            "status": "not_implemented",
            "message": "Daemon process supervision is not implemented in this slice.",
        }

    def stop_service(self, service_id: str) -> dict[str, Any]:
        service = self.get_service(service_id)
        if service.lifecycle != "daemon":
            return {
                "status": "not_applicable",
                "message": (
                    "The hub must not kill command-per-client processes launched by agent hosts."
                ),
            }
        return {
            "status": "not_implemented",
            "message": "Daemon process supervision is not implemented in this slice.",
        }

    def restart_service(self, service_id: str) -> dict[str, Any]:
        service = self.get_service(service_id)
        if service.lifecycle != "daemon":
            return {
                "status": "not_applicable",
                "message": "Only manager-owned daemon services can be restarted.",
            }
        return {
            "status": "not_implemented",
            "message": "Daemon process supervision is not implemented in this slice.",
        }

    def tail_service_logs(self, service_id: str, lines: int = 200) -> dict[str, Any]:
        service = self.get_service(service_id)
        log_paths = service.manifest.get("logs", {}) if isinstance(service.manifest, dict) else {}
        return {
            "id": service.id,
            "lines": [],
            "requested_lines": lines,
            "message": "No readable service logs are available through this slice.",
            "declared_logs": log_paths,
        }

    def list_guidelines(self) -> dict[str, Any]:
        return list_guidelines(self.config.guidelines_dir, self.config.examples_dir)

    def get_guideline(self, guideline_id: str) -> str:
        return get_guideline(self.config.guidelines_dir, guideline_id)

    def recommend_server_type(self, payload: dict[str, Any]) -> dict[str, Any]:
        return recommend_server_type(payload)

    def list_example_files(self, example_id: str) -> list[str]:
        return list_example_files(self.config.examples_dir, example_id)

    def get_example_file(self, example_id: str, path: str) -> str:
        return get_example_file(self.config.examples_dir, example_id, path)
