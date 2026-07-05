# Guidelines Tool

The meta MCP server should expose authoring guidance for future agents.

This exists because future agents may be less capable and may need explicit preferences, examples, and decision rules before creating or modifying MCP servers.

## Purpose

The guidelines tool answers:

- When should a new MCP server be created?
- Should it be stdio, HTTP daemon, external, or gateway-based?
- What files are required?
- What patterns should be copied?
- What examples should be used as reference?
- What should be avoided?

## Source Files

Guidelines are stored under:

```text
guidelines/
```

Initial files:

```text
guidelines/SERVER_AUTHORING_GUIDELINES.md
guidelines/examples/python-stdio-fastmcp/
```

## Meta MCP Tools

### `hub.list_guidelines`

Returns available guideline documents and example groups.

### `hub.get_guideline`

Returns one guideline document.

Input:

```json
{
  "id": "server-authoring"
}
```

### `hub.recommend_server_type`

Returns a recommendation for what kind of MCP server to create.

Input:

```json
{
  "shared_across_projects": true,
  "local_only": true,
  "needs_long_running_process": false,
  "needs_multiple_simultaneous_clients": false,
  "needs_browser_ui": false,
  "stores_durable_data": true,
  "remote_access_required": false
}
```

Output:

```json
{
  "recommendation": "local_stdio_command_per_client",
  "manifest": {
    "lifecycle": "command_per_client",
    "transport": "stdio"
  },
  "reason": "The capability is local, durable, and shared across agents, but it does not need a long-running process or network listener.",
  "reference_examples": [
    "hub://guidelines/examples/python-stdio-fastmcp"
  ]
}
```

### `hub.get_example_code`

Returns example code or an example file listing.

Input:

```json
{
  "example_id": "python-stdio-fastmcp",
  "path": "src/example_memory_server/__main__.py"
}
```

### `hub.get_scaffold_checklist`

Returns the required files and validation checklist for a new server.

## Resources

```text
hub://guidelines/server-authoring
hub://guidelines/examples
hub://guidelines/examples/python-stdio-fastmcp
hub://guidelines/examples/python-stdio-fastmcp/{path}
```

## Default Recommendation Logic

Default to:

```text
local stdio command-per-client server
```

Recommend an HTTP daemon only when:

- A shared live process is required.
- Multiple clients must use the same process at the same time.
- There is expensive warm state.
- A browser UI is part of the server.
- Remote or VPS deployment is an actual near-term requirement.

Recommend no new server when:

- A script is enough.
- The data belongs in the current project repository.
- The capability has no cross-project reuse value.
- The proposed server would only wrap one shell command.

## Example Code Policy

Examples should be small, complete, and biased toward local stdio.

They should include:

- Manifest.
- Capability brief.
- README.
- Startup script.
- Test script.
- Minimal tests.
- Clear storage path.

Examples should not include:

- Secrets.
- Network listeners unless the example is explicitly for HTTP daemon mode.
- Complex framework behavior unrelated to MCP server authoring.
