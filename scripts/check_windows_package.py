"""Isolated packaged checks using a fake model server, never real conversations."""

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class ModelStub(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, status, value):
        content = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        self.send_json(200, {"data": [{"id": "packaging-test-model"}]})

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if payload.get("model") == "missing-model":
            self.send_json(404, {"error": "Synthetic missing model"})
        else:
            self.send_json(200, {"choices": [{"message": {"role": "assistant", "content": "OK"}}]})


def run_process(command, environment, timeout=40):
    return subprocess.run(command, env=environment, timeout=timeout, check=False,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          creationflags=subprocess.CREATE_NO_WINDOW).returncode


def installer_is_registered():
    import winreg

    key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\{61E722A9-E745-41D0-BE45-9D334730D46D}_is1"
    for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_READ | view):
                return True
        except FileNotFoundError:
            pass
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--application", type=Path, default=ROOT / "dist/Nexus/Nexus.exe")
    parser.add_argument("--installer", type=Path)
    parser.add_argument("--voice-model", type=Path)
    parser.add_argument("--report", type=Path, default=ROOT / "build/windows-package-check.json")
    args = parser.parse_args()
    if sys.platform != "win32":
        raise SystemExit("Run on Windows")
    if args.installer and installer_is_registered():
        raise SystemExit("Existing Nexus installation detected; isolated installer test skipped to preserve it")
    report = {"model_server": "synthetic HTTP stub; no real inference quality claim", "checks": {}}
    if args.installer:
        with args.installer.open("rb") as stream:
            report["installer_sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
    server = ThreadingHTTPServer(("127.0.0.1", 0), ModelStub)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with tempfile.TemporaryDirectory(prefix="packaged-check-", dir=ROOT / "build") as temporary:
            root = Path(temporary)
            environment = os.environ.copy()
            environment["NEXUS_DATA_DIR"] = str(root / "data")
            environment["QT_QPA_PLATFORM"] = "offscreen"
            environment["HF_HUB_OFFLINE"] = "1"
            environment["HF_HUB_DISABLE_TELEMETRY"] = "1"
            windows = Path(os.environ.get("SystemRoot", "C:/Windows"))
            environment["PATH"] = os.pathsep.join([str(windows / "System32"), str(windows)])
            from backend.user_settings import SettingsStore, UserPreferences

            preferences = UserPreferences.defaults()
            preferences.providers[0].base_url = f"http://127.0.0.1:{server.server_port}/v1"
            SettingsStore(root / "data/settings.json").save(preferences)
            app = str(args.application.resolve())

            def check(name, condition):
                report["checks"][name] = bool(condition)
                if not condition:
                    raise RuntimeError(f"Packaged check failed: {name}")

            def events(task, arguments):
                path = root / f"{task}-{time.time_ns()}.jsonl"
                environment["NEXUS_SETUP_EVENTS"] = str(path)
                code = run_process([app, task, *arguments], environment)
                values = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
                return code, values

            smoke = root / "smoke.json"
            check("desktop_imports_and_resources", run_process([app, "--self-test", str(smoke)], environment) == 0)
            internal = args.application.resolve().parent / "_internal"
            notices = internal / "distribution-notices"
            check("packaged_distribution_notices", all((notices / name).is_file() for name in ("COPYING", "LICENSE", "SOURCE_ACCESS.txt", "dependency-sources.json", "nexus-source.zip")))
            check("unneeded_native_libraries_excluded", not any(path.name.lower() in {"qpdf.dll", "qt6pdf.dll", "opengl32sw.dll"} or (path.name.lower().startswith("libportaudio") and path.name.lower() != "libportaudio64bit.dll") for path in internal.rglob("*.dll")))
            payload = json.loads(smoke.read_text())
            check("frozen_three_step_wizard", payload["frozen"] and payload["wizard_steps"] == 3)
            check("frozen_top_edge_and_customization", payload["top_edge_notch"] and payload["appearance_controls"])
            check("frozen_memory_cards", payload["memory_cards"])
            check("frozen_original_sound_assets", payload["sound_assets"])
            check("frozen_speech_detector_no_microphone", payload["speech_detector"])
            check("frozen_speech_input_controls", payload["speech_input_controls"])
            code, values = events("--onboarding-task", ["discover"])
            check("local_discovery", code == 0 and any(item["healthy"] and "packaging-test-model" in item["models"] for item in values[-1]["providers"]))
            code, values = events("--onboarding-task", ["test", "--provider", "lm-studio", "--model", "packaging-test-model"])
            check("connection_round_trip", code == 0 and values[-1]["stage"] == "ready")
            code, values = events("--onboarding-task", ["test", "--provider", "lm-studio", "--model", "missing-model"])
            check("missing_model_not_success", code != 0 and values[-1]["stage"] == "failed")
            if args.voice_model:
                environment["NEXUS_SUPERTONIC_MODEL_DIR"] = str(args.voice_model.resolve())
                code, values = events("--prepare-voice", [])
                check("local_voice_engine_offline", code == 0 and values[-1]["stage"] == "ready")

            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            environment["NEXUS_BACKEND_PORT"] = str(port)
            api = subprocess.Popen([app, "--backend"], env=environment, creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                url = f"http://127.0.0.1:{port}"
                deadline = time.monotonic() + 15
                healthy = False
                while time.monotonic() < deadline and api.poll() is None:
                    try:
                        with urllib.request.urlopen(url + "/health", timeout=1) as response:
                            healthy = response.status == 200
                            break
                    except (urllib.error.URLError, TimeoutError):
                        time.sleep(0.1)
                check("packaged_api_health", healthy)
                request = urllib.request.Request(url + "/api/v1/documents", data=json.dumps({
                    "name": "packaging-sample.md", "content": (ROOT / "docs/demo/project-brief.md").read_text(encoding="utf-8"),
                    "source_type": "markdown",
                }).encode(), headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(request, timeout=12) as response:
                    check("sample_document_ingestion", response.status in {200, 201})
            finally:
                api.terminate()
                try:
                    api.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    api.kill()
                    api.wait(timeout=3)
            check("api_process_cleanup", api.poll() is not None)

            if args.installer:
                target = root / "installed"
                if not target.resolve().is_relative_to((ROOT / "build").resolve()):
                    raise RuntimeError("Installer test target escapes build")
                sentinel = root / "data/preserve-on-uninstall.txt"
                sentinel.write_text("synthetic test data", encoding="utf-8")
                install_log = root / "installer.log"
                install_code = run_process([str(args.installer.resolve()), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/NOICONS", "/CURRENTUSER", f"/DIR={target}", f"/LOG={install_log}"], environment, timeout=90)
                report["installer_exit_code"] = install_code
                if install_code != 0 and install_log.exists():
                    report["installer_log_tail"] = install_log.read_text(encoding="utf-8-sig", errors="replace")[-6000:]
                try:
                    check("installer_completed", install_code == 0 and (target / "Nexus.exe").is_file())
                    check("installed_app_opens_without_python", run_process([str(target / "Nexus.exe"), "--self-test", str(root / "installed-smoke.json")], environment) == 0)
                    upgrade_code = run_process([str(args.installer.resolve()), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/NOICONS", "/CURRENTUSER", f"/DIR={target}"], environment, timeout=90)
                    check("installer_upgrade_completed", upgrade_code == 0 and sentinel.read_text() == "synthetic test data" and run_process([str(target / "Nexus.exe"), "--self-test", str(root / "upgraded-smoke.json")], environment) == 0)
                finally:
                    uninstall = target / "unins000.exe"
                    if uninstall.is_file():
                        uninstall_code = run_process([str(uninstall), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"], environment, timeout=60)
                        check("uninstaller_completed", uninstall_code == 0 and not (target / "Nexus.exe").exists())
                check("uninstall_preserves_user_data", sentinel.read_text() == "synthetic test data")
                check("uninstall_removes_test_registration", not installer_is_registered())
    except Exception as exc:
        report["error"] = type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        server.shutdown()
        server.server_close()
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
        if report.get("error"):
            print(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
