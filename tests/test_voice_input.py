import threading
from types import SimpleNamespace

import numpy as np
import pytest
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication

from backend.audio_transcriber import AudioRecorder
from backend.user_settings import SettingsStore, UserPreferences
from backend.voice_activity import VoiceActivity
from frontend.app import SpotlightApp
from frontend.voice_settings import VoiceSettings
from frontend.voice_worker import VoiceRecordWorker


def samples(level, count=100):
    return np.full((count, 1), level, dtype=np.float32)


def test_vad_ends_after_speech_and_silence_but_not_short_pause():
    detector = VoiceActivity(silence_seconds=0.5)
    assert not detector.feed(samples(0.05, 300), 1000)
    assert detector.heard_speech
    assert not detector.feed(samples(0, 300), 1000)
    assert detector.feed(samples(0, 201), 1000)


def test_vad_rejects_low_noise_and_single_short_click():
    detector = VoiceActivity()
    for _ in range(100):
        assert not detector.feed(samples(0.003), 1000)
    assert not detector.heard_speech
    detector.feed(samples(0.1, 10), 1000)
    assert not detector.heard_speech


def test_recorder_bounds_memory_and_clears_captured_samples():
    recorder = AudioRecorder(sample_rate=1000, max_seconds=0.5)
    recorder.is_recording = True
    recorder._callback(samples(0.05, 800), 800, None, None)
    assert recorder.finished.is_set()
    assert not recorder.is_recording
    assert len(recorder.stop()) == 500
    assert recorder.frames == []
    assert len(recorder.stop()) == 0


def test_recorder_silence_times_out_without_transcription_audio():
    recorder = AudioRecorder(sample_rate=1000)
    recorder.is_recording = True
    recorder._callback(samples(0, 10_000), 10_000, None, None)
    assert recorder.finished.is_set()
    assert len(recorder.stop()) == 0


def test_recorder_reports_overflow_instead_of_transcribing_corrupted_audio():
    recorder = AudioRecorder()
    recorder.is_recording = True
    recorder._callback(samples(0.05), 100, None, "input overflow")
    assert recorder.finished.is_set()
    assert recorder.capture_error
    assert not recorder.frames


def test_missing_selected_microphone_does_not_open_default(monkeypatch):
    monkeypatch.setattr("backend.audio_transcriber.input_devices", lambda: [])
    recorder = AudioRecorder(device="disconnected")
    with pytest.raises(RuntimeError, match="mikrofon bulunamadı"):
        recorder.start()
    assert recorder.stream is None


def test_selected_microphone_and_failed_start_release_stream(monkeypatch):
    calls = {}

    class Stream:
        def __init__(self, **kwargs):
            calls.update(kwargs)

        def start(self):
            raise RuntimeError("device unavailable")

        def close(self):
            calls["closed"] = True

    monkeypatch.setattr("backend.audio_transcriber.input_devices", lambda: [{"id": "mic", "index": 7}])
    monkeypatch.setattr("backend.audio_transcriber.sd.InputStream", Stream)
    recorder = AudioRecorder(device="mic")
    with pytest.raises(RuntimeError):
        recorder.start()
    assert calls["device"] == 7
    assert calls["closed"]
    assert recorder.stream is None
    assert not recorder.is_recording


def test_voice_worker_uses_auto_end_and_selected_language():
    app = QApplication.instance() or QApplication([])
    completed = threading.Event()
    completed.set()
    recorder = SimpleNamespace(start=lambda: None, stop=lambda: samples(0.05), finished=completed)
    seen = []

    def transcribe(audio, language):
        seen.append(language)
        return "Hello"

    worker = VoiceRecordWorker(recorder, SimpleNamespace(transcribe=transcribe), language="en")
    text = []
    worker.text_ready.connect(text.append)
    worker.run()
    assert seen == ["en"]
    assert text == ["Hello"]
    app.processEvents()


def test_silent_recording_does_not_load_whisper():
    app = QApplication.instance() or QApplication([])
    completed = threading.Event()
    completed.set()

    def forbidden(*args, **kwargs):
        raise AssertionError("Silence must not reach Whisper")

    recorder = SimpleNamespace(start=lambda: None, stop=lambda: np.array([]), finished=completed)
    worker = VoiceRecordWorker(recorder, SimpleNamespace(transcribe=forbidden))
    text = []
    worker.text_ready.connect(text.append)
    worker.run()
    assert text == [""]
    app.processEvents()


def test_voice_preferences_roundtrip_and_disconnected_selection(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr("frontend.voice_settings.input_devices", lambda: [{"id": "mic1", "name": "Test mic"}])
    preferences = UserPreferences.defaults()
    preferences.voice_output_device = "disconnected"
    panel = VoiceSettings(preferences)
    panel.input.setCurrentIndex(panel.input.findData("mic1"))
    panel.mode.setCurrentIndex(panel.mode.findData("vad"))
    panel.silence.setValue(1.5)
    panel.threshold.setValue(2.0)
    panel.apply(preferences)
    store = SettingsStore(tmp_path / "voice.json")
    store.save(preferences)
    loaded = store.load()
    assert loaded.voice_input_device == "mic1"
    assert loaded.voice_output_device == "disconnected"
    assert loaded.voice_input_mode == "vad"
    assert loaded.voice_silence_seconds == 1.5
    assert loaded.voice_threshold == 0.02
    panel.close()
    app.processEvents()


def test_push_to_talk_handles_press_repeat_release_and_focus_loss(monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    window.voice_input_mode = "push_to_talk"
    calls = []

    def begin():
        calls.append("start")
        window.voice_record_worker = SimpleNamespace(
            stop_recording=lambda: calls.append("stop"), cancel=lambda: calls.append("cancel")
        )

    monkeypatch.setattr(window, "toggle_voice_recording", begin)
    for kind, repeat in ((QEvent.Type.KeyPress, False), (QEvent.Type.KeyPress, True), (QEvent.Type.KeyRelease, False)):
        app.sendEvent(window.input_line, QKeyEvent(kind, Qt.Key.Key_F2, Qt.KeyboardModifier.NoModifier, "", repeat))
    assert calls == ["start", "stop"]
    window.voice_record_worker = None
    app.sendEvent(window.input_line, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_F2, Qt.KeyboardModifier.NoModifier))
    app.sendEvent(window, QEvent(QEvent.Type.WindowDeactivate))
    assert calls[-2:] == ["start", "cancel"]
    assert window.voice_record_worker is None
    assert not window._voice_key_down
    window.close()
    app.processEvents()


def test_disconnected_stream_exits_and_releases_microphone():
    app = QApplication.instance() or QApplication([])
    stopped = []
    recorder = SimpleNamespace(start=lambda: None, stop=lambda: stopped.append(True),
                               stream=SimpleNamespace(active=False))
    worker = VoiceRecordWorker(recorder, object())
    errors = []
    worker.error_received.connect(errors.append)
    worker.run()
    assert stopped
    assert "bağlantısı kesildi" in errors[0]
    app.processEvents()


def test_recording_interrupts_chat_and_speech_without_opening_real_microphone(monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    cancelled = []
    window.worker = SimpleNamespace(cancel=lambda: cancelled.append("chat"))
    window.stream_voice_worker = SimpleNamespace(stop=lambda: cancelled.append("speech"))
    opened = []

    class InputWorker(VoiceRecordWorker):
        def start(self):
            opened.append(self.recorder)

    monkeypatch.setattr("frontend.app.VoiceRecordWorker", InputWorker)
    window.toggle_voice_recording()
    assert cancelled == ["chat", "speech"]
    assert len(opened) == 1
    assert "Mikrofon hazırlanıyor" in window.output_browser.toPlainText()
    assert "Konuşmaya başlayabilirsin" not in window.output_browser.toPlainText()
    current = window.voice_record_worker
    current.recording_started.emit()
    assert "Konuşmaya başlayabilirsin" in window.output_browser.toPlainText()
    assert not window.input_line.isEnabled()
    assert window.worker is None
    window._cancel_voice_input()
    assert window.input_line.isEnabled()
    before = window.output_browser.toPlainText()
    current.recording_started.emit()
    assert window.output_browser.toPlainText() == before  # Late readiness is discarded.
    window.close()
    app.processEvents()


@pytest.mark.parametrize("scenario", ["success", "failure", "cancel", "stopped"])
def test_microphone_ready_only_after_successful_uncancelled_start(scenario):
    finished = threading.Event()
    finished.set()
    events = []

    def start():
        events.append("start")
        if scenario == "failure":
            raise RuntimeError("Device unavailable")
        if scenario == "cancel":
            worker.cancel()

    recorder = SimpleNamespace(start=start, stop=lambda: [], finished=finished)
    worker = VoiceRecordWorker(recorder, object())
    worker.recording_started.connect(lambda: events.append("ready"))
    if scenario == "stopped":
        worker.stop_recording()
    worker.run()
    assert events == (["start", "ready"] if scenario == "success" else ["start"])
