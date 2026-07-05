from __future__ import annotations

import json
from typing import Any

from .dashboard_style import DASHBOARD_CSS
from .manager import HubManager


class HtmlResponse:
    def __init__(self, content: str) -> None:
        self.content = content


def render_dashboard(manager: HubManager, notice: dict[str, Any] | None = None) -> HtmlResponse:
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
      <form method="post" action="/dashboard/rescan">
        <button class="primary" type="submit">Rescan</button>
      </form>
    </header>
    {_notice_html(notice)}
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


def render_service_detail(
    manager: HubManager,
    service_id: str,
    focus: str = "overview",
    action_result: dict[str, Any] | None = None,
) -> HtmlResponse:
    service = manager.describe_service(service_id)
    connection = _connection_html(manager, service, expanded=True)
    validation = _validation_html(service, expanded=True)
    action_panel = _notice_html(action_result)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape(service["name"])} - MCP Hub</title>
  <style>{DASHBOARD_CSS}</style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>{_escape(service["name"])}</h1>
        <p class="muted"><code>{_escape(service_id)}</code> detail view</p>
      </div>
      <form method="get" action="/">
        <button class="primary" type="submit">Back</button>
      </form>
    </header>
    {action_panel}
    <section class="detail-grid">
      <div class="detail-card">
        <h2>Service</h2>
        <dl>
          <dt>Lifecycle</dt><dd>{_escape(service["lifecycle"])}</dd>
          <dt>Transport</dt><dd>{_escape(service["transport"])}</dd>
          <dt>Status</dt><dd>{_status_badge(service)}</dd>
          <dt>Summary</dt><dd>{_escape(service.get("summary", ""))}</dd>
        </dl>
        <div class="control-stack">{_controls_html(service)}</div>
      </div>
      <div class="detail-card {focus}">
        <h2>Connection</h2>
        {connection}
      </div>
      <div class="detail-card">
        <h2>Validation</h2>
        {validation}
      </div>
    </section>
  </main>
</body>
</html>"""
    return HtmlResponse(html)


def _service_row(manager: HubManager, service: dict[str, Any]) -> str:
    service_id = str(service["id"])
    validation = _validation_html(service)
    connection = _connection_html(manager, service)
    controls = _controls_html(service)
    row_class = "invalid-row" if not service.get("valid") else ""
    return (
        f'<tr class="{row_class}">'
        f'<td><strong class="service-name">{_escape(service["name"])}</strong><br>'
        f"<code>{_escape(service_id)}</code><br>"
        f'<span class="muted">{_escape(service.get("version", ""))}</span></td>'
        f"<td>{_escape(service['lifecycle'])}</td>"
        f"<td>{_escape(service['transport'])}</td>"
        f"<td>{_status_badge(service)}</td>"
        f"<td>{_escape(service.get('summary', ''))}</td>"
        f"<td>{validation}</td>"
        f"<td>{connection}</td>"
        f"<td>{controls}</td>"
        "</tr>"
    )


def _validation_html(service: dict[str, Any], expanded: bool = False) -> str:
    errors = list(service.get("validation_errors", []))
    warnings = list(service.get("validation_warnings", []))
    if not errors and not warnings:
        return '<span class="ready">Valid</span>'
    items = "".join(f"<li>{_escape(item)}</li>" for item in errors + warnings)
    open_attr = " open" if expanded or errors else ""
    label = f"{len(errors)} error(s), {len(warnings)} warning(s)"
    return (
        f'<details class="validation-detail"{open_attr}>'
        f'<summary>{label}</summary><ul class="errors">{items}</ul></details>'
    )


def _connection_html(manager: HubManager, service: dict[str, Any], expanded: bool = False) -> str:
    if not service.get("valid"):
        return '<span class="muted">Unavailable until valid.</span>'
    recipe = manager.get_connection(str(service["id"]))
    class_name = "connection-large" if expanded else ""
    return (
        f'<pre class="{class_name}">{_escape(json.dumps(recipe, indent=2, sort_keys=True))}</pre>'
    )


def _controls_html(service: dict[str, Any]) -> str:
    service_id = _escape(str(service["id"]))
    lifecycle = service["lifecycle"]
    if lifecycle == "command_per_client":
        return _post_button(f"/dashboard/services/{service_id}/probe", "Probe") + _link_button(
            f"/dashboard/services/{service_id}/connection", "Connection"
        )
    if lifecycle == "daemon":
        return (
            _post_button(f"/dashboard/services/{service_id}/start", "Start", primary=True)
            + _post_button(f"/dashboard/services/{service_id}/stop", "Stop")
            + _post_button(f"/dashboard/services/{service_id}/restart", "Restart")
            + _link_button(f"/dashboard/services/{service_id}/connection", "Connection")
        )
    if lifecycle == "external":
        return _post_button(f"/dashboard/services/{service_id}/probe", "Health") + _link_button(
            f"/dashboard/services/{service_id}/connection", "Connection"
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


def _notice_html(notice: dict[str, Any] | None) -> str:
    if not notice:
        return ""
    title = notice.get("title", "Result")
    payload = notice.get("payload", {})
    body = json.dumps(payload, indent=2, sort_keys=True)
    return (
        '<section class="notice-panel">'
        f"<h2>{_escape(title)}</h2>"
        f"<pre>{_escape(body)}</pre>"
        "</section>"
    )


def _status_badge(service: dict[str, Any]) -> str:
    status_class = str(service["status"]).lower().replace(" ", "-")
    return f'<span class="status {status_class}">{_escape(service["status"])}</span>'


def _escape(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
