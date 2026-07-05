# Architecture

## Overview

MCP Hub is composed of a manager, dashboard, meta MCP server, CLI scripts, server folders, and templates.

```text
Agent
  |
  | stdio MCP by default
  v
Meta MCP Server
  |
  | local Manager API
  v
Manager
  |       |        |
  v       v        v
Server  Server   Server

Browser
  |
  | HTTP
  v
Dashboard
  |
  | local Manager API
  v
Manager
```

## Manager

The manager owns:

- Discovery.
- Manifest validation.
- Registry state.
- Process supervision.
- Health checks.
- Lifecycle actions.
- Log indexing.
- Connection recipe generation.

The manager should expose a local API on `127.0.0.1` only.

Example local endpoints:

```text
GET  /services
GET  /services/{id}
POST /services/{id}/start
POST /services/{id}/stop
POST /services/{id}/restart
POST /services/{id}/probe
POST /services/rescan
GET  /services/{id}/logs
GET  /services/{id}/capabilities
GET  /services/{id}/connection
GET  /health
```

The manager is the only component that starts or stops child server daemon processes.

For command-per-client servers, the manager validates and probes the launch recipe but does not pretend to own a persistent background service.

## Service Lifecycle Classes

MCP Hub separates transport from lifecycle.

```text
command_per_client
  A client launches the process for its own MCP session.
  Typical transport: stdio.
  Hub actions: validate, probe, enable, disable, expose connection recipe.

daemon
  A long-running process accepts client connections.
  Typical transport: streamable_http.
  Hub actions: start, stop, restart, supervise, health-check, expose URL.

external
  A service owned by something else.
  Typical transport: streamable_http.
  Hub actions: validate metadata, health-check if configured, expose URL.
```

The dashboard and meta MCP server must expose the lifecycle class so agents and humans do not confuse "ready to launch" with "currently running".

## Meta MCP Server

The meta MCP server is the one MCP server that future agents can be configured to use first.

It does not own lifecycle state. It calls the manager API.

The default local transport is stdio. Each agent host launches its own meta MCP process. Optional Streamable HTTP mode can be added later, but it is secondary.

It exposes:

- Service registry tools.
- Service lifecycle tools.
- Capability resources.
- Guidelines tools.
- Example code resources.
- README resources.
- Manifest resources.
- Connection information for individual MCP servers.

It should return direct connection details for child servers instead of pretending the child server is part of the meta server.

The meta MCP server is allowed to start, stop, or probe services only by calling the manager API.

## Dashboard

The dashboard is a local human interface over the same manager API.

It should be useful without an LLM:

- See what is up.
- See what is down.
- See why something is invalid.
- Start and stop daemon services.
- Probe command-per-client services.
- Copy connection configs.
- Inspect capability briefs.
- Inspect logs.

## Child MCP Servers

Child servers live in `servers/{id}/`.

They are standalone silos. The hub may supervise them, but they remain independently publishable.

For daemon services, the manager starts them through:

1. The `scripts.start` path in `mcp-server.yaml`, if present.
2. The explicit `entrypoint` command in `mcp-server.yaml`, otherwise.

The startup path must be public and documented.

For command-per-client services, the manager uses the same script or entrypoint only for probe and validation. Actual agent use happens through the direct MCP launch recipe returned by the meta MCP server or copied from the dashboard.

Most child MCP servers should be command-per-client stdio servers. Daemon services are supported for the cases that genuinely need a shared live process.

## Registry

The registry stores discovered services and runtime state.

Initial implementation can use:

```text
data/registry.json
```

Later implementation can move to:

```text
data/registry.sqlite
```

Registry state should include:

- Service id.
- Name.
- Version.
- Folder path.
- Manifest path.
- Status.
- Lifecycle class.
- Health state.
- Last health check.
- PID if process-managed.
- Declared transport.
- Declared connection details.
- Validation errors.
- Log paths.
- Capability summary.
- README path.

## Runtime Adapters

The manager should define a runtime adapter interface early, even if only one adapter exists.

```text
RuntimeAdapter.start(service)
RuntimeAdapter.stop(service)
RuntimeAdapter.restart(service)
RuntimeAdapter.status(service)
RuntimeAdapter.logs(service)
RuntimeAdapter.probe(service)
```

Initial adapter:

```text
ProcessRuntimeAdapter
```

Future adapters:

```text
ContainerRuntimeAdapter
RemoteRuntimeAdapter
```

This keeps future Podman or VPS migration possible without making version 1 complicated.

## Data Flow For Start

Daemon service:

```text
Dashboard or Meta MCP calls start_service(memory-server)
Manager loads registry entry
Manager validates manifest if needed
Manager resolves startup script or entrypoint
Manager starts process using declared working directory
Manager records PID and log paths
Manager runs health check
Manager returns status
```

Command-per-client service:

```text
Dashboard or Meta MCP calls probe_service(memory-server)
Manager loads registry entry
Manager validates manifest if needed
Manager starts a temporary probe process
Manager performs MCP initialize if configured
Manager terminates the probe process
Manager returns Ready or Probe Failed
```

## Data Flow For Discovery

```text
Manager scans servers/*/mcp-server.yaml
Manager validates manifest schema
Manager checks required files
Manager reads CAPABILITIES.md summary
Manager determines lifecycle class
Manager records valid and invalid services
Dashboard and Meta MCP read from registry
```

## Connection Recipe Generation

The manager should generate connection recipes from the manifest instead of letting every UI construct its own format.

For stdio services:

```json
{
  "transport": "stdio",
  "command": "uv",
  "args": ["run", "python", "-m", "memory_server"],
  "cwd": "D:\\Programming\\codex\\mcp-hub\\servers\\memory-server",
  "env": {}
}
```

For Streamable HTTP services:

```json
{
  "transport": "streamable_http",
  "url": "http://127.0.0.1:7441/mcp",
  "headers": {}
}
```

The dashboard may transform these recipes into host-specific snippets, but the recipe itself is the canonical data.

## Guidelines Corpus

The meta MCP server exposes a local guidelines corpus:

```text
guidelines/SERVER_AUTHORING_GUIDELINES.md
guidelines/examples/
```

These files are read-only guidance for agents. They should explain the user's preferences for server type selection and provide small reference implementations.

Guidelines are not child services. They are part of the meta MCP server's own capability surface.

## Network Binding

Default ports should be configurable, but local-only:

```yaml
manager:
  host: 127.0.0.1
  port: 7420

dashboard:
  host: 127.0.0.1
  port: 7421

meta_mcp:
  default_transport: stdio
  streamable_http:
    enabled: false
    host: 127.0.0.1
    port: 7422
```

No component should bind to `0.0.0.0` unless the user explicitly enables remote mode.

## Internal Authority Boundary

The authority boundary is:

```text
Meta MCP and Dashboard may request lifecycle actions.
Manager decides whether those actions are valid.
Runtime adapter performs only manager-approved actions.
Child server owns its own MCP implementation and data.
```

This prevents the meta MCP server from becoming an accidental second supervisor.
