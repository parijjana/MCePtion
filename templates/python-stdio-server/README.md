# Example Server

This is a template for a standalone stdio MCP server managed by MCP Hub.

## Standalone Use

```powershell
.\scripts\start.ps1
```

## Managed Use

Copy this folder into:

```text
mcp-hub/servers/
```

Then rescan from the MCP Hub dashboard or manager CLI.

## Test

```powershell
.\scripts\test.ps1
```

## Agent Config

Replace the command and args with this server's real entrypoint.

```json
{
  "mcpServers": {
    "example-server": {
      "command": "uv",
      "args": ["run", "python", "-m", "example_server"]
    }
  }
}
```
