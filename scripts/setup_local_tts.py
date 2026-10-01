"""Download and safely extract the official Supertonic int8 model."""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.setup_events import report  # noqa: E402
from backend.supertonic_speaker import (  # noqa: E402
    MODEL_NAME,
    _create_engine,
    model_directory,
    model_is_ready,
)

MODEL_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/"
    f"{MODEL_NAME}.tar.bz2"
)
MODELS_DIR = model_directory().parent
ARCHIVE_PATH = MODELS_DIR / f"{MODEL_NAME}.tar.bz2"
TARGET_DIR = MODELS_DIR / MODEL_NAME


def _progress(blocks: int, block_size: int, total: int) -> None:
    if total <= 0:
        return
    percent = min(100, blocks * block_size * 100 // total)
    if percent == getattr(_progress, "last_percent", -1):
        return
    _progress.last_percent = percent
    report("downloading", percent=percent)


def _safe_extract(archive: tarfile.TarFile, destination: Path) -> None:
    root = destination.resolve()
    for member in archive.getmembers():
        target = (destination / member.name).resolve()
        if root not in target.parents and target != root:
            raise RuntimeError(f"Unsafe archive entry: {member.name}")
    archive.extractall(destination, filter="data")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args(argv)
    report("checking")
    if not all(importlib.util.find_spec(name) for name in ("sherpa_onnx", "soundfile")):
        report("runtime_missing")
        return 1
    try:
        if not model_is_ready(TARGET_DIR):
            if not args.download:
                report("failed")
                return 1
            MODELS_DIR.mkdir(parents=True, exist_ok=True)
            # A killed download leaves only an isolated staging directory.
            with tempfile.TemporaryDirectory(dir=MODELS_DIR, prefix="voice-setup-") as temporary:
                staging = Path(temporary)
                archive_path = staging / "model.tar.bz2"
                with urllib.request.urlopen(MODEL_URL, timeout=30) as response, archive_path.open("wb") as stream:
                    total = int(response.headers.get("Content-Length", "0"))
                    blocks = 0
                    _progress.last_percent = -1
                    while chunk := response.read(256 * 1024):
                        stream.write(chunk)
                        blocks += 1
                        _progress(blocks, 256 * 1024, total)
                report("extracting")
                with tarfile.open(archive_path, "r:bz2") as archive:
                    _safe_extract(archive, staging)
                extracted = staging / MODEL_NAME
                if not model_is_ready(extracted):
                    raise RuntimeError("Incomplete model")
                if TARGET_DIR.exists():
                    # Keep an incomplete prior model recoverable; never delete user files.
                    TARGET_DIR.rename(TARGET_DIR.with_name(TARGET_DIR.name + ".incomplete-" + uuid.uuid4().hex[:8]))
                shutil.move(str(extracted), str(TARGET_DIR))
        report("validating")
        engine = _create_engine()
        del engine
    except Exception:
        report("failed")
        return 1
    report("ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
