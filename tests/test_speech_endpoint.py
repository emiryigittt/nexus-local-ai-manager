from types import SimpleNamespace

import numpy as np

from backend.audio_transcriber import AudioRecorder
from backend.speech_endpoint import SpeechEndpoint
from backend.speech_model import resolve_speech_model
from backend.user_settings import UserPreferences
from frontend.app import SpotlightApp


def test_pauses_resume_but_background_noise_does_not_extend_endpoint(monkeypatch):
    monkeypatch.setattr("backend.speech_endpoint.get_vad_model", lambda: None)
    current = []
    monkeypatch.setattr("backend.speech_endpoint.get_speech_timestamps", lambda *args, **kwargs: current)
    endpoint = SpeechEndpoint(silence_seconds=1.2)
    current.append({"start": 0, "end": 5120})
    assert not endpoint.feed(np.full(5120, .02, dtype=np.float32))
    assert endpoint.heard_speech
    current.clear()
    assert not endpoint.feed(np.full(8000, .01, dtype=np.float32))  # Noise and a 0.5s pause.
    current.append({"start": 13120, "end": 16320})
    assert not endpoint.feed(np.full(3200, .03, dtype=np.float32))  # Continues the sentence.
    current.clear()
    assert not endpoint.feed(np.full(16000, .01, dtype=np.float32))
    assert endpoint.feed(np.full(4000, .01, dtype=np.float32))
    assert endpoint.silence >= 1.2
    endpoint.clear()
    assert not len(endpoint.samples)


def test_device_callback_never_runs_neural_inference(monkeypatch):
    calls = []
    recorder = AudioRecorder()
    recorder.is_recording = True
    recorder.auto_stop = True
    recorder.endpoint = SimpleNamespace(heard_speech=True, feed=lambda audio: calls.append(True) or True,
                                        clear=lambda: None)
    recorder._callback(np.full((480, 1), .01, dtype=np.float32), 480, None, None)
    assert not calls and not recorder.finished.is_set()
    recorder.poll_endpoint()
    assert calls and recorder.finished.is_set()
    recorder.stop()


def test_model_resolution_is_cached_only_and_rejects_missing_tokenizer(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr("backend.speech_model.download_model", lambda size, **kwargs: calls.append(kwargs) or str(tmp_path))
    (tmp_path / "model.bin").touch()
    (tmp_path / "config.json").touch()
    import pytest

    with pytest.raises(RuntimeError, match="Incomplete"):
        resolve_speech_model("small")
    assert calls == [{"local_files_only": True}]


def test_auto_finish_is_default_and_push_to_talk_remains_manual(monkeypatch):
    from frontend.voice_worker import VoiceRecordWorker

    window = SpotlightApp()
    captured = []
    monkeypatch.setattr(VoiceRecordWorker, "start", lambda worker: captured.append(worker.recorder.auto_stop))
    try:
        assert UserPreferences.defaults().voice_auto_finish
        window.toggle_voice_recording()
        assert captured == [True]
        window._cancel_voice_input()
        window.voice_input_mode = "push_to_talk"
        window.toggle_voice_recording()
        assert captured == [True, False]
        window._cancel_voice_input()
    finally:
        window.close()


def test_review_keeps_transcript_editable_without_submitting(monkeypatch):
    from backend.user_settings import settings_store

    previous = settings_store.load()
    window = SpotlightApp()
    sent = []
    monkeypatch.setattr(window, "send_message", lambda: sent.append(True))
    try:
        settings_store.update(voice_review_before_send=True)
        window.on_voice_text_ready("  Yarın görüşelim.  ")
        assert not sent and window.input_line.text() == "Yarın görüşelim."
        assert window.input_line.isEnabled()
        settings_store.update(voice_review_before_send=False)
        window.on_voice_text_ready("Devam edelim.")
        assert sent == [True]
    finally:
        settings_store.save(previous)
        window.close()


def test_cancelled_capture_is_erased_without_transcribing():
    import threading

    from frontend.voice_worker import VoiceRecordWorker

    audio = np.full(1600, .02, dtype=np.float32)
    finished = threading.Event()
    finished.set()
    recorder = SimpleNamespace(start=lambda: worker.cancel(), stop=lambda: audio, finished=finished)
    worker = VoiceRecordWorker(recorder, object())
    worker.run()
    assert not np.any(audio)
