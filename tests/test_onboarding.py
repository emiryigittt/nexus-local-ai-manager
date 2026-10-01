import asyncio
import json
import sys

import httpx
import pytest
from PyQt6.QtCore import QProcess
from PyQt6.QtWidgets import QDialog, QMessageBox

from backend.runtime import resource_root, task_command
from backend.user_settings import ProviderProfile, SettingsStore, UserPreferences
from frontend.app import SpotlightApp
from frontend.local_voice_setup import LocalVoiceSetupPanel
from frontend.onboarding import OnboardingDialog
from frontend.setup_task import SetupTask
from scripts import onboarding_task, setup_local_tts


def populated_dialog(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    preferences = UserPreferences.defaults()
    preferences.web_consent = True
    preferences.memory_enabled = True
    store.save(preferences)
    dialog = OnboardingDialog(store=store)
    dialog.results = [{"id": "ollama", "name": "Ollama", "healthy": True, "models": ["sample-a", "sample-b"]}]
    dialog.provider.addItem("Ollama", "ollama")
    dialog.fill_models()
    return dialog, store


def test_cancelled_first_run_preserves_preferences(tmp_path):
    dialog, store = populated_dialog(tmp_path)
    original = store.path.read_bytes()
    dialog.language.setCurrentIndex(dialog.language.findData("en"))
    dialog.reject()
    assert dialog.result() == QDialog.DialogCode.Rejected
    assert store.path.read_bytes() == original


def test_finish_requires_inference_and_preserves_privacy(tmp_path):
    dialog, store = populated_dialog(tmp_path)
    dialog.finish_setup()
    assert not store.load().setup_complete
    dialog.job = "test"
    dialog.completed(True)
    dialog.language.setCurrentIndex(dialog.language.findData("en"))
    dialog.finish_setup()
    preferences = store.load()
    assert preferences.setup_complete and preferences.language == "en"
    assert preferences.selected_provider_id == "ollama"
    assert preferences.providers[1].selected_model == "sample-a"
    assert preferences.web_consent and preferences.memory_enabled
    assert not preferences.wake_word_enabled and not preferences.cloud_speech_consent


def test_model_change_invalidates_successful_test(tmp_path):
    dialog, store = populated_dialog(tmp_path)
    dialog.job = "test"
    dialog.completed(True)
    dialog.model.setCurrentIndex(1)
    dialog.finish_setup()
    assert not store.load().setup_complete
    dialog.reject()


def test_empty_server_and_failed_discovery_cannot_complete(tmp_path):
    dialog = OnboardingDialog(store=SettingsStore(tmp_path / "settings.json"))
    dialog.pages.setCurrentIndex(1)
    dialog.job = "discover"
    dialog.receive({"stage": "ready", "providers": [{"id": "ollama", "healthy": True, "models": []}]})
    dialog.completed(True)
    assert dialog.provider.count() == 0
    assert not dialog.next.isEnabled()
    assert "bulunamadı" in dialog.status.text()
    dialog.reject()


@pytest.mark.parametrize("url, allowed", [
    ("http://127.0.0.1:1234/v1", True), ("http://[::1]:8080/v1", True),
    ("http://localhost:11434/v1", True), ("https://example.com/v1", False),
    ("http://192.168.1.2/v1", False), ("file:///private", False),
])
def test_automatic_discovery_only_uses_loopback(url, allowed):
    assert onboarding_task.is_loopback(ProviderProfile("test", "Test", "custom", url)) == allowed


def test_inference_failure_does_not_leak_response(monkeypatch, capsys):
    class Client:
        def __init__(self, **options):
            assert options["trust_env"] is False

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, **options):
            assert options["json"]["stream"] is False
            return httpx.Response(500, request=httpx.Request("POST", url), text="PRIVATE TOKEN")

    monkeypatch.setattr(onboarding_task.httpx, "AsyncClient", Client)
    assert asyncio.run(onboarding_task.run("test", "ollama", "sample")) == 1
    assert json.loads(capsys.readouterr().out) == {"stage": "failed"}


def test_event_success_requires_ready_and_clean_exit(tmp_path):
    task = SetupTask()
    events, results = [], []
    task.event_received.connect(events.append)
    task.completed.connect(results.append)
    task.path = tmp_path / "events"
    task.path.write_text('{"stage":"ready"}\n', encoding="utf-8")
    task._finished(1, QProcess.ExitStatus.NormalExit)
    assert results == [False] and events == [{"stage": "ready"}]
    assert not (tmp_path / "events").exists()


def test_frozen_tasks_do_not_invoke_python_module(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", "C:/test/bundle", raising=False)
    assert task_command("prepare-whisper", "setup_wake_model.py", ["--download"]) == [sys.executable, "--prepare-whisper", "--download"]
    assert resource_root().as_posix() == "C:/test/bundle"


def test_voice_download_requires_explicit_confirmation(monkeypatch):
    panel = LocalVoiceSetupPanel("en")
    seen = []
    monkeypatch.setattr(panel, "start", seen.append)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    panel.confirm_download()
    assert seen == []
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    panel.confirm_download()
    assert seen == [True]
    panel.close()


def test_voice_check_does_not_download(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(setup_local_tts, "TARGET_DIR", tmp_path / "missing")
    monkeypatch.setattr(setup_local_tts.importlib.util, "find_spec", lambda name: True)
    monkeypatch.setattr(setup_local_tts.urllib.request, "urlopen", lambda *args, **kwargs: pytest.fail("unexpected download"))
    assert setup_local_tts.main([]) == 1
    assert [json.loads(line)["stage"] for line in capsys.readouterr().out.splitlines()] == ["checking", "failed"]


def test_stopping_setup_terminates_child_and_removes_events(monkeypatch):
    task = SetupTask()
    monkeypatch.setattr("frontend.setup_task.task_command", lambda *args: [sys.executable, "-c", "import time; time.sleep(30)"])
    task.start("unused", "unused.py")
    path = task.path
    assert task.process.waitForStarted(3000)
    assert task.busy
    assert task.stop()
    assert not task.busy and not path.exists()


def test_sample_document_is_real_local_content_and_waits_for_send(monkeypatch):
    requests = []
    monkeypatch.setattr("frontend.app.request_json", lambda *args: requests.append(args))
    window = SpotlightApp()
    window.try_sample_document()
    assert len(requests) == 1
    method, route, payload = requests[0]
    assert method == "POST" and route == "/api/v1/documents"
    assert payload["name"] == "project-brief.md" and "Aurora" in payload["content"]
    assert window.knowledge_enabled and window.knowledge_btn.isChecked()
    assert "Örnek proje" in window.input_line.text()
    assert window.worker is None
    window.close()


def test_voice_archive_rejects_path_traversal(tmp_path):
    import io
    import tarfile

    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        item = tarfile.TarInfo("../outside.txt")
        item.size = 1
        archive.addfile(item, io.BytesIO(b"x"))
    stream.seek(0)
    with tarfile.open(fileobj=stream) as archive, pytest.raises(RuntimeError, match="Unsafe"):
        setup_local_tts._safe_extract(archive, tmp_path / "inside")
    assert not (tmp_path / "outside.txt").exists()
