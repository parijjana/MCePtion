# Manager API Contract

The Manager API is the internal local API used by the dashboard, CLI, and meta MCP server.

It is not intended as the public MCP interface. It is the lifecycle authority for the framework.

## Base Rules

- Bind to `127.0.0.1` by default.
- Return JSON.
- Use structured errors.
- Enforce lifecycle rules centrally.
- Never let dashboard, CLI, or meta MCP bypass the manager for lifecycle actions.

## Service Summary Shape

```json
{
  "id": "memory-server",
  "name": "Memory Server",
  "version": "0.1.0",
  "description": "Stores reusable agent memory and project lessons.",
  "lifecycle": "command_per_client",
  "transport": "stdio",
  "status": "Ready",
  "enabled": true,
  "valid": true,
  "folder": "D:\\Programming\\codex\\mcp-hub\\servers\\memory-server",
  "capabilities_path": "CAPABILITIES.md",
  "readme_path": "README.md",
  "validation_errors": [],
  "last_checked_at": "2026-07-04T12:00:00Z"
}
```

## Endpoints

### `GET /services`

Returns all registered, invalid, disabled, and optionally removed services.

Query parameters:

```text
include_disabled=true
include_invalid=true
```

### `GET /services/{id}`

Returns one service summary plus detail.

### `POST /services/rescan`

Re-runs discovery and validation.

Response should include:

```json
{
  "added": ["memory-server"],
  "changed": [],
  "removed": [],
  "invalid": []
}
```

### `POST /services/{id}/start`

Starts a daemon service.

For `command_per_client`, return:

```json
{
  "status": "not_applicable",
  "message": "This service is launched by each MCP client. Use probe or connection details instead."
}
```

### `POST /services/{id}/stop`

Stops a manager-owned daemon service.

The manager must not kill unrelated processes started by agent hosts.

### `POST /services/{id}/restart`

Restarts a manager-owned daemon service.

### `POST /services/{id}/probe`

Runs a health probe appropriate to the lifecycle and transport.

### `GET /services/{id}/connection`

Returns the canonical direct connection recipe.

### `GET /services/{id}/capabilities`

Returns `CAPABILITIES.md`.

### `GET /services/{id}/readme`

Returns `README.md`.

### `GET /services/{id}/manifest`

Returns normalized manifest data.

### `GET /services/{id}/logs`

Returns recent log lines from declared log locations.

Query parameters:

```text
stream=false
lines=200
source=stdout|stderr|framework
```

### `GET /guidelines`

Returns available guideline documents and example groups.

### `GET /guidelines/{id}`

Returns one guideline document.

Example ids:

```text
server-authoring
```

### `POST /guidelines/recommend-server-type`

Returns the user's preferred server type recommendation for a proposed capability.

The default recommendation should be local stdio command-per-client when the capability is local, reusable, and does not need a long-running shared process.

### `GET /guidelines/examples`

Returns available example groups.

### `GET /guidelines/examples/{example_id}`

Returns an example file tree.

### `GET /guidelines/examples/{example_id}/files/{path}`

Returns one example file.

The manager must treat example code retrieval as read-only. Retrieving example code must not copy, execute, install, or modify anything.

## Error Shape

```json
{
  "error": {
    "code": "PORT_CONFLICT",
    "message": "Declared port conflicts with another enabled daemon service.",
    "details": {
      "port": 7441,
      "conflicting_service": "lessons-server"
    }
  }
}
```

## Required Error Codes

```text
SERVICE_NOT_FOUND
SERVICE_INVALID
LIFECYCLE_ACTION_NOT_APPLICABLE
PORT_CONFLICT
COMMAND_NOT_FOUND
HEALTH_CHECK_FAILED
STARTUP_TIMEOUT
PROCESS_EXITED
PERMISSION_DENIED
CONFIG_INVALID
GUIDELINE_NOT_FOUND
EXAMPLE_NOT_FOUND
```

## Event Log

The manager should keep a small structured event history per service.

Example event:

```json
{
  "time": "2026-07-04T12:00:00Z",
  "service_id": "memory-server",
  "level": "info",
  "event": "probe_completed",
  "message": "MCP initialize probe succeeded."
}
```
