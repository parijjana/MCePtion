from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("Example Memory Server")


class MemoryRecord(BaseModel):
    id: str
    text: str
    tags: list[str] = Field(default_factory=list)
    project: str | None = None
    created_at: str


def data_dir() -> Path:
    default_dir = Path(__file__).resolve().parents[2] / "data"
    return Path(os.environ.get("EXAMPLE_MEMORY_DATA_DIR", default_dir))


def store_path() -> Path:
    return data_dir() / "memories.jsonl"


def read_records() -> list[MemoryRecord]:
    path = store_path()
    if not path.exists():
        return []

    records: list[MemoryRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(MemoryRecord.model_validate_json(line))
    return records


def append_record(record: MemoryRecord) -> None:
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(record.model_dump_json())
        handle.write("\n")


@mcp.tool()
def add_memory(
    text: str, tags: list[str] | None = None, project: str | None = None
) -> dict[str, Any]:
    """Store a durable memory record."""
    record = MemoryRecord(
        id=str(uuid4()),
        text=text,
        tags=tags or [],
        project=project,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    append_record(record)
    return record.model_dump()


@mcp.tool()
def search_memory(query: str, project: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    """Search stored memory records by simple case-insensitive text matching."""
    normalized_query = query.casefold()
    matches: list[MemoryRecord] = []

    for record in reversed(read_records()):
        if project and record.project != project:
            continue
        searchable = " ".join([record.text, record.project or "", " ".join(record.tags)]).casefold()
        if normalized_query in searchable:
            matches.append(record)
        if len(matches) >= limit:
            break

    return [record.model_dump() for record in matches]


@mcp.resource("memory://recent")
def recent_memories() -> str:
    """Return recent memory records as JSON."""
    records = [record.model_dump() for record in read_records()[-20:]]
    return json.dumps(records, indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
