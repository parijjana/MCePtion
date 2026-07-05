# MCP Hub Plan

## Problem

Several useful MCP servers may be built over time by different agents. Configuring each server repeatedly for every new agent is tedious, error-prone, and easy to abandon.

The desired workflow is:

1. Install and run one local framework on the primary PC.
2. Copy independently usable MCP server folders into the framework.
3. Let the framework discover, validate, monitor, describe, and lifecycle-manage those servers.
4. Point any future agent at one meta MCP server.
5. Let the agent inspect what services exist, what they do, and how to connect to them.

Most intended child servers are local. They exist because the user needs shared memory and shared preferences across projects and agents, not because the user wants a network service. Examples include lessons learned, reusable project context, and default UI design choices.

Therefore the default child server shape should be local stdio, not Streamable HTTP.

## Non-Negotiable Constraint

Each child MCP server must remain standalone.

This means:

- It has its own repository-ready folder.
- It has its own README.
- It has its own startup and test scripts.
- It can be copied out of the hub and used directly by another person.
- When the hub starts or probes the server, it uses the same public command or script an external user would use.
- The hub must not require private imports, shared process state, or hidden protocol changes.

## Product Model

MCP Hub is a local MCP service manager, not primarily a tool gateway.

It contains three major runtime components:

```text
Dashboard  -> Manager API -> Supervisor
Meta MCP   -> Manager API -> Supervisor
CLI        -> Manager API -> Supervisor
```

The manager is the lifecycle authority. The dashboard and meta MCP server are clients of the manager.

The meta MCP server should be stdio-first. In the default local setup, each agent host launches the meta MCP process as its own stdio MCP server. That meta process then reads hub state or calls the local manager API. Optional Streamable HTTP mode may be added later for hosts that prefer HTTP, but it should not be the default local path.

## Critical Transport And Lifecycle Distinction

MCP transport type is not the same thing as service lifecycle.

This matters most for `stdio`.

A `stdio` MCP server is normally launched by the MCP client or host for that specific connection. It communicates through that process's stdin and stdout. A separate manager process cannot start one shared stdio server in the background and then let unrelated agents attach to it directly. If MCP Hub did that, it would need to become a proxy or bridge, which is not the default product goal.

Therefore MCP Hub must classify services by lifecycle:

```text
command_per_client
  Usually stdio.
  The hub validates the server, records the direct launch recipe, runs health probes, and tells agents how to connect.
  The hub does not keep the server "running" for other clients.

daemon
  Usually Streamable HTTP.
  The hub can start, stop, restart, supervise, and health-check the server process.
  Agents connect to the server's declared URL.

external
  A server owned by another supervisor, machine, or service account.
  The hub records metadata, capabilities, health, and connection details but does not own lifecycle.
```

Dashboard labels must reflect this distinction:

```text
command_per_client: Ready, Invalid, Disabled, Probe Failed
daemon: Stopped, Starting, Running, Unhealthy, Crashed, Disabled
external: Reachable, Unreachable, Unknown, Disabled
```

The user-facing "start" and "stop" buttons are only true lifecycle operations for daemon services. For command-per-client servers, the dashboard should show actions such as Probe, Test, Enable, Disable, View Config, and Open Logs.

## What The Meta MCP Server Does

The meta MCP server tells agents what is available and how to connect.

It should expose tools such as:

```text
hub.list_services
hub.describe_service
hub.get_service_status
hub.get_service_connection
hub.get_service_capabilities
hub.list_guidelines
hub.get_guideline
hub.recommend_server_type
hub.get_example_code
hub.start_service
hub.stop_service
hub.restart_service
hub.rescan_services
hub.tail_service_logs
```

It should expose resources such as:

```text
hub://services/{service_id}/capabilities
hub://services/{service_id}/readme
hub://services/{service_id}/manifest
hub://guidelines/server-authoring
hub://guidelines/examples/python-stdio-fastmcp
```

The meta MCP server does not need to proxy every child server's tools by default.

The meta MCP server cannot assume every agent host can dynamically add new MCP connections from inside a conversation. Its job is to expose accurate service metadata and connection recipes. Whether the agent can use that recipe automatically depends on that agent host's MCP implementation.

The dashboard should therefore also provide copyable config snippets for common hosts. The meta MCP server should provide the same snippets as data.

The guidelines tools are part of the product, not optional docs. They encode the user's preferences for when to create a new server, which lifecycle and transport to choose, and what example code to copy. They are especially important for less capable agents.

## What The Manager Does

The manager:

- Scans `servers/*/mcp-server.yaml`.
- Validates each manifest.
- Registers valid services.
- Marks invalid folders with validation errors.
- Starts enabled daemon services.
- Stops and restarts daemon services.
- Probes command-per-client services without treating them as background daemons.
- Runs health checks.
- Tracks process IDs, ports, status, last check time, and log paths.
- Reads and indexes the guidelines corpus for meta MCP and dashboard use.
- Provides a local Manager API used by the dashboard, CLI, and meta MCP server.

## What The Dashboard Does

The dashboard provides a local browser interface for humans.

Minimum dashboard features:

- List all discovered services.
- Show status, health, transport, ports, and last check time.
- Start, stop, and restart daemon services.
- Probe command-per-client services.
- Trigger a rescan.
- View manifest validation errors.
- View exposed capability summaries.
- View logs.
- Show copyable connection details for each server.
- Show the meta MCP connection details for agent setup.

The dashboard should not show misleading controls. A stdio command-per-client server should not have a Stop button unless the hub is currently running a probe process for it.

## Server Discovery Workflow

The intended no-LLM workflow is:

1. Download or copy a server folder into `servers/`.
2. Ensure the folder contains `mcp-server.yaml`.
3. Ensure the folder contains `CAPABILITIES.md`.
4. Click Rescan in the dashboard or run a rescan command.
5. The manager validates the folder and adds it to the registry.
6. If the server is a daemon and `autostart` is enabled, the manager starts it.
7. If the server is command-per-client, the manager marks it Ready after validation and optional health probing.

Version 1 does not manage child server GitHub repositories. The install mechanism is manual copy into the designated `servers/` directory followed by rescan.

## Modes

### Standalone Mode

The child server is run directly:

```powershell
.\servers\memory-server\scripts\start.ps1
```

This is the canonical mode for external users and conformance testing.

### Managed Mode

The hub starts the same server through its manifest or startup script:

```powershell
.\scripts\start-framework.ps1
```

The server remains an independent process and uses the same MCP behavior as standalone mode.

For command-per-client services, managed mode means the hub manages registration, validation, probing, documentation, and connection recipes. It does not own a persistent server process.

For daemon services, managed mode means the hub owns the process lifecycle.

### Optional Gateway Mode

Future versions may optionally proxy child tools through one MCP endpoint for agents that only support one MCP connection.

This must be disabled by default and must not become the canonical execution mode for child servers.

If added, gateway mode must be explicit per service:

```yaml
gateway:
  enabled: false
```

Gateway mode is a compatibility layer, not the source of truth for testing or documentation.

## Capability Briefs

Every service must include `CAPABILITIES.md`.

This file is not a skill, not a full README, and not a generated tool list. It is the high-level brief an agent reads before deciding whether to use a server.

It should answer:

- What does this server own?
- When should an agent use it?
- When should an agent avoid it?
- What data is safe or unsafe to store?
- What are the main workflows?
- What are the direct connection options?

The meta MCP server exposes this file as a resource and may also return a short summary from it in `hub.describe_service`.

## Local First, VPS Later

Version 1 should run only on the local machine and bind HTTP services to `127.0.0.1`.

The architecture should still prepare for later deployment by using runtime adapters:

```text
ProcessRuntimeAdapter
ContainerRuntimeAdapter
RemoteRuntimeAdapter
```

Only the process adapter is required initially.

## Private Git Sync

Git sync should be optional and conservative.

For version 1, Git sync does not manage child server repositories. The user copies server folders into `servers/`.

Future environment replication may use GitHub to recreate the same hub plus child server set on another PC. That should be treated as installation orchestration, not as merging child server ownership into the hub.

It may sync:

- Knowledge files.
- Server configuration.
- Server source code only when the hub repo actually owns that code.
- Capability docs.
- Non-secret data intended for reuse.

It must not sync:

- Secrets.
- Tokens.
- Runtime logs.
- Cache folders.
- Build output.
- Local process state.

Sync must operate from explicit include rules, not broad repository adds. The default should be dry-run or disabled until the user enables it.

## Guidelines Corpus

The hub should include a local guidelines corpus under:

```text
guidelines/
```

The initial required document is:

```text
guidelines/SERVER_AUTHORING_GUIDELINES.md
```

The initial required example is:

```text
guidelines/examples/python-stdio-fastmcp/
```

The meta MCP server exposes these through `hub.get_guideline`, `hub.recommend_server_type`, and `hub.get_example_code`.

Default guidance:

- Prefer local stdio command-per-client servers.
- Create a server only when the capability is reusable across projects, agents, or future sessions.
- Use HTTP daemon servers only when a long-running shared process is genuinely needed.
- Keep each server's data ownership narrow.
- Store durable shared memory in a simple local store such as JSONL, Markdown, or SQLite.
- Never store secrets in memory servers or manifests.

## Manager State Model

The manager should separate durable configuration from runtime state.

Durable configuration:

```text
framework.yaml
servers/*/mcp-server.yaml
servers/*/CAPABILITIES.md
servers/*/README.md
```

Runtime state:

```text
data/runtime-state.json
data/registry.sqlite
logs/
```

Runtime state should be rebuildable from the server folders plus active process inspection.

## Failure Handling

MCP Hub must make failure states visible instead of hiding them.

Expected failure classes:

- Invalid manifest.
- Missing required file.
- Duplicate service id.
- Port conflict.
- Startup command not found.
- Startup exits immediately.
- Health check timeout.
- Stale PID.
- Log path unavailable.
- Git sync conflict.
- External service unreachable.

The dashboard and meta MCP server should expose enough detail to fix the issue without reading source code.

## Security Baseline

Initial local security expectations:

- Bind dashboard, manager API, and any optional meta MCP HTTP endpoint to `127.0.0.1`.
- Keep secrets outside Git.
- Do not expose the dashboard to LAN or internet by default.
- Validate manifests before running anything.
- Show the exact command the manager will run.
- Store logs under the hub's `logs/` directory or the child server's declared log paths.
- Avoid writing protocol logs to stdio for stdio MCP servers.
