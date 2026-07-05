# MCP Server Authoring Guidelines

These guidelines describe when to create MCP servers, what type to create, and how to keep them useful across agents and projects.

They are written for agents that may not have enough judgment to infer the intended architecture from scattered notes.

## Default Choice

Prefer a local stdio MCP server with `lifecycle.type: command_per_client`.

This is the normal choice for this environment because most useful servers are local tools over local files, local knowledge, or local preferences.

Use stdio when:

- The server is only used on this machine.
- Each agent can launch its own process.
- The server stores shared durable data in files or SQLite.
- The server does not need to accept browser or remote network traffic.
- The server should be easy for other users to run in their own local environment.

## Why Create A Server At All

Create an MCP server when the capability should be shared across projects, agents, or future sessions.

Good reasons:

- Durable memory across projects.
- Lessons learned from repeated bugs.
- Default UI/UX preferences.
- Reusable codebase audit tools.
- Shared local indexes.
- Stable project context that multiple agents should read.
- Tools with a clear domain owner and repeatable interface.

Poor reasons:

- One-off scripts.
- Single-project helpers with no reuse value.
- Thin wrappers around a command the agent can run directly.
- Data that belongs in the current repository.
- Anything involving secrets without a clear storage model.

## Server Type Selection

### Local Stdio Server

Use this for the majority of personal MCP servers.

Examples:

- Lessons learned server.
- UI design preferences server.
- Project context lookup server.
- Local snippets server.
- Standards or audit helper server.

Manifest shape:

```yaml
lifecycle:
  type: command_per_client

transport:
  type: stdio
```

### Local HTTP Daemon

Use this only when a long-running process is genuinely useful.

Good reasons:

- Multiple clients need the same live process at the same time.
- The server has expensive warm state.
- The server exposes a browser UI.
- The server needs push-style behavior or long-lived subscriptions.
- The server is being prepared for LAN, VPS, or container hosting.

Manifest shape:

```yaml
lifecycle:
  type: daemon

transport:
  type: streamable_http
```

### External Service

Use this when MCP Hub should document and health-check a service it does not own.

Manifest shape:

```yaml
lifecycle:
  type: external
```

### Gateway Or Proxy

Do not use this by default.

Gateway mode is only for compatibility with hosts that cannot connect to multiple MCP servers or cannot launch local stdio commands. It must not become the canonical way to test or describe a child server.

## Tool, Resource, And Prompt Choices

Use tools for actions:

- Write memory.
- Run an audit.
- Update a preference.
- Search with parameters.

Use resources for readable context:

- `lessons://recent`
- `preferences://ui`
- `project://current/summary`
- `hub://services/{id}/capabilities`

Use prompts only when the server owns a reusable interaction pattern.

Do not make everything a tool. Agents should be able to read stable context without causing side effects.

## Data Ownership

Each server should own one domain.

Good boundaries:

- `lessons-server` owns lessons learned.
- `ui-preferences-server` owns UI/UX defaults.
- `project-context-server` owns project summaries and local context indexes.

Poor boundaries:

- One giant server that owns all personal memory.
- Several servers writing the same file.
- A server that edits arbitrary repositories without a narrow purpose.

## Storage Preference

Start simple:

- JSONL for append-only records.
- SQLite for searchable structured data.
- Markdown for human-readable durable notes.

Avoid:

- Global mutable blobs with no schema.
- Binary formats unless required.
- Data paths outside the server folder unless the manifest documents them.

## Required Files

Every server should include:

```text
mcp-server.yaml
CAPABILITIES.md
README.md
scripts/start.ps1
scripts/test.ps1
src/
tests/
```

`CAPABILITIES.md` is the agent-facing brief. It is not the same as README and it is not a Codex skill.

## Example Code

Use the examples under:

```text
guidelines/examples/
```

The default reference example is:

```text
guidelines/examples/python-stdio-fastmcp/
```

## GitHub Policy

Version 1 does not manage child server repositories.

The user copies server folders into:

```text
servers/
```

Later environment replication may use GitHub to reproduce the same hub plus child server set on another machine, but the result should still be local execution once setup is complete.
