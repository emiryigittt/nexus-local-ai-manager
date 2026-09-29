"""Runtime configuration for Nexus.

The project deliberately avoids a mandatory dotenv dependency. Copy
``.env.example`` values into your shell, launcher, or IDE environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _as_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return min(max(value, minimum), maximum)


def _as_float(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        return default
    return min(max(value, minimum), maximum)


@dataclass(frozen=True, slots=True)
class Settings:
    """Settings shared by the API and desktop client."""

    api_base_url: str
    api_key: str
    model: str
    request_timeout: float
    max_tokens: int
    temperature: float
    backend_host: str
    backend_port: int

    @property
    def chat_url(self) -> str:
        return f"{self.api_base_url}/chat/completions"

    @property
    def models_url(self) -> str:
        return f"{self.api_base_url}/models"

    @property
    def backend_url(self) -> str:
        return f"http://{self.backend_host}:{self.backend_port}"

    @property
    def provider_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            api_base_url=os.getenv(
                "NEXUS_API_BASE_URL", "http://127.0.0.1:1234/v1"
            ).rstrip("/"),
            api_key=os.getenv("NEXUS_API_KEY", ""),
            model=os.getenv("NEXUS_MODEL", "google/gemma-4-e4b"),
            request_timeout=_as_float("NEXUS_REQUEST_TIMEOUT", 180.0, 5.0, 600.0),
            max_tokens=_as_int("NEXUS_MAX_TOKENS", 2048, 64, 32768),
            temperature=_as_float("NEXUS_TEMPERATURE", 0.2, 0.0, 2.0),
            backend_host=os.getenv("NEXUS_BACKEND_HOST", "127.0.0.1"),
            backend_port=_as_int("NEXUS_BACKEND_PORT", 8000, 1, 65535),
        )


settings = Settings.from_env()
