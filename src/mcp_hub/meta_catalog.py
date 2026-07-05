from __future__ import annotations

from typing import Any

from .manager import HubManager


def tools() -> list[dict[str, Any]]:
    return [
        _tool("hub.list_services", "List discovered MCP services.", _service_filters_schema()),
        _tool("hub.describe_service", "Describe one MCP service.", _service_id_schema()),
        _tool(
            "hub.get_service_connection",
            "Return a direct connection recipe for a service.",
            _service_id_schema(),
        ),
        _tool(
            "hub.get_service_capabilities",
            "Return a service CAPABILITIES.md file.",
            _service_id_schema({"format": {"type": "string", "default": "markdown"}}),
        ),
        _tool("hub.get_service_readme", "Return a service README.md file.", _service_id_schema()),
        _tool(
            "hub.get_service_status",
            "Return service status and validation detail.",
            _service_id_schema(),
        ),
        _tool("hub.list_guidelines", "List server authoring guidelines and examples."),
        _tool("hub.get_guideline", "Return a guideline document.", _id_schema("id")),
        _tool(
            "hub.recommend_server_type",
            "Recommend what kind of MCP server to create.",
            _recommendation_schema(),
        ),
        _tool("hub.get_example_code", "Return reference example code.", _example_schema()),
        _tool("hub.rescan_services", "Rescan local copied server folders."),
        _tool(
            "hub.probe_service",
            "Probe a service without treating stdio as a daemon.",
            _service_id_schema(),
        ),
        _tool("hub.start_service", "Start a daemon service when applicable.", _service_id_schema()),
        _tool("hub.stop_service", "Stop a daemon service when applicable.", _service_id_schema()),
        _tool(
            "hub.restart_service", "Restart a daemon service when applicable.", _service_id_schema()
        ),
        _tool(
            "hub.tail_service_logs",
            "Return recent service log lines when declared.",
            _service_id_schema(),
        ),
    ]


def resources(manager: HubManager) -> list[dict[str, Any]]:
    items = [
        {"uri": "hub://services", "name": "Services", "mimeType": "application/json"},
        {
            "uri": "hub://guidelines/server-authoring",
            "name": "Server Authoring Guidelines",
            "mimeType": "text/markdown",
        },
        {
            "uri": "hub://guidelines/examples",
            "name": "Guideline Examples",
            "mimeType": "application/json",
        },
        {
            "uri": "hub://guidelines/examples/python-stdio-fastmcp",
            "name": "Python stdio FastMCP example",
            "mimeType": "application/json",
        },
    ]
    for service in manager.list_services():
        service_id = service["id"]
        for name in ["capabilities", "readme", "manifest", "connection", "status"]:
            items.append(
                {
                    "uri": f"hub://services/{service_id}/{name}",
                    "name": f"{service_id} {name}",
                }
            )
    return items


def _tool(
    name: str, description: str, input_schema: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": input_schema or {"type": "object", "properties": {}},
    }


def _id_schema(field: str) -> dict[str, Any]:
    return {"type": "object", "properties": {field: {"type": "string"}}, "required": [field]}


def _service_id_schema(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    properties = {"id": {"type": "string"}}
    if extra:
        properties.update(extra)
    return {"type": "object", "properties": properties, "required": ["id"]}


def _service_filters_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "include_disabled": {"type": "boolean", "default": True},
            "include_invalid": {"type": "boolean", "default": True},
        },
    }


def _example_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "example_id": {"type": "string"},
            "path": {"type": "string"},
        },
        "required": ["example_id"],
    }


def _recommendation_schema() -> dict[str, Any]:
    boolean_keys = [
        "shared_across_projects",
        "local_only",
        "stores_durable_data",
        "needs_long_running_process",
        "needs_multiple_simultaneous_clients",
        "needs_browser_ui",
        "remote_access_required",
    ]
    return {
        "type": "object",
        "properties": {key: {"type": "boolean"} for key in boolean_keys},
    }
