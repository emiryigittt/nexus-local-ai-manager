import json
from string import Formatter
from weakref import ref

import httpx
import pytest
from PyQt6 import sip
from PyQt6.QtWidgets import QApplication, QDialogButtonBox, QLabel

from backend.user_settings import SettingsStore
from frontend.app import ChatWorker, SpotlightApp
from frontend.i18n import ENGLISH, UiText
from frontend.setup_dialog import SetupDialog


@pytest.fixture
def language_store(monkeypatch, tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    store.update(language="en", setup_complete=True)
    monkeypatch.setattr("frontend.app.settings_store", store)
    monkeypatch.setattr("frontend.spotlight_view.settings_store", store)
    return store


def test_catalog_preserves_format_fields_and_has_safe_fallback():
    def fields(value):
        return {name for _, name, _, _ in Formatter().parse(value) if name is not None}

    for source, translated in ENGLISH.items():
        assert translated.strip()
        assert fields(source) == fields(translated), source
    assert UiText("unknown")("Araçlar") == "Araçlar"
    assert UiText("en")("untranslated-id") == "untranslated-id"
    assert UiText("en")("{count} çalışan yerel sağlayıcı bulundu.", count=2) == "Found 2 running local providers."


def test_language_bindings_do_not_retain_or_update_deleted_widgets(qt_application):
    ui = UiText("tr")
    widget = QLabel()
    ui.bind(widget, "setText", "Araçlar")
    tracked = ref(widget)
    del widget
    assert tracked() is None
    deleted = QLabel()
    ui.bind(deleted, "setText", "Araçlar")
    sip.delete(deleted)
    survivor = QLabel()
    ui.bind(survivor, "setText", "Araçlar")
    ui.set_language("en")
    assert survivor.text() == "Tools"
    assert len(ui._bindings) == 1


def test_english_main_window_controls_and_accessible_names(language_store):
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    try:
        assert window.input_line.placeholderText() == "Ask Nexus anything…"
        assert window.input_line.accessibleName() == "Nexus message field"
        assert window.send_button.accessibleName() == "Send message · Enter"
        assert window.private_btn.text() == "Private session"
        assert window.knowledge_btn.text() == "Answer from my documents"
        assert window.speaker_btn.text() == "Read responses aloud"
        assert window.findChild(QLabel, "welcomeTitle").text() == "What's on your mind?"
        assert window.context_button.text() == "Add from clipboard  ·  Permission required"
    finally:
        window.close()
        app.processEvents()


def test_language_switch_keeps_conversation_draft_attachment_and_modes(language_store):
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()
    try:
        identifier = window.current_conversation_id
        window.private_session = True
        window.private_btn.setChecked(True)
        window.toggle_knowledge()
        window._private_history = [{"role": "user", "content": "unchanged"}]
        window._show_output()
        window.append_response("**Yanıt stays exactly as written.**")
        window.input_line.setText("Unsent Türkçe draft")
        window.active_image_b64 = "synthetic-image"
        window.active_image_name = "example.png"
        editor, browser = window.input_line, window.output_browser
        for language, badge in (("tr", "ÖZEL OTURUM"), ("en", "PRIVATE SESSION")):
            window.apply_ui_language(language)
            assert window.local_badge.text() == badge
            assert window.current_conversation_id == identifier
            assert window.input_line is editor and window.output_browser is browser
            assert window.input_line.text() == "Unsent Türkçe draft"
            assert window.streaming_text == "**Yanıt stays exactly as written.**"
            assert window.active_image_b64 == "synthetic-image"
            assert "example.png" in window.input_line.placeholderText()
            assert window._private_history == [{"role": "user", "content": "unchanged"}]
            assert window.private_btn.isChecked() and window.knowledge_btn.isChecked()
        assert not language_store.load().cloud_speech_consent
        assert window.input_line.placeholderText() == "What would you like to know about example.png?"
        window.new_conversation()
        assert window.input_line.placeholderText() == "Ask Nexus anything…"
    finally:
        window.close()
        app.processEvents()


def test_saved_settings_language_applies_without_window_rebuild(language_store, monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()

    class ChooseTurkish(SetupDialog):
        def exec(self):
            self.language.setCurrentIndex(self.language.findData("tr"))
            self.save()
            return self.result()

    monkeypatch.setattr("frontend.app.SetupDialog", lambda parent: ChooseTurkish(language_store, parent))
    try:
        editor = window.input_line
        window.input_line.setText("Keep my draft")
        window.open_settings()
        assert window.input_line is editor
        assert window.input_line.text() == "Keep my draft"
        assert window.input_line.placeholderText() == "Nexus'a bir şey sor…"
        assert language_store.load().language == "tr"
        reopened = SpotlightApp()
        assert reopened.private_btn.text() == "Özel oturum"
        reopened.close()
    finally:
        window.close()
        app.processEvents()


def test_english_settings_cancel_keeps_language_and_permissions(language_store):
    app = QApplication.instance() or QApplication([])
    before = language_store.path.read_bytes()
    dialog = SetupDialog(language_store)
    assert [dialog.tabs.tabText(i) for i in range(3)] == ["General", "Privacy", "Voice"]
    assert dialog.cloud_speech.text() == "Allow cloud speech when needed"
    assert dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Save).text() == "Save"
    dialog.language.setCurrentIndex(dialog.language.findData("tr"))
    dialog.cloud_speech.setChecked(True)
    dialog.reject()
    assert language_store.path.read_bytes() == before
    app.processEvents()


async def test_worker_translates_status_not_user_text(monkeypatch):
    app = QApplication.instance() or QApplication([])
    captured = []
    client_type = httpx.AsyncClient

    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, text='{"event":"chunk","text":"Aynı yanıt"}\n{"event":"done"}\n')

    monkeypatch.setattr("frontend.app.httpx.AsyncClient", lambda **kwargs: client_type(
        transport=httpx.MockTransport(handler), **kwargs))
    worker = ChatWorker("Aynı soru", language="en")
    statuses, chunks = [], []
    worker.status_changed.connect(statuses.append)
    worker.response_chunk.connect(chunks.append)
    await worker._stream()
    app.processEvents()
    assert statuses == ["The local model is thinking…"]
    assert chunks == ["Aynı yanıt"]
    assert captured[0]["text"] == "Aynı soru"
    assert captured[0]["private"] is False
