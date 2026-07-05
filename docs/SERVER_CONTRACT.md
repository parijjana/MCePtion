# Server Contract

Every child MCP server must satisfy this contract to be managed by MCP Hub.

## Required Folder Layout

```text
servers/
  memory-server/
    mcp-server.yaml
    CAPABILITIES.md
    README.md
    scripts/
      start.ps1
      stop.ps1
      test.ps1
    src/
    tests/
```

The manager discovers services by scanning:

```text
servers/*/mcp-server.yaml
```

The `servers/` directory is a local install area. Version 1 expects the user to copy server folders into it manually.

MCP Hub should not treat copied child servers as part of the hub repository unless the user explicitly decides to vendor or track one.

## Required Files

### `mcp-server.yaml`

Machine-readable manifest used by the manager, dashboard, and meta MCP server.

### `CAPABILITIES.md`

Agent-readable high-level description of what the server can do, when to use it, and when not to use it.

This is not a `SKILL.md`. It is discovery documentation for any agent.

### `README.md`

Human/developer documentation for installing, running, testing, and publishing the server.

### `scripts/start.ps1`

Standalone startup or launch script.

For daemon services this starts the background service.

For command-per-client stdio services this launches the MCP process for the calling client. The hub may run it only as a temporary probe.

### `scripts/test.ps1`

Standalone validation script.

## Lifecycle Classes

Every server must declare one lifecycle class.

```yaml
lifecycle:
  type: command_per_client
```

Supported values:

```text
command_per_client
  The MCP client launches a new process per connection.
  This is the expected lifecycle for most local stdio servers and should be the default choice.

daemon
  The server runs as a long-lived process supervised by MCP Hub.
  This is the expected lifecycle for Streamable HTTP servers that run locally and truly need a shared live process.

external
  The server is managed outside MCP Hub.
  MCP Hub stores discovery, capabilities, health, and connection details only.
```

The manager must reject a manifest that asks for impossible semantics, such as a shared background `stdio` server without an explicit bridge or gateway configuration.

## Manifest Example For Stdio

```yaml
schema_version: 1
id: memory-server
name: Memory Server
version: 0.1.0
description: Stores reusable agent memory and project lessons.

enabled: true
autostart: false
restart_policy: on_failure

lifecycle:
  type: command_per_client

entrypoint:
  type: command
  command: uv
  args:
    - run
    - python
    - -m
    - memory_server
  working_directory: .

transport:
  type: stdio

scripts:
  start: scripts/start.ps1
  stop: scripts/stop.ps1
  test: scripts/test.ps1

health:
  type: mcp_initialize
  timeout_seconds: 5

ports: []

logs:
  stdout: logs/stdout.log
  stderr: logs/stderr.log

metadata:
  repository: https://github.com/example/memory-server
  license: MIT
  tags:
    - memory
    - context
```

## Manifest Example For Streamable HTTP

```yaml
schema_version: 1
id: lessons-server
name: Lessons Server
version: 0.1.0
description: Stores and searches lessons learned across projects.

enabled: true
autostart: true
restart_policy: on_failure

lifecycle:
  type: daemon

entrypoint:
  type: command
  command: uv
  args:
    - run
    - python
    - -m
    - lessons_server
  working_directory: .

transport:
  type: streamable_http
  url: http://127.0.0.1:7441/mcp

scripts:
  start: scripts/start.ps1
  stop: scripts/stop.ps1
  test: scripts/test.ps1

health:
  type: http
  url: http://127.0.0.1:7441/health
  timeout_seconds: 5

ports:
  - 7441

logs:
  stdout: logs/stdout.log
  stderr: logs/stderr.log

metadata:
  repository: https://github.com/example/lessons-server
  license: MIT
  tags:
    - lessons
    - knowledge
```

## External Service Example

```yaml
schema_version: 1
id: shared-memory-server
name: Shared Memory Server
version: 0.1.0
description: Connects to a memory MCP server managed outside this hub.

enabled: true
autostart: false
restart_policy: never

lifecycle:
  type: external

entrypoint:
  type: none

transport:
  type: streamable_http
  url: http://127.0.0.1:7501/mcp

scripts:
  test: scripts/test.ps1

health:
  type: http
  url: http://127.0.0.1:7501/health
  timeout_seconds: 5

ports: []

logs:
  stdout: ""
  stderr: ""

metadata:
  repository: https://github.com/example/shared-memory-server
  license: MIT
  tags:
    - memory
```

## `CAPABILITIES.md` Template

```md
# Memory Server Capabilities

## Purpose

Stores and retrieves durable agent memory across projects, including lessons, decisions, recurring preferences, and project context.

## When To Use

- Recall previous decisions from this machine.
- Store a reusable lesson learned from a bug or design issue.
- Retrieve project-specific context before editing.
- Search reusable notes across projects.

## When Not To Use

- Do not store secrets.
- Do not store large binary files.
- Do not use this as the source of truth for project documentation.
- Do not use it for temporary logs.

## Main Capabilities

- Search stored memories by keyword or project.
- Add new lessons with tags and project scope.
- Retrieve recent decisions.
- List known projects.
- Attach lightweight metadata to memories.

## Data Scope

Data is stored locally by default and may be synced to a private Git repository if framework sync is enabled.

## Safety Notes

Do not store credentials, API keys, private tokens, or sensitive personal data.

## Typical Workflow

1. Search for relevant context before beginning work.
2. Use returned lessons to guide implementation.
3. Add a new lesson only when the result is reusable.
```

## Validity Rules

A server is valid when:

- `mcp-server.yaml` parses correctly.
- `schema_version` is supported.
- `id` is unique.
- `lifecycle.type` is supported.
- `CAPABILITIES.md` exists.
- `README.md` exists.
- The declared startup script or entrypoint exists when lifecycle requires it.
- The declared test script exists.
- The transport is supported.
- Lifecycle and transport are compatible.
- Declared ports do not conflict with another enabled daemon service.
- Path fields are relative to the server root unless explicitly documented otherwise.
- Commands do not require shell expansion to be interpreted correctly.

Invalid services should appear in the dashboard with actionable validation errors.

## Managed Mode Rule

The manager may pass a `--managed` flag to startup scripts only for logging, PID, or environment behavior.

The flag must not change MCP protocol behavior.

The child server must remain usable without the hub.

## Capability Brief Validation

`CAPABILITIES.md` should include these headings:

```text
Purpose
When To Use
When Not To Use
Main Capabilities
Data Scope
Safety Notes
Typical Workflow
```

The manager should not reject a server solely because the prose is imperfect, but it should warn when a required heading is missing.

## Connection Recipe Rules

The manager derives connection recipes from the manifest.

For `stdio`, the recipe must include:

- `command`
- `args`
- `cwd`
- optional `env`

For Streamable HTTP, the recipe must include:

- `url`
- optional `headers`

Secrets must never be embedded directly in a manifest. Use environment variable names or secret references instead.

## Status Semantics

Command-per-client services:

```text
Ready
Disabled
Invalid
Probe Failed
```

Daemon services:

```text
Stopped
Starting
Running
Unhealthy
Crashed
Disabled
Invalid
```

External services:

```text
Reachable
Unreachable
Unknown
Disabled
Invalid
```
