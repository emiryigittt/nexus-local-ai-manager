import json
import sys

import pytest
from PyQt6.QtCore import QProcess
from PyQt6.QtWidgets import QDialog, QMessageBox

from backend.user_settings import SettingsStore, UserPreferences
from backend.wake_model import resolve_wake_model
from frontend.setup_dialog import SetupDialog
from frontend.voice_settings import VoiceSettings
from frontend.wake_setup import WakeSetupPanel
from scripts import setup_wake_model


@pytest.mark.parametrize("allow_download", [False, True])
def test_model_resolution_requires_explicit_network_flag(monkeypatch, tmp_path, allow_download):
    for name in ("model.bin", "config.json", "tokenizer.json"):
        (tmp_path / name).touch()
    seen = []

    def download(name, **options):
        seen.append((name, options))
        return str(tmp_path)

    monkeypatch.setattr("backend.wake_model.download_model", download)
    assert resolve_wake_model(allow_download=allow_download) == tmp_path
    assert seen == [("base", {"local_files_only": not allow_download})]


def test_incomplete_cache_is_rejected(monkeypatch, tmp_path):
    (tmp_path / "model.bin").touch()
    monkeypatch.setattr("backend.wake_model.download_model", lambda *args, **kwargs: str(tmp_path))
    with pytest.raises(RuntimeError, match="Incomplete"):
        resolve_wake_model()


@pytest.mark.parametrize("args, allowed", [([], False), (["--download"], True)])
def test_setup_command_validates_model_without_audio(monkeypatch, capsys, args, allowed):
    seen = []
    monkeypatch.setattr(setup_wake_model, "resolve_wake_model",
                        lambda **options: seen.append(options) or "model-cache")
    monkeypatch.setattr(setup_wake_model, "load_wake_model", lambda path: seen.append(path))
    monkeypatch.setattr("sounddevice.InputStream", lambda **kwargs: pytest.fail("microphone opened"))
    assert setup_wake_model.main(args) == 0
    assert seen == [{"allow_download": allowed}, "model-cache"]
    stages = [json.loads(line)["stage"] for line in capsys.readouterr().out.splitlines()]
    assert stages == ["downloading" if allowed else "checking", "validating", "ready"]


def test_setup_command_does_not_expose_exception_details(monkeypatch, capsys):
    def fail(**kwargs):
        raise RuntimeError("PRIVATE PATH AND TOKEN")

    monkeypatch.setattr(setup_wake_model, "resolve_wake_model", fail)
    assert setup_wake_model.main([]) == 1
    output = capsys.readouterr()
    assert "PRIVATE" not in output.out + output.err
    assert json.loads(output.out.splitlines()[-1]) == {"stage": "failed"}


def test_download_requires_confirmation_with_no_as_default(monkeypatch):
    panel = WakeSetupPanel("en")
    seen = []
    monkeypatch.setattr(panel, "start", lambda **kwargs: seen.append(kwargs))

    def reject(*args):
        assert args[-1] == QMessageBox.StandardButton.No
        assert "Hugging Face" in args[2] and "does not grant listening permission" in args[2]
        return QMessageBox.StandardButton.No

    monkeypatch.setattr(QMessageBox, "question", reject)
    panel.confirm_download()
    assert seen == []
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    panel.confirm_download()
    assert seen == [{"download": True}]
    panel.close()


@pytest.mark.parametrize("download", [False, True])
def test_setup_process_arguments_are_fixed_and_offline_by_default(monkeypatch, download):
    panel = WakeSetupPanel()
    calls = []
    monkeypatch.setattr(panel.process, "start", lambda: calls.append(panel.process.arguments()))
    panel.start(download=download)
    assert panel.process.program() == sys.executable
    assert calls[0][0].endswith("setup_wake_model.py")
    assert calls[0][1:] == (["--download"] if download else [])
    assert not panel.check.isEnabled() and panel.cancel.isEnabled()
    panel.process_error(QProcess.ProcessError.FailedToStart)
    assert panel.check.isEnabled() and not panel.cancel.isEnabled()
    assert "başlatılamadı" in panel.status.text()
    assert not panel.timeout.isActive()
    panel.close()


@pytest.mark.parametrize("exit_code, stage, success", [(0, "ready", True), (1, "ready", False),
                                                       (0, "validating", False)])
def test_only_clean_validated_exit_reports_success(monkeypatch, exit_code, stage, success):
    panel = WakeSetupPanel("en")
    data = [b'not json PRIVATE\n{"stage": []}\n[]\n' + json.dumps({"stage": stage}).encode() + b"\n"]
    monkeypatch.setattr(panel.process, "readAllStandardOutput", lambda: data.pop() if data else b"")
    panel.finished(exit_code, QProcess.ExitStatus.NormalExit)
    assert ("Model verified" in panel.status.text()) == success
    if not success:
        assert "Set up model" in panel.status.text()
    assert "PRIVATE" not in panel.status.text()
    panel.close()


def test_output_buffer_is_bounded_and_cancelled_success_is_ignored(monkeypatch):
    panel = WakeSetupPanel("en")
    data = [b"x" * 10000, b'\n{"stage":"ready"}\n']
    monkeypatch.setattr(panel.process, "readAllStandardOutput", lambda: data.pop(0) if data else b"")
    panel.read_output()
    assert len(panel.buffer) == 4096
    panel.stop()
    panel.finished(0, QProcess.ExitStatus.NormalExit)
    assert "Task stopped" in panel.status.text()
    assert "Model verified" not in panel.status.text()
    panel.close()


def test_reject_settings_kills_preparation_process_without_changing_consent(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    store.save(UserPreferences.defaults())
    before = store.path.read_bytes()
    dialog = SetupDialog(store)
    panel = dialog.voice.wake_setup
    # Real disposable child, no download/model/microphone involved.
    panel.process.setProgram(sys.executable)
    panel.process.setArguments(["-c", "import time; time.sleep(30)"])
    panel.process.start()
    try:
        assert panel.process.waitForStarted(2000)
        dialog.voice.wake.setChecked(True)  # Unsaved consent must remain unsaved.
        dialog.reject()
        assert not panel.busy
        assert dialog.result() == QDialog.DialogCode.Rejected
        assert store.path.read_bytes() == before
    finally:
        panel.stop_and_wait()
        dialog.close()


def test_timeout_stops_child_and_reports_timeout():
    panel = WakeSetupPanel("en")
    panel.process.setProgram(sys.executable)
    panel.process.setArguments(["-c", "import time; time.sleep(30)"])
    panel.process.start()
    try:
        assert panel.process.waitForStarted(2000)
        panel.timed_out()
        assert panel.stop_and_wait()
        assert "timed out" in panel.status.text()
        assert panel.check.isEnabled()
    finally:
        panel.stop_and_wait()
        panel.close()


def test_device_check_never_opens_microphone_or_changes_selected_device(monkeypatch):
    monkeypatch.setattr("sounddevice.InputStream", lambda **kwargs: pytest.fail("microphone opened"))
    monkeypatch.setattr("frontend.voice_settings.input_devices", lambda: [{"id": "mic", "name": "Test mic"}])
    preferences = UserPreferences.defaults()
    preferences.language = "en"
    preferences.voice_input_device = "disconnected"
    panel = VoiceSettings(preferences)
    assert "disconnected" in panel.microphone_status.text()
    assert panel.input.currentData() == "disconnected"
    panel.input.setCurrentIndex(panel.input.findData("mic"))
    assert "have not been tested" in panel.microphone_status.text()
    assert not panel.wake.isChecked()
    assert not panel.wake_setup.busy
    panel.close()
