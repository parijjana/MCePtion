# Example Memory Server Capabilities

## Purpose

Demonstrates a local stdio MCP server that stores durable memory records in JSONL.

## When To Use

- Use as a starting point for a local personal MCP server.
- Use when a server needs simple shared data across agents.
- Use when stdio command-per-client behavior is enough.

## When Not To Use

- Do not use this as a production memory system without adding validation, backup, and migration rules.
- Do not store secrets.
- Do not use this when a shared daemon process is required.

## Main Capabilities

- Add memory records.
- Search memory records by simple text matching.
- Read recent memory records through a resource.

## Data Scope

Data is stored under the server's local `data/` directory by default.

## Safety Notes

This example avoids network listeners and should run locally through stdio.

## Typical Workflow

1. Agent calls `add_memory` to store a reusable note.
2. Agent calls `search_memory` to find prior notes.
3. Agent reads `memory://recent` for recent context.
