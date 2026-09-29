"""Start and supervise the Nexus API and desktop application."""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from backend.config import settings

PROJECT_ROOT = Path(__file__).resolve().parent


def _is_backend_ready() -> bool:
    try:
        with urllib.request.urlopen(f"{settings.backend_url}/health", timeout=1) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def _wait_for_backend(process: subprocess.Popen | None, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _is_backend_ready():
            return
        if process is not None and process.poll() is not None:
            raise RuntimeError(f"Nexus API exited with code {process.returncode}.")
        time.sleep(0.2)
    raise RuntimeError(f"Nexus API did not start at {settings.backend_url}.")


def _stop(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()


def main() -> int:
    backend_process = None
    frontend_process = None
    try:
        if not _is_backend_ready():
            backend_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "backend.main:app",
                    "--host",
                    settings.backend_host,
                    "--port",
                    str(settings.backend_port),
                ],
                cwd=PROJECT_ROOT,
                env=os.environ.copy(),
            )
        _wait_for_backend(backend_process)

        frontend_process = subprocess.Popen(
            [sys.executable, "-m", "frontend.app"],
            cwd=PROJECT_ROOT,
            env=os.environ.copy(),
        )
        return frontend_process.wait()
    except KeyboardInterrupt:
        return 0
    except RuntimeError as exc:
        print(f"Nexus could not start: {exc}", file=sys.stderr)
        return 1
    finally:
        _stop(frontend_process)
        _stop(backend_process)


if __name__ == "__main__":
    raise SystemExit(main())
