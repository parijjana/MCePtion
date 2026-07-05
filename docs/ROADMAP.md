# Roadmap

## Version 0.1: Local Skeleton

- Create repository structure.
- Add `framework.yaml`.
- Add manifest schema.
- Add server validator.
- Add lifecycle model: `command_per_client`, `daemon`, and `external`.
- Add process runtime adapter.
- Add basic manager API.
- Add meta MCP server with registry tools.
- Add stdio-first meta MCP launcher contract.
- Add basic dashboard with lifecycle-aware labels.
- Add start and stop scripts.
- Add one sample stdio server.
- Add authoring guidelines resource and one Python stdio example.

## Version 0.2: Real Local Use

- Add health checks.
- Add log viewing.
- Add rescan flow.
- Add Windows autostart installer.
- Add server template generator.
- Add `CAPABILITIES.md` resource exposure.
- Add copyable per-server agent config output.
- Add stdio probe flow that does not leave a fake background service running.
- Add HTTP daemon supervision with restart policy.
- Add `hub.recommend_server_type`.
- Add `hub.get_example_code`.

## Version 0.3: Knowledge Sync

- Add optional private Git sync.
- Add sync include/exclude rules.
- Add sync status to dashboard.
- Add conflict handling policy.
- Add backup and restore docs.
- Add dry-run sync preview.

## Version 0.3.5: Environment Replication Planning

- Add optional `environment/servers.yaml`.
- Add optional `environment/servers.lock.yaml`.
- Keep child servers independently cloned or copied.
- Do not add automatic GitHub orchestration until local copy-in workflow is stable.

## Version 0.4: Hardening

- Add dashboard auth token.
- Add manager API token.
- Add config validation tests.
- Add service permission declarations.
- Add safer environment variable handling.
- Add structured audit logs.
- Add command allowlist and path boundary checks.
- Add manifest schema migration tests.

## Version 0.5: Portability

- Add container runtime adapter design.
- Add optional Podman adapter prototype.
- Add remote runtime adapter design.
- Add VPS deployment guide.
- Add reverse proxy and TLS guide.
- Add remote mode security checklist.

## Version 0.6: Optional Compatibility Gateway

- Add explicit opt-in gateway/proxy design.
- Keep direct server use as the canonical mode.
- Require per-service gateway enablement.
- Add tests proving gateway mode does not change standalone server behavior.

## Explicit Non-Goals For Early Versions

- No Podman requirement.
- No public internet exposure.
- No forced tool proxying through the meta MCP server.
- No hidden shared runtime for child servers.
- No automatic syncing of secrets, logs, caches, or build output.
- No claim that stdio servers are background daemons.
- No version 1 management of child server Git repositories.
