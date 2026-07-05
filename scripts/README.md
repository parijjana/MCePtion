# Scripts

This directory will contain the framework-level scripts.

Planned scripts:

- `start-framework.ps1`
- `stop-framework.ps1`
- `status-framework.ps1`
- `start-meta-stdio.ps1`
- `rescan-services.ps1`
- `validate-server.ps1`
- `run-tests.ps1`
- `gate.ps1`
- `install-autostart.ps1`
- `uninstall-autostart.ps1`
- `new-server.ps1`

`gate.ps1` is the broader verifier. It runs `uv run python scripts/gate.py`, preserves the native exit code, and uses the repo-local `.uv-cache` directory.

`start-framework.ps1` starts the manager/dashboard process in the background through `mcp_hub.framework`, writes runtime state under `data/runtime-state.json`, and writes manager output under `logs/`.

`status-framework.ps1` reads the recorded runtime state and reports whether the recorded manager PID is alive.

`stop-framework.ps1` stops only the recorded manager PID. It does not stop command-per-client stdio child server processes launched by agent hosts.

`validate-server.ps1 .\servers\<name>` runs the standalone copy-in validator for one
server folder and preserves the CLI exit code. It prints JSON, does not require the
manager process, and does not run the child server's start or test scripts.
