"""Check Whisper base offline; download only with an explicit --download flag.

No microphone, settings store, transcription, or audio playback is used.
Output is a small content-free JSON-lines protocol for the settings UI.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.setup_events import report  # noqa: E402
from backend.wake_model import load_wake_model, resolve_wake_model  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Allow a Hugging Face model download")
    args = parser.parse_args(argv)
    report("downloading" if args.download else "checking")
    try:
        directory = resolve_wake_model(allow_download=args.download)
        report("validating")
        model = load_wake_model(directory)
        del model
    except Exception:
        # Local paths, tokens and remote response bodies must not enter UI/logs.
        report("failed")
        return 1
    report("ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
