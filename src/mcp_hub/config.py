from __future__ import annotations

from pathlib import Path

from .models import HubConfig
from .simple_yaml import load_yaml


def load_config(root: Path | None = None) -> HubConfig:
    hub_root = (root or Path.cwd()).resolve()
    data = load_yaml(hub_root / "framework.yaml")

    manager = data.get("manager", {})
    dashboard = data.get("dashboard", {})
    servers = data.get("servers", {})
    guidelines = data.get("guidelines", {})

    return HubConfig(
        root=hub_root,
        manager_host=str(manager.get("host", "127.0.0.1")),
        manager_port=int(manager.get("port", 7420)),
        manager_state_file=_resolve(
            hub_root, str(manager.get("state_file", "./data/runtime-state.json"))
        ),
        dashboard_host=str(dashboard.get("host", manager.get("host", "127.0.0.1"))),
        dashboard_port=int(dashboard.get("port", manager.get("port", 7420))),
        servers_dir=_resolve(hub_root, str(servers.get("directory", "./servers"))),
        guidelines_dir=_resolve(hub_root, str(guidelines.get("directory", "./guidelines"))),
        examples_dir=_resolve(
            hub_root, str(guidelines.get("examples_directory", "./guidelines/examples"))
        ),
        logs_dir=_resolve(hub_root, "./logs"),
    )


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()
