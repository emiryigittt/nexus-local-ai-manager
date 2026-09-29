import asyncio
import threading
import time

import httpx
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication

from backend.user_settings import SettingsStore, UserPreferences
from frontend.app import ChatWorker, SpotlightApp
from frontend.setup_dialog import SetupDialog
from frontend.voice_worker import StreamingVoiceWorker, VoiceRecordWorker


def pump(app, predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.005)
    app.processEvents()
    assert predicate()


def test_markdown_stream_completion_and_cancel_never_raise():
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    window.append_response("**Merhaba** ")
    window.append_response('<img src="https://example.invalid/pixel">')
    window.active_memory_sources = [{"content": "Tercih", "id": "one"}]
    window.complete_response()
    assert "Merhaba" in window.output_browser.toPlainText()
    assert "Kullanılan hafıza" in window.output_browser.toPlainText()
    assert '<img src="https://' not in window.output_browser.toHtml()
    window.response_was_cancelled()
    assert "durduruldu" in window.output_browser.toPlainText()
    window.close()
    app.processEvents()


def test_private_switch_clears_context_and_blocks_persistent_memory(monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    original_id = window.current_conversation_id
    window.input_line.add_to_history("normal prompt")
    window.active_memory_sources = [{"content": "old"}]
    window.toggle_private_session()
    assert window.current_conversation_id != original_id
    assert not window.active_memory_sources
    assert not window.input_line.history.history
    window._pending_prompt = "Adı Orion"
    window.append_response("Anladım")
    window.complete_response()
    assert window._private_history[0]["content"] == "Adı Orion"

    def forbidden(*args, **kwargs):
        raise AssertionError("Private data must not be saved")

    monkeypatch.setattr("frontend.app.memory_repository.add", forbidden)
    window.input_line.setText("/remember private fact")
    window.send_message()
    assert "kalıcı hafızaya" in window.output_browser.toPlainText()
    window.toggle_private_session()
    assert not window._private_history
    window.close()
    app.processEvents()


class SlowWorker(QThread):
    response_chunk = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.release = threading.Event()

    def run(self):
        self.release.wait(3)
        self.response_chunk.emit("old response")

    def cancel(self):
        self.requestInterruption()


def test_new_chat_keeps_cancelled_worker_alive_and_ignores_late_response():
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    worker = SlowWorker()
    window.worker = worker
    window._track_worker(worker)
    window._connect_current(worker, "worker", worker.response_chunk, window.append_response)
    worker.start()
    try:
        window.new_conversation()
        assert worker in window._workers
        worker.release.set()
        pump(app, lambda: not window._workers)
        assert window.streaming_text == ""
    finally:
        worker.release.set()
        window.close()


def test_stop_speech_retains_worker_until_finished_and_discards_late_audio(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    window.tts_enabled = True
    worker = StreamingVoiceWorker(backend="local")
    entered, release = threading.Event(), threading.Event()
    paths = []

    def synthesize(text, path):
        paths.append(path)
        entered.set()
        release.wait(3)
        return True

    worker.speaker.speak_to_file = synthesize
    window.stream_voice_worker = worker
    window._track_worker(worker)
    worker.audio_ready.connect(window.play_audio)
    worker.enqueue("A queued sentence")
    worker.start()
    try:
        pump(app, entered.is_set)
        window.toggle_tts()
        assert worker in window._workers
        assert window.stream_voice_worker is None
        release.set()
        pump(app, lambda: not window._workers)
        from pathlib import Path
        assert all(not Path(path).exists() for path in paths)
        assert not window.audio_queue
    finally:
        release.set()
        window.close()


def test_chat_cancel_interrupts_pending_network_request(monkeypatch):
    app = QApplication.instance() or QApplication([])
    entered = threading.Event()
    client_type = httpx.AsyncClient

    async def stalled(request):
        entered.set()
        await asyncio.sleep(60)
        return httpx.Response(200)

    monkeypatch.setattr("frontend.app.httpx.AsyncClient", lambda **kwargs: client_type(
        transport=httpx.MockTransport(stalled), **kwargs
    ))
    worker = ChatWorker("Test")
    worker.start()
    try:
        pump(app, entered.is_set)
        worker.cancel()
        assert worker.wait(2000)
    finally:
        worker.cancel()
        worker.wait(2000)


def test_setup_preserves_model_and_uses_each_providers_own_selection(tmp_path):
    app = QApplication.instance() or QApplication([])
    store = SettingsStore(tmp_path / "settings.json")
    preferences = UserPreferences.defaults()
    preferences.providers[0].selected_model = "lm-model"
    preferences.providers[1].selected_model = "ollama-model"
    store.save(preferences)
    dialog = SetupDialog(store)
    assert dialog.model.currentText() == "lm-model"
    dialog.provider.setCurrentIndex(1)
    assert dialog.model.currentText() == "ollama-model"
    dialog.save()
    assert store.selected_provider().selected_model == "ollama-model"
    dialog.close()
    app.processEvents()


def test_recording_stop_before_run_is_not_lost():
    app = QApplication.instance() or QApplication([])
    calls = []

    class Recorder:
        def start(self):
            calls.append("start")

        def stop(self):
            calls.append("stop")
            return []

    class Transcriber:
        def transcribe(self, audio):
            return "Test"

    worker = VoiceRecordWorker(Recorder(), Transcriber())
    worker.stop_recording()
    worker.start()
    assert worker.wait(2000)
    assert calls[0] == "start"
    assert "stop" in calls
    app.processEvents()


def test_close_waits_for_worker_without_blocking_ui():
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    worker = SlowWorker()
    window.worker = worker
    window._track_worker(worker)
    worker.start()
    try:
        started = time.monotonic()
        window.close()
        assert time.monotonic() - started < 1
        assert window._quitting
        assert worker in window._workers
        worker.release.set()
        pump(app, lambda: not window._workers)
        # Drain the shutdown poll before subsequent tests use QApplication.
        pump(app, lambda: not window.isVisible())
    finally:
        worker.release.set()
        window.close()


def test_short_sentences_are_not_dropped_from_speech_queue():
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    worker = StreamingVoiceWorker(backend="local")
    window.stream_voice_worker = worker
    window.append_response("Merhaba! Evet. ")
    assert worker.sentences.get_nowait() == "Merhaba!"
    assert worker.sentences.get_nowait() == "Evet."
    window.close()
    app.processEvents()


def test_enabling_speech_reads_current_answer_and_persists_preference(tmp_path, monkeypatch):
    from types import SimpleNamespace

    app = QApplication.instance() or QApplication([])
    store = SettingsStore(tmp_path / "voice-settings.json")
    monkeypatch.setattr("frontend.app.settings_store", store)
    monkeypatch.delenv("NEXUS_TTS_ENABLED", raising=False)
    created = []

    class ProbeWorker(QThread):
        audio_ready = pyqtSignal(str)
        error_received = pyqtSignal(str)

        def __init__(self, backend=None):
            super().__init__()
            self.speaker = SimpleNamespace(backend="local")
            self.texts = []
            created.append(self)

        def enqueue(self, text):
            self.texts.append(text)

        def finish(self):
            pass

        def stop(self):
            pass

        def run(self):
            pass

    monkeypatch.setattr("frontend.app.StreamingVoiceWorker", ProbeWorker)
    window = SpotlightApp()
    window.append_response("Merhaba!")
    window.complete_response()
    window.toggle_tts()
    assert created[0].texts == ["Merhaba!"]
    assert store.load().tts_enabled
    pump(app, lambda: not window._workers)
    window.close()

    reopened = SpotlightApp()
    assert reopened.tts_enabled
    reopened.toggle_tts()
    assert not store.load().tts_enabled
    reopened.close()
    app.processEvents()


def test_loading_audio_is_not_replaced_by_next_ready_sentence(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    window.tts_enabled = True
    window.current_audio_path = str(tmp_path / "loading.wav")
    queued = tmp_path / "next.wav"
    queued.write_bytes(b"test")

    def forbidden():
        raise AssertionError("Must not replace a file still loading in the player")

    monkeypatch.setattr(window, "_play_next_audio", forbidden)
    window.play_audio(str(queued))
    assert window.audio_queue == [str(queued)]
    window.close()
    app.processEvents()


def test_deadline_flush_keeps_unfinished_word(monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    worker = StreamingVoiceWorker(backend="local")
    window.stream_voice_worker = worker
    text = "Bu uzun cümlede noktalama beklemeden konuşmaya başlayabilir ve tamamlanma"
    window.append_response(text)
    monkeypatch.setattr("frontend.app.time.monotonic", lambda: window._speech_wait_started + 2)
    window._flush_waiting_speech()
    assert worker.sentences.get_nowait() + " " + window.speech_buffer == text
    assert window.speech_buffer == "tamamlanma"
    window.close()
    app.processEvents()


def test_worker_reports_caption_before_audio_and_bounds_work():
    from pathlib import Path

    app = QApplication.instance() or QApplication([])
    worker = StreamingVoiceWorker(backend="local")
    events = []
    worker.chunk_ready.connect(lambda path, text, elapsed, backend: events.append(
        ("caption", path, text, elapsed, backend)))
    worker.audio_ready.connect(lambda path: events.append(("audio", path)))
    worker.speaker.speak_to_file = lambda text, path: True
    worker.enqueue("uzun cümle " * 60)
    worker.finish()
    worker.start()
    assert worker.wait(3000)
    app.processEvents()
    assert len(events) > 2
    for caption, audio in zip(events[::2], events[1::2], strict=True):
        assert caption[0] == "caption" and audio[:2] == ("audio", caption[1])
        assert len(caption[2]) <= 180
        assert caption[3] >= 0 and caption[4] == "local"
        Path(caption[1]).unlink(missing_ok=True)


def test_memory_preview_explains_pending_approval(monkeypatch, tmp_path):
    from backend.memory import MemoryRepository

    app = QApplication.instance() or QApplication([])
    repository = MemoryRepository(tmp_path / "memory.db")
    repository.add_candidate("Kısa cevapları sever", "preference", "response.style")
    monkeypatch.setattr("frontend.app.memory_repository", repository)
    window = SpotlightApp()
    window.show_remembered_context()
    assert "1 aday kayıt" in window.output_browser.toPlainText()
    assert "onayınızı bekliyor" in window.output_browser.toPlainText()
    window.close()
    app.processEvents()
