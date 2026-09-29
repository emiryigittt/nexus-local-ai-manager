"""Synthetic offline wake-phrase check. Never opens a microphone or plays audio.

Requires installed Supertonic assets/runtime and an already cached Whisper base.
Temporary WAVs contain only the fixed phrases below, never ambient/user audio.
"""

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, choices=range(1, 21), default=1)
    args = parser.parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    import numpy as np
    from faster_whisper.audio import decode_audio

    from backend.supertonic_speaker import synthesize_to_file
    from backend.wake_capture import WakeBuffer
    from backend.wake_word import LocalWakeDetector

    detector = LocalWakeDetector()
    detector.prepare()
    # Diagnostic text is from fixed synthetic fixtures only, never a microphone.
    original_transcribe = detector.model.transcribe
    decoded = []

    def trace_synthetic(*args, **kwargs):
        segments, info = original_transcribe(*args, **kwargs)
        segments = list(segments)
        decoded[:] = [{"text": item.text, "logprob": round(item.avg_logprob, 3),
                       "no_speech": round(item.no_speech_prob, 3)} for item in segments]
        return iter(segments), info

    detector.model.transcribe = trace_synthetic
    results = []
    with tempfile.TemporaryDirectory(prefix="nexus-wake-check-") as directory:
        fixtures = (
            ("en", "Hey Nexus.", True),
            ("tr", "Hey Nexus.", True),
            ("en", "Hey, next.", False),
            ("en", "Tell me about Nexus.", False),
            ("tr", "Bugün hava nasıl?", False),
        ) * args.repetitions
        for language, phrase, expected in fixtures:
            os.environ["NEXUS_TTS_LANGUAGE"] = language
            path = str(Path(directory) / "synthetic.wav")
            if not synthesize_to_file(phrase, path):
                raise RuntimeError("Synthetic speech could not be generated")
            audio = decode_audio(path, sampling_rate=16000)
            # Exercise the same buffering as the live worker, including a phrase
            # crossing the old fixed four-second boundary. No device is opened.
            source = np.concatenate((np.zeros(60800, dtype=np.float32), audio,
                                     np.zeros(9600, dtype=np.float32)))
            buffer = WakeBuffer()
            detector.language = language
            decoded.clear()
            started = time.monotonic()
            detected = False
            for offset in range(0, len(source), 480):
                clip = buffer.feed(source[offset:offset + 480])
                if clip is not None:
                    detected = detector.detects(clip) or detected
                    clip.fill(0)
            results.append({"language": language, "phrase": phrase, "expected": expected,
                            "detected": detected, "decoded": list(decoded),
                            "seconds": round(time.monotonic() - started, 2)})
            audio.fill(0)
            source.fill(0)
            buffer.clear()
    print(json.dumps({"microphone_opened": False, "offline": True,
                      "positive_hits": sum(item["expected"] and item["detected"] for item in results),
                      "positive_total": sum(item["expected"] for item in results),
                      "false_positives": sum(not item["expected"] and item["detected"] for item in results),
                      "results": results}, ensure_ascii=True))
    return 0 if all(item["detected"] == item["expected"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
