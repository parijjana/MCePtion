from __future__ import annotations

from pathlib import Path
from typing import Any


class GuidelineNotFoundError(KeyError):
    pass


class ExampleNotFoundError(KeyError):
    pass


def list_guidelines(guidelines_dir: Path, examples_dir: Path) -> dict[str, Any]:
    documents = []
    server_authoring = guidelines_dir / "SERVER_AUTHORING_GUIDELINES.md"
    if server_authoring.exists():
        documents.append(
            {
                "id": "server-authoring",
                "path": str(server_authoring),
                "title": "Server Authoring Guidelines",
            }
        )

    examples = []
    if examples_dir.exists():
        for path in sorted(examples_dir.iterdir()):
            if path.is_dir():
                examples.append({"id": path.name, "path": str(path)})

    return {"guidelines": documents, "examples": examples}


def get_guideline(guidelines_dir: Path, guideline_id: str) -> str:
    mapping = {"server-authoring": guidelines_dir / "SERVER_AUTHORING_GUIDELINES.md"}
    path = mapping.get(guideline_id)
    if not path or not path.exists():
        raise GuidelineNotFoundError(guideline_id)
    return path.read_text(encoding="utf-8")


def list_example_files(examples_dir: Path, example_id: str) -> list[str]:
    root = _example_root(examples_dir, example_id)
    return [
        str(path.relative_to(root)).replace("\\", "/")
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    ]


def get_example_file(examples_dir: Path, example_id: str, relative_path: str) -> str:
    root = _example_root(examples_dir, example_id)
    requested = (root / relative_path).resolve()
    if root not in requested.parents and requested != root:
        raise ExampleNotFoundError(relative_path)
    if not requested.exists() or not requested.is_file():
        raise ExampleNotFoundError(relative_path)
    return requested.read_text(encoding="utf-8")


def recommend_server_type(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("shared_across_projects") and not payload.get("stores_durable_data"):
        return {
            "recommendation": "no_new_server",
            "manifest": {},
            "reason": (
                "The capability does not appear reusable across projects or durable enough "
                "to justify an MCP server."
            ),
            "reference_examples": [],
        }

    if payload.get("remote_access_required") and not payload.get("local_only", True):
        return {
            "recommendation": "external_streamable_http_service",
            "manifest": {"lifecycle": "external", "transport": "streamable_http"},
            "reason": (
                "The capability needs remote access or ownership outside the local hub, so "
                "the hub should record metadata and connection details without owning it."
            ),
            "reference_examples": [],
        }

    needs_daemon = any(
        bool(payload.get(key))
        for key in [
            "needs_long_running_process",
            "needs_multiple_simultaneous_clients",
            "needs_browser_ui",
            "remote_access_required",
        ]
    )
    if needs_daemon:
        return {
            "recommendation": "local_streamable_http_daemon",
            "manifest": {"lifecycle": "daemon", "transport": "streamable_http"},
            "reason": (
                "The capability needs a shared live process, browser UI, simultaneous "
                "clients, or remote-ready behavior."
            ),
            "reference_examples": [],
        }

    return {
        "recommendation": "local_stdio_command_per_client",
        "manifest": {"lifecycle": "command_per_client", "transport": "stdio"},
        "reason": (
            "The capability is local and reusable, but it does not need a long-running "
            "process or network listener."
        ),
        "reference_examples": ["hub://guidelines/examples/python-stdio-fastmcp"],
    }


def _example_root(examples_dir: Path, example_id: str) -> Path:
    root = (examples_dir / example_id).resolve()
    examples_root = examples_dir.resolve()
    if examples_root not in root.parents and root != examples_root:
        raise ExampleNotFoundError(example_id)
    if not root.exists() or not root.is_dir():
        raise ExampleNotFoundError(example_id)
    return root
