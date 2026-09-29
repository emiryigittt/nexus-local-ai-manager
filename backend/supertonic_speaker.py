"""Natural, fully local Turkish speech synthesis through sherpa-onnx."""

from __future__ import annotations

import importlib.util
import os
import threading
from pathlib import Path

MODEL_NAME = "sherpa-onnx-supertonic-3-tts-int8-2026-05-11"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "duration_predictor.int8.onnx",
    "text_encoder.int8.onnx",
    "vector_estimator.int8.onnx",
    "vocoder.int8.onnx",
    "tts.json",
    "unicode_indexer.bin",
    "voice.bin",
)

_engine = None
_engine_lock = threading.Lock()
_generation_lock = threading.Lock()


def model_directory() -> Path:
    configured = os.getenv("NEXUS_SUPERTONIC_MODEL_DIR")
    return Path(configured) if configured else PROJECT_ROOT / "models" / MODEL_NAME


def model_is_ready(path: Path | None = None) -> bool:
    directory = path or model_directory()
    return all((directory / name).is_file() for name in REQUIRED_FILES)


def runtime_is_ready() -> bool:
    """Model assets alone are insufficient when optional packages are absent."""
    return model_is_ready() and all(
        importlib.util.find_spec(name) is not None for name in ("sherpa_onnx", "soundfile")
    )


def _create_engine():
    try:
        import sherpa_onnx
    except ImportError as exc:
        raise RuntimeError(
            "Local neural voice requires requirements-tts.txt to be installed."
        ) from exc

    directory = model_directory()
    if not model_is_ready(directory):
        raise RuntimeError(
            "Supertonic model is not installed. Run scripts/setup_local_tts.py."
        )

    supertonic = sherpa_onnx.OfflineTtsSupertonicModelConfig(
        duration_predictor=str(directory / REQUIRED_FILES[0]),
        text_encoder=str(directory / REQUIRED_FILES[1]),
        vector_estimator=str(directory / REQUIRED_FILES[2]),
        vocoder=str(directory / REQUIRED_FILES[3]),
        tts_json=str(directory / REQUIRED_FILES[4]),
        unicode_indexer=str(directory / REQUIRED_FILES[5]),
        voice_style=str(directory / REQUIRED_FILES[6]),
    )
    config = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            supertonic=supertonic,
            num_threads=max(1, int(os.getenv("NEXUS_TTS_THREADS", "2"))),
            provider=os.getenv("NEXUS_TTS_PROVIDER", "cpu"),
            debug=False,
        )
    )
    if not config.validate():
        raise RuntimeError("The Supertonic model configuration is invalid.")
    return sherpa_onnx.OfflineTts(config)


def _get_engine():
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = _create_engine()
        return _engine


def synthesize_to_file(text: str, output_path: str) -> bool:
    """Generate natural Turkish speech locally and write a PCM WAV file."""
    if not text.strip():
        return False

    try:
        import sherpa_onnx
        import soundfile as sf

        from backend.user_settings import settings_store

        preferences = settings_store.load()
        generation = sherpa_onnx.GenerationConfig()
        generation.sid = int(os.getenv("NEXUS_SUPERTONIC_SPEAKER", str(preferences.tts_local_voice)))
        generation.num_steps = int(os.getenv("NEXUS_SUPERTONIC_STEPS", str(preferences.tts_steps)))
        generation.speed = float(os.getenv("NEXUS_SUPERTONIC_SPEED", str(preferences.tts_speed)))
        generation.extra["lang"] = os.getenv("NEXUS_TTS_LANGUAGE", preferences.language)

        with _generation_lock:
            audio = _get_engine().generate(text, generation)
        if len(audio.samples) == 0:
            return False
        sf.write(output_path, audio.samples, audio.sample_rate, subtype="PCM_16")
        path = Path(output_path)
        return path.is_file() and path.stat().st_size > 0
    except (ImportError, OSError, RuntimeError, TypeError, ValueError):
        return False
