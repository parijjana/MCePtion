from __future__ import annotations

from pathlib import Path
from typing import Any


class SimpleYamlError(ValueError):
    """Raised when the local YAML subset parser cannot parse a file."""


def load_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    return loads(text)


def loads(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    pending: list[tuple[int, dict[str, Any], str]] = []

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent % 2 != 0:
            raise SimpleYamlError(
                f"Line {line_number}: indentation must use multiples of two spaces."
            )

        content = _strip_comment(raw_line.strip())
        if not content:
            continue

        while pending and indent > pending[-1][0]:
            pending_indent, parent, key = pending.pop()
            container: Any = [] if content.startswith("- ") else {}
            parent[key] = container
            stack.append((pending_indent, container))

        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise SimpleYamlError(f"Line {line_number}: invalid indentation.")

        parent = stack[-1][1]

        if content.startswith("- "):
            if not isinstance(parent, list):
                raise SimpleYamlError(f"Line {line_number}: list item found outside a list.")
            parent.append(_parse_scalar(content[2:].strip()))
            continue

        if ":" not in content:
            raise SimpleYamlError(f"Line {line_number}: expected a key/value pair.")

        key, raw_value = content.split(":", 1)
        key = key.strip()
        value_text = raw_value.strip()
        if not key:
            raise SimpleYamlError(f"Line {line_number}: empty key.")
        if not isinstance(parent, dict):
            raise SimpleYamlError(f"Line {line_number}: key/value pair found inside a scalar list.")

        if value_text:
            parent[key] = _parse_scalar(value_text)
        else:
            parent[key] = {}
            pending.append((indent, parent, key))

    return root


def _strip_comment(value: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(value):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return value[:index].rstrip()
    return value


def _parse_scalar(value: str) -> Any:
    if value == "":
        return ""
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "Null", "none", "None", "~"}:
        return None
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in inner.split(",")]
    try:
        return int(value)
    except ValueError:
        return value
