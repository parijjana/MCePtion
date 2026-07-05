# Copy-In Validation Execution Plan

Status: ACTIVE

## Objective

Implement and harden the MCP Hub copy-in validation workflow.

The user workflow is:

```text
1. Copy an independent MCP server folder into mcp-hub/servers/<name>.
2. Run .\scripts\validate-server.ps1 .\servers\<name>.
3. Fix actionable validation errors if any.
4. Run rescan or use the dashboard/meta MCP server.
```

The workflow must not require GitHub, a shared runtime, a running framework process, or LLM intervention.

## Required Reading

Before editing, read:

```text
D:\Programming\codex\AGENTS.md
D:\Programming\codex\progress-logs\2026-07-05.md
mcp-hub/docs/NEXT_SESSION_PLAN.md
mcp-hub/docs/PLAN.md
mcp-hub/docs/SERVER_CONTRACT.md
mcp-hub/docs/OPERATIONS.md
mcp-hub/docs/TEST_STRATEGY.md
mcp-hub/gate/gate.yaml
```

## Current State

`scripts/validate-server.ps1` already calls:

```powershell
uv run mcp-hub --root . validate-server <path>
```

The CLI currently loads `mcp-server.yaml` through discovery and returns `service.as_dict()`.

That is a useful base, but this slice needs a complete workflow contract, tests, and clearer output for copied child server folders.

## Non-Negotiable Rules

- Do not require the framework manager process to be running.
- Do not run child server startup scripts during validation.
- Do not clone, pull, push, or inspect Git remotes.
- Do not treat copied child servers as part of the hub source tree.
- Do not track files under `servers/*` except `servers/README.md` and `servers/.gitkeep`.
- Do not weaken existing validation rules just to make fixtures pass.
- Keep each Python file under the configured size gate. If a file is near 300 lines, split helpers into a new module.

## Desired Output Shape

The validation command should print JSON by default, because agents and scripts need stable output.

Minimum JSON shape:

```json
{
  "schema_version": 1,
  "path": "D:\\Programming\\codex\\mcp-hub\\servers\\memory-server",
  "inside_servers_dir": true,
  "valid": true,
  "status": "Ready",
  "service": {
    "id": "memory-server",
    "name": "Memory Server",
    "lifecycle": "command_per_client",
    "transport": "stdio"
  },
  "errors": [],
  "warnings": [],
  "connection": {
    "transport": "stdio",
    "command": "uv",
    "args": ["run", "python", "-m", "memory_server"],
    "cwd": "D:\\Programming\\codex\\mcp-hub\\servers\\memory-server",
    "env": {}
  },
  "next_actions": [
    "Run .\\scripts\\rescan-services.ps1 or use the dashboard Rescan button."
  ]
}
```

For invalid services:

```json
{
  "schema_version": 1,
  "valid": false,
  "status": "Invalid",
  "errors": [
    "CAPABILITIES.md is required.",
    "scripts.test does not exist: scripts/test.ps1"
  ],
  "next_actions": [
    "Fix the listed errors and rerun validation."
  ]
}
```

Warnings must not make the command fail. Errors must make the command exit non-zero.

## Implementation Tasks

### Task 1: Add A Validation Result Builder

Preferred approach:

- Add `src/mcp_hub/validation.py`.
- Keep discovery as the low-level manifest validator.
- Build a workflow-level result around `load_service`.

Required behavior:

- Resolve the provided path relative to the hub root.
- Detect whether the resolved path is inside `config.servers_dir`.
- Load and validate `mcp-server.yaml`.
- Include `service.as_dict()`.
- Include flattened `errors` and `warnings`.
- Include the connection recipe only when the service is valid.
- Include actionable `next_actions`.

Do not run the child server's start/test scripts in this slice.

### Task 2: Wire CLI Output

Update `mcp_hub.cli validate-server` to print the workflow result.

Required exit behavior:

- Exit `0` when there are no validation errors.
- Exit `1` when validation errors exist.
- Exit `1` for unreadable paths or invalid manifests.

The PowerShell wrapper should remain simple and preserve the native exit code.

### Task 3: Add Copy-In Fixtures

Use existing fixtures where practical. Add only small extra fixtures if needed.

Required cases:

- Valid stdio server copied under `servers/`.
- Invalid server missing `CAPABILITIES.md`.
- Server with missing `README.md`.
- Server with missing script paths.
- Server with absolute script or working-directory paths.

Prefer creating fixtures in tests dynamically when that avoids adding many files.

### Task 4: Add Tests

Add focused tests for:

- `validate_server_path` or equivalent result-builder function.
- CLI exit code for valid copied server.
- CLI exit code for invalid copied server.
- PowerShell wrapper behavior if practical without duplicating CLI coverage.
- The result reports `inside_servers_dir: true` for copied servers.
- The result reports `inside_servers_dir: false` for paths outside `servers/` without failing solely for that reason.
- Invalid outputs contain actionable errors and no connection recipe.
- Valid outputs contain a connection recipe and rescan/dashboard next action.

Use persistent ignored workspaces through `tests/workspace_utils.py`; do not use `TemporaryDirectory`.

### Task 5: Documentation

Update:

```text
mcp-hub/README.md
mcp-hub/docs/OPERATIONS.md
mcp-hub/docs/TEST_STRATEGY.md
mcp-hub/docs/NEXT_SESSION_PLAN.md
mcp-hub/scripts/README.md
D:\Programming\codex\features\mcp-hub-copy-in-validation-workflow.md
D:\Programming\codex\progress-logs\2026-07-05.md
```

Required docs content:

- The copy-in workflow.
- The validation command.
- The fact that validation does not run or install the server.
- The fact that copied child server folders remain ignored by git.

Mark the next-session plan item as implemented only after tests and gate pass.

## Acceptance Commands

Run from `D:\Programming\codex\mcp-hub`:

```powershell
.\scripts\validate-server.ps1 .\tests\fixtures\valid-stdio-server
.\scripts\validate-server.ps1 .\tests\fixtures\invalid-missing-capabilities
uv run python -m unittest discover -s tests -p "test*.py"
.\scripts\gate.ps1
```

Expected:

- Valid fixture command exits `0`.
- Invalid fixture command exits non-zero and reports `CAPABILITIES.md is required.`
- Unit tests pass.
- Gate passes.

## Final Report Requirements

The worker must report:

```text
Changed files:
- ...

Validation output:
<valid command one-line summary or key JSON fields>
<invalid command key JSON fields and exit behavior>

Gate:
GATE PASS ...

Unresolved issues:
- ...
```

Do not summarize failed commands as "failed"; include the actionable error line.

## Out Of Scope

- Running child server scripts.
- Installing child server dependencies.
- GitHub orchestration.
- Environment replication.
- Podman/VPS support.
- A dashboard redesign.
- Proxying child tools through the meta MCP server.
