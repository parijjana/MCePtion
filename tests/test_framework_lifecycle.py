from __future__ import annotations

import os
import unittest
from pathlib import Path
from shutil import copytree
from unittest.mock import patch

from workspace_utils import test_workspace

from mcp_hub.framework import FrameworkController

ROOT = Path(__file__).resolve().parents[1]


class FakeProcess:
    def __init__(self, pid: int = 4321) -> None:
        self.pid = pid

    def poll(self) -> int | None:
        return None


class FrameworkLifecycleTests(unittest.TestCase):
    def test_status_reports_stopped_without_state(self) -> None:
        controller = FrameworkController.from_root(_copy_hub_minimum("framework-status"))

        result = controller.status()

        self.assertEqual(result["status"], "stopped")
        self.assertTrue(result["state_path"].endswith("data\\runtime-state.json"))

    def test_start_refuses_duplicate_running_manager(self) -> None:
        hub_root = _copy_hub_minimum("framework-duplicate-start")
        controller = FrameworkController.from_root(hub_root)
        controller._write_state(
            {
                "schema_version": 1,
                "manager": {
                    "status": "running",
                    "pid": os.getpid(),
                    "host": "127.0.0.1",
                    "port": 7420,
                    "url": "http://127.0.0.1:7420",
                },
            }
        )

        result = controller.start()

        self.assertEqual(result["status"], "already_running")
        self.assertEqual(result["manager"]["pid"], os.getpid())

    def test_start_replaces_stale_record_and_writes_runtime_state(self) -> None:
        hub_root = _copy_hub_minimum("framework-stale-start")
        controller = FrameworkController.from_root(hub_root)
        controller._write_state(
            {"schema_version": 1, "manager": {"status": "running", "pid": 999999}}
        )

        with (
            patch("mcp_hub.framework._is_process_alive", return_value=False),
            patch("mcp_hub.framework._spawn_manager", return_value=FakeProcess(pid=2468)),
            patch("mcp_hub.framework._wait_for_health", return_value=True),
        ):
            result = controller.start()

        status = controller.status()
        self.assertEqual(result["status"], "started")
        self.assertEqual(status["manager"]["pid"], 2468)
        self.assertTrue(status["manager"]["stale_replaced"])
        self.assertTrue(Path(status["manager"]["log_path"]).name.startswith("manager-"))

    def test_stop_targets_only_recorded_pid(self) -> None:
        hub_root = _copy_hub_minimum("framework-stop")
        controller = FrameworkController.from_root(hub_root)
        controller._write_state(
            {"schema_version": 1, "manager": {"status": "running", "pid": 2468}}
        )
        stopped: list[int] = []

        def record_stop(pid: int) -> None:
            stopped.append(pid)

        with (
            patch("mcp_hub.framework._is_process_alive", return_value=True),
            patch("mcp_hub.framework._terminate_process", side_effect=record_stop),
            patch("mcp_hub.framework._wait_until_stopped", return_value=True),
        ):
            result = controller.stop()

        self.assertEqual(result["status"], "stopped")
        self.assertEqual(stopped, [2468])
        self.assertEqual(controller.status()["status"], "stopped")


def _copy_hub_minimum(name: str) -> Path:
    hub_root = test_workspace(name) / "hub"
    hub_root.mkdir(parents=True, exist_ok=True)
    (hub_root / "servers").mkdir(exist_ok=True)
    copytree(ROOT / "guidelines", hub_root / "guidelines", dirs_exist_ok=True)
    (hub_root / "framework.yaml").write_text(
        (ROOT / "framework.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    return hub_root


if __name__ == "__main__":
    unittest.main()
