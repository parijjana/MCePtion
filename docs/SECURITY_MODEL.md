# Security Model

## Default Trust Boundary

MCP Hub is local-only by default.

Default binding:

```text
127.0.0.1
```

No manager, dashboard, or meta MCP endpoint should bind to `0.0.0.0` unless remote mode is explicitly enabled.

## Main Risks

### Running Arbitrary Commands

Server manifests define commands. That is useful and dangerous.

Controls:

- Validate all manifests before running commands.
- Show the exact command, args, working directory, and environment references in the dashboard.
- Require paths to stay inside the service folder unless explicitly allowed.
- Prefer argv arrays over shell command strings.
- Avoid shell expansion in manifest commands.

Retrieving guidelines or example code must never execute that code.

### Secrets In Manifests

Manifests should not contain secret values.

Allowed:

```yaml
env:
  API_TOKEN:
    from_env: MEMORY_SERVER_API_TOKEN
```

Not allowed:

```yaml
env:
  API_TOKEN: real-token-value
```

### Dashboard Exposure

The dashboard can start local processes, so it is a control surface.

Controls:

- Bind to localhost.
- Add token auth before any remote mode.
- Validate Origin headers for browser requests.
- Do not expose remote mode without TLS and authentication.

### Meta MCP Control

The meta MCP server can expose lifecycle tools.

Controls:

- Lifecycle tools call the manager API.
- The manager enforces lifecycle and permission rules.
- Dangerous actions should be visible in logs.
- Remote mode should allow read-only meta MCP operation if desired.

### Git Sync

Git sync can accidentally publish sensitive data.

Controls:

- Disabled by default.
- Explicit include rules.
- Dry-run first.
- Never sync logs, caches, secrets, tokens, or process state.
- Show pending sync files in the dashboard.

### Child Server GitHub Orchestration

Version 1 must not automatically clone, pull, push, or update child server repositories.

Future environment replication may use GitHub, but it must remain explicit and should install local copies before runtime use.

## Remote Mode Requirements

Remote mode is out of scope for version 1.

Before remote mode is allowed:

- Token or stronger authentication.
- TLS through a reverse proxy or equivalent.
- Explicit bind address.
- CORS and Origin policy.
- Backup and restore procedure.
- Secrets stored outside Git.
- Dashboard exposure reviewed separately from meta MCP exposure.
