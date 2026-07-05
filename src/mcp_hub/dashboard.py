from __future__ import annotations

import json
from typing import Any

from .dashboard_style import DASHBOARD_CSS
from .manager import HubManager


class HtmlResponse:
    def __init__(self, content: str) -> None:
        self.content = content


def render_dashboard(manager: HubManager) -> HtmlResponse:
    services = manager.list_services()
    rows = "\n".join(_service_row(manager, service) for service in services)
    if not rows:
        rows = (
            '<tr><td colspan="8" class="empty">No services discovered. Copy server folders '
            "into <code>servers/</code> and rescan.</td></tr>"
        )
    api_url = f"http://{manager.config.manager_host}:{manager.config.manager_port}"
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MCP Hub</title>
  <style>{DASHBOARD_CSS}</style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>MCP Hub</h1>
        <p class="muted">Manager and dashboard: <code>{_escape(api_url)}</code></p>
      </div>
      <form method="post" action="/services/rescan">
        <button class="primary" type="submit">Rescan</button>
      </form>
    </header>
    <h2>Services</h2>
    <table>
      <thead>
        <tr>
          <th>Service</th>
          <th>Lifecycle</th>
          <th>Transport</th>
          <th>Status</th>
          <th>Capability Brief</th>
          <th>Validation</th>
          <th>Connection</th>
          <th>Controls</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    <h2>Agent Setup</h2>
    <div class="meta">
      <div class="meta-block">
        <p class="muted">Meta MCP stdio command</p>
        <pre>.\\scripts\\start-meta-stdio.ps1</pre>
      </div>
      <div class="meta-block">
        <p class="muted">Manager API</p>
        <pre>GET /services
POST /services/rescan
GET /services/&lt;id&gt;/connection
GET /guidelines</pre>
      </div>
    </div>
  </main>
</body>
</html>"""
    return HtmlResponse(html)


def _service_row(manager: HubManager, service: dict[str, Any]) -> str:
    service_id = str(service["id"])
    validation = _validation_html(service)
    connection = _connection_html(manager, service)
    controls = _controls_html(service)
    status_class = str(service["status"]).lower().replace(" ", "-")
    return (
        "<tr>"
        f'<td><strong class="service-name">{_escape(service["name"])}</strong><br>'
        f"<code>{_escape(service_id)}</code><br>"
        f'<span class="muted">{_escape(service.get("version", ""))}</span></td>'
        f"<td>{_escape(service['lifecycle'])}</td>"
        f"<td>{_escape(service['transport'])}</td>"
        f'<td class="status {status_class}">{_escape(service["status"])}</td>'
        f"<td>{_escape(service.get('summary', ''))}</td>"
        f"<td>{validation}</td>"
        f"<td>{connection}</td>"
        f"<td>{controls}</td>"
        "</tr>"
    )


def _validation_html(service: dict[str, Any]) -> str:
    errors = list(service.get("validation_errors", []))
    warnings = list(service.get("validation_warnings", []))
    if not errors and not warnings:
        return '<span class="ready">Valid</span>'
    items = "".join(f"<li>{_escape(item)}</li>" for item in errors + warnings)
    return f'<ul class="errors">{items}</ul>'


def _connection_html(manager: HubManager, service: dict[str, Any]) -> str:
    if not service.get("valid"):
        return '<span class="muted">Unavailable until valid.</span>'
    recipe = manager.get_connection(str(service["id"]))
    return f"<pre>{_escape(json.dumps(recipe, indent=2, sort_keys=True))}</pre>"


def _controls_html(service: dict[str, Any]) -> str:
    service_id = _escape(str(service["id"]))
    lifecycle = service["lifecycle"]
    if lifecycle == "command_per_client":
        return _post_button(f"/services/{service_id}/probe", "Probe") + _link_button(
            f"/services/{service_id}/connection", "Connection"
        )
    if lifecycle == "daemon":
        return (
            _post_button(f"/services/{service_id}/start", "Start", primary=True)
            + _post_button(f"/services/{service_id}/stop", "Stop")
            + _post_button(f"/services/{service_id}/restart", "Restart")
            + _link_button(f"/services/{service_id}/connection", "Connection")
        )
    if lifecycle == "external":
        return _post_button(f"/services/{service_id}/probe", "Health") + _link_button(
            f"/services/{service_id}/connection", "Connection"
        )
    return '<span class="muted">No actions.</span>'


def _post_button(action: str, label: str, primary: bool = False) -> str:
    class_name = ' class="primary"' if primary else ""
    return (
        f'<form method="post" action="{action}">'
        f'<button{class_name} type="submit">{label}</button></form>'
    )


def _link_button(href: str, label: str) -> str:
    return f'<form method="get" action="{href}"><button type="submit">{label}</button></form>'


def _escape(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
