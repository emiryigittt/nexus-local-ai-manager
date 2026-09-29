"""One offline-by-default model path shared by wake detection and explicit setup."""

import logging
from pathlib import Path

from faster_whisper import WhisperModel
from faster_whisper.utils import download_model


def resolve_wake_model(*, allow_download=False):
    directory = Path(download_model("base", local_files_only=not allow_download))
    # Even with a local model, an absent tokenizer could cause a network fallback.
    required = ("model.bin", "config.json", "tokenizer.json")
    if not all((directory / name).is_file() for name in required):
        raise RuntimeError("Incomplete offline wake model")
    return directory


def load_wake_model(directory):
    model = WhisperModel(str(directory), device="cpu", compute_type="int8",
                         cpu_threads=2, local_files_only=True)
    model.logger = logging.Logger("nexus.wake.private", level=logging.CRITICAL + 1)
    return model
