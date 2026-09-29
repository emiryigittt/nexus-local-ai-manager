"""Measure local synthesis latency using fixed synthetic text; no audio playback/network."""

import json
import os
import sys
import tempfile
import time
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    with tempfile.TemporaryDirectory(prefix="nexus-tts-benchmark-") as directory:
        os.environ["NEXUS_DATA_DIR"] = directory
        from backend.supertonic_speaker import synthesize_to_file

        results = []
        for steps in (8, 8, 4, 4):
            os.environ["NEXUS_SUPERTONIC_STEPS"] = str(steps)
            path = str(Path(directory) / "synthetic.wav")
            started = time.monotonic()
            ok = synthesize_to_file("Merhaba. Bugünkü işleri birlikte planlayabiliriz.", path)
            elapsed = time.monotonic() - started
            if not ok:
                raise RuntimeError("Local synthesis failed")
            with wave.open(path) as audio:
                duration = audio.getnframes() / audio.getframerate()
            results.append({"steps": steps, "cold": not results, "generation_seconds": round(elapsed, 3),
                            "audio_seconds": round(duration, 3), "rtf": round(elapsed / duration, 3)})
        print(json.dumps({"synthetic_only": True, "played": False, "results": results}))


if __name__ == "__main__":
    main()
