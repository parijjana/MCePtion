# Test Strategy

## Unit Tests

Manager:

- Loads valid `framework.yaml`.
- Rejects invalid global config.
- Discovers services under `servers/*/mcp-server.yaml`.
- Validates required files.
- Detects duplicate service ids.
- Detects port conflicts.
- Rejects incompatible lifecycle and transport combinations.
- Produces canonical connection recipes.

Runtime adapters:

- Starts daemon services with correct working directory.
- Stops only manager-owned daemon services.
- Does not kill command-per-client processes not launched by the manager.
- Probes stdio services with a temporary process.

Meta MCP server:

- Lists services.
- Describes services.
- Returns `CAPABILITIES.md`.
- Returns direct connection recipes.
- Returns server authoring guidelines.
- Returns example code without executing it.
- Recommends local stdio command-per-client for normal local shared-memory use cases.
- Refuses `start_service` for command-per-client services with a clear message.
- Calls manager API for lifecycle actions.

Dashboard API:

- Shows invalid services.
- Shows lifecycle-aware actions.
- Shows logs.
- Shows copyable connection details.

Copy-in validation:

- Returns JSON for valid and invalid copied server folders.
- Exits `0` for valid copied servers and non-zero for invalid copied servers.
- Reports whether the checked folder is under `servers/`.
- Reports missing `README.md`, missing `CAPABILITIES.md`, missing script paths, and absolute manifest paths.
- Includes a connection recipe only for valid services.
- Does not start the framework or run child server scripts.

## Integration Tests

- Copy a valid template service into `servers/` and rescan.
- Copy an invalid service into `servers/` and confirm validation errors.
- Start and stop a fake Streamable HTTP daemon.
- Probe a fake stdio MCP server.
- Confirm registry state survives manager restart.
- Read guidelines through the meta MCP server.
- Read the Python stdio example through the meta MCP server.

## End-To-End Smoke Tests

Windows local smoke:

```powershell
.\scripts\validate-server.ps1 .\tests\fixtures\valid-stdio-server
.\scripts\validate-server.ps1 .\tests\fixtures\invalid-missing-capabilities
.\scripts\start-framework.ps1
.\scripts\status-framework.ps1
.\scripts\rescan-services.ps1
.\scripts\stop-framework.ps1
```

## Local Gate

The repository also has a one-command verifier:

```powershell
.\scripts\gate.ps1
```

It reads `gate/gate.yaml`, writes `gate_report.json`, and prints the one-line `GATE PASS` or `GATE FAIL` digest. The gate keeps strict mypy, coverage gating, Markdown size gating, CI workflow behavior, and metrics behavior behind config toggles so those policies can be enabled later without changing the gate shape.

Meta MCP smoke:

- Connect to the meta MCP endpoint.
- Call `hub.list_services`.
- Read `hub://services/{id}/capabilities`.
- Request `hub.get_service_connection`.
- Request `hub.get_guideline`.
- Request `hub.recommend_server_type`.
- Request `hub.get_example_code`.

Dashboard smoke:

- Open dashboard.
- Confirm service table renders.
- Confirm command-per-client services show Probe, not Stop.
- Confirm daemon services show Start or Stop as appropriate.

## Regression Tests

Every bug in discovery, manifest parsing, lifecycle control, config generation, or Git sync should get a regression test.

## Test Data

Keep fixtures small:

```text
tests/fixtures/valid-stdio-server/
tests/fixtures/valid-http-daemon/
tests/fixtures/invalid-missing-capabilities/
tests/fixtures/invalid-duplicate-id/
tests/fixtures/guidelines/
```
