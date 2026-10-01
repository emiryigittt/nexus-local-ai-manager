"""Experimental, offline phrase spotting. Ambient audio never leaves this module.

This deliberately uses the existing cached Whisper base model, not a dedicated
low-power keyword model. Only a boolean detection escapes; transcripts are not
logged, persisted, forwarded to the chat model, or used as command text.
"""

import math
import re
import unicodedata

from backend.wake_model import load_wake_model, resolve_wake_model


def matches_wake_phrase(text: str) -> bool:
    # Full utterance only: mentioning Nexus inside a conversation must not wake it.
    normalized = "".join(char for char in unicodedata.normalize("NFKD", text.casefold())
                         if not unicodedata.combining(char))
    tokens = re.findall(r"[^\W_]+", normalized, flags=re.UNICODE)
    # Accent/spacing variants occur in Turkish decoding of the English name.
    # Keep whole-utterance matching: no fuzzy matches or ordinary mentions.
    return tokens in (["hey", "nexus"], ["hey", "neksus"],
                      ["hey", "nex", "us"], ["heynexus"], ["heyneksus"])


class LocalWakeDetector:
    def __init__(self, language="en"):
        self.model = None
        self.language = language if language in {"en", "tr"} else "en"

    def prepare(self):
        if self.model is None:
            try:
                self.model = load_wake_model(resolve_wake_model())
            except Exception:
                raise RuntimeError(
                    "Hey Nexus için yerel Whisper base modeli yüklenemedi. "
                    "Ayarlar → Ses bölümünden yerel modeli hazırlayın; ardından yeniden deneyin."
                ) from None

    def detects(self, audio) -> bool:
        segments, _ = self.model.transcribe(
            audio, language=self.language, beam_size=1, temperature=0,
            condition_on_previous_text=False, vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
        )
        segments = list(segments)
        if not segments or any(
            not math.isfinite(item.no_speech_prob) or not math.isfinite(item.avg_logprob)
            or not 0 <= item.no_speech_prob <= 0.5 or item.avg_logprob < -0.8
            for item in segments
        ):
            return False
        return matches_wake_phrase(" ".join(item.text for item in segments))
