import os
from pathlib import Path

import pytest
from PyQt6.QtCore import QCoreApplication, QEvent, Qt
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QLabel

from backend.user_settings import SettingsStore
from frontend.app import SpotlightApp
from frontend.design import ActionCard, ComposerFrame
from frontend.setup_dialog import SetupDialog


@pytest.fixture(scope="module", autouse=True)
def preview_fonts(qt_application):
    # Same local font loading as preview_ui: Windows offscreen may miss Segoe UI.
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for name in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf"):
        if (fonts / name).exists():
            QFontDatabase.addApplicationFont(str(fonts / name))


def dispose(widget):
    widget.close()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_action_cards_are_keyboard_buttons_and_retranslate(monkeypatch, qt_application):
    seen = []
    for name in ("analyze_clipboard", "start_research", "toggle_voice_recording"):
        monkeypatch.setattr(SpotlightApp, name, lambda self, checked=False, name=name: seen.append(name))
    window = SpotlightApp()
    window._setup_prompted = True
    window.show()
    qt_application.processEvents()
    try:
        cards = window.findChildren(ActionCard)
        assert len(cards) == 3
        for card in cards:
            assert card.accessibleName() and card.accessibleDescription()
            card.setFocus()
            QTest.keyClick(card, Qt.Key.Key_Space)
        assert seen == ["analyze_clipboard", "start_research", "toggle_voice_recording"]
        window.apply_ui_language("en")
        assert cards[0].accessibleName() == "Explore clipboard"
        assert "Work with" in cards[0].accessibleDescription()
    finally:
        dispose(window)


def test_composer_focus_ring_follows_keyboard_focus(qt_application):
    window = SpotlightApp()
    window._setup_prompted = True
    window.show()
    qt_application.processEvents()
    try:
        window.input_line.setText("Draft")
        window.input_line.setFocus()
        qt_application.processEvents()
        composer = window.findChild(ComposerFrame)
        assert composer.property("focused") is True
        QTest.keyClick(window.input_line, Qt.Key.Key_Tab)
        assert qt_application.focusWidget() is window.send_button
        assert composer.property("focused") is False
        assert window.input_line.text() == "Draft"
    finally:
        dispose(window)


@pytest.mark.parametrize("language", ["tr", "en"])
def test_compact_main_window_keeps_cards_and_controls_inside(language, qt_application):
    window = SpotlightApp()
    window._setup_prompted = True
    window.apply_ui_language(language)
    window.setFixedSize(640, 560)
    window.show()
    qt_application.processEvents()
    try:
        for widget in [*window.findChildren(ActionCard), window.send_button, window.mic_btn, window.local_badge]:
            assert window.rect().contains(widget.mapTo(window, widget.rect().topLeft()))
            assert window.rect().contains(widget.mapTo(window, widget.rect().bottomRight()))
        for card in window.findChildren(ActionCard):
            assert window.welcome.rect().contains(card.mapTo(window.welcome, card.rect().bottomRight()))
            for label in card.findChildren(QLabel):
                assert label.fontMetrics().horizontalAdvance(label.text()) <= label.width()
        assert window.findChild(QLabel, "welcomeTitle").geometry().bottom() < window.welcome.height()
    finally:
        dispose(window)


@pytest.mark.parametrize("language", ["tr", "en"])
def test_voice_sections_preserve_unsaved_choices_and_consent(language, tmp_path, qt_application):
    store = SettingsStore(tmp_path / "settings.json")
    store.update(language=language)
    before = store.path.read_bytes()
    dialog = SetupDialog(store)
    dialog.resize(560, 600)
    dialog.tabs.setCurrentIndex(2)
    dialog.show()
    qt_application.processEvents()
    try:
        voice = dialog.voice
        assert voice.sections.count() == 3
        assert voice.sections.tabText(1) == "Hey Nexus"
        assert voice.sections.tabText(0) == ("Input" if language == "en" else "Giriş")
        voice.mode.setCurrentIndex(voice.mode.findData("push_to_talk"))
        voice.sections.setCurrentIndex(1)
        voice.wake.setChecked(True)
        voice.sections.setCurrentIndex(2)
        voice.speed.setValue(1.15)
        voice.sections.setCurrentIndex(0)
        assert voice.mode.currentData() == "push_to_talk"
        assert voice.wake.isChecked()
        assert voice.speed.value() == 1.15
        assert not voice.wake_setup.busy
        assert not store.load().wake_word_enabled
        dialog.reject()
        assert store.path.read_bytes() == before
    finally:
        dispose(dialog)
