import sqlite3

from backend.conversations import ConversationRepository


def test_get_finds_conversations_outside_the_list_window(tmp_path):
    repository = ConversationRepository(tmp_path / "window.db")
    oldest = repository.create("Eski konuşma", conversation_id="oldest")
    for index in range(505):
        repository.create(f"Konuşma {index}")
    # Pencere dışında kaldığını kesinleştirmek için en eski kaydı sabit bir tarihe çek.
    with sqlite3.connect(repository.path) as connection:
        connection.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            ("2020-01-01T00:00:00+00:00", oldest),
        )

    assert oldest not in {item["id"] for item in repository.list(limit=500)}
    assert repository.get(oldest)["title"] == "Eski konuşma"
    assert repository.get("missing") is None


def test_conversation_lifecycle_and_search(tmp_path):
    repository = ConversationRepository(tmp_path / "nexus.db")
    conversation_id = repository.create(
        "Nexus roadmap", provider_id="ollama", model_id="qwen3:8b"
    )
    repository.add_message(conversation_id, "user", "Yerel belge araması ekle")
    repository.add_message(conversation_id, "assistant", "Bunu yerel RAG ile yapabiliriz.")

    assert repository.list()[0]["id"] == conversation_id
    assert repository.list("RAG")[0]["id"] == conversation_id
    assert [item["role"] for item in repository.messages(conversation_id)] == [
        "user",
        "assistant",
    ]

    assert repository.update(conversation_id, title="Yeni başlık", pinned=True)
    assert repository.list()[0]["title"] == "Yeni başlık"
    assert repository.delete(conversation_id)
    assert repository.list() == []


def test_conversation_create_is_idempotent_for_stream_retries(tmp_path):
    repository = ConversationRepository(tmp_path / "nexus.db")

    first = repository.create("İlk başlık", conversation_id="fixed")
    second = repository.create("Değişmemeli", conversation_id="fixed")

    assert first == second == "fixed"
    assert repository.list()[0]["title"] == "İlk başlık"


def test_rolling_summary_is_upserted_without_copying_messages(tmp_path):
    repository = ConversationRepository(tmp_path / "summaries.db")
    repository.upsert_summary("conversation", "chat-1", "İlk özet", 4)
    repository.upsert_summary("conversation", "chat-1", "Güncel özet", 6)

    summary = repository.summary("conversation", "chat-1")

    assert summary["summary"] == "Güncel özet"
    assert summary["source_message_count"] == 6


def test_history_search_treats_user_input_as_text_not_fts_syntax(tmp_path):
    repository = ConversationRepository(tmp_path / "search.db")
    identifier = repository.create("Python")
    repository.add_message(identifier, "user", "Python testi")
    assert repository.list('Python? "')[0]["id"] == identifier
    assert repository.list("::**") == []
