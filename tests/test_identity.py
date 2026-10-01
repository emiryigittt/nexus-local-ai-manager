import json

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog

from backend import main
from backend.conversations import ConversationRepository
from backend.identity import CORE_IDENTITY, preferred_name, profile_memories
from backend.memory import MemoryRepository
from backend.user_settings import SettingsStore, UserPreferences
from frontend.introduction import IntroductionDialog


@pytest.fixture
def identity_environment(tmp_path, monkeypatch):
    store = SettingsStore(tmp_path / "settings.json")
    preferences = UserPreferences.defaults()
    preferences.providers[0].selected_model = "identity-test-model"
    store.save(preferences)
    repository = MemoryRepository(tmp_path / "memory.db")
    conversations = ConversationRepository(tmp_path / "conversations.db")
    monkeypatch.setattr(main, "settings_store", store)
    monkeypatch.setattr(main, "memory_repository", repository)
    monkeypatch.setattr(main, "conversation_repository", conversations)

    async def retrieve(*args, **kwargs):
        return repository.for_context()

    async def research(*args, **kwargs):
        return {"brief": "[1] Example source: https://example.test/research"}

    monkeypatch.setattr(main, "retrieve_memories", retrieve)
    monkeypatch.setattr(main, "conduct_deep_research", research)
    return store, repository, conversations


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["chat", "vision", "research", "action"])
async def test_same_identity_and_approved_profile_in_all_modes(identity_environment, mode):
    store, repository, _ = identity_environment
    store.update(memory_enabled=True, web_consent=True)
    repository.save_introduction({"user.name": ("Ada", "fact"), "user.goal": ("Launch Orion", "goal")})
    repository.set_profile_summary("Prefers practical examples")
    kwargs = {"text": "Hello"}
    if mode == "vision":
        kwargs["image"] = "synthetic-image"
    elif mode == "research":
        kwargs["text"] = "/web Orion"
    elif mode == "action":
        kwargs["action_id"] = "summarize"
    content, instruction, sources = await main._build_prompt(main.ChatRequest(**kwargs), include_metadata=True)
    serialized = json.dumps(content)
    assert instruction.startswith(CORE_IDENTITY)
    assert f'"mode": "{mode}"' in instruction
    assert "Ada" in serialized and "Launch Orion" in serialized
    assert "Prefers practical examples" in serialized
    assert "Ada" not in instruction  # Personal facts never become system rules.
    assert len(sources) == 2 and len({item["id"] for item in sources}) == 2
    if mode != "chat":
        assert "Do not ask personal getting-to-know-you questions" in instruction


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["chat", "vision", "research"])
@pytest.mark.parametrize("private", [False, True])
async def test_disabled_memory_and_private_sessions_never_read_profile(identity_environment, monkeypatch, mode, private):
    store, repository, _ = identity_environment
    store.update(memory_enabled=private, web_consent=True)

    def forbidden(*args, **kwargs):
        raise AssertionError("Saved profile must not be read")

    monkeypatch.setattr(repository, "for_context", forbidden)
    monkeypatch.setattr(repository, "profile_summary", forbidden)
    content, instruction, sources = await main._build_prompt(main.ChatRequest(
        text="/web test" if mode == "research" else "hello",
        image="synthetic-image" if mode == "vision" else None, private=private,
    ), include_metadata=True)
    assert sources == [] and "User-approved profile" not in str(content)
    assert '"approved_memory_context_enabled": false' in instruction
    if private:
        assert "no new memory is saved" in instruction


@pytest.mark.asyncio
async def test_personal_question_cadence_and_explicit_opt_out(identity_environment):
    store, _, conversations = identity_environment
    conversations.create("Greeting", conversation_id="one")
    conversations.add_message("one", "user", "Hi")
    conversations.add_message("one", "assistant", "Hi! What are you working on?")
    payload, _ = await main._model_payload(main.ChatRequest(text="Orion", conversation_id="one"))
    assert "Do not ask personal getting-to-know-you questions" in payload["messages"][0]["content"]
    store.update(personal_questions_enabled=False)
    _, instruction = await main._build_prompt(main.ChatRequest(text="Hi"))
    assert "Do not ask personal getting-to-know-you questions" in instruction
    assert "Task clarifications are allowed" in instruction


@pytest.mark.asyncio
async def test_candidate_correction_requires_approval_and_forgetting_is_effective(identity_environment):
    store, repository, _ = identity_environment
    store.update(memory_enabled=True)
    repository.save_introduction({"user.name": ("Ada", "fact")})
    replacement, _ = repository.add_candidate("Deniz", "fact", "user.name")
    assert preferred_name(profile_memories(repository, store.load())) == "Ada"
    repository.activate(replacement)
    assert preferred_name(profile_memories(repository, store.load())) == "Deniz"
    content, _, sources = await main._build_prompt(main.ChatRequest(text="Hi"), include_metadata=True)
    assert "Deniz" in content and "Ada" not in content
    assert [item["id"] for item in sources] == [replacement]
    repository.delete(replacement)
    content, _ = await main._build_prompt(main.ChatRequest(text="Hi"))
    assert content == "Hi"  # No separate hidden profile brings the old name back.


def test_introduction_transaction_and_replacement_keep_previous_record(tmp_path):
    repository = MemoryRepository(tmp_path / "memory.db")
    repository.save_introduction({"user.name": ("Ada", "fact")})
    old_id = repository.list()[0]["id"]
    with pytest.raises(ValueError):
        repository.save_introduction({"user.name": ("Deniz", "fact"), "user.goal": ("x", "invalid")})
    assert repository.list()[0]["content"] == "Ada"
    repository.save_introduction({"user.name": ("Deniz", "fact")})
    assert len(repository.list()) == 2
    assert repository.for_context()[0]["content"] == "Deniz"
    assert next(item for item in repository.list() if item["id"] == old_id)["status"] == "superseded"
    repository.save_introduction({"user.name": ("Deniz", "fact")})
    assert len(repository.list()) == 2


@pytest.mark.parametrize("language", ["tr", "en"])
def test_introduction_review_save_and_cancel_are_local_and_explicit(tmp_path, language):
    store = SettingsStore(tmp_path / "settings.json")
    store.update(language=language, web_consent=True)
    repository = MemoryRepository(tmp_path / "memory.db")
    dialog = IntroductionDialog(store=store, repository=repository)
    try:
        dialog.fields["user.name"].setText("Ada <b>test</b>")
        dialog.fields["user.work"].setText("Learning Python")
        dialog.fields["user.goal"].setText("Launch Orion")
        dialog.style.setCurrentIndex(dialog.style.findData("short"))
        dialog.learn.setChecked(True)
        for _ in range(4):
            dialog.advance()
        assert dialog.pages.currentIndex() == 4
        assert "Ada <b>test</b>" in dialog.review.text()
        assert dialog.review.textFormat() == Qt.TextFormat.PlainText
        assert repository.list() == [] and not store.load().introduction_complete
        dialog.save()
        assert dialog.result() == QDialog.DialogCode.Accepted
        preferences = store.load()
        assert preferences.memory_enabled and preferences.memory_auto_learn and preferences.introduction_complete
        assert preferences.web_consent and not preferences.wake_word_enabled
        assert not preferences.cloud_speech_consent and not preferences.memory_reference_history
        assert len(repository.for_context()) == 4
        reopened = IntroductionDialog(store=store, repository=repository)
        try:
            assert reopened.fields["user.name"].text() == "Ada <b>test</b>"
            assert reopened.style.currentData() == "short"
            original = store.path.read_bytes()
            reopened.fields["user.name"].setText("Not saved")
            reopened.reject()
            assert store.path.read_bytes() == original
            assert preferred_name(profile_memories(repository, store.load())) == "Ada <b>test</b>"
        finally:
            reopened.close()
    finally:
        dialog.close()


def test_skip_and_empty_introduction_preserve_conservative_permissions(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    repository = MemoryRepository(tmp_path / "memory.db")
    dialog = IntroductionDialog(store=store, repository=repository)
    dialog.fields["user.name"].setText("Do not save")
    dialog.skip()
    preferences = store.load()
    assert preferences.introduction_complete and not preferences.personal_questions_enabled
    assert not preferences.memory_enabled and not preferences.memory_auto_learn
    assert not preferences.web_consent and not preferences.cloud_speech_consent
    assert repository.list() == []
    dialog = IntroductionDialog(store=store, repository=repository)
    dialog.learn.setChecked(True)
    dialog.save()
    assert repository.list() == [] and not store.load().memory_auto_learn
    dialog.close()


def test_failed_save_keeps_review_and_retry_does_not_duplicate(tmp_path, monkeypatch):
    store = SettingsStore(tmp_path / "settings.json")
    repository = MemoryRepository(tmp_path / "memory.db")
    dialog = IntroductionDialog(store=store, repository=repository)
    dialog.fields["user.name"].setText("Ada")
    original_save = store.save

    def failed(*args):
        raise OSError("Synthetic failure")

    monkeypatch.setattr(store, "save", failed)
    dialog.save()
    assert dialog.result() == QDialog.DialogCode.Rejected and dialog.status.text()
    assert not store.load().introduction_complete
    monkeypatch.setattr(store, "save", original_save)
    dialog.save()
    assert dialog.result() == QDialog.DialogCode.Accepted and len(repository.list()) == 1
    dialog.close()


def test_greeting_respects_memory_edits_and_private_session(identity_environment, monkeypatch):
    from frontend import app as desktop

    store, repository, _ = identity_environment
    store.update(setup_complete=True, introduction_complete=True, memory_enabled=True)
    repository.save_introduction({"user.name": ("Ada", "fact")})
    monkeypatch.setattr(desktop, "settings_store", store)
    monkeypatch.setattr(desktop, "memory_repository", repository)
    window = desktop.SpotlightApp()
    try:
        assert window.welcome_title.text() == "Merhaba, Ada."
        repository.delete_all()
        window.refresh_identity_greeting()
        assert window.welcome_title.text() == "Aklında ne var?"
        repository.save_introduction({"user.name": ("Deniz", "fact")})
        window.private_session = True
        window.refresh_identity_greeting()
        assert window.welcome_title.text() == "Aklında ne var?"
        assert not window.introduction_button.isEnabled()
        window.private_session = False
        store.update(memory_enabled=False)
        window.refresh_identity_greeting()
        assert window.welcome_title.text() == "Aklında ne var?"
    finally:
        window.close()


def test_first_setup_opens_introduction_only_until_completed(identity_environment, monkeypatch):
    from frontend import app as desktop

    store, repository, _ = identity_environment
    store.update(setup_complete=True)
    monkeypatch.setattr(desktop, "settings_store", store)
    monkeypatch.setattr(desktop, "memory_repository", repository)

    class CompletedSetup:
        def __init__(self, **kwargs):
            pass

        def exec(self):
            return QDialog.DialogCode.Accepted

    monkeypatch.setattr(desktop, "OnboardingDialog", CompletedSetup)
    window = desktop.SpotlightApp()
    calls = []
    monkeypatch.setattr(window, "open_introduction", lambda: calls.append("introduction"))
    try:
        window.open_onboarding()
        assert calls == ["introduction"]
        store.update(introduction_complete=True)
        window.open_onboarding()
        assert calls == ["introduction"]
    finally:
        window.close()


def test_long_profile_can_be_scrolled_for_review(tmp_path, qt_application):
    store = SettingsStore(tmp_path / "settings.json")
    repository = MemoryRepository(tmp_path / "memory.db")
    dialog = IntroductionDialog(store=store, repository=repository)
    try:
        dialog.fields["user.name"].setText("N" * 60)
        dialog.fields["user.work"].setText("Work and interests " * 15)
        dialog.fields["user.goal"].setText("Current goal details " * 20)
        dialog.pages.setCurrentIndex(4)
        dialog.sync()
        dialog.resize(560, 590)
        dialog.show()
        qt_application.processEvents()
        assert dialog.review_scroll.verticalScrollBar().maximum() > 0
        assert dialog.next.isVisible() and dialog.later.isVisible()
        assert dialog.review.text().endswith(dialog.fields["user.goal"].text().strip())
    finally:
        dialog.close()
