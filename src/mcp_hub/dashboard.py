from __future__ import annotations

import json
from typing import Any

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
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f7f8;
      --panel: #ffffff;
      --ink: #1f2328;
      --muted: #59636e;
      --line: #ccd4dc;
      --accent: #0969da;
      --bad: #b42318;
      --good: #1a7f37;
      --warn: #9a6700;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Segoe UI, Arial, sans-serif;
      font-size: 14px;
    }}
    main {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 22px;
    }}
    header {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }}
    h1 {{ font-size: 24px; margin: 0 0 4px; }}
    h2 {{ font-size: 16px; margin: 22px 0 10px; }}
    p {{ margin: 0; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #e8edf2;
      font-size: 12px;
      text-transform: uppercase;
      color: #3d4650;
    }}
    code, pre {{
      background: #eef2f5;
      border: 1px solid #d8dee4;
      border-radius: 4px;
      font-family: Consolas, monospace;
    }}
    code {{ padding: 1px 4px; }}
    pre {{
      min-width: 260px;
      max-width: 420px;
      max-height: 220px;
      margin: 0;
      padding: 8px;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    button {{
      min-width: 76px;
      min-height: 30px;
      border: 1px solid #8c959f;
      border-radius: 4px;
      background: #ffffff;
      color: var(--ink);
      cursor: pointer;
    }}
    button.primary {{
      border-color: var(--accent);
      color: #ffffff;
      background: var(--accent);
    }}
    form {{ display: inline-block; margin: 0 6px 6px 0; }}
    .muted {{ color: var(--muted); }}
    .status {{ font-weight: 700; }}
    .ready, .running {{ color: var(--good); }}
    .invalid {{ color: var(--bad); }}
    .stopped, .unknown {{ color: var(--warn); }}
    .errors {{ color: var(--bad); margin: 0; padding-left: 18px; }}
    .empty {{ color: var(--muted); }}
    .toolbar {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
    }}
    .meta-block {{
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 12px;
    }}
  </style>
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
        f"<td><strong>{_escape(service['name'])}</strong><br>"
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
