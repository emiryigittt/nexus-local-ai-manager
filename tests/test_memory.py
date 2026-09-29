from backend.memory import MemoryRepository


def test_memory_is_explicit_editable_and_deletable(tmp_path):
    repository = MemoryRepository(tmp_path / "memory.db")
    memory_id = repository.add(" Kullanıcı kısa yanıtları sever. ", "preference")

    assert repository.list(True)[0]["content"] == "Kullanıcı kısa yanıtları sever."
    assert repository.list(True)[0]["memory_type"] == "preference"
    assert repository.update(
        memory_id, "Kullanıcı teknik yanıtları sever.", enabled=False, memory_type="preference"
    )
    assert repository.list(True) == []
    assert repository.delete(memory_id)
    assert repository.list() == []


def test_memory_rejects_unknown_type(tmp_path):
    repository = MemoryRepository(tmp_path / "typed.db")

    try:
        repository.add("test", "secret")
    except ValueError as exc:
        assert "Unknown memory type" in str(exc)
    else:
        raise AssertionError("Unknown memory type should be rejected")


def test_project_memory_is_isolated_from_global_context(tmp_path):
    repository = MemoryRepository(tmp_path / "scopes.db")
    global_id = repository.add("Türkçe yanıt ver", "instruction")
    project_id = repository.add(
        "Nexus Windows-first", "project_decision", "project", "nexus"
    )
    repository.add("Başka karar", "project_decision", "project", "other")

    assert [item["id"] for item in repository.for_context()] == [global_id]
    nexus_ids = {item["id"] for item in repository.for_context("nexus")}
    assert nexus_ids == {global_id, project_id}


def test_memory_keeps_source_provenance(tmp_path):
    repository = MemoryRepository(tmp_path / "sources.db")
    memory_id = repository.add(
        "Kaynaklı bilgi",
        "fact",
        source_conversation_id="conversation-1",
        source_message_id="message-2",
    )

    memory = next(item for item in repository.list() if item["id"] == memory_id)

    assert memory["source_conversation_id"] == "conversation-1"
    assert memory["source_message_id"] == "message-2"


def test_memory_context_prioritizes_pinned_and_skips_expired(tmp_path):
    repository = MemoryRepository(tmp_path / "ranking.db")
    ordinary = repository.add("Normal", importance=0.9)
    pinned = repository.add("Pinned", importance=0.1, pinned=True)
    repository.add("Expired", expires_at="2000-01-01T00:00:00+00:00")

    results = repository.for_context()

    assert [item["id"] for item in results] == [pinned, ordinary]
    repository.mark_used([pinned])
    assert next(item for item in repository.list() if item["id"] == pinned)["last_used_at"]


def test_memory_status_and_version_history(tmp_path):
    repository = MemoryRepository(tmp_path / "versions.db")
    memory_id = repository.add("Eski tercih", "preference")

    assert repository.update(
        memory_id,
        "Yeni tercih",
        memory_type="preference",
        status="superseded",
    )

    current = next(item for item in repository.list() if item["id"] == memory_id)
    assert current["status"] == "superseded"
    assert repository.for_context() == []
    assert repository.versions(memory_id)[0]["content"] == "Eski tercih"


def test_candidates_deduplicate_and_supersede_on_activation(tmp_path):
    repository = MemoryRepository(tmp_path / "dedup.db")
    original = repository.add(
        "Kısa yanıtları tercih eder",
        "preference",
        memory_key="response.length",
    )

    duplicate, outcome = repository.add_candidate(
        "Kısa yanıtları tercih eder", "preference", "response.length"
    )
    assert (duplicate, outcome) == (original, "duplicate")

    replacement, outcome = repository.add_candidate(
        "Ayrıntılı yanıtları tercih eder", "preference", "response.length"
    )
    assert outcome == "replacement"
    assert repository.activate(replacement)

    values = {item["id"]: item for item in repository.list()}
    assert values[original]["status"] == "superseded"
    assert values[replacement]["status"] == "active"


def test_memory_profile_and_delete_all(tmp_path):
    repository = MemoryRepository(tmp_path / "profile.db")
    repository.set_profile_summary("Kullanıcı teknik ve kısa cevapları tercih eder.")
    repository.add("Python kullanır", "fact")

    assert repository.profile_summary().startswith("Kullanıcı teknik")

    repository.delete_all()

    assert repository.profile_summary() == ""
    assert repository.list() == []
