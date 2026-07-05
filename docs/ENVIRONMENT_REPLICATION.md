# Environment Replication

Version 1 does not manage child server GitHub repositories.

The user installs child servers by copying their folders into:

```text
servers/
```

MCP Hub discovers them from:

```text
servers/*/mcp-server.yaml
```

## Current Policy

- No automatic clone.
- No automatic pull.
- No automatic push.
- No submodule management.
- No assumption that copied servers belong to the hub repository.
- The `servers/` directory is a local install area.

## Future Goal

Later, MCP Hub may support reproducing the same environment on another machine.

The goal is:

```text
same meta server
same installed child server set
same local execution model
```

The result should still run locally once setup is complete.

## Proposed Future Manifest

```yaml
schema_version: 1
servers:
  - id: lessons-server
    source:
      type: git
      url: git@github.com:example/lessons-server.git
      ref: main
    target: servers/lessons-server
    expected_manifest: mcp-server.yaml

  - id: ui-preferences-server
    source:
      type: git
      url: git@github.com:example/ui-preferences-server.git
      ref: v0.2.0
    target: servers/ui-preferences-server
    expected_manifest: mcp-server.yaml
```

## Proposed Future Lockfile

```yaml
schema_version: 1
servers:
  - id: lessons-server
    url: git@github.com:example/lessons-server.git
    ref: main
    resolved_commit: abc123
    target: servers/lessons-server
```

## Important Boundary

Environment replication should orchestrate installation, not merge server ownership.

Each child server must remain:

- Independently runnable.
- Independently testable.
- Independently publishable.
- Directly usable without MCP Hub.

## Sync Exclusions

Never replicate:

- Secrets.
- Runtime logs.
- Local process state.
- Caches.
- Build output.
- User-specific tokens.
