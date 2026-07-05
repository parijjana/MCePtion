from __future__ import annotations

import argparse
from pathlib import Path

from .runner import load_and_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--print-config", action="store_true")
    parser.add_argument("--ci", action="store_true")
    parser.add_argument(
        "--only", nargs="*", choices=["analysis", "size", "structure", "tests", "coverage"]
    )
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    config, result, config_message = load_and_run(
        root, set(args.only or []), args.ci, args.print_config
    )
    if config_message:
        print(config_message)
        return 0 if not config_message.startswith("[config]") else 1
    assert config is not None and result is not None
    if result.passed:
        print(result.summary_line())
        return 0
    for line in result.failure_lines(config.output.failure_limit_per_category):
        print(line)
    return 1
