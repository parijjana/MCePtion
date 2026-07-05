from __future__ import annotations

import unittest
from pathlib import Path
from shutil import copytree

from workspace_utils import test_workspace

from mcp_hub.api_server import HtmlResponse, LocalThreadingHTTPServer, _html_dashboard
from mcp_hub.dashboard import render_dashboard
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

    def test_dashboard_shows_stdio_connection_and_probe_without_stop(self) -> None:
        hub_root = _copy_hub_minimum("dashboard-valid-stdio")
        copytree(
            ROOT / "tests" / "fixtures" / "valid-stdio-server",
            hub_root / "servers" / "valid-stdio-server",
            dirs_exist_ok=True,
        )

        html = render_dashboard(HubManager.from_root(hub_root)).content

        self.assertIn("Valid local stdio server fixture.", html)
        self.assertIn('action="/services/valid-stdio/probe"', html)
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
        self.assertIn("Invalid", html)

    def test_dashboard_shows_daemon_start_stop_restart_controls(self) -> None:
        hub_root = _copy_hub_minimum("dashboard-daemon")
        _write_daemon_fixture(hub_root / "servers" / "valid-daemon")

        html = render_dashboard(HubManager.from_root(hub_root)).content

        self.assertIn('action="/services/valid-daemon/start"', html)
        self.assertIn('action="/services/valid-daemon/stop"', html)
        self.assertIn('action="/services/valid-daemon/restart"', html)
        self.assertIn("&quot;transport&quot;: &quot;streamable_http&quot;", html)


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
