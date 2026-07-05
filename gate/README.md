# Gate

`gate/gate.yaml` controls the local CI gate.

Run it from the project root:

```powershell
.\scripts\gate.ps1
```

The gate always writes `gate_report.json` at the project root. When `--ci` is used it also writes `gate_summary.md`.

`size-baseline.json` freezes current oversized gate implementation files so the
ratchet can shrink them later without blocking the first local gate.

Config toggles keep the initial gate narrow:

- `analysis.mypy.enabled`
- `coverage.enabled`, `coverage.measure`, `coverage.gate`
- `size.markdown.enabled`, `size.markdown.gate`, `size.markdown.warn_only`
- `ci.enabled`, `ci.workflow_enabled`
- `metrics.enabled`, `metrics.append_history`
