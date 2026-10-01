"""Cached-only command models; setup is the sole download entry point."""

from pathlib import Path

from faster_whisper.utils import download_model

MODELS = ("base", "small")


def resolve_speech_model(size, *, allow_download=False):
    if size not in MODELS:
        raise ValueError("Unsupported speech model")
    directory = Path(download_model(size, local_files_only=not allow_download))
    if not all((directory / name).is_file() for name in ("model.bin", "config.json", "tokenizer.json")):
        raise RuntimeError("Incomplete local speech model")
    return directory
