# Design Decisions

## 1. Manager-First, Not Gateway-First

Decision:

MCP Hub is primarily a service manager and registry.

Reason:

Child MCP servers must remain independently usable and publishable. A gateway-first design would make the hub the default way to use them and weaken that claim.

## 2. Direct Server Use Is Canonical

Decision:

The meta MCP server returns direct connection recipes.

Reason:

The user wants to be able to say each server is used the same way other users can use it.

## 2.5. Local Stdio Is The Default Child Server Shape

Decision:

Most child servers should be local stdio command-per-client servers.

Reason:

The expected use cases are shared local memory, lessons learned, preferences, and project context. These do not need network listeners by default.

## 3. `CAPABILITIES.md` Is Required

Decision:

Every server has a high-level capability brief.

Reason:

Agents need concise operational context before deciding whether to use a server. README files are often too installation-focused, and `SKILL.md` is specific to skill systems rather than generic MCP discovery.

## 4. Stdio Is Command-Per-Client

Decision:

The manager does not present stdio services as shared background daemons.

Reason:

Stdio MCP servers communicate over the stdin and stdout of the process launched by a client. Pretending they are always running would be inaccurate unless the hub adds a bridge or proxy.

## 5. Gateway Mode Is Optional And Later

Decision:

Gateway/proxy support is out of the default path.

Reason:

It may be useful for agents that only support one MCP connection, but it must not become the source of truth for standalone server behavior.

## 6. Process Runtime First, Adapter Boundary Now

Decision:

Version 1 uses local processes, but the manager code should define a runtime adapter boundary.

Reason:

This keeps Podman, VPS, and remote service support possible later without making the first implementation heavy.

## 7. Copy-In Servers First, GitHub Orchestration Later

Decision:

Version 1 discovers server folders copied into `servers/`.

Reason:

The first goal is to remove agent setup friction, not to manage the GitHub lifecycle of every child server. Future environment replication can install the same server set on another machine without changing the local execution model.

## 8. Guidelines Are A Meta MCP Capability

Decision:

The meta MCP server exposes authoring guidelines and example code.

Reason:

Less capable agents need explicit local preferences for when to create servers, which transport to choose, and what code shape to copy.
