from backend.user_settings import SettingsStore, UserPreferences


def test_settings_store_round_trip(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    preferences = UserPreferences.defaults()
    preferences.setup_complete = True
    preferences.language = "en"
    preferences.providers[1].selected_model = "qwen3:8b"
    preferences.selected_provider_id = "ollama"
    preferences.clipboard_policy = "always"

    store.save(preferences)
    loaded = store.load()

    assert loaded.setup_complete is True
    assert loaded.language == "en"
    assert loaded.selected_provider_id == "ollama"
    assert store.selected_provider().selected_model == "qwen3:8b"
    assert loaded.clipboard_policy == "always"


def test_settings_store_recovers_from_invalid_json(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("not-json", encoding="utf-8")

    loaded = SettingsStore(path).load()

    assert loaded.selected_provider_id == "lm-studio"
    assert len(loaded.providers) == 3
    assert loaded.memory_enabled is False
    assert loaded.memory_auto_learn is False
    assert loaded.memory_reference_history is False


def test_memory_controls_are_persisted_independently(tmp_path):
    store = SettingsStore(tmp_path / "memory-controls.json")
    preferences = UserPreferences.defaults()
    preferences.memory_enabled = True
    preferences.memory_auto_learn = False
    preferences.memory_reference_history = True
    store.save(preferences)

    loaded = store.load()

    assert loaded.memory_enabled is True
    assert loaded.memory_auto_learn is False
    assert loaded.memory_reference_history is True
def test_voice_personality_preferences_survive_restart(tmp_path):
    from backend.user_settings import SettingsStore, UserPreferences

    store = SettingsStore(tmp_path / "voice.json")
    preferences = UserPreferences.defaults()
    preferences.tts_local_voice = 7
    preferences.tts_edge_voice = "tr-TR-EmelNeural"
    preferences.tts_speed = 1.15
    preferences.tts_steps = 4
    store.save(preferences)
    reloaded = SettingsStore(store.path).load()
    assert (reloaded.tts_local_voice, reloaded.tts_edge_voice, reloaded.tts_speed,
            reloaded.tts_steps) == (7, "tr-TR-EmelNeural", 1.15, 4)
