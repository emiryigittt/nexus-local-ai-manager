from backend.config import Settings


def test_settings_read_environment(monkeypatch):
    monkeypatch.setenv("NEXUS_API_BASE_URL", "http://localhost:9999/v1/")
    monkeypatch.setenv("NEXUS_MODEL", "my/model")
    monkeypatch.setenv("NEXUS_MAX_TOKENS", "4096")

    configured = Settings.from_env()

    assert configured.chat_url == "http://localhost:9999/v1/chat/completions"
    assert configured.model == "my/model"
    assert configured.max_tokens == 4096


def test_settings_fall_back_and_clamp_invalid_values(monkeypatch):
    monkeypatch.setenv("NEXUS_MAX_TOKENS", "not-a-number")
    monkeypatch.setenv("NEXUS_TEMPERATURE", "99")

    configured = Settings.from_env()

    assert configured.max_tokens == 2048
    assert configured.temperature == 2.0
