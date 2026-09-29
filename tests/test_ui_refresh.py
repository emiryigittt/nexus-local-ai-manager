from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDialogButtonBox, QMenu

from backend.user_settings import SettingsStore
from frontend.app import SpotlightApp
from frontend.setup_dialog import SetupDialog


def test_tools_menu_preserves_privacy_and_knowledge_toggles():
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    assert isinstance(window.private_btn.parent(), QMenu)
    window.private_btn.trigger()
    assert window.private_session and window.private_btn.isChecked()
    window.knowledge_btn.trigger()
    assert window.knowledge_enabled and window.knowledge_btn.isChecked()
    window.close()
    app.processEvents()


def test_send_button_and_keyboard_focus_are_available(monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    window._setup_prompted = True
    window.show()
    app.processEvents()
    assert not window.send_button.isEnabled()
    window.input_line.setText("Bir fikrim var")
    assert window.send_button.isEnabled()
    window.input_line.setFocus()
    QTest.keyClick(window.input_line, Qt.Key.Key_Tab)
    assert app.focusWidget() is window.send_button
    # Clicking/Enter share the same existing request path, without a live provider.
    sent = []
    monkeypatch.setattr(window, "trigger_analysis", lambda *args, **kwargs: sent.append(args[0]))
    window.send_button.click()
    assert sent == ["Bir fikrim var"]
    window.input_line.setEnabled(False)
    assert not window.send_button.isEnabled()
    window.close()
    app.processEvents()


def test_response_copy_and_paragraph_spacing():
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    window._show_output()
    window._render_markdown("## Başlık\n\nBirinci paragraf.\n\nİkinci paragraf.")
    assert window.response_bar.isVisibleTo(window)
    assert window.output_browser.document().begin().blockFormat().lineHeight() == 140
    previous = QApplication.clipboard().text()
    try:
        window.copy_response()
        assert "İkinci paragraf." in QApplication.clipboard().text()
    finally:
        QApplication.clipboard().setText(previous)
    window.show_welcome_state()
    assert not window.response_bar.isVisibleTo(window)
    window.close()
    app.processEvents()


def test_settings_are_sectioned_and_choices_persist(tmp_path):
    app = QApplication.instance() or QApplication([])
    store = SettingsStore(tmp_path / "settings.json")
    dialog = SetupDialog(store=store)
    assert [dialog.tabs.tabText(i) for i in range(dialog.tabs.count())] == ["Genel", "Gizlilik", "Ses"]
    dialog.cloud_speech.setChecked(True)
    dialog.voice.mode.setCurrentIndex(dialog.voice.mode.findData("push_to_talk"))
    dialog.save()
    assert store.load().cloud_speech_consent
    assert store.load().voice_input_mode == "push_to_talk"
    buttons = dialog.findChild(QDialogButtonBox)
    assert buttons.button(QDialogButtonBox.StandardButton.Save).text() == "Kaydet"
    dialog.close()
    app.processEvents()


def test_long_status_cannot_expand_the_window():
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    window._setup_prompted = True
    window.show()
    app.processEvents()
    width = window.width()
    window.model_status.setText("çok uzun sağlayıcı adı " * 100)
    app.processEvents()
    assert window.width() == width
    assert len(window.model_status.text()) < len(window.model_status.full_text)
    assert window.send_button.mapTo(window, window.send_button.rect().topRight()).x() < width
    assert not window.wake_button.isVisibleTo(window)
    window.close()
    app.processEvents()
