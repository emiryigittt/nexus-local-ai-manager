import threading
from types import SimpleNamespace

import numpy as np
import pytest
from PyQt6.QtWidgets import QApplication

from backend.user_settings import SettingsStore, UserPreferences
from backend.wake_word import LocalWakeDetector, matches_wake_phrase
from frontend.app import SpotlightApp
from frontend.wake_worker import WakeWordWorker


@pytest.mark.parametrize("text", ["Hey Nexus", "Hey, Nexus!", "HEY NEKSUS."])
def test_exact_wake_phrase(text):
    assert matches_wake_phrase(text)


@pytest.mark.parametrize("text", ["Nexus", "hey", "", "Hey Nexus hava nasıl", "say hey nexus", "hey nexuses"])
def test_mentions_and_partial_phrases_do_not_wake(text):
    assert not matches_wake_phrase(text)


def test_detector_is_cached_only_and_does_not_bias_transcription(monkeypatch, tmp_path):
    calls = {}
    for name in ("model.bin", "config.json", "tokenizer.json"):
        (tmp_path / name).touch()

    def cached_model(name, **kwargs):
        assert name == "base"
        assert kwargs == {"local_files_only": True}
        return str(tmp_path)

    monkeypatch.setattr("backend.wake_model.download_model", cached_model)

    def model(*args, **kwargs):
        calls.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr("backend.wake_model.WhisperModel", model)
    detector = LocalWakeDetector()
    detector.prepare()
    assert calls["local_files_only"] is True
    assert calls["device"] == "cpu"
    assert not detector.model.logger.isEnabledFor(50)
    options = {}

    def transcribe(audio, **kwargs):
        options.update(kwargs)
        return iter([SimpleNamespace(text="Hey Nexus", no_speech_prob=0.1, avg_logprob=-0.2)]), None

    detector.model.transcribe = transcribe
    assert detector.detects(np.ones(16000))
    assert options["vad_filter"]
    assert "initial_prompt" not in options
    detector.model.transcribe = lambda *args, **kwargs: (
        iter([SimpleNamespace(text="Hey Nexus", no_speech_prob=0.9, avg_logprob=-0.2)]), None
    )
    assert not detector.detects(np.ones(16000))


def test_incomplete_cache_never_enters_tokenizer_network_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr("backend.wake_model.download_model", lambda *args, **kwargs: str(tmp_path))
    monkeypatch.setattr("backend.wake_model.WhisperModel", lambda *args, **kwargs: pytest.fail("network fallback"))
    with pytest.raises(RuntimeError, match="yerel Whisper"):
        LocalWakeDetector().prepare()


@pytest.mark.parametrize("language", ["tr", "en"])
def test_detector_uses_selected_language_without_relaxing_phrase_matching(language):
    detector = LocalWakeDetector(language=language)
    seen = []

    def transcribe(audio, **options):
        seen.append(options["language"])
        return iter([SimpleNamespace(text="Hey next", no_speech_prob=0.1, avg_logprob=-0.2)]), None

    detector.model = SimpleNamespace(transcribe=transcribe)
    assert not detector.detects(np.ones(16000))
    assert seen == [language]


def fake_recorder():
    ready = threading.Event()
    ready.set()
    audio = np.ones(1600, dtype=np.float32)
    calls = []
    recorder = SimpleNamespace(
        start=lambda: calls.append("start"),
        stop=lambda: calls.append("stop"),
        cancel=lambda: calls.append("cancel"), take=lambda: audio,
        ready=ready, error=False,
    )
    return recorder, audio, calls


def test_worker_keeps_capture_during_inference_but_releases_before_handoff():
    app = QApplication.instance() or QApplication([])
    recorder, audio, calls = fake_recorder()

    def detects(data):
        assert calls == ["start"]
        assert np.any(data)
        return True

    worker = WakeWordWorker(UserPreferences.defaults(), SimpleNamespace(prepare=lambda: None, detects=detects), recorder)
    found = []
    worker.detected.connect(lambda: found.append(calls[-1] == "stop"))
    worker.run()
    assert found == [True]
    assert not np.any(audio)
    app.processEvents()


def test_cancel_during_inference_suppresses_late_detection():
    app = QApplication.instance() or QApplication([])
    recorder, audio, _ = fake_recorder()

    def detects(data):
        worker.cancel()
        return True

    worker = WakeWordWorker(UserPreferences.defaults(), SimpleNamespace(prepare=lambda: None, detects=detects), recorder)
    found = []
    worker.detected.connect(lambda: found.append(True))
    worker.run()
    assert not found
    assert not np.any(audio)
    app.processEvents()


def test_cancel_before_start_never_loads_model_or_opens_microphone():
    app = QApplication.instance() or QApplication([])
    recorder, _, calls = fake_recorder()

    def forbidden():
        pytest.fail("Model must not load after cancellation")

    worker = WakeWordWorker(UserPreferences.defaults(), SimpleNamespace(prepare=forbidden), recorder)
    worker.cancel()
    worker.run()
    assert "start" not in calls
    app.processEvents()


def test_worker_error_never_exposes_ambient_text():
    app = QApplication.instance() or QApplication([])
    recorder, audio, _ = fake_recorder()

    def failure(data):
        raise RuntimeError("PRIVATE AMBIENT PHRASE")

    worker = WakeWordWorker(UserPreferences.defaults(), SimpleNamespace(prepare=lambda: None, detects=failure), recorder)
    errors = []
    worker.failed.connect(errors.append)
    worker.run()
    assert len(errors) == 1
    assert "PRIVATE" not in errors[0]
    assert not np.any(audio)
    app.processEvents()


@pytest.fixture
def wake_window(monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    store = SettingsStore(tmp_path / "wake.json")
    store.update(setup_complete=True)
    monkeypatch.setattr("frontend.app.settings_store", store)
    monkeypatch.setattr("frontend.wake_controller.settings_store", store)
    window = SpotlightApp()
    window.wake.timer.stop()
    # A visible indicator is required. Avoid showing a real window/microphone.
    monkeypatch.setattr(window, "isVisible", lambda: True)
    yield window, store
    window.wake.worker = None
    window.close()
    app.processEvents()


def test_wake_is_off_by_default_and_requires_consent(wake_window, monkeypatch):
    window, store = wake_window

    def forbidden(*args):
        pytest.fail("Must not create a listener without consent")

    monkeypatch.setattr("frontend.wake_controller.WakeWordWorker", forbidden)
    window.wake.tick()
    assert window.wake.worker is None
    window.wake.enabled = True  # Session state cannot override persisted consent.
    window.wake.tick()
    assert window.wake.worker is None
    assert not store.load().wake_word_on_startup


def test_snooze_and_revocation_cancel_listener(wake_window):
    window, store = wake_window
    store.update(wake_word_enabled=True)
    window.wake.enabled = True
    cancelled = []
    worker = SimpleNamespace(cancel=lambda: cancelled.append(True))
    window.wake.worker = worker
    window.wake.snooze()
    assert cancelled
    assert not window.wake.allowed()
    window.wake.snooze_until = 0
    store.update(wake_word_enabled=False)
    window.wake.tick()
    assert len(cancelled) == 2
    assert not window.wake.allowed()


def test_wake_handoff_waits_for_worker_completion(wake_window, monkeypatch):
    window, store = wake_window
    store.update(wake_word_enabled=True)
    window.wake.enabled = True
    worker = SimpleNamespace(isInterruptionRequested=lambda: False, detection_deadline=float("inf"))
    window.wake.worker = worker
    seen = []
    monkeypatch.setattr(window.wake, "show_window", lambda: seen.append("show"))
    monkeypatch.setattr(window, "toggle_voice_recording", lambda **kwargs: seen.append(kwargs))
    window.wake._detected(worker)
    assert not seen
    window.wake._finished(worker)
    assert seen == ["show", {"wake_triggered": True}]
    assert window.wake.worker is None


def test_late_detection_after_revocation_cannot_open_window(wake_window, monkeypatch):
    window, store = wake_window
    store.update(wake_word_enabled=True)
    window.wake.enabled = True
    worker = SimpleNamespace(isInterruptionRequested=lambda: False, detection_deadline=float("inf"))
    window.wake.worker = worker
    window.wake._detected(worker)
    store.update(wake_word_enabled=False)
    monkeypatch.setattr(window.wake, "show_window", lambda: pytest.fail("revoked"))
    window.wake._finished(worker)


def test_manual_microphone_handoff_is_cancelled_when_window_hides(wake_window):
    window, _ = wake_window
    cancelled = []
    worker = SimpleNamespace(cancel=lambda: cancelled.append(True))
    window.wake.worker = worker
    assert window.wake.defer_microphone(lambda: pytest.fail("stale recording"))
    assert cancelled
    window._cancel_voice_input()
    window.wake._finished(worker)
    assert window.wake.pending is None


def test_speech_playback_blocks_wake_listener(wake_window):
    window, store = wake_window
    store.update(wake_word_enabled=True)
    window.wake.enabled = True
    window.current_audio_path = "playing.wav"
    window.wake.tick()
    assert window.wake.worker is None
    assert window.wake.state == "Asistan meşgul"
    window.current_audio_path = None


def test_stopping_worker_during_capture_releases_microphone():
    app = QApplication.instance() or QApplication([])
    started = threading.Event()
    stopped = threading.Event()
    recorder = SimpleNamespace(
        start=started.set,
        stop=stopped.set, cancel=stopped.set,
        ready=started, error=False, take=lambda: (stopped.wait(0.01), None)[1],
    )
    worker = WakeWordWorker(UserPreferences.defaults(), SimpleNamespace(prepare=lambda: None), recorder)
    worker.start()
    assert started.wait(2)
    worker.cancel()
    assert worker.wait(2000)
    assert stopped.is_set()
    app.processEvents()


def test_saved_consent_does_not_imply_startup_listening(wake_window):
    window, store = wake_window
    store.update(wake_word_enabled=True, wake_word_on_startup=False)
    # A newly constructed controller/window must stay paused until a user action.
    second = SpotlightApp()
    second.wake.timer.stop()
    assert not second.wake.enabled
    second.close()


def test_error_disables_automatic_retry(wake_window):
    window, store = wake_window
    store.update(wake_word_enabled=True)
    window.wake.enabled = True
    worker = SimpleNamespace(isInterruptionRequested=lambda: False)
    window.wake.worker = worker
    window.wake._failed(worker, "Unavailable")
    window.wake._finished(worker)
    assert not window.wake.enabled
    assert window.wake.worker is None
    assert window.wake.state == "Unavailable"


@pytest.mark.parametrize("state", ["paused", "snoozed", "failed", "listening"])
def test_saving_settings_preserves_session_listening_choice(wake_window, monkeypatch, state):
    window, store = wake_window
    wake = window.wake
    store.update(wake_word_enabled=True)
    monkeypatch.setattr(wake, "tick", lambda: None)  # No real listener.
    wake.reconfigure()  # Explicit first-time grant.
    assert wake.enabled
    wake.enabled = state in {"snoozed", "listening"}
    wake.snooze_until = 12345 if state == "snoozed" else 0
    wake.error = "Device unavailable" if state == "failed" else ""
    before = (wake.enabled, wake.snooze_until, wake.error)
    store.update(language="en")
    wake.reconfigure()
    assert (wake.enabled, wake.snooze_until, wake.error) == before
    store.update(wake_word_enabled=False)
    wake.reconfigure()
    assert not wake.enabled and not wake.allowed()
    store.update(wake_word_enabled=True)
    wake.reconfigure()
    assert wake.enabled and wake.snooze_until == 0 and not wake.error


def test_stop_invalidates_already_detected_call(wake_window, monkeypatch):
    window, store = wake_window
    store.update(wake_word_enabled=True)
    window.wake.enabled = True
    cancelled = []
    worker = SimpleNamespace(isInterruptionRequested=lambda: False, cancel=lambda: cancelled.append(True),
                             detection_deadline=float("inf"))
    window.wake.worker = worker
    window.wake._detected(worker)
    assert window.wake.detected
    window.wake.stop_worker()
    monkeypatch.setattr(window.wake, "show_window", lambda: pytest.fail("cancelled handoff"))
    window.wake._finished(worker)
    assert cancelled and not window.wake.detected


def test_loss_of_visible_indicator_blocks_handoff(wake_window, monkeypatch):
    window, store = wake_window
    store.update(wake_word_enabled=True)
    window.wake.enabled = True
    worker = SimpleNamespace(isInterruptionRequested=lambda: False, detection_deadline=float("inf"))
    window.wake.worker = worker
    window.wake._detected(worker)
    assert window.wake.detected
    monkeypatch.setattr(window, "isVisible", lambda: False)
    monkeypatch.setattr(window.wake.tray, "isVisible", lambda: False)
    monkeypatch.setattr(window.wake, "show_window", lambda: pytest.fail("no listening indicator"))
    window.wake._finished(worker)


@pytest.mark.parametrize("expire_after_detection", [False, True])
def test_expired_ui_signals_cannot_wake(wake_window, monkeypatch, expire_after_detection):
    window, store = wake_window
    store.update(wake_word_enabled=True)
    window.wake.enabled = True
    worker = SimpleNamespace(isInterruptionRequested=lambda: False,
                             detection_deadline=float("inf") if expire_after_detection else 0.0)
    window.wake.worker = worker
    window.wake._detected(worker)
    assert window.wake.detected == expire_after_detection
    worker.detection_deadline = 0.0
    monkeypatch.setattr(window.wake, "show_window", lambda: pytest.fail("expired signal"))
    window.wake._finished(worker)


def test_modal_dialog_blocks_pending_manual_microphone(wake_window, monkeypatch):
    window, _ = wake_window
    worker = SimpleNamespace(cancel=lambda: None)
    window.wake.worker = worker
    assert window.wake.defer_microphone(lambda: pytest.fail("microphone inside modal dialog"))
    monkeypatch.setattr("frontend.wake_controller.QApplication.activeModalWidget", lambda: object())
    window.wake._finished(worker)


def test_wake_indicator_and_tray_follow_ui_language(wake_window):
    window, store = wake_window
    store.update(wake_word_enabled=True)
    window.wake.enabled = True
    window.apply_ui_language("en")
    window.wake._set_state("Dinliyor · yerel mikrofon açık")
    assert "Listening" in window.wake_button.text()
    assert "microphone on" in window.wake_button.accessibleDescription()
    assert window.wake.snooze_action.text() == "Snooze for 15 minutes"
    window.apply_ui_language("tr")
    assert "Dinliyor" in window.wake_button.text()


def test_slow_inference_never_triggers_an_old_call(monkeypatch):
    recorder, audio, calls = fake_recorder()
    worker = WakeWordWorker(UserPreferences.defaults(),
                            SimpleNamespace(prepare=lambda: None, detects=lambda data: True), recorder)
    times = iter([10.0, 12.01])
    monkeypatch.setattr("frontend.wake_worker.time.monotonic", lambda: next(times))
    takes = []

    def take():
        if not takes:
            takes.append(True)
            return audio
        worker.cancel()
        return None

    recorder.take = take
    found, states = [], []
    worker.detected.connect(lambda: found.append(True))
    worker.state_changed.connect(states.append)
    worker.run()
    assert not found and not np.any(audio)
    assert "stop" in calls
    assert any("eski çağrı" in state for state in states)


@pytest.mark.parametrize("phase, message", [("model", "modeli hazır değil"),
                                           ("capture", "mikrofonu kullanamıyor"),
                                           ("inference", "ses algılaması durdu")])
def test_worker_errors_identify_stage_without_exposing_audio(phase, message):
    recorder, audio, _ = fake_recorder()

    def fail(*args):
        raise RuntimeError("PRIVATE AMBIENT PHRASE")

    detector = SimpleNamespace(prepare=fail if phase == "model" else lambda: None,
                               detects=fail)
    if phase == "capture":
        recorder.start = fail
    worker = WakeWordWorker(UserPreferences.defaults(), detector, recorder)
    errors = []
    worker.failed.connect(errors.append)
    worker.run()
    assert len(errors) == 1 and message in errors[0]
    assert "PRIVATE" not in errors[0]
    if phase == "inference":
        assert not np.any(audio)


def test_capture_release_failure_cannot_start_command_recording():
    recorder, audio, _ = fake_recorder()
    recorder.stop = lambda: setattr(recorder, "error", True)
    worker = WakeWordWorker(UserPreferences.defaults(),
                            SimpleNamespace(prepare=lambda: None, detects=lambda data: True), recorder)
    found, errors = [], []
    worker.detected.connect(lambda: found.append(True))
    worker.failed.connect(errors.append)
    worker.run()
    assert not found and len(errors) == 1
    assert not np.any(audio)


def test_cancellation_during_capture_release_suppresses_detection():
    recorder, audio, _ = fake_recorder()
    worker = WakeWordWorker(UserPreferences.defaults(),
                            SimpleNamespace(prepare=lambda: None, detects=lambda data: True), recorder)
    recorder.stop = worker.cancel
    found = []
    worker.detected.connect(lambda: found.append(True))
    worker.run()
    assert not found and not np.any(audio)


@pytest.mark.parametrize("no_speech, logprob", [(float("nan"), -0.2), (0.1, float("nan")),
                                               (float("inf"), -0.2), (0.1, float("inf")),
                                               (-0.1, -0.2), (0.1, -0.81)])
def test_invalid_or_low_confidence_scores_never_wake(no_speech, logprob):
    detector = LocalWakeDetector()
    detector.model = SimpleNamespace(transcribe=lambda *args, **kwargs: (
        iter([SimpleNamespace(text="Hey Nexus", no_speech_prob=no_speech, avg_logprob=logprob)]), None))
    assert not detector.detects(np.ones(16000))
