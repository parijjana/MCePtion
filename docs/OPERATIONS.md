# Operations

## Startup Sequence

Framework startup should follow this order:

1. Load `framework.yaml`.
2. Validate global configuration.
3. Bind the manager API to `127.0.0.1`.
4. Scan `servers/*/mcp-server.yaml`.
5. Validate manifests and required files.
6. Build the registry.
7. Start enabled daemon services with `autostart: true`.
8. Probe enabled command-per-client services if configured.
9. Start the dashboard.
10. Start the optional Streamable HTTP meta MCP endpoint if enabled.

The stdio meta MCP server is normally launched by each agent host when the agent connects. The framework startup script should still make sure the manager and dashboard are ready for it.

Current implementation note: `start-framework.ps1` starts the manager API in the background through `mcp_hub.framework`. The dashboard is served from the same local process at the manager API root. Runtime state is written to `data/runtime-state.json`, including PID, host, port, URL, start time, and log path.

## Shutdown Sequence

Framework shutdown should follow this order:

1. Stop accepting dashboard and meta MCP lifecycle requests.
2. Stop daemon services owned by the manager.
3. Wait for graceful shutdown.
4. Terminate services that exceed their stop timeout.
5. Flush runtime state.
6. Close logs.

Command-per-client services should not be killed because their live processes are owned by the agent hosts that launched them.

The stdio meta MCP process is also owned by the agent host that launched it and should not be killed by framework shutdown unless it was launched by a framework-controlled probe.

Current implementation note: `stop-framework.ps1` stops only the PID recorded in `data/runtime-state.json`. If that PID is stale, shutdown marks the runtime state stopped instead of killing unrelated processes.

## Rescan

Rescan should:

1. Re-read manifests.
2. Detect added, removed, and changed services.
3. Preserve runtime status for unchanged daemon services.
4. Mark removed daemon services as orphaned if a process is still running.
5. Report validation errors without deleting existing state.

The dashboard should display added, changed, invalid, and removed services clearly.

Current dashboard behavior: the manager root page lists discovered services, validation errors, capability summaries, direct connection recipes, and lifecycle-aware controls. Command-per-client stdio services expose Probe and Connection actions. Daemon services expose Start, Stop, Restart, and Connection actions.

## Health Checks

Recommended health check behavior:

```text
command_per_client + stdio:
  Start temporary process.
  Send MCP initialize if supported by the health probe.
  Terminate temporary process.

daemon + streamable_http:
  Check process status.
  Call configured health URL or MCP initialize.

external:
  Call configured health URL or mark Unknown if no check is declared.
```

## Logs

The manager should keep framework logs separate from service logs.

```text
logs/framework.log
logs/manager.log
logs/meta-mcp.log
logs/dashboard.log
logs/services/{service_id}/stdout.log
logs/services/{service_id}/stderr.log
```

Current manager startup logs are written as `logs/manager-YYYYMMDD-HHMMSS.log`.

For stdio MCP servers, protocol stdout must remain clean. Diagnostic logs should go to stderr or a log file.

## Windows Autostart

The planned autostart script should create a user-level startup entry that runs:

```powershell
D:\Programming\codex\mcp-hub\scripts\start-framework.ps1
```

It should also provide an uninstall script.

The script should not require admin rights for the default user-level install.

## CLI Commands

Planned commands:

```powershell
.\scripts\start-framework.ps1
.\scripts\stop-framework.ps1
.\scripts\status-framework.ps1
.\scripts\rescan-services.ps1
.\scripts\validate-server.ps1 .\servers\memory-server
.\scripts\new-server.ps1 memory-server --language python --transport stdio
```

The CLI should call the same manager API as the dashboard and meta MCP server after the manager is running.

## Installing Child Servers

Version 1 install flow:

1. Copy a server folder into `servers/`.
2. Run `.\scripts\validate-server.ps1 .\servers\<name>`.
3. Fix manifest or capability errors if shown.
4. Copy the connection recipe into the target agent host if needed.

No GitHub clone, pull, push, or submodule operation is part of the required version 1 workflow.
Validation is a static check of `mcp-server.yaml`, required files, declared script paths,
relative path rules, lifecycle/transport compatibility, warnings, and the derived
connection recipe. It does not require the framework manager to be running and does not
run the copied server's startup or test scripts.
