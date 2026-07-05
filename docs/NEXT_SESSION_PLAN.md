# Next Session Plan

Target date: 2026-07-05

## Objective

Continue MCP Hub after the CI gate checkpoint is complete. The next session should move the project from a validated scaffold toward a locally usable manager.

## Required First Read

Before editing, read:

```text
docs/PLAN.md
docs/ARCHITECTURE.md
docs/MANAGER_API_CONTRACT.md
docs/META_MCP_CONTRACT.md
docs/OPERATIONS.md
docs/TEST_STRATEGY.md
gate/gate.yaml
```

Run this before and after changes:

```powershell
.\scripts\gate.ps1
```

## Work Items

### 1. Implement Real Framework Lifecycle Control

Status: implemented in the 2026-07-05 lifecycle slice.

Goal: make `start-framework.ps1` and `stop-framework.ps1` manage real local runtime state instead of acting as thin launch helpers.

Expected behavior:

- Start the manager API/dashboard process.
- Write runtime state under ignored `data/` or `logs/`.
- Record PID, port, start time, and log file path.
- Refuse duplicate starts unless the recorded process is stale.
- Stop only the recorded process.
- Keep stdio child servers as command-per-client services unless their manifest declares a daemon lifecycle.

Acceptance:

- `.\scripts\start-framework.ps1` starts the local manager/dashboard.
- `.\scripts\stop-framework.ps1` stops it.
- `.\scripts\gate.ps1` still passes.

### 2. Make The Dashboard Useful

Status: implemented in the 2026-07-05 dashboard usefulness slice.

Goal: show enough information to manage local child servers without reading raw manifests.

Expected behavior:

- Show discovered services from `servers/`.
- Show validation state and high-level capability summary.
- Show direct connection recipe for each valid stdio server.
- Show start/stop controls only where the lifecycle supports them.
- Show clear labels for `command_per_client`, `daemon`, and `external` services.

Acceptance:

- Dashboard loads from the manager process.
- Invalid copied servers are visible with actionable validation errors.
- Stdio services do not show misleading background start/stop controls.
- `.\scripts\gate.ps1` still passes.

### 3. Harden The Meta MCP Server

Status: implemented in the 2026-07-05 meta MCP hardening slice.

Goal: make the meta MCP server genuinely useful as the one server an agent connects to first.

Expected exposed capabilities:

- List available child servers.
- Return high-level capability/readme summaries.
- Return direct connection instructions for a selected server.
- Return server-authoring guidelines.
- Return example-code references for less capable agents.
- Recommend when to create stdio, daemon, or external servers.

Acceptance:

- `.\scripts\start-meta-stdio.ps1` launches the meta MCP server.
- Existing meta MCP tests cover list, capability, guideline, and connection-recipe paths.
- `.\scripts\gate.ps1` still passes.

### 4. Add A Copy-In Validation Workflow

Status: implemented in the 2026-07-05 copy-in validation slice.

Goal: support the intended local workflow where the user copies an independent MCP server folder into `servers/`.

Expected behavior:

- `.\scripts\validate-server.ps1 .\servers\<name>` validates one copied server.
- Validation reports missing `README.md`, `CAPABILITIES.md`, manifest fields, bad scripts, and absolute local paths.
- Validation does not require GitHub or a shared runtime.
- Copied child server folders remain ignored by git.

Acceptance:

- A valid fixture copied under `servers/` validates cleanly.
- An invalid fixture copied under `servers/` reports actionable errors.
- `.\scripts\gate.ps1` still passes.

## Out Of Scope Tomorrow

- GitHub Actions.
- Metrics branch behavior.
- Private Git sync for child servers.
- Podman or VPS deployment.
- A proxy gateway that namespaces child tools.
- Rewriting independent child servers to fit a shared runtime.
