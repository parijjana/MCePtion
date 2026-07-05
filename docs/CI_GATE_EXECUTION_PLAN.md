# CI Gate Execution Plan

Status: ACTIVE

## Objective

Implement the local CI gate for MCP Hub using `D:\Programming\codex\CI_STANDARD.md` as the governing standard.

This plan is written for an executor agent. Follow it in order. Do not implement adjacent features unless a task below explicitly asks for them.

## Required Reading

Before editing files, read:

```text
D:\Programming\codex\CI_STANDARD.md
mcp-hub/docs/PLAN.md
mcp-hub/docs/ARCHITECTURE.md
mcp-hub/docs/TEST_STRATEGY.md
mcp-hub/README.md
```

## Non-Negotiable Rules

- One gate command is the verifier.
- Success prints exactly one line.
- Failure prints only capped actionable lines.
- Full details go to `gate_report.json`.
- Gate behavior is controlled by `gate/gate.yaml`.
- Do not hardcode policy choices that belong in `gate/gate.yaml`.
- Do not add GitHub Actions in the first implementation unless this plan is updated.
- Do not add metrics branch behavior in the first implementation unless this plan is updated.
- Do not remove or weaken existing tests to make the gate pass.

## Files To Create

```text
mcp-hub/gate/gate.yaml
mcp-hub/gate/README.md
mcp-hub/scripts/gate.py
mcp-hub/scripts/gate.ps1
mcp-hub/tests/test_gate_config.py
mcp-hub/tests/test_gate_size.py
mcp-hub/tests/test_gate_structure.py
mcp-hub/tests/test_gate_output.py
```

## Files To Edit

```text
mcp-hub/.gitignore
mcp-hub/README.md
mcp-hub/pyproject.toml
mcp-hub/scripts/README.md
mcp-hub/scripts/run-tests.ps1
mcp-hub/docs/TEST_STRATEGY.md
progress-logs/2026-07-04.md
```

Only edit additional files if a test or implementation requirement makes it necessary.

## Gate Config Requirement

Create `mcp-hub/gate/gate.yaml`.

This file controls the gate's behavior. The four agreed policy choices must be configurable here:

1. Strict mypy is disabled initially but can be enabled later.
2. Coverage is measured or disabled independently from coverage gating.
3. Markdown/document size checks are separate from Python size checks and can be warning-only.
4. CI workflow and metrics behavior are disabled initially and can be enabled later.

Initial config:

```yaml
schema_version: 1

output:
  success_one_line: true
  failure_limit_per_category: 15
  report_path: gate_report.json
  summary_path: gate_summary.md

toolchain:
  python: "3.14"
  uv_required: true

paths:
  source:
    - src
    - scripts
  tests:
    - tests
  docs:
    - docs
    - README.md
    - guidelines
    - templates
  include:
    - pyproject.toml
    - framework.yaml
  exclude:
    - .venv
    - .uv-cache
    - __pycache__
    - src/*.egg-info
    - data
    - logs
    - reports
    - servers/*
    - "!servers/README.md"
    - "!servers/.gitkeep"

analysis:
  ruff:
    enabled: true
    gate: true
    max_errors: 0
    max_warnings: 0
  mypy:
    enabled: false
    gate: false
    strict: false
    scenario: "Enable after manager/meta interfaces stabilize."

size:
  python:
    enabled: true
    gate: true
    max_file_lines: 300
    max_function_statements: 40
    baseline_path: gate/size-baseline.json
  markdown:
    enabled: true
    gate: false
    warn_only: true
    max_file_lines: 500
    scenario: "Docs are intentionally substantial while architecture is being designed."

structure:
  enabled: true
  gate: true
  rules:
    no_generated_artifacts:
      enabled: true
      patterns:
        - ".venv/"
        - ".uv-cache/"
        - "__pycache__/"
        - "*.pyc"
        - "*.egg-info/"
    copied_servers_not_tracked:
      enabled: true
      allowed:
        - "servers/README.md"
        - "servers/.gitkeep"
    no_absolute_manifest_paths:
      enabled: true
      manifest_glob: "**/mcp-server.yaml"

tests:
  unittest:
    enabled: true
    gate: true
    command:
      - python
      - -m
      - unittest
      - discover
      - -s
      - tests
      - -p
      - "test*.py"

coverage:
  enabled: false
  measure: false
  gate: false
  min_percent: null
  scenario: "Enable measurement after the gate is stable; gate later through ratchet."

ci:
  enabled: false
  workflow_enabled: false
  scenario: "Enable after mcp-hub has its own GitHub remote."

metrics:
  enabled: false
  append_history: false
  branch: ci-metrics
  scenario: "Enable only after GitHub Actions exists and the local gate is stable."
```

If the executor chooses TOML instead of YAML, stop and update this plan first. YAML is preferred because MCP Hub already uses YAML-shaped manifests.

## Output Contract

Success must print exactly one line:

```text
GATE PASS  sha=<short|none>  tests=<passed>/<total>  analysis=<E>E/<W>W  size=<n>  struct=<n>  cov=<pct|n/a>%
```

For a local folder without Git, use:

```text
sha=none
```

Failure must print:

```text
GATE FAIL  sha=<short|none>
[G2 size] <path> <current> > <limit-or-baseline>
[G3 struct] <path> <rule-id> <message>
[G4 test] <test-name>
          <first failure line>
```

Failure output must be capped by `output.failure_limit_per_category`.

The gate must always write `gate_report.json`.

## Report Shape

`gate_report.json` must be structured and small.

Minimum shape:

```json
{
  "schema_version": 1,
  "pass": true,
  "sha": "none",
  "checks": {
    "analysis": {
      "enabled": true,
      "errors": 0,
      "warnings": 0,
      "tool_results": []
    },
    "size": {
      "enabled": true,
      "violations": []
    },
    "structure": {
      "enabled": true,
      "violations": []
    },
    "tests": {
      "enabled": true,
      "passed": 14,
      "total": 14,
      "failures": []
    },
    "coverage": {
      "enabled": false,
      "percent": null,
      "gated": false
    }
  },
  "wall_secs": 0.0
}
```

Do not put narrative commentary in this report.

## Implementation Tasks

### Task 1: Add Gate Config Loader

Implement config loading in `scripts/gate.py`.

Allowed behavior:

- Read `gate/gate.yaml`.
- Reuse `mcp_hub.simple_yaml` if practical.
- Fail with one `[config]` line if config is missing or invalid.
- Respect all `enabled`, `gate`, and `warn_only` toggles.

Acceptance command:

```powershell
uv run python scripts/gate.py --print-config
```

Expected:

```text
GATE CONFIG OK  schema=1
```

### Task 2: Add G4 Test Check

Implement the unittest check first.

Allowed behavior:

- Run the command from `gate/gate.yaml`.
- Capture stdout/stderr.
- Parse unittest summary enough to report passed/total/failures.
- Do not stream raw test output during normal mode.
- Include raw captured output only in `gate_report.json`, and keep it capped.

Acceptance command:

```powershell
uv run python scripts/gate.py --only tests
```

Expected:

```text
GATE PASS  sha=none  tests=14/14  analysis=0E/0W  size=0  struct=0  cov=n/a%
```

If the test count changes because new tests are added, use the actual count.

### Task 3: Add G2 Python Size Check

Implement Python file size checks.

Allowed behavior:

- Count non-generated `.py` files under configured source and tests paths.
- Enforce `size.python.max_file_lines`.
- Create no baseline entries unless the user explicitly runs a future `--shrink-baseline`.
- If no baseline exists and all files are under limit, pass with zero violations.

Do not implement a baseline-widening path.

Acceptance command:

```powershell
uv run python scripts/gate.py --only size
```

Expected:

```text
GATE PASS  sha=none  tests=0/0  analysis=0E/0W  size=0  struct=0  cov=n/a%
```

### Task 4: Add Configurable Markdown Size Behavior

Implement Markdown size scanning controlled by:

```yaml
size.markdown.enabled
size.markdown.gate
size.markdown.warn_only
```

Required behavior:

- If enabled and warning-only, record warnings in `gate_report.json`.
- Do not fail the gate unless `size.markdown.gate: true`.
- Do not mix Markdown size counts into Python size ratchet counts.

Acceptance command:

```powershell
uv run python scripts/gate.py --only size
```

Expected:

- Gate passes even if a Markdown file exceeds the configured warning limit.
- `gate_report.json` contains the warning.

### Task 5: Add G3 Structural Checks

Implement the configured structural rules:

- `no_generated_artifacts`
- `copied_servers_not_tracked`
- `no_absolute_manifest_paths`

Required behavior:

- Generated/runtime directories must not be considered source.
- Copied servers under `servers/` are ignored except `servers/README.md` and `servers/.gitkeep`.
- Manifest path fields should be relative. Do not reject URL fields.

Acceptance command:

```powershell
uv run python scripts/gate.py --only structure
```

Expected:

```text
GATE PASS  sha=none  tests=0/0  analysis=0E/0W  size=0  struct=0  cov=n/a%
```

### Task 6: Add Ruff Analysis, Leave Mypy Toggle Off

Add Ruff as a dependency or dev dependency.

Update `pyproject.toml` with minimal Ruff configuration.

Required behavior:

- If `analysis.ruff.enabled: true`, run Ruff.
- If Ruff is missing, fail with a clear config/tooling message.
- If `analysis.mypy.enabled: false`, do not run mypy.
- Mypy implementation may be stubbed as disabled, but the config toggle must exist and be parsed.

Acceptance command:

```powershell
uv run python scripts/gate.py --only analysis
```

Expected:

```text
GATE PASS  sha=none  tests=0/0  analysis=0E/0W  size=0  struct=0  cov=n/a%
```

If Ruff reports violations, fix the code rather than disabling Ruff.

### Task 7: Add Coverage Toggle Without Gate

Implement config parsing for coverage.

Required behavior:

- With `coverage.enabled: false`, report `cov=n/a%`.
- With `coverage.measure: false`, do not run coverage tools.
- With `coverage.gate: false`, measured coverage must not fail the gate.
- Do not add coverage dependencies yet unless enabling measurement.

Acceptance command:

```powershell
uv run python scripts/gate.py --only coverage
```

Expected:

```text
GATE PASS  sha=none  tests=0/0  analysis=0E/0W  size=0  struct=0  cov=n/a%
```

### Task 8: Add CI And Metrics Toggles Without Implementing CI

Implement config parsing for:

```yaml
ci.enabled
ci.workflow_enabled
metrics.enabled
metrics.append_history
```

Required behavior:

- `--ci` may write `gate_summary.md`.
- If CI is disabled, `--ci` should still run locally but must not assume GitHub.
- Metrics disabled means no metrics branch, no CSV append, no Git command.

Acceptance command:

```powershell
uv run python scripts/gate.py --ci
```

Expected:

- Gate runs.
- `gate_summary.md` is written.
- No GitHub workflow files are created.
- No metrics branch operation is attempted.

### Task 9: Add PowerShell Wrapper

Create `scripts/gate.ps1`.

Required behavior:

- Set `$env:UV_CACHE_DIR` to `.uv-cache`.
- Run `uv run python scripts/gate.py` with all provided args.
- Exit with the native exit code.

Acceptance command:

```powershell
.\scripts\gate.ps1
```

Expected:

```text
GATE PASS  sha=none  tests=14/14  analysis=0E/0W  size=0  struct=0  cov=n/a%
```

### Task 10: Wire Existing Test Harness To Gate

Update `scripts/run-tests.ps1` only if necessary.

Preferred behavior:

- Keep `run-tests.ps1` as the raw test runner.
- Add `gate.ps1` as the broader verifier.
- Do not make raw test output the default agent-facing gate output.

Acceptance commands:

```powershell
.\scripts\run-tests.ps1
.\scripts\gate.ps1
```

Both must pass.

### Task 11: Documentation Updates

Update:

```text
mcp-hub/README.md
mcp-hub/scripts/README.md
mcp-hub/docs/TEST_STRATEGY.md
```

Required content:

- How to run the gate.
- What success output means.
- Where `gate_report.json` is written.
- Explain that strict mypy, coverage gating, Markdown size gating, CI workflow, and metrics are config toggles.

Acceptance check:

```powershell
Select-String -Path README.md,docs\TEST_STRATEGY.md,scripts\README.md -Pattern "gate.ps1","gate_report.json","gate.yaml"
```

Expected:

- At least one match for each pattern.

## Explicit Toggles The Executor Must Preserve

### Strict Mypy

Config path:

```yaml
analysis.mypy.enabled
analysis.mypy.gate
analysis.mypy.strict
```

Initial value:

```yaml
enabled: false
gate: false
strict: false
```

Scenario:

Enable after manager/meta interfaces stabilize.

### Coverage

Config path:

```yaml
coverage.enabled
coverage.measure
coverage.gate
coverage.min_percent
```

Initial value:

```yaml
enabled: false
measure: false
gate: false
min_percent: null
```

Scenario:

Measure after gate is stable. Gate later through ratchet or minimum only after the metric is trustworthy.

### Markdown Size

Config path:

```yaml
size.markdown.enabled
size.markdown.gate
size.markdown.warn_only
size.markdown.max_file_lines
```

Initial value:

```yaml
enabled: true
gate: false
warn_only: true
max_file_lines: 500
```

Scenario:

MCP Hub has substantial design docs. Python size should be hard-gated now; Markdown size should warn until docs stabilize.

### CI Workflow And Metrics

Config paths:

```yaml
ci.enabled
ci.workflow_enabled
metrics.enabled
metrics.append_history
```

Initial value:

```yaml
ci:
  enabled: false
  workflow_enabled: false
metrics:
  enabled: false
  append_history: false
```

Scenario:

Enable after MCP Hub has its own GitHub remote and local gate is green.

## Out Of Scope

Do not implement these in this task:

- GitHub Actions workflow.
- `ci-metrics` branch.
- Coverage measurement dependencies.
- Strict mypy enforcement.
- Daemon supervision features.
- Dashboard redesign.
- MCP SDK replacement of the minimal stdio meta server.

## Final Acceptance

Run:

```powershell
.\scripts\run-tests.ps1
.\scripts\gate.ps1
uv run python scripts/gate.py --print-config
uv run python scripts/gate.py --only tests
uv run python scripts/gate.py --only size
uv run python scripts/gate.py --only structure
uv run python scripts/gate.py --only analysis
uv run python scripts/gate.py --only coverage
uv run python scripts/gate.py --ci
```

All commands must succeed.

Final report from the executor must include:

```text
Task 1: <command pasted output>
Task 2: <command pasted output>
...
Final: <.\scripts\gate.ps1 pasted output>
```

Do not summarize commands as "passed"; paste the one-line output for each acceptance command.
