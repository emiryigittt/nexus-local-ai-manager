import gc
import os
import sys
import weakref
from pathlib import Path

import pytest
from PyQt6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFontDatabase
from PyQt6.QtWidgets import QLabel

from frontend.app import SpotlightApp


@pytest.fixture(scope="module", autouse=True)
def dock_fonts(qt_application):
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for name in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf"):
        if (fonts / name).exists():
            QFontDatabase.addApplicationFont(str(fonts / name))


def test_view_switch_preserves_live_content_and_draft(qt_application):
    window = SpotlightApp()
    try:
        window.input_line.setText("Unsent draft")
        window.active_image_b64 = "synthetic-image"
        window.active_image_name = "sample.png"
        window.streaming_text = "Existing response"
        identifier = window.current_conversation_id
        editor, browser = window.input_line, window.output_browser
        for mode in ("chat", "dock", "notch", "chat"):
            window.set_shell_mode(mode)
            assert window.current_conversation_id == identifier
            assert window.input_line is editor and window.output_browser is browser
            assert window.input_line.text() == "Unsent draft"
            assert window.active_image_b64 == "synthetic-image"
            assert window.streaming_text == "Existing response"
            assert window.home_tab.property("selected") == (mode == "dock")
            assert window.chat_tab.property("selected") == (mode == "chat")
    finally:
        window.close()


@pytest.mark.parametrize("draft", ["", "Keep my question"])
def test_document_drop_adds_local_context_without_sending(tmp_path, monkeypatch, draft):
    document = tmp_path / "brief.txt"
    document.write_text("A local project brief", encoding="utf-8")
    calls = []
    monkeypatch.setattr("frontend.app.request_json", lambda *args: calls.append(args))
    window = SpotlightApp()
    try:
        window.input_line.setText(draft)
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(document))])
        enter = QDragEnterEvent(QPoint(50, 50), Qt.DropAction.CopyAction, mime,
                               Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        window.dragEnterEvent(enter)
        assert enter.isAccepted()
        drop = QDropEvent(QPointF(50, 50), Qt.DropAction.CopyAction, mime,
                          Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        window.dropEvent(drop)
        assert drop.isAccepted()
        assert calls == [("POST", "/api/v1/documents", {
            "name": "brief.txt", "content": "A local project brief", "source_type": "txt"})]
        assert window.knowledge_enabled and window.knowledge_btn.isChecked()
        assert window._shell_mode == "chat" and window.document_hint.isVisibleTo(window)
        assert "brief.txt" in window.document_hint.text()
        assert window.input_line.text() == (draft or "Eklediğim belgedeki önemli noktaları özetle.")
        assert window.worker is None
        window.apply_ui_language("en")
        assert window.document_hint.text() == "Added to local library · brief.txt"
        window.set_shell_mode("dock")
        assert window.document_hint.isHidden()
        window.new_conversation()
        assert window.document_hint.isHidden()
    finally:
        window.close()


def test_corrupt_document_drop_leaves_draft_and_context_unchanged(tmp_path, monkeypatch):
    document = tmp_path / "broken.pdf"
    document.write_bytes(b"not a PDF")
    errors = []
    monkeypatch.setattr("frontend.app.QMessageBox.warning", lambda *args: errors.append(args))
    window = SpotlightApp()
    try:
        window.input_line.setText("Keep this draft")
        assert not window.add_local_document(document)
        assert errors and not window.knowledge_enabled
        assert window.input_line.text() == "Keep this draft"
        assert window._shell_mode == "notch" and window.document_hint.isHidden()
    finally:
        window.close()


def test_closed_panels_release_global_event_filter_without_callback_errors(monkeypatch, qt_application):
    errors, windows = [], []
    monkeypatch.setattr(sys, "excepthook", lambda *args: errors.append(args))
    for _ in range(4):
        window = SpotlightApp()
        window.close()
        windows.append(weakref.ref(window))
        del window
    gc.collect()
    qt_application.processEvents()
    assert not errors
    assert all(reference() is None for reference in windows)


def test_response_expands_dock_without_resetting_draft():
    window = SpotlightApp()
    try:
        assert window._shell_mode == "notch"
        window.input_line.setText("Follow-up draft")
        window._show_output()
        assert window._shell_mode == "chat"
        assert window.output_browser.isVisibleTo(window)
        assert window.input_line.text() == "Follow-up draft"
        window.home_tab.click()
        assert window.dock_overview.isVisibleTo(window)
        window.chat_tab.click()
        assert window.output_browser.isVisibleTo(window)
    finally:
        window.close()


def test_dock_tools_use_real_existing_workflows(monkeypatch):
    calls = []
    for name in ("import_document", "open_memory_manager", "start_research", "toggle_voice_recording"):
        monkeypatch.setattr(SpotlightApp, name, lambda self, *args, name=name: calls.append(name))
    window = SpotlightApp()
    try:
        for button in window.dock_tools:
            button.click()
        assert calls == ["import_document", "open_memory_manager", "start_research", "toggle_voice_recording"]
    finally:
        window.close()


def test_visible_private_control_stays_in_sync_with_menu():
    window = SpotlightApp()
    try:
        window.private_pill.click()
        assert window.private_session and window.private_btn.isChecked()
        assert window.private_pill.isChecked()
        window.private_btn.trigger()
        assert not window.private_session and not window.private_pill.isChecked()
    finally:
        window.close()


@pytest.mark.parametrize("language", ["tr", "en"])
def test_dock_controls_fit_and_labels_translate(language, qt_application):
    window = SpotlightApp()
    window._setup_prompted = True
    window.apply_ui_language(language)
    window.apply_motion_preference(True)
    window.set_shell_mode("dock")
    window.show()
    qt_application.processEvents()
    window.setWindowOpacity(1)
    try:
        assert window.dock_tools[1].text() == ("Memory" if language == "en" else "Hafıza")
        assert window.size().width() == 460 and window.size().height() == 188
        assert window.composer.isHidden() and window.footer_widget.isHidden()
        for control in [*window.dock_tools, window.pin_button, window.mini_badge]:
            assert window.rect().contains(control.mapTo(window, control.rect().bottomRight()))
            assert control.isVisibleTo(window)
        for label in window.dock_overview.findChildren(QLabel):
            if label.objectName() != "dockStatus":
                assert label.fontMetrics().horizontalAdvance(label.text()) <= label.width()
        window._response_complete = False
        window._refresh_visual_activity()
        assert window.dock_avatar.mode == "thinking"
        assert window.dock_title.text() == ("Nexus thinking" if language == "en" else "Nexus düşünüyor")
        window.apply_motion_preference(True)
        assert window.dock_avatar.reduced
    finally:
        window.close()
