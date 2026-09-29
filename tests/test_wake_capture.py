import threading
import time
from types import SimpleNamespace

import numpy as np
from PyQt6.QtWidgets import QApplication

from backend.user_settings import UserPreferences
from backend.wake_capture import WakeBuffer, WakeCapture
from frontend.wake_worker import WakeWordWorker


def feed(buffer, level, seconds):
    clips = []
    for _ in range(round(seconds / 0.01)):
        clip = buffer.feed(np.full(buffer.rate // 100, level, dtype=np.float32))
        if clip is not None:
            clips.append(clip)
    return clips


def test_phrase_crossing_old_four_second_boundary_is_not_split():
    buffer = WakeBuffer(sample_rate=1000)
    assert not feed(buffer, 0, 3.8)
    assert not feed(buffer, 0.1, 1)
    clips = feed(buffer, 0, 0.6)
    assert len(clips) == 1
    assert np.count_nonzero(clips[0]) == 1000
    assert len(clips[0]) <= 1800  # Speech plus pre-roll and trailing silence.
    assert not np.any(buffer.samples)


def test_long_speech_windows_overlap_and_memory_stays_bounded():
    buffer = WakeBuffer(sample_rate=1000)
    clips = []
    source = np.linspace(0.1, 0.2, 8000, dtype=np.float32)
    for offset in range(0, len(source), 10):
        clip = buffer.feed(source[offset:offset + 10])
        if clip is not None:
            clips.append(clip)
    assert len(clips) == 3
    assert all(len(clip) == 4000 for clip in clips)
    np.testing.assert_array_equal(clips[0][-2000:], clips[1][:2000])
    np.testing.assert_array_equal(clips[1][-2000:], clips[2][:2000])
    assert buffer.samples.nbytes == 4000 * 4
    buffer.clear()
    assert not np.any(buffer.samples)


def test_silence_and_separated_clicks_never_queue_inference():
    buffer = WakeBuffer(sample_rate=1000)
    assert not feed(buffer, 0.002, 20)
    for _ in range(10):
        assert not feed(buffer, 0.1, 0.05)
        assert not feed(buffer, 0, 0.6)


def test_backlog_retains_only_latest_clip_and_erases_replaced_audio():
    capture = WakeCapture()
    first = np.ones(100, dtype=np.float32)
    second = np.full(100, 2, dtype=np.float32)
    clips = iter([first, second])
    capture.buffer.feed = lambda data: next(clips)
    for _ in range(2):
        capture._callback(np.ones(10), 10, None, None)
    assert capture.pending.qsize() == 1
    assert not np.any(first)
    assert capture.take() is second
    capture.stop()


def test_old_pending_audio_is_discarded_instead_of_late_wakeup():
    capture = WakeCapture()
    clip = np.ones(100, dtype=np.float32)
    capture.pending.put((time.monotonic() - 3, clip))
    assert capture.take() is None
    assert not np.any(clip)


def test_capture_failure_rejects_bad_audio():
    for audio, status in ((np.ones(10), "overflow"), (np.full(10, np.nan), None)):
        capture = WakeCapture()
        capture._callback(audio, 10, None, status)
        assert capture.error
        assert capture.cancelled.is_set()
        assert capture.pending.empty()


def mock_stream(monkeypatch):
    calls = []

    class Stream:
        active = True

        def __init__(self, **kwargs):
            calls.append(("open", kwargs))

        def start(self):
            calls.append(("start", None))

        def abort(self):
            calls.append(("abort", None))

        def close(self):
            calls.append(("close", None))

    monkeypatch.setattr("backend.wake_capture.sd.InputStream", Stream)
    return calls


def test_capture_opens_device_once_and_closes_on_cancel(monkeypatch):
    calls = mock_stream(monkeypatch)
    monkeypatch.setattr("backend.wake_capture.input_devices", lambda: [{"id": "mic", "index": 9}])
    capture = WakeCapture(device="mic")
    capture.start()
    assert capture.ready.wait(2)
    capture.cancel()
    assert capture.closed.wait(2)
    capture.stop()
    assert [kind for kind, _ in calls] == ["open", "start", "abort", "close"]
    assert calls[0][1]["device"] == 9
    assert not np.any(capture.buffer.samples)


def test_missing_selected_device_never_opens_default(monkeypatch):
    calls = mock_stream(monkeypatch)
    monkeypatch.setattr("backend.wake_capture.input_devices", lambda: [])
    capture = WakeCapture(device="missing")
    capture.start()
    assert capture.closed.wait(2)
    capture.stop()
    assert capture.error
    assert not calls


def test_failed_stream_start_still_closes_and_clears_capture(monkeypatch):
    closed = []

    class Stream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            raise RuntimeError("Unavailable")

        def abort(self):
            pass

        def close(self):
            closed.append(True)

    monkeypatch.setattr("backend.wake_capture.sd.InputStream", Stream)
    capture = WakeCapture()
    capture.start()
    assert capture.closed.wait(2)
    capture.stop()
    assert capture.error and closed
    assert capture.pending.empty()


def test_cancel_closes_microphone_while_inference_is_still_running(monkeypatch):
    app = QApplication.instance() or QApplication([])
    calls = mock_stream(monkeypatch)
    capture = WakeCapture()
    inference = threading.Event()
    finish_inference = threading.Event()

    def detects(audio):
        inference.set()
        assert finish_inference.wait(3)
        return True

    worker = WakeWordWorker(UserPreferences.defaults(), SimpleNamespace(prepare=lambda: None, detects=detects), capture)
    detections = []
    worker.detected.connect(lambda: detections.append(True))
    try:
        worker.start()
        assert capture.ready.wait(2)
        clip = np.ones(16000, dtype=np.float32)
        capture.pending.put((time.monotonic(), clip))
        assert inference.wait(2)
        # Capture still accepts a new phrase while the old one is being decoded.
        pending = np.ones(16000, dtype=np.float32)
        capture.pending.put((time.monotonic(), pending))
        worker.cancel()
        assert capture.closed.wait(1)
        assert worker.isRunning()
        assert calls[-1][0] == "close"
        assert not np.any(pending)
    finally:
        finish_inference.set()
        worker.cancel()
        assert worker.wait(3000)
    app.processEvents()
    assert not detections
    assert not np.any(clip)
