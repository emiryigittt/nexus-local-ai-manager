"""Selectable local-first text-to-speech backends."""

from __future__ import annotations

import asyncio
import inspect
import os
import sys
import threading
from pathlib import Path

import edge_tts
import pyttsx3

_local_engine_lock = threading.Lock()

class SpeechSpeaker:
    """Use local Windows speech by default, with explicit Edge TTS opt-in."""

    def __init__(
        self,
        voice: str | None = None,
        rate: int | None = None,
        backend: str | None = None,
    ) -> None:
        selected_backend = backend or os.getenv("NEXUS_TTS_BACKEND", "auto")
        self.backend = selected_backend.casefold()
        self.requested_backend = self.backend
        self.last_error = ""
        self.last_word_timings = []
        if self.backend == "auto":
            from backend.supertonic_speaker import runtime_is_ready

            self.backend = "supertonic" if runtime_is_ready() else "local"
        if self.backend not in {"supertonic", "local", "edge"}:
            self.backend = "local"
        self.voice = voice
        self.local_voice = os.getenv("NEXUS_TTS_VOICE")
        try:
            self.rate = rate or int(os.getenv("NEXUS_TTS_RATE", "180"))
        except ValueError:
            self.rate = 180

    @property
    def file_suffix(self) -> str:
        return ".mp3" if self.backend == "edge" else ".wav"

    def speak_to_file(self, text: str, output_path: str) -> bool:
        """Write speech with the explicitly selected backend."""
        if not text.strip():
            return False
        self.last_error = ""
        self.last_word_timings = []

        if self.backend == "edge":
            from backend.user_settings import settings_store

            if not settings_store.load().cloud_speech_consent:
                self.last_error = "Bulut sesi için ayarlardan izin vermelisiniz."
                return False
            return asyncio.run(self._edge_to_file(text, output_path))
        if self.backend == "supertonic":
            from backend.supertonic_speaker import synthesize_to_file

            if synthesize_to_file(text, output_path):
                return True
            if self.requested_backend != "auto":
                self.last_error = "Supertonic hazır değil. Ayarlar → Ses → Yanıt sesi bölümünden sesi hazırlayın."
                return False
            self.backend = "local"

        with _local_engine_lock:
            return self._local_to_file(text, output_path)

    def _local_to_file(self, text: str, output_path: str) -> bool:
        engine = None
        com = None
        try:
            if sys.platform == "win32":
                import pythoncom

                pythoncom.CoInitialize()
                com = pythoncom
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            local_voice = self.voice or self.local_voice
            if local_voice:
                engine.setProperty("voice", local_voice)
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            path = Path(output_path)
            ok = path.exists() and path.stat().st_size > 44
            if not ok:
                self.last_error = "Windows ses motoru boş bir ses dosyası üretti."
            return ok
        except Exception as exc:
            self.last_error = f"Windows ses motoru: {exc}"
            return False
        finally:
            if engine is not None:
                try:
                    engine.stop()
                except Exception:
                    pass
                del engine
            if com is not None:
                com.CoUninitialize()

    async def _edge_to_file(self, text: str, output_path: str) -> bool:
        from backend.user_settings import settings_store

        preferences = settings_store.load()
        voice = self.voice or os.getenv("NEXUS_EDGE_TTS_VOICE") or preferences.tts_edge_voice
        try:
            rate = f"{round((preferences.tts_speed - 1) * 100):+d}%"
            options = {"rate": rate}
            if "boundary" in inspect.signature(edge_tts.Communicate).parameters:
                options["boundary"] = "WordBoundary"
            communication = edge_tts.Communicate(text, voice, **options)
            with Path(output_path).open("wb") as audio:
                async for message in communication.stream():
                    if message["type"] == "audio":
                        audio.write(message["data"])
                    elif message["type"] == "WordBoundary":
                        start = message["offset"] / 10_000
                        self.last_word_timings.append((start, start + message["duration"] / 10_000, message["text"]))
            path = Path(output_path)
            return path.exists() and path.stat().st_size > 0
        except Exception as exc:
            self.last_error = f"Bulut sesi üretilemedi: {exc}"
            return False
