from __future__ import annotations

import argparse
import ctypes
import json
import os
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from .config import load_config
from .models import HubConfig


class RuntimeStateError(ValueError):
    pass


class FrameworkController:
    def __init__(self, config: HubConfig) -> None:
        self.config = config

    @classmethod
    def from_root(cls, root: Path | None = None) -> "FrameworkController":
        return cls(load_config(root))

    def start(self, timeout_seconds: float = 10.0) -> dict[str, Any]:
        state = self._read_state()
        recorded = _manager_state(state)
        pid = _int_or_none(recorded.get("pid"))
        if recorded.get("status") == "running" and pid and _is_process_alive(pid):
            return {
                "status": "already_running",
                "message": "MCePtion manager is already running.",
                "manager": self._status_from_record(recorded, alive=True),
            }

        stale_replaced = bool(recorded.get("status") == "running" and pid)
        log_path = self._next_log_path()
        process = _spawn_manager(self.config, log_path)
        manager = self._running_record(process.pid, log_path, stale_replaced)

        if not _wait_for_health(self._health_url(), process, timeout_seconds):
            _terminate_process(process.pid)
            _wait_until_stopped(process.pid, 3.0)
            manager["status"] = "startup_failed"
            manager["stopped_at"] = _utc_now()
            self._write_state({"schema_version": 1, "manager": manager})
            return {
                "status": "startup_failed",
                "message": "Manager process did not become healthy before the timeout.",
                "manager": manager,
            }

        self._write_state({"schema_version": 1, "manager": manager})
        return {"status": "started", "manager": manager}

    def stop(self, timeout_seconds: float = 10.0) -> dict[str, Any]:
        state = self._read_state()
        recorded = _manager_state(state)
        pid = _int_or_none(recorded.get("pid"))
        if not pid:
            return {"status": "not_running", "message": "No manager PID is recorded."}

        if not _is_process_alive(pid):
            stopped = self._stopped_record(recorded, stale=True)
            self._write_state({"schema_version": 1, "manager": stopped})
            return {"status": "stale", "message": "Recorded manager process is not running."}

        _terminate_process(pid)
        if not _wait_until_stopped(pid, timeout_seconds):
            return {
                "status": "stop_failed",
                "message": "Recorded manager process did not stop before the timeout.",
                "pid": pid,
            }

        stopped = self._stopped_record(recorded, stale=False)
        self._write_state({"schema_version": 1, "manager": stopped})
        return {"status": "stopped", "pid": pid}

    def status(self) -> dict[str, Any]:
        state = self._read_state()
        recorded = _manager_state(state)
        pid = _int_or_none(recorded.get("pid"))
        if not pid:
            return {"status": "stopped", "state_path": str(self.config.manager_state_file)}
        alive = _is_process_alive(pid)
        if recorded.get("status") == "running" and not alive:
            status = "stale"
        else:
            status = str(recorded.get("status", "unknown"))
        return {
            "status": status,
            "alive": alive,
            "manager": self._status_from_record(recorded, alive=alive),
            "state_path": str(self.config.manager_state_file),
        }

    def _read_state(self) -> dict[str, Any]:
        path = self.config.manager_state_file
        if not path.exists():
            return {"schema_version": 1}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeStateError(f"Runtime state is not valid JSON: {path}") from exc
        if not isinstance(data, dict):
            raise RuntimeStateError(f"Runtime state must be a JSON object: {path}")
        return data

    def _write_state(self, state: dict[str, Any]) -> None:
        path = self.config.manager_state_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")

    def _next_log_path(self) -> Path:
        self.config.logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        return self.config.logs_dir / f"manager-{stamp}.log"

    def _running_record(self, pid: int, log_path: Path, stale_replaced: bool) -> dict[str, Any]:
        return {
            "status": "running",
            "pid": pid,
            "host": self.config.manager_host,
            "port": self.config.manager_port,
            "url": self._base_url(),
            "dashboard_url": self._base_url(),
            "started_at": _utc_now(),
            "log_path": str(log_path),
            "root": str(self.config.root),
            "stale_replaced": stale_replaced,
        }

    def _stopped_record(self, recorded: dict[str, Any], stale: bool) -> dict[str, Any]:
        return {
            **recorded,
            "status": "stopped",
            "stopped_at": _utc_now(),
            "stale": stale,
        }

    def _status_from_record(self, recorded: dict[str, Any], alive: bool) -> dict[str, Any]:
        return {**recorded, "alive": alive, "health_url": self._health_url()}

    def _base_url(self) -> str:
        return f"http://{self.config.manager_host}:{self.config.manager_port}"

    def _health_url(self) -> str:
        return f"{self._base_url()}/health"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mcp-hub-framework")
    parser.add_argument("--root", default=".", help="MCePtion root directory.")
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("start")
    subparsers.add_parser("stop")
    subparsers.add_parser("status")
    args = parser.parse_args(argv)

    try:
        controller = FrameworkController.from_root(Path(args.root).resolve())
        if args.command == "start":
            result = controller.start(timeout_seconds=args.timeout_seconds)
            _print_json(result)
            return 0 if result["status"] in ("started", "already_running") else 1
        if args.command == "stop":
            result = controller.stop(timeout_seconds=args.timeout_seconds)
            _print_json(result)
            return 1 if result["status"] == "stop_failed" else 0
        if args.command == "status":
            _print_json(controller.status())
            return 0
    except (FileNotFoundError, RuntimeStateError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 2


def _spawn_manager(config: HubConfig, log_path: Path) -> subprocess.Popen[Any]:
    log = log_path.open("a", encoding="utf-8")
    command = [sys.executable, "-m", "mcp_hub.api_server", "--root", str(config.root)]
    kwargs: dict[str, Any] = {
        "cwd": config.root,
        "stdout": log,
        "stderr": subprocess.STDOUT,
        "stdin": subprocess.DEVNULL,
        "text": True,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(
            subprocess, "DETACHED_PROCESS", 0
        )
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(command, **kwargs)


def _wait_for_health(url: str, process: subprocess.Popen[Any], timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        if _health_ok(url, timeout=0.5):
            return True
        time.sleep(0.1)
    return False


def _health_ok(url: str, timeout: float) -> bool:
    try:
        with urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 300
    except OSError, URLError, TimeoutError:
        return False


def _is_process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        return _windows_process_alive(pid)
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _terminate_process(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return


def _windows_process_alive(pid: int) -> bool:
    process_query_limited_information = 0x1000
    still_active = 259
    handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        return False
    exit_code = ctypes.c_ulong()
    try:
        if not ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return False
        return exit_code.value == still_active
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _wait_until_stopped(pid: int, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not _is_process_alive(pid):
            return True
        time.sleep(0.1)
    return not _is_process_alive(pid)


def _manager_state(state: dict[str, Any]) -> dict[str, Any]:
    manager = state.get("manager", {})
    return manager if isinstance(manager, dict) else {}


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
