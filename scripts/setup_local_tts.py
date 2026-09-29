"""Download and safely extract the official Supertonic int8 model."""

from __future__ import annotations

import sys
import tarfile
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.supertonic_speaker import MODEL_NAME, model_is_ready  # noqa: E402

MODEL_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/"
    f"{MODEL_NAME}.tar.bz2"
)
MODELS_DIR = PROJECT_ROOT / "models"
ARCHIVE_PATH = MODELS_DIR / f"{MODEL_NAME}.tar.bz2"
TARGET_DIR = MODELS_DIR / MODEL_NAME


def _progress(blocks: int, block_size: int, total: int) -> None:
    if total <= 0:
        return
    percent = min(100, blocks * block_size * 100 // total)
    if percent == getattr(_progress, "last_percent", -1):
        return
    _progress.last_percent = percent
    print(f"\rDownloading Supertonic model... {percent:3d}%", end="", flush=True)


def _safe_extract(archive: tarfile.TarFile, destination: Path) -> None:
    root = destination.resolve()
    for member in archive.getmembers():
        target = (destination / member.name).resolve()
        if root not in target.parents and target != root:
            raise RuntimeError(f"Unsafe archive entry: {member.name}")
    archive.extractall(destination, filter="data")


def main() -> int:
    if model_is_ready(TARGET_DIR):
        print(f"Supertonic is already installed at {TARGET_DIR}")
        return 0

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Source: {MODEL_URL}")
    try:
        urllib.request.urlretrieve(MODEL_URL, ARCHIVE_PATH, _progress)
        print("\nExtracting model...")
        with tarfile.open(ARCHIVE_PATH, "r:bz2") as archive:
            _safe_extract(archive, MODELS_DIR)
    except Exception as exc:
        print(f"\nSetup failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if ARCHIVE_PATH.exists():
            ARCHIVE_PATH.unlink()

    if not model_is_ready(TARGET_DIR):
        print("Model archive did not contain the expected files.", file=sys.stderr)
        return 1
    print(f"Supertonic is ready at {TARGET_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
