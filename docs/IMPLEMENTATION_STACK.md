# Implementation Stack

## Default Stack

Version 1 should use Python on Windows with `uv`.

Recommended components:

```text
Python                 Core implementation language
uv                     Environment and command runner
FastAPI or Starlette   Manager API and dashboard backend
SQLite                 Durable registry when JSON state becomes too small
psutil                 Local process inspection and supervision
PyYAML or ruamel.yaml  Manifest parsing
pytest or unittest     Test suite
```

For MCP protocol support, use the official MCP Python SDK or a compatible library selected and pinned when implementation starts.

The reference stdio example currently uses:

```python
from mcp.server.fastmcp import FastMCP
```

Verify the official SDK API and pin the version before turning reference examples into production servers.

## Why Python

- Existing local tooling already uses Python and `uv`.
- Windows process management is practical.
- Text, YAML, JSON, and Markdown handling are straightforward.
- The same code can move later to a VPS.
- It keeps early implementation cheaper than a multi-language stack.

## Dashboard Options

Version 1 dashboard can be simple.

Recommended path:

```text
FastAPI/Starlette backend
Server-rendered HTML or small static frontend
No heavy frontend framework until needed
```

The dashboard is operational UI, not a marketing site. It should be dense, clear, and focused on status and actions.

## Meta MCP Transport

The default meta MCP transport should be stdio.

The framework startup script prepares the local manager and dashboard. Agent hosts launch the stdio meta MCP process when they connect.

Optional Streamable HTTP support can be added for hosts that prefer URL-based MCP configuration, but it should remain secondary for local-first use.

## Persistence

Start with files where possible:

```text
framework.yaml
servers/*/mcp-server.yaml
data/runtime-state.json
logs/*.log
```

Move registry state to SQLite when needed:

```text
data/registry.sqlite
```

Runtime state must remain rebuildable from manifests and process inspection.

## Dependency Policy

- Pin dependencies once implementation starts.
- Keep the manager core independent from dashboard rendering.
- Keep MCP protocol code isolated from lifecycle supervision.
- Avoid dependencies that require admin rights on Windows.
- Avoid container dependencies in version 1.
