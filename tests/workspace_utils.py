from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT / ".test-tmp"


def test_workspace(name: str) -> Path:
    path = WORKSPACE_ROOT / name
    path.mkdir(parents=True, exist_ok=True)
    return path
