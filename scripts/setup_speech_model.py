"""Prepare a selected command model. No recording, playback or user audio."""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "60")

from faster_whisper import WhisperModel  # noqa: E402

from backend.setup_events import report  # noqa: E402
from backend.speech_model import MODELS, resolve_speech_model  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=MODELS, default="small")
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args(argv)
    report("downloading" if args.download else "checking")
    try:
        directory = resolve_speech_model(args.model, allow_download=args.download)
        report("validating")
        model = WhisperModel(str(directory), device="cpu", compute_type="int8",
                             cpu_threads=4, local_files_only=True)
        del model
    except Exception:
        report("failed")
        return 1
    report("ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
