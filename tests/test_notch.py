"""Top-edge preview behavior, focus, anchoring and ongoing-work preservation."""

import pytest
from PyQt6.QtCore import QAbstractAnimation, QRect
from PyQt6.QtTest import QTest

from frontend.app import SpotlightApp
from frontend.notch import NotchController


@pytest.fixture
def notch_window(qt_application, monkeypatch):
    window = SpotlightApp()
    window._setup_prompted = True
    window.apply_motion_preference(True)
    monkeypatch.setattr(window.notch_controller, "pointer_inside", lambda: False)
    window.show()
    window.wake.timer.stop()
    qt_application.processEvents()
    yield window
    window.close()
    qt_application.processEvents()


def test_default_notch_is_quiet_and_top_centered(notch_window):
    window = notch_window
    assert window._shell_mode == "notch"
    assert window.geometry() == window.notch_controller.target_rect("notch")
    assert window.width() == 180 and window.height() == 36
    assert window.notch_button.isVisibleTo(window)
    assert window.header.isHidden() and window.composer.isHidden()
    assert window.footer_widget.isHidden() and window.dock_overview.isHidden()
    window.apply_motion_preference(False)
    window.notch_avatar.set_mode("idle")
    assert window.notch_avatar.ambient_animation.state() == QAbstractAnimation.State.Stopped


def test_delayed_hover_opens_without_activation_or_editor_focus(notch_window, monkeypatch):
    window, activations, focus = notch_window, [], []
    controller = window.notch_controller
    monkeypatch.setattr(controller, "pointer_inside", lambda: True)
    monkeypatch.setattr(window, "activateWindow", lambda: activations.append(True))
    monkeypatch.setattr(window.input_line, "setFocus", lambda *args: focus.append(True))
    controller.enter()
    assert window._shell_mode == "notch" and controller.open_timer.isActive()
    QTest.qWait(200)
    assert window._shell_mode == "dock"
    assert not controller.pinned and not window.pin_button.isChecked()
    assert not activations and not focus
    assert window.height() == 188


def test_brief_hover_and_pointer_exit_do_not_open(notch_window, monkeypatch):
    controller = notch_window.notch_controller
    monkeypatch.setattr(controller, "pointer_inside", lambda: True)
    controller.enter()
    controller.leave()
    QTest.qWait(200)
    assert notch_window._shell_mode == "notch" and not controller.open_timer.isActive()
    controller.enter()
    monkeypatch.setattr(controller, "pointer_inside", lambda: False)
    QTest.qWait(200)
    assert notch_window._shell_mode == "notch"


def test_preview_closes_after_leave_and_pin_retains_it(notch_window):
    window, controller = notch_window, notch_window.notch_controller
    window.set_shell_mode("dock", transient=True)
    controller.leave()
    assert window._shell_mode == "dock"
    QTest.qWait(400)
    assert window._shell_mode == "notch"
    window.set_shell_mode("dock", transient=True)
    window.pin_button.click()
    controller.leave()
    QTest.qWait(400)
    assert window._shell_mode == "dock" and controller.pinned
    window.apply_ui_language("en")
    assert window.pin_button.accessibleName() == "Unpin mini panel"
    window.pin_button.click()
    QTest.qWait(400)
    assert window._shell_mode == "notch"


def test_pointer_return_and_modal_dialog_keep_preview(notch_window, monkeypatch):
    window, controller = notch_window, notch_window.notch_controller
    window.set_shell_mode("dock", transient=True)
    controller.leave()
    controller.enter()
    assert not controller.close_timer.isActive()
    monkeypatch.setattr("frontend.notch.QApplication.activeModalWidget", lambda: object())
    controller.leave()
    QTest.qWait(400)
    assert window._shell_mode == "dock" and controller.close_timer.isActive()
    monkeypatch.setattr("frontend.notch.QApplication.activeModalWidget", lambda: None)
    QTest.qWait(400)
    assert window._shell_mode == "notch"


def test_click_opens_chat_and_collapsing_keeps_live_work(notch_window):
    window = notch_window
    window.input_line.setText("Unsent follow-up")
    window.streaming_text = "Partial answer"
    window._response_complete = False
    window._recording_ready = True
    identifier = window.current_conversation_id
    window.notch_button.click()
    assert window._shell_mode == "chat" and window.composer.isVisibleTo(window)
    window.collapse_to_notch()
    assert window._shell_mode == "notch" and window.isVisible()
    assert window._recording_ready and not window._response_complete
    assert window.input_line.text() == "Unsent follow-up"
    assert window.streaming_text == "Partial answer"
    assert window.current_conversation_id == identifier
    window._recording_ready = False
    window.toggle_visibility()
    assert window._shell_mode == "chat"
    window.toggle_visibility()
    assert window._shell_mode == "notch"
    window.escape_action()
    assert window.isVisible()


@pytest.mark.parametrize("available", [QRect(-1920, 40, 1920, 1040), QRect(0, 48, 640, 480)])
@pytest.mark.parametrize("mode", ["notch", "dock", "chat"])
def test_anchor_handles_taskbar_offsets_negative_origins_and_small_screens(available, mode):
    target = NotchController.anchored_rect(available, mode)
    assert available.contains(target)
    assert target.top() == available.top()
    assert abs(target.center().x() - available.center().x()) <= 1


def test_reanchor_settles_transition_and_hide_stops_hover_timers(notch_window, monkeypatch):
    window, controller = notch_window, notch_window.notch_controller
    target = QRect(-1500, 40, 180, 36)
    monkeypatch.setattr(controller, "target_rect", lambda mode: target)
    controller.reanchor()
    assert window.geometry() == target
    controller.enter()
    controller.close_timer.start()
    window.hide()
    assert not controller.open_timer.isActive() and not controller.close_timer.isActive()


def test_collapsed_state_keeps_real_activity_and_badge(notch_window):
    window = notch_window
    window._response_complete = False
    window._refresh_visual_activity()
    assert window.notch_avatar.mode == "thinking"
    assert window.notch_indicator.property("activity") == "thinking"
    window.apply_ui_language("en")
    assert "Nexus thinking" in window.notch_button.accessibleName()
    window.toggle_private_session()
    assert window.mini_badge.text() == window.local_badge.text() == "PRIVATE SESSION"
    assert window.notch_avatar.animation.state() == QAbstractAnimation.State.Stopped
