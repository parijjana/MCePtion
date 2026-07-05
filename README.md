# MCP Hub

MCP Hub is a planned local service manager for independently usable MCP servers.

The goal is to run one framework on this machine, point future agents at one meta MCP server, and let the framework discover, validate, monitor, describe, and lifecycle-manage the individual MCP servers that live inside `servers/`.

The important constraint is that each child MCP server must remain usable on its own. The hub may supervise a server, but it must not require the server to be imported into a shared runtime or rewritten behind a proxy.

Most child servers are expected to be local stdio servers. The main reason to create them is durable shared capability across projects and agents, such as lessons learned, project context, and default UI design preferences.

## Planned Shape

```text
mcp-hub/
  README.md
  framework.yaml
  docs/
  manager/
  meta-server/
  dashboard/
  scripts/
  servers/
  templates/
  data/
  logs/
```

## Primary Commands

Planned commands:

```powershell
.\scripts\start-framework.ps1
.\scripts\stop-framework.ps1
.\scripts\status-framework.ps1
.\scripts\start-meta-stdio.ps1
.\scripts\install-autostart.ps1
.\scripts\new-server.ps1 memory-server --language python --transport stdio
.\scripts\validate-server.ps1 .\servers\memory-server
.\scripts\gate.ps1
```

## Core Documents

- [docs/PLAN.md](docs/PLAN.md) records the product and implementation plan.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) describes the manager, dashboard, and meta MCP split.
- [docs/SERVER_CONTRACT.md](docs/SERVER_CONTRACT.md) defines the required folder and manifest contract for child servers.
- [docs/META_MCP_CONTRACT.md](docs/META_MCP_CONTRACT.md) defines the meta MCP tools, resources, and response shapes.
- [docs/GUIDELINES_TOOL.md](docs/GUIDELINES_TOOL.md) defines the meta MCP guidance tools for future server authors.
- [docs/MANAGER_API_CONTRACT.md](docs/MANAGER_API_CONTRACT.md) defines the internal manager API used by dashboard, CLI, and meta MCP.
- [docs/OPERATIONS.md](docs/OPERATIONS.md) describes startup, shutdown, rescan, health, logs, and autostart behavior.
- [docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md) records the local security model and remote-mode requirements.
- [docs/TEST_STRATEGY.md](docs/TEST_STRATEGY.md) defines the validation strategy.
- [docs/IMPLEMENTATION_STACK.md](docs/IMPLEMENTATION_STACK.md) records the recommended implementation stack.
- [docs/DESIGN_DECISIONS.md](docs/DESIGN_DECISIONS.md) records the main architectural decisions.
- [docs/ENVIRONMENT_REPLICATION.md](docs/ENVIRONMENT_REPLICATION.md) records the copy-in policy and future GitHub orchestration path.
- [docs/CI_GATE_EXECUTION_PLAN.md](docs/CI_GATE_EXECUTION_PLAN.md) records the executor plan for applying the gate standard.
- [docs/NEXT_SESSION_PLAN.md](docs/NEXT_SESSION_PLAN.md) records the next implementation slice.
- [docs/ROADMAP.md](docs/ROADMAP.md) captures the staged delivery plan.

## Local Gate

`.\scripts\gate.ps1` is the local verifier for MCP Hub. It reads `gate/gate.yaml`, runs the enabled checks, and always writes `gate_report.json` at the project root. When invoked with `--ci`, it also writes `gate_summary.md`.

The success line is intentionally one line:

```text
GATE PASS  sha=<short|none>  tests=<passed>/<total>  analysis=<E>E/<W>W  size=<n>  struct=<n>  cov=<pct|n/a>%
```

Strict mypy, coverage gating, Markdown size gating, CI workflow behavior, and metrics behavior are config toggles in `gate/gate.yaml`. The initial gate keeps strict mypy off, coverage measurement off, Markdown size warning-only, and CI/metrics disabled.

## Local Framework Lifecycle

`.\scripts\start-framework.ps1` starts the local manager/dashboard process in the background. The current slice serves the dashboard from the manager API root at `http://127.0.0.1:7420/`.

Runtime state is written to `data/runtime-state.json`, and manager output is written to timestamped files under `logs/`. These paths are intentionally ignored because they are local process state.

Use:

```powershell
.\scripts\status-framework.ps1
.\scripts\stop-framework.ps1
```

The start command refuses a duplicate start while the recorded manager PID is alive. If the recorded PID is stale, startup replaces the stale runtime record.

## Dashboard

The dashboard is served from the manager root URL after the framework starts:

```text
http://127.0.0.1:7420/
```

It lists discovered services, lifecycle class, transport, validation status, capability brief, direct connection recipe, and lifecycle-aware controls. Command-per-client stdio services show Probe and Connection actions instead of misleading Stop controls. Daemon services show Start, Stop, Restart, and Connection actions.

## Important Design Constraint

Stdio MCP servers are command-per-client services. The hub can validate them, probe them, and publish their direct launch recipe, but it cannot make one shared background stdio process available to arbitrary agents without adding an explicit bridge or gateway.

The meta MCP server is also stdio-first. The framework can optionally expose an HTTP meta MCP endpoint later, but the preferred local agent setup is a stdio command that launches the meta MCP process for that agent session.

Child server folders copied into `servers/` are local installs and are ignored by this repository by default.

## Copy-In Validation

To add a child server, copy its independent folder into `servers/<name>` and run:

```powershell
.\scripts\validate-server.ps1 .\servers\<name>
```

The command prints stable JSON and exits non-zero when required files, manifest fields,
script paths, or path-safety rules fail. It does not start the framework, install
dependencies, run child server scripts, clone repositories, or require GitHub.

## Repository Policy

MCP Hub is its own Git repository under `mcp-hub/`. Track source code, tests, templates, gate configuration, framework configuration, lockfiles, and the approved project documentation set.

Markdown tracking is allowed for this project in:

- `README.md`
- `docs/*.md`
- `guidelines/*.md`
- `templates/**/README.md`
- `scripts/README.md`
- `environment/README.md`
- `servers/README.md`

Do not track generated, runtime, cache, or local install state:

- `.venv/`, `.uv-cache/`, `.ruff_cache/`, `.test-tmp/`, and `__pycache__/`
- `data/`, `logs/`, `gate_report.json`, and `gate_summary.md`
- `src/*.egg-info/`
- zip snapshots and packaged archives
- copied child servers under `servers/*`, except `servers/README.md` and `servers/.gitkeep`

Root workspace planning files such as `features/`, `progress-logs/`, and `lessons-learnt/` are parent-workspace records and should not be tracked in this repository.
