"""Durable, non-secret user preferences and local provider profiles."""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from backend.app_paths import ensure_data_dirs, settings_path


@dataclass(slots=True)
class ProviderProfile:
    id: str
    name: str
    kind: str
    base_url: str
    selected_model: str = ""
    api_key_ref: str = ""
    enabled: bool = True
    is_local: bool = True
    capabilities: list[str] = field(default_factory=lambda: ["text"])

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ProviderProfile:
        allowed = {item.name for item in cls.__dataclass_fields__.values()}
        return cls(**{key: item for key, item in value.items() if key in allowed})


@dataclass(slots=True)
class UserPreferences:
    schema_version: int = 1
    setup_complete: bool = False
    language: str = "tr"
    theme: str = "dark"
    reduced_motion: bool = False
    global_shortcut: str = "alt+space"
    selected_provider_id: str = "lm-studio"
    tts_enabled: bool = False
    tts_backend: str = "auto"
    tts_local_voice: int = 0
    tts_edge_voice: str = "tr-TR-AhmetNeural"
    tts_speed: float = 1.0
    tts_steps: int = 8
    voice_input_device: str = ""
    voice_output_device: str = ""
    voice_input_mode: str = "toggle"
    voice_silence_seconds: float = 1.2
    voice_threshold: float = 0.012
    wake_word_enabled: bool = False
    wake_word_on_startup: bool = False
    cloud_speech_consent: bool = False
    web_consent: bool = False
    memory_enabled: bool = False
    memory_auto_learn: bool = False
    memory_reference_history: bool = False
    clipboard_policy: str = "ask"
    embedding_model: str = ""
    providers: list[ProviderProfile] = field(default_factory=list)

    @classmethod
    def defaults(cls) -> UserPreferences:
        return cls(
            providers=[
                ProviderProfile(
                    id="lm-studio",
                    name="LM Studio",
                    kind="lm_studio",
                    base_url="http://127.0.0.1:1234/v1",
                ),
                ProviderProfile(
                    id="ollama",
                    name="Ollama",
                    kind="ollama",
                    base_url="http://127.0.0.1:11434/v1",
                ),
                ProviderProfile(
                    id="llama-cpp",
                    name="llama.cpp",
                    kind="llama_cpp",
                    base_url="http://127.0.0.1:8080/v1",
                ),
            ]
        )

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> UserPreferences:
        value = dict(value)
        raw_providers = value.pop("providers", [])
        allowed = {item.name for item in cls.__dataclass_fields__.values()}
        preferences = cls(**{key: item for key, item in value.items() if key in allowed})
        preferences.providers = [ProviderProfile.from_dict(item) for item in raw_providers]
        if not preferences.providers:
            preferences.providers = cls.defaults().providers
        return preferences


class SettingsStore:
    def __init__(self, path: Path | None = None):
        self.path = path or settings_path()
        self._lock = threading.RLock()

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> UserPreferences:
        with self._lock:
            if not self.path.exists():
                return UserPreferences.defaults()
            try:
                value = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                return UserPreferences.defaults()
            return UserPreferences.from_dict(dict(value))

    def save(self, preferences: UserPreferences) -> None:
        with self._lock:
            if self.path == settings_path():
                ensure_data_dirs()
            else:
                self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(asdict(preferences), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary.replace(self.path)

    def update(self, **changes: Any) -> UserPreferences:
        preferences = self.load()
        for key, value in changes.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)
        self.save(preferences)
        return preferences

    def selected_provider(self) -> ProviderProfile | None:
        preferences = self.load()
        return next(
            (item for item in preferences.providers if item.id == preferences.selected_provider_id),
            preferences.providers[0] if preferences.providers else None,
        )


settings_store = SettingsStore()
