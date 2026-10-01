from pathlib import Path

import pytest
from PyQt6.QtCore import QAbstractAnimation, QMimeData, QPoint, Qt, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtTest import QTest

from frontend.app import SpotlightApp
from frontend.companion import CompanionAvatar
from frontend.micro_motion import MotionButton


@pytest.fixture
def visible_window(qt_application):
    window = SpotlightApp()
    window._setup_prompted = True
    window.apply_motion_preference(False)
    window.show()
    qt_application.processEvents()
    yield window
    window.close()
    qt_application.processEvents()


def running(animation):
    return animation.state() == QAbstractAnimation.State.Running


def test_interrupted_view_transitions_preserve_content_and_finish_in_screen(visible_window):
    window = visible_window
    window.input_line.setText("Keep my unsent draft")
    window.streaming_text = "Keep my partial answer"
    identifier = window.current_conversation_id
    window.set_shell_mode("chat")
    assert running(window.shell_transition.animation)
    window.shell_transition.animation.setCurrentTime(110)
    assert 36 < window.height() < 640
    window.set_shell_mode("dock")
    window.shell_transition.finish()
    assert window.height() == 188
    window.set_shell_mode("chat")
    window.apply_motion_preference(True)
    assert window.height() == 640
    assert not running(window.shell_transition.animation)
    assert window.shell_transition.cover is None
    assert window.current_conversation_id == identifier
    assert window.input_line.text() == "Keep my unsent draft"
    assert window.streaming_text == "Keep my partial answer"
    assert window.screen().availableGeometry().contains(window.geometry())


@pytest.mark.parametrize("mode", ["entrance", "listening", "thinking", "speaking"])
def test_avatar_modes_render_movement_and_reduced_motion_stays_static(mode, qt_application):
    avatar = CompanionAvatar()
    avatar.show()
    try:
        avatar.set_mode(mode)
        avatar.phase = .15
        first = avatar.grab().toImage()
        avatar.phase = .6
        assert avatar.grab().toImage() != first
        avatar.set_reduced_motion(True)
        avatar.phase = .15
        first = avatar.grab().toImage()
        avatar.phase = .6
        assert avatar.grab().toImage() == first
        assert not running(avatar.animation)
        assert not avatar.blink_timer.isActive()
    finally:
        avatar.close()


def test_completed_answer_and_error_have_distinct_finite_reactions(visible_window):
    window = visible_window
    window._show_output()
    window.shell_transition.finish()
    window._response_complete = False
    window._refresh_visual_activity()
    assert window.activity_logo.mode == "thinking"
    assert window.activity_indicator.isVisibleTo(window)
    window.append_response("A synthetic complete answer")
    window.complete_response()
    assert window.activity_logo.reaction == "success"
    assert running(window.activity_logo.reaction_animation)
    assert window.activity_indicator.isHidden()
    window.activity_logo.reaction_animation.setCurrentTime(900)
    assert window.activity_logo.reaction == ""
    window.display_error("Synthetic connection failure")
    assert window.activity_logo.reaction == "error"
    window.activity_logo.reaction_animation.setCurrentTime(600)
    assert window.activity_logo.reaction == ""


def test_speaking_follows_player_state_and_listening_takes_priority(visible_window, monkeypatch):
    window = visible_window
    monkeypatch.setattr(window.media_player, "playbackState", lambda: QMediaPlayer.PlaybackState.PlayingState)
    window._on_playback_state(None)
    assert window.dock_avatar.mode == "speaking"
    window._recording_ready = True
    window._refresh_visual_activity()
    assert window.dock_avatar.mode == "listening"
    window._recording_ready = False
    monkeypatch.setattr(window.media_player, "playbackState", lambda: QMediaPlayer.PlaybackState.StoppedState)
    window._on_playback_state(None)
    assert window.dock_avatar.mode == "idle"


def test_drag_cue_accepts_only_supported_local_files_and_stops_on_leave(visible_window):
    window = visible_window
    for url, accepted in [(QUrl("https://example.test/document.pdf"), False),
                          (QUrl.fromLocalFile(str(Path.cwd() / "unsupported.exe")), False),
                          (QUrl.fromLocalFile(str(Path.cwd() / "example.pdf")), True)]:
        mime = QMimeData()
        mime.setUrls([url])
        event = QDragEnterEvent(QPoint(100, 100), Qt.DropAction.CopyAction, mime,
                               Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        window.dragEnterEvent(event)
        assert event.isAccepted() == accepted
        assert window.drop_target.isVisibleTo(window) == accepted
    assert running(window.drop_target.animation)
    window.dragLeaveEvent(QDragLeaveEvent())
    assert window.drop_target.isHidden()
    assert not running(window.drop_target.animation)


def test_buttons_animate_without_duplicate_keyboard_actions(qt_application):
    calls = []
    button = MotionButton("Action")
    button.clicked.connect(lambda: calls.append(True))
    button.show()
    try:
        QTest.keyClick(button, Qt.Key.Key_Space)
        assert calls == [True]
        assert running(button.ripple_animation)
        button.set_reduced_motion(True)
        assert not running(button.ripple_animation)
        QTest.keyClick(button, Qt.Key.Key_Space)
        assert calls == [True, True]
        assert not running(button.ripple_animation)
    finally:
        button.close()


def test_hide_stops_reactions_blinks_drop_and_transition(visible_window, qt_application):
    window = visible_window
    window.set_shell_mode("dock")
    window.shell_transition.finish()
    window.dock_avatar.set_mode("idle")
    assert window.dock_avatar.blink_timer.isActive()
    window.dock_avatar.react("success")
    window.drop_target.show()
    window.set_shell_mode("chat")
    window.hide()
    assert not running(window.shell_transition.animation)
    assert not running(window.drop_target.animation)
    for avatar in (window.hero_logo, window.activity_logo, window.dock_avatar, window.inline_avatar, window.notch_avatar):
        assert not running(avatar.animation)
        assert not running(avatar.reaction_animation)
        assert not running(avatar.blink_animation)
        assert not running(avatar.ambient_animation)
        assert not avatar.blink_timer.isActive()


def test_reduced_motion_keeps_state_and_turns_off_all_motion(visible_window):
    window = visible_window
    window._response_complete = False
    window._refresh_visual_activity()
    window.drop_target.show()
    window.dock_tools[0]._hover(1)
    window.apply_motion_preference(True)
    assert window.dock_avatar.mode == "thinking"
    assert not running(window.dock_avatar.animation)
    assert not running(window.drop_target.animation)
    assert not running(window.dock_tools[0].hover_animation)
    window.apply_ui_language("en")
    assert window.drop_target.text == "Drop a document or image here"
    window.drop_target.hide()


def test_presence_responds_to_available_space_and_preserves_the_answer(visible_window, qt_application):
    window = visible_window
    window._show_output()
    window.shell_transition.finish()
    window.append_response("A response that must survive layout changes.")
    window.input_line.setText("Keep this draft")
    assert window.presence_panel.isVisibleTo(window)
    assert window.activity_logo.width() == 140
    assert window.inline_avatar.isHidden()
    for width, height in [(640, 560), (800, 640)]:
        window.setFixedSize(width, height)
        qt_application.processEvents()
        wide = width >= 740
        assert window.presence_panel.isVisibleTo(window) == wide
        assert window.inline_avatar.isVisibleTo(window) != wide
        assert window.input_line.text() == "Keep this draft"
        assert window.output_browser.toPlainText() == "A response that must survive layout changes."
        assert window.output_browser.width() >= (480 if wide else 540)
        assert window.rect().contains(window.send_button.mapTo(window, window.send_button.rect().bottomRight()))
    window.show_welcome_state()
    assert window.presence_panel.isHidden()
    assert window.hero_logo.width() == 136


def test_idle_breathing_is_visible_only_and_reduced_motion_is_static(qt_application):
    avatar = CompanionAvatar(140)
    avatar.show()
    try:
        avatar.set_mode("idle")
        assert running(avatar.ambient_animation)
        avatar.ambient_phase = .25
        first = avatar.grab().toImage()
        avatar.ambient_phase = .75
        assert avatar.grab().toImage() != first
        avatar.set_mode("thinking")
        assert not running(avatar.ambient_animation)
        avatar.set_mode("idle")
        avatar.set_reduced_motion(True)
        avatar.ambient_phase = .25
        first = avatar.grab().toImage()
        avatar.ambient_phase = .75
        assert avatar.grab().toImage() == first
        assert not running(avatar.ambient_animation)
        avatar.set_reduced_motion(False)
        assert running(avatar.ambient_animation)
        avatar.hide()
        assert not running(avatar.ambient_animation)
    finally:
        avatar.close()


def test_large_presence_shares_actual_status_and_accessible_language(visible_window):
    window = visible_window
    window._show_output()
    window.shell_transition.finish()
    window._response_complete = False
    window._refresh_visual_activity()
    window.update_status("Synthetic model status")
    assert window.presence_status.full_text == "Synthetic model status"
    assert window.presence_panel.property("activity") == "thinking"
    window.apply_ui_language("en")
    assert window.presence_title.text() == "Nexus thinking"
    assert window.activity_logo.accessibleName() == "Nexus thinking"
    window.apply_motion_preference(True)
    assert not running(window.activity_logo.animation)
    assert not running(window.activity_logo.ambient_animation)
    assert window.presence_panel.isVisibleTo(window)
