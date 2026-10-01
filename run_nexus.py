"""Start and supervise the Nexus API and desktop application."""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from backend.app_paths import ensure_data_dirs
from backend.config import settings
from backend.runtime import frozen, resource_root

PROJECT_ROOT = resource_root()


def configure_frozen_logging():
    if frozen():
        role = {"--backend": "backend", "--frontend": "frontend"}.get(sys.argv[1] if len(sys.argv) > 1 else "", "desktop")
        path = ensure_data_dirs() / "logs" / f"{role}.log"
        # Truncate at each launch to avoid unbounded local logs.
        stream = path.open("w", encoding="utf-8", buffering=1)
        sys.stdout = sys.stderr = stream


def dispatch(argv):
    if not argv:
        return main()
    task = argv[0]
    if task == "--backend":
        import uvicorn

        uvicorn.run("backend.main:app", host=settings.backend_host, port=settings.backend_port, access_log=False)
        return 0
    if task == "--frontend":
        from frontend.app import main as desktop_main

        return desktop_main()
    if task == "--prepare-whisper":
        from scripts.setup_wake_model import main as prepare

        return prepare(argv[1:])
    if task == "--prepare-speech":
        from scripts.setup_speech_model import main as prepare

        return prepare(argv[1:])
    if task == "--prepare-voice":
        from scripts.setup_local_tts import main as prepare

        return prepare(argv[1:])
    if task == "--onboarding-task":
        from scripts.onboarding_task import main as prepare

        return prepare(argv[1:])
    if task == "--self-test":
        import json

        import numpy as np
        from PyQt6.QtWidgets import QApplication

        from backend.main import app as api
        from backend.speech_endpoint import SpeechEndpoint
        from frontend.app import SpotlightApp
        from frontend.memory_dialog import MemoryCardDelegate, MemoryDialog
        from frontend.onboarding import OnboardingDialog
        from frontend.setup_dialog import SetupDialog
        from frontend.sound_feedback import SoundFeedback

        app = QApplication([])
        window = SpotlightApp()
        dialog = OnboardingDialog()
        appearance = SetupDialog(parent=window)
        memory = MemoryDialog(parent=window)
        endpoint = SpeechEndpoint()
        stopped_on_silence = endpoint.feed(np.zeros(5120, dtype=np.float32))
        detector_ready = not stopped_on_silence and not endpoint.heard_speech
        endpoint.clear()
        result = {
            "frozen": frozen(), "api_routes": len(api.routes),
            "wizard_steps": dialog.pages.count(),
            "sample_document": (resource_root() / "docs/demo/project-brief.md").is_file(),
            "brand_asset": (resource_root() / "frontend/assets/nexus-mark.svg").is_file(),
            "top_edge_notch": window._shell_mode == "notch" and window.geometry() == window.notch_controller.target_rect("notch"),
            "appearance_controls": appearance.tabs.count() == 4 and appearance.appearance.character.findData("cat") >= 0,
            "memory_cards": memory.tabs.count() == 2 and isinstance(memory.list.itemDelegate(), MemoryCardDelegate),
            "speech_detector": detector_ready,
            "speech_input_controls": (appearance.voice.transcription_model.findData("small") >= 0
                                      and hasattr(appearance.voice, "auto_finish")
                                      and hasattr(appearance.voice, "review")),
            "sound_assets": all((resource_root() / "frontend/assets/sounds" / f"{name}.wav").is_file()
                                for name in SoundFeedback.NAMES),
        }
        appearance.reject()
        memory.close()
        dialog.reject()
        window.close()
        app.processEvents()
        target = Path(argv[1]) if len(argv) > 1 else ensure_data_dirs() / "logs" / "self-test.json"
        target.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return 0 if all(result[key] for key in ("sample_document", "brand_asset", "top_edge_notch", "appearance_controls", "memory_cards", "sound_assets", "speech_detector", "speech_input_controls")) else 1
    raise RuntimeError("Unknown Nexus launch option.")


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
                [sys.executable, "--backend"] if frozen() else [
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
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        _wait_for_backend(backend_process)

        frontend_process = subprocess.Popen(
            [sys.executable, "--frontend"] if frozen() else [sys.executable, "-m", "frontend.app"],
            cwd=PROJECT_ROOT,
            env=os.environ.copy(),
            creationflags=subprocess.CREATE_NO_WINDOW if frozen() and os.name == "nt" else 0,
        )
        return frontend_process.wait()
    except KeyboardInterrupt:
        return 0
    except (OSError, RuntimeError) as exc:
        print(f"Nexus could not start: {exc}", file=sys.stderr)
        if frozen():
            from PyQt6.QtWidgets import QApplication, QMessageBox

            app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "Nexus", "Nexus başlatılamadı. Uygulamayı yeniden açın.\nAyrıntılar: %LOCALAPPDATA%\\Nexus\\logs\\desktop.log")
            del app
        return 1
    finally:
        _stop(frontend_process)
        _stop(backend_process)


if __name__ == "__main__":
    configure_frozen_logging()
    raise SystemExit(dispatch(sys.argv[1:]))
