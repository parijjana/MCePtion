# Meta MCP Contract

The meta MCP server is the agent-facing registry, control surface, and authoring guidance server for MCP Hub.

It does not proxy child server tools by default. It exposes service discovery, capability briefs, direct connection recipes, and lifecycle requests.

The default local transport for the meta MCP server is stdio. Agent hosts should normally launch it as a command-per-client server. Optional Streamable HTTP mode may exist later, but it is not the preferred local path.

## Tools

### `hub.list_services`

Returns all discovered services.

Input:

```json
{
  "include_disabled": true,
  "include_invalid": true
}
```

Output:

```json
{
  "services": [
    {
      "id": "memory-server",
      "name": "Memory Server",
      "version": "0.1.0",
      "lifecycle": "command_per_client",
      "transport": "stdio",
      "status": "Ready",
      "summary": "Stores reusable agent memory and project lessons.",
      "capabilities_resource": "hub://services/memory-server/capabilities"
    }
  ]
}
```

### `hub.describe_service`

Returns one service with manifest summary, lifecycle, status, and links to resources.

Input:

```json
{
  "id": "memory-server"
}
```

Output:

```json
{
  "id": "memory-server",
  "name": "Memory Server",
  "version": "0.1.0",
  "description": "Stores reusable agent memory and project lessons.",
  "lifecycle": "command_per_client",
  "transport": "stdio",
  "status": "Ready",
  "health": {
    "state": "passing",
    "last_checked_at": "2026-07-04T12:00:00Z"
  },
  "resources": {
    "capabilities": "hub://services/memory-server/capabilities",
    "readme": "hub://services/memory-server/readme",
    "manifest": "hub://services/memory-server/manifest"
  }
}
```

### `hub.get_service_connection`

Returns the canonical direct connection recipe.

For stdio:

```json
{
  "id": "memory-server",
  "lifecycle": "command_per_client",
  "connection": {
    "transport": "stdio",
    "command": "uv",
    "args": ["run", "python", "-m", "memory_server"],
    "cwd": "D:\\Programming\\codex\\mcp-hub\\servers\\memory-server",
    "env": {}
  },
  "notes": [
    "This is a command-per-client service. The agent host launches its own process."
  ]
}
```

For Streamable HTTP:

```json
{
  "id": "lessons-server",
  "lifecycle": "daemon",
  "connection": {
    "transport": "streamable_http",
    "url": "http://127.0.0.1:7441/mcp",
    "headers": {}
  },
  "notes": [
    "This service must be running before clients connect."
  ]
}
```

### `hub.get_service_capabilities`

Returns the parsed or raw `CAPABILITIES.md`.

Input:

```json
{
  "id": "memory-server",
  "format": "markdown"
}
```

### `hub.get_service_status`

Returns status, health, validation errors, process information when applicable, and recent events.

### `hub.list_guidelines`

Returns available guideline documents and example groups.

### `hub.get_guideline`

Returns a guideline document, such as the server authoring guidance.

Input:

```json
{
  "id": "server-authoring"
}
```

### `hub.recommend_server_type`

Recommends what kind of MCP server to create.

Input:

```json
{
  "shared_across_projects": true,
  "local_only": true,
  "stores_durable_data": true,
  "needs_long_running_process": false,
  "needs_multiple_simultaneous_clients": false,
  "needs_browser_ui": false,
  "remote_access_required": false
}
```

Output:

```json
{
  "recommendation": "local_stdio_command_per_client",
  "manifest": {
    "lifecycle": "command_per_client",
    "transport": "stdio"
  },
  "reason": "The capability is local and reusable across agents, but it does not need a long-running process.",
  "reference_examples": [
    "hub://guidelines/examples/python-stdio-fastmcp"
  ]
}
```

### `hub.get_example_code`

Returns example file content or an example file listing.

Input:

```json
{
  "example_id": "python-stdio-fastmcp",
  "path": "src/example_memory_server/__main__.py"
}
```

### `hub.start_service`

Starts daemon services.

For command-per-client services, this must return a clear message that the service is launched by the client and offer `hub.probe_service` instead.

### `hub.stop_service`

Stops daemon services owned by the manager.

For command-per-client services, this must not kill unrelated client-launched instances.

### `hub.restart_service`

Restarts daemon services owned by the manager.

### `hub.probe_service`

Runs a readiness probe.

For stdio services, this may launch a temporary process, perform MCP initialization, and then terminate the probe process.

### `hub.rescan_services`

Re-runs discovery and validation.

### `hub.tail_service_logs`

Returns recent log lines from declared log paths. It must not expose secrets intentionally stored outside logs.

## Resources

```text
hub://services
hub://services/{service_id}/capabilities
hub://services/{service_id}/readme
hub://services/{service_id}/manifest
hub://services/{service_id}/connection
hub://services/{service_id}/status
hub://guidelines/server-authoring
hub://guidelines/examples
hub://guidelines/examples/python-stdio-fastmcp
hub://guidelines/examples/python-stdio-fastmcp/{path}
```

## Error Shape

Tool errors should be structured.

```json
{
  "error": {
    "code": "SERVICE_INVALID",
    "message": "Service manifest is invalid.",
    "details": [
      "CAPABILITIES.md is missing.",
      "transport.type must be one of: stdio, streamable_http."
    ]
  }
}
```

## Capability Summary

`hub.list_services` may include a short summary derived from the manifest description or the first paragraph of `CAPABILITIES.md`.

The full `CAPABILITIES.md` remains the source of truth.
