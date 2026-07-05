# Python Stdio FastMCP Example

This example shows the preferred shape for a small local stdio MCP server.

Use it for servers that:

- Run locally.
- Store durable shared data.
- Are launched per MCP client connection.
- Should remain independently usable outside MCP Hub.

## Files

```text
mcp-server.yaml
CAPABILITIES.md
pyproject.toml
src/example_memory_server/__main__.py
scripts/start.ps1
scripts/test.ps1
tests/test_storage.py
```

## Run

```powershell
.\scripts\start.ps1
```

## Test

```powershell
.\scripts\test.ps1
```

## Notes

This is reference code for server authors. Pin and verify the MCP SDK version when turning it into production code.
