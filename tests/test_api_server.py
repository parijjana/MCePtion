from __future__ import annotations

import unittest
from pathlib import Path
from shutil import copytree

from workspace_utils import test_workspace

from mcp_hub.api_server import HtmlResponse, LocalThreadingHTTPServer, _handler, _html_dashboard
from mcp_hub.dashboard import render_dashboard
from mcp_hub.dashboard_style import DASHBOARD_CSS
from mcp_hub.manager import HubManager

ROOT = Path(__file__).resolve().parents[1]


class ApiServerTests(unittest.TestCase):
    def test_dashboard_renders_meta_command(self) -> None:
        response = _html_dashboard(HubManager.from_root(ROOT))

        self.assertIsInstance(response, HtmlResponse)
        self.assertIn("MCP Hub", response.content)
        self.assertIn("start-meta-stdio.ps1", response.content)
        self.assertIn("Services", response.content)

    def test_server_allows_address_reuse_for_script_restarts(self) -> None:
        self.assertTrue(LocalThreadingHTTPServer.allow_reuse_address)

    def test_dashboard_uses_neo_brutalist_style_markers(self) -> None:
        response = _html_dashboard(HubManager.from_root(ROOT))

        self.assertIn("border: 4px solid var(--line)", response.content)
        self.assertIn("box-shadow: var(--shadow)", response.content)
        self.assertIn("--yellow: #ffd400", response.content)
        self.assertIn("border-radius: 0", response.content)
        self.assertIsInstance(DASHBOARD_CSS, str)

    def test_dashboard_shows_stdio_connection_and_probe_without_stop(self) -> None:
        hub_root = _copy_hub_minimum("dashboard-valid-stdio")
        copytree(
            ROOT / "tests" / "fixtures" / "valid-stdio-server",
            hub_root / "servers" / "valid-stdio-server",
            dirs_exist_ok=True,
        )

        html = render_dashboard(HubManager.from_root(hub_root)).content

        self.assertIn("Valid local stdio server fixture.", html)
        self.assertIn('action="/dashboard/services/valid-stdio/probe"', html)
        self.assertIn('action="/dashboard/services/valid-stdio/connection"', html)
        self.assertIn("&quot;command&quot;: &quot;uv&quot;", html)
        self.assertIn("&quot;transport&quot;: &quot;stdio&quot;", html)
        self.assertNotIn(">Stop<", html)

    def test_dashboard_shows_invalid_service_errors(self) -> None:
        hub_root = _copy_hub_minimum("dashboard-invalid-service")
        copytree(
            ROOT / "tests" / "fixtures" / "invalid-missing-capabilities",
            hub_root / "servers" / "invalid-missing-capabilities",
            dirs_exist_ok=True,
        )

        html = render_dashboard(HubManager.from_root(hub_root)).content

        self.assertIn("CAPABILITIES.md is required.", html)
        self.assertIn("Unavailable until valid.", html)
        self.assertIn("validation-detail", html)
        self.assertIn('class="invalid-row"', html)
        self.assertIn("Invalid", html)

    def test_dashboard_shows_daemon_start_stop_restart_controls(self) -> None:
        hub_root = _copy_hub_minimum("dashboard-daemon")
        _write_daemon_fixture(hub_root / "servers" / "valid-daemon")

        html = render_dashboard(HubManager.from_root(hub_root)).content

        self.assertIn('action="/dashboard/services/valid-daemon/start"', html)
        self.assertIn('action="/dashboard/services/valid-daemon/stop"', html)
        self.assertIn('action="/dashboard/services/valid-daemon/restart"', html)
        self.assertIn("&quot;transport&quot;: &quot;streamable_http&quot;", html)

    def test_dashboard_rescan_route_returns_html_notice(self) -> None:
        hub_root = _copy_hub_minimum("dashboard-route-rescan")
        manager = HubManager.from_root(hub_root)
        handler = _handler(manager).__new__(_handler(manager))

        response = handler._route("POST", ["dashboard", "rescan"])

        self.assertIsInstance(response, HtmlResponse)
        self.assertIn("Rescan complete", response.content)
        self.assertIn("notice-panel", response.content)

    def test_dashboard_probe_route_shows_result_panel(self) -> None:
        hub_root = _copy_hub_minimum("dashboard-route-probe")
        copytree(
            ROOT / "tests" / "fixtures" / "valid-stdio-server",
            hub_root / "servers" / "valid-stdio-server",
            dirs_exist_ok=True,
        )
        manager = HubManager.from_root(hub_root)
        handler = _handler(manager).__new__(_handler(manager))

        response = handler._route("POST", ["dashboard", "services", "valid-stdio", "probe"])

        self.assertIsInstance(response, HtmlResponse)
        self.assertIn("Probe result", response.content)
        self.assertIn("&quot;status&quot;: &quot;ready&quot;", response.content)

    def test_dashboard_connection_route_returns_focused_detail_view(self) -> None:
        hub_root = _copy_hub_minimum("dashboard-route-connection")
        copytree(
            ROOT / "tests" / "fixtures" / "valid-stdio-server",
            hub_root / "servers" / "valid-stdio-server",
            dirs_exist_ok=True,
        )
        manager = HubManager.from_root(hub_root)
        handler = _handler(manager).__new__(_handler(manager))

        response = handler._route("GET", ["dashboard", "services", "valid-stdio", "connection"])

        self.assertIsInstance(response, HtmlResponse)
        self.assertIn("detail view", response.content)
        self.assertIn("connection-large", response.content)
        self.assertIn("&quot;command&quot;: &quot;uv&quot;", response.content)


def _copy_hub_minimum(name: str) -> Path:
    hub_root = test_workspace(name) / "hub"
    hub_root.mkdir(parents=True, exist_ok=True)
    (hub_root / "servers").mkdir(exist_ok=True)
    copytree(ROOT / "guidelines", hub_root / "guidelines", dirs_exist_ok=True)
    (hub_root / "framework.yaml").write_text(
        (ROOT / "framework.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    return hub_root


def _write_daemon_fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "scripts").mkdir(exist_ok=True)
    (root / "scripts" / "start.ps1").write_text("exit 0\n", encoding="utf-8")
    (root / "scripts" / "test.ps1").write_text("exit 0\n", encoding="utf-8")
    (root / "README.md").write_text("# Valid Daemon\n", encoding="utf-8")
    (root / "CAPABILITIES.md").write_text(
        """# Valid Daemon Capabilities

## Purpose

Daemon fixture.

## When To Use

- In dashboard tests.

## When Not To Use

- Outside tests.

## Main Capabilities

- Validate daemon controls.

## Data Scope

Local fixture data.

## Safety Notes

No secrets.

## Typical Workflow

1. Load fixture.
""",
        encoding="utf-8",
    )
    (root / "mcp-server.yaml").write_text(
        """schema_version: 1
id: valid-daemon
name: Valid Daemon
version: 0.1.0
description: Valid HTTP daemon server fixture.
enabled: true
lifecycle:
  type: daemon
entrypoint:
  type: command
  command: python
  args:
    - -m
    - http.server
  working_directory: .
transport:
  type: streamable_http
  url: http://127.0.0.1:9876/mcp
scripts:
  start: scripts/start.ps1
  test: scripts/test.ps1
ports:
  - 9876
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
