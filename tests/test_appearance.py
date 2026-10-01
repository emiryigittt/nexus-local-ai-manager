import wave
from pathlib import Path

from PyQt6.QtCore import QAbstractAnimation

from backend.memory import MemoryRepository
from backend.memory_jobs import MemoryJobStatus
from backend.user_settings import SettingsStore, UserPreferences
from frontend.app import SpotlightApp
from frontend.appearance import readable_accent, valid_color
from frontend.memory_dialog import MemoryDialog
from frontend.setup_dialog import SetupDialog
from frontend.sound_feedback import SoundFeedback
from scripts.check_public_repo import path_problem


def test_customization_save_and_cancel_keep_other_settings(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    store.update(setup_complete=True)
    before = store.path.read_bytes()
    dialog = SetupDialog(store)
    dialog.appearance.set_color("#ff0088")
    dialog.appearance.character.setCurrentIndex(1)
    dialog.appearance.rgb.setChecked(True)
    dialog.appearance.sounds.setChecked(True)
    dialog.appearance.volume.setValue(32)
    dialog.reject()
    assert store.path.read_bytes() == before
    dialog = SetupDialog(store)
    try:
        dialog.appearance.set_color("#ff0088")
        dialog.appearance.character.setCurrentIndex(1)
        dialog.appearance.rgb.setChecked(True)
        dialog.appearance.sounds.setChecked(True)
        dialog.appearance.volume.setValue(32)
        dialog.save()
        saved = store.load()
        assert saved.accent_color == "#ff0088" and saved.companion_style == "cat"
        assert saved.rgb_enabled and saved.ui_sounds_enabled and saved.ui_sound_volume == 32
        assert not saved.web_consent and not saved.cloud_speech_consent and not saved.memory_auto_learn
    finally:
        dialog.close()


def test_legacy_preferences_gain_quiet_defaults_and_invalid_color_falls_back():
    preferences = UserPreferences.from_dict({"setup_complete": True})
    assert preferences.accent_color == "#55ef9d" and not preferences.ui_sounds_enabled
    assert preferences.companion_style == "robot" and not preferences.rgb_enabled
    assert valid_color("invalid") == "#55ef9d"
    assert min(readable_accent("#000000").getRgb()[:3]) >= 140


def test_rgb_and_character_apply_without_resetting_chat_and_stop_hidden(qt_application):
    window = SpotlightApp()
    window._setup_prompted = True
    preferences = UserPreferences.defaults()
    preferences.accent_color, preferences.companion_style = "#ba9fff", "cat"
    preferences.rgb_enabled = True
    try:
        window.input_line.setText("Keep my draft")
        window.streaming_text = "Keep my answer"
        identifier = window.current_conversation_id
        window.apply_motion_preference(False)
        window.apply_appearance(preferences)
        window.show()
        qt_application.processEvents()
        assert window.accent_edge.timer.isActive()
        for avatar in (window.hero_logo, window.activity_logo, window.dock_avatar, window.inline_avatar, window.notch_avatar):
            assert avatar.character == "cat" and avatar.accent.name() == "#ba9fff"
        assert window.input_line.text() == "Keep my draft" and window.streaming_text == "Keep my answer"
        assert window.current_conversation_id == identifier
        window.apply_motion_preference(True)
        assert not window.accent_edge.timer.isActive()
        assert window.notch_avatar.animation.state() == QAbstractAnimation.State.Stopped
        window.apply_motion_preference(False)
        window.hide()
        assert not window.accent_edge.timer.isActive()
    finally:
        window.close()


def test_sound_toggle_volume_and_no_hover_sound(qt_application, monkeypatch):
    class FakeEffect:
        def __init__(self, parent):
            self.played, self.stopped = False, False

        def setSource(self, value):
            self.source = value

        def setLoopCount(self, value):
            pass

        def setVolume(self, value):
            self.volume = value

        def play(self):
            self.played = True

        def stop(self):
            self.stopped = True

    monkeypatch.setattr("frontend.sound_feedback.QSoundEffect", FakeEffect)
    sound = SoundFeedback()
    assert not sound.play("open") and not sound.effects
    sound.configure(True, 24)
    assert sound.play("open")
    assert sound.effects["open"].played and sound.effects["open"].volume == .24
    sound.configure(False, 24)
    assert sound.effects["open"].stopped and not sound.play("success")
    sound.configure(True, 0)
    assert not sound.play("success")
    window = SpotlightApp()
    window._setup_prompted = True
    calls = []
    monkeypatch.setattr(window.sound_feedback, "play", lambda *args: calls.append(args))
    monkeypatch.setattr(window.notch_controller, "pointer_inside", lambda: True)
    window.show()
    try:
        window.notch_controller._open_preview()
        assert window._shell_mode == "dock" and not calls
        window.open_full_chat()
        assert calls == [("open",)]
    finally:
        window.close()


def test_original_chimes_are_short_and_only_named_assets_are_publishable():
    for name in SoundFeedback.NAMES:
        relative = Path("frontend/assets/sounds") / f"{name}.wav"
        assert path_problem(relative) is None
        with wave.open(str(relative)) as sound:
            assert sound.getnchannels() == 1 and sound.getsampwidth() == 2
            assert 0 < sound.getnframes() / sound.getframerate() <= .3
    assert path_problem(Path("frontend/assets/sounds/private-recording.wav"))


def test_memory_cards_filters_clear_stale_editor_and_summary_save(tmp_path):
    repository = MemoryRepository(tmp_path / "memory.db")
    repository.add("Use concise answers", "preference")
    dialog = MemoryDialog(repository)
    try:
        assert dialog.content.toPlainText() == "Use concise answers"
        assert dialog.save_button.isEnabled() and not dialog.activate_button.isEnabled()
        dialog.search.setText("does not exist")
        assert not dialog.list.count() and not dialog.content.toPlainText()
        assert not dialog.editor.isEnabled() and not dialog.delete_button.isEnabled()
        assert not dialog.save_button.isEnabled() and not dialog.empty_state.isHidden()
        dialog.summary.setPlainText("Likes practical explanations")
        dialog.save_summary()
        assert repository.profile_summary() == "Likes practical explanations"
        dialog.search.clear()
        dialog.content.setPlainText("Use brief, actionable answers")
        dialog.save_selected()
        assert repository.list()[0]["content"] == "Use brief, actionable answers"
    finally:
        dialog.close()


def test_memory_operations_release_database_handles(tmp_path):
    path = tmp_path / "memory.db"
    repository = MemoryRepository(path)
    repository.add("One memory", "fact")
    jobs = MemoryJobStatus(path)
    identifier = jobs.start()
    jobs.finish(identifier, "completed", 1)
    assert jobs.latest()["count"] == 1
    assert repository.list()[0]["content"] == "One memory"
    path.rename(tmp_path / "moved.db")
