"""Paths and child commands shared by source and frozen Windows builds."""

import sys
from pathlib import Path


def frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def task_command(task: str, script: str, arguments=()) -> list[str]:
    if frozen():
        return [sys.executable, f"--{task}", *arguments]
    return [sys.executable, str(resource_root() / "scripts" / script), *arguments]
