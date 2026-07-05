# Servers Directory

Copy independently usable MCP server folders into this directory.

Each child folder must contain:

```text
mcp-server.yaml
CAPABILITIES.md
README.md
scripts/start.ps1
scripts/test.ps1
```

Version 1 treats this directory as a local install area, not as a GitHub repository manager.

The MCP Hub repository should not commit copied server folders by default. Future environment replication may clone or restore server folders into this directory, but each child server should remain independently usable and publishable.
