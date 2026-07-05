# Product Requirements

## Product

MCP Hub is a local framework for managing independently usable MCP servers.

## Primary User

The primary user is a developer who uses multiple LLM agents and wants to avoid repeatedly configuring the same local MCP servers in every new agent environment.

## Goals

- Provide one local framework startup script.
- Provide one stdio-first meta MCP server that agents can connect to first.
- Keep every managed MCP server independently runnable and publishable.
- Provide a dashboard for human lifecycle, health, and log inspection.
- Support precise server scaffolding so new servers can be added without LLM intervention.
- Preserve a path to private Git sync, VPS hosting, and later containerized runtimes.
- Avoid misleading lifecycle behavior for stdio servers.
- Make server capabilities readable by humans and agents.
- Provide server-authoring guidelines and example code through the meta MCP server.

## User Stories

### Discover Existing Servers

As an agent, I can call the meta MCP server and list available MCP services, so I can decide which server is relevant.

### Read Capability Briefs

As an agent, I can read each server's `CAPABILITIES.md`, so I understand the server's purpose, boundaries, and safe usage.

### Get Direct Connection Details

As an agent, I can request direct connection details for an individual server, so I can use that server independently instead of relying on a proxy.

### Get Authoring Guidance

As an agent, I can ask the meta MCP server for guidelines and example code, so I can create or modify a server according to the user's preferences.

### Understand Lifecycle Semantics

As the user, I can see whether a service is command-per-client, daemon, or external, so I know whether start/stop controls are real process controls or readiness checks.

### Manage Servers Locally

As the user, I can open a dashboard and use lifecycle-appropriate controls for each MCP server.

### Add A Server Without An LLM

As the user, I can copy a valid server folder into `servers/`, rescan, and have the framework register it.

## Functional Requirements

- The framework must scan `servers/*/mcp-server.yaml`.
- The framework must validate required manifest fields.
- The framework must require `CAPABILITIES.md` for each service.
- The framework must expose capability docs through the meta MCP server.
- The framework must show invalid services and validation errors in the dashboard.
- The framework must support stdio and Streamable HTTP child MCP servers.
- The framework must distinguish `command_per_client`, `daemon`, and `external` lifecycle classes.
- The framework must default new local server guidance to stdio command-per-client.
- The manager must own lifecycle operations.
- The dashboard, meta MCP server, and CLI must call the manager instead of spawning child servers directly.
- The meta MCP server must expose direct connection recipes.
- The meta MCP server must expose authoring guidelines and example code.
- The dashboard must show lifecycle-appropriate controls.
- The validator must reject incompatible lifecycle and transport combinations.

## Non-Functional Requirements

- Local services bind to `127.0.0.1` by default.
- The meta MCP server supports stdio as the default local agent integration.
- Runtime logs, caches, secrets, and process state stay out of Git.
- Child server protocol behavior is the same in standalone and managed modes.
- The architecture supports a future container runtime adapter without requiring containers in version 1.
- Startup scripts must work on Windows first.
- Runtime state must be rebuildable from manifests and process inspection.
- The framework must not claim that a stdio server is running for arbitrary external clients unless an explicit bridge or gateway is enabled.

## Success Metrics

- A valid server copied into `servers/` appears after rescan without editing hub code.
- An invalid server appears with actionable validation errors.
- A command-per-client stdio server shows as Ready after validation or probe, not Running.
- A daemon HTTP server can be started, stopped, restarted, and health-checked from the dashboard.
- The meta MCP server can return `CAPABILITIES.md`, manifest data, status, and connection recipes for every valid service.
- The meta MCP server can recommend local stdio, daemon HTTP, external, or no-server based on declared needs.
- The user can configure a new agent by starting with the meta MCP connection details.

## Out Of Scope For Version 1

- Public internet hosting.
- Required Podman or Docker.
- Forced gateway/proxying of child tools.
- Multi-user access control.
- Automatic publication to GitHub.
- Dynamic reconfiguration of every possible agent host.
- Managing child server GitHub repositories in version 1.
