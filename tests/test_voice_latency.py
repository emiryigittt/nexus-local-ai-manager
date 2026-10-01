import asyncio
import time
from types import SimpleNamespace

import numpy as np
import pytest

from backend import main
from backend.memory import MemoryRepository
from backend.memory_retrieval import retrieve_memories
from backend.user_settings import SettingsStore, UserPreferences
from backend.wake_capture import WakeBuffer
from frontend.app import SpotlightApp
from frontend.speech_follow import word_at
from frontend.wake_setup import WakeSetupPanel


def test_cloud_word_boundaries_follow_actual_playback_and_pauses():
    timings = [(100, 400, "Hello"), (700, 1200, "Nexus")]
    assert word_at("Hello Nexus", 250, 1500, timings) == 0
    assert word_at("Hello Nexus", 600, 1500, timings) == 0
    assert word_at("Hello Nexus", 800, 1500, timings) == 1
    assert word_at("Hello Nexus", 0, 0, timings) == -1


def test_local_word_follow_is_bounded_and_moves_with_player():
    assert word_at("Merhaba Nexus", 0, 1000) == 0
    assert word_at("Merhaba Nexus", 999, 1000) == 1
    assert word_at("Merhaba Nexus", 10000, 1000) == 1


def test_stream_render_coalesces_tokens_without_losing_text(monkeypatch):
    window = SpotlightApp()
    calls = []
    monkeypatch.setattr(window, "_render_markdown", lambda text: calls.append(text))
    try:
        for _ in range(200):
            window.append_response("x")
        assert calls == ["x"]
        window.complete_response()
        assert calls[-1] == "x" * 200 and len(calls) == 2
        assert not window.render_timer.isActive()
    finally:
        window.close()


def test_speech_highlights_repeated_words_in_order_and_clears_on_stop(monkeypatch):
    window = SpotlightApp()
    monkeypatch.setattr(window.media_player, "duration", lambda: 1000)
    try:
        window._render_markdown("😀 **Nexus** merhaba. Nexus tekrar.")
        window.speech_follow.start("Nexus merhaba.")
        window.speech_follow.update(0)
        selected = window.output_browser.extraSelections()[0]
        assert selected.cursor.selectedText() == "Nexus"
        first_position = selected.cursor.position()
        window.speech_follow.finish()
        window.speech_follow.start("Nexus tekrar.")
        window.speech_follow.update(0)
        assert window.output_browser.extraSelections()[0].cursor.position() > first_position
        window._stop_speech()
        assert not window.output_browser.extraSelections()
        assert not window.speech_follow.text and not window.speech_follow.offset
    finally:
        window.close()


@pytest.mark.asyncio
async def test_slow_embedding_falls_back_with_bounded_first_token_delay(tmp_path, monkeypatch):
    repository = MemoryRepository(tmp_path / "memory.db")
    repository.add("Python kullanır", "fact")
    cancelled = []

    async def slow(texts):
        try:
            await asyncio.sleep(20)
        finally:
            cancelled.append(True)

    monkeypatch.setattr("backend.memory_retrieval.embed_texts", slow)
    started = time.monotonic()
    selected = await retrieve_memories("Python", None, repository=repository)
    assert time.monotonic() - started < 1.2
    assert selected[0]["content"] == "Python kullanır" and cancelled


@pytest.mark.asyncio
async def test_new_answer_cancels_optional_model_work():
    cancelled = []

    async def background():
        try:
            await asyncio.sleep(20)
        finally:
            cancelled.append(True)

    task = asyncio.create_task(background())
    main._memory_tasks.add(task)
    await asyncio.sleep(0)
    try:
        started = time.monotonic()
        await main._prioritize_interactive_request()
        assert time.monotonic() - started < .5
        assert task.cancelled() and cancelled
    finally:
        main._memory_tasks.discard(task)


def test_microphone_test_requires_click_and_reports_threshold_without_transcript(tmp_path, monkeypatch):
    store = SettingsStore(tmp_path / "settings.json")
    monkeypatch.setattr("frontend.wake_setup.settings_store", store)
    panel = WakeSetupPanel()
    assert panel.test_worker is None and not panel.busy
    cleanup = []
    panel.test_threshold = .012
    panel.test_worker = SimpleNamespace(capture=SimpleNamespace(peak_level=.002), deleteLater=lambda: cleanup.append(True))
    panel.test_finished()
    assert "Ses eşiğine" in panel.status.text()
    assert cleanup and not panel.test_worker
    assert not store.load().wake_word_enabled  # A short test never grants ambient listening.
    panel.close()


def test_short_quiet_call_passes_separate_wake_gate():
    default = UserPreferences.defaults()
    wake = WakeBuffer(threshold=default.wake_word_threshold)
    ordinary = WakeBuffer(threshold=default.voice_threshold)
    clips = [[], []]
    # Fixed synthetic samples below the ordinary input gate; no device is used.
    for buffer, results in zip((wake, ordinary), clips, strict=True):
        for _ in range(20):
            clip = buffer.feed(np.full(480, .006, dtype=np.float32))
            if clip is not None:
                results.append(clip)
        for _ in range(20):
            clip = buffer.feed(np.zeros(480, dtype=np.float32))
            if clip is not None:
                results.append(clip)
        buffer.clear()
    assert len(clips[0]) == 1 and not clips[1]


def test_diagnostic_waits_for_ambient_release_and_is_tracked_for_quit(monkeypatch):
    window = SpotlightApp()
    window.wake.timer.stop()
    panel = WakeSetupPanel(parent=window)
    starts = []
    monkeypatch.setattr("frontend.wake_setup.WakeWordWorker.start", lambda worker: starts.append(worker))
    monkeypatch.setattr(window.wake, "stop_worker", lambda: None)
    window.wake.worker = object()  # Still awaiting release of the shared device.
    try:
        panel.start_microphone_test()
        worker = panel.test_worker
        assert worker in window._workers and not starts
        assert panel.test_start_timer.isActive()
        window.wake.worker = None
        panel.start_test_worker()
        assert starts == [worker]
        assert worker.detector is window.wake.detector
        worker.cancel()
        worker.finished.emit()
        assert panel.test_worker is None and worker not in window._workers
    finally:
        window.wake.worker = None
        panel.close()
        window.close()
