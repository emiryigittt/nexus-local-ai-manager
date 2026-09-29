"""Play a short local voice test through the real desktop speech pipeline.

Run with the same Python environment as Nexus. User settings/history are untouched.
Checks WAV content and Qt playback completion, not whether a person hears the speaker.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nexus-voice-check-") as directory:
        os.environ["NEXUS_DATA_DIR"] = directory
        os.environ["NEXUS_TTS_ENABLED"] = "0"
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

        import numpy as np
        from PyQt6.QtCore import QTimer
        from PyQt6.QtMultimedia import QMediaDevices, QMediaPlayer
        from PyQt6.QtWidgets import QApplication

        from frontend.app import SpotlightApp

        app = QApplication([])
        window = SpotlightApp()
        result = {"generated": False, "played": False, "errors": [],
                  "generated_chunks": 0, "played_chunks": 0, "caption_matches": 0}
        result["device"] = QMediaDevices.defaultAudioOutput().description()
        window.streaming_text = "Merhaba. Nexus sesli yanıt testi başarılı."
        window.toggle_tts()
        worker = window.stream_voice_worker
        result["backend"] = worker.speaker.backend

        def audio_ready(path):
            try:
                with wave.open(path, "rb") as audio:
                    frames = audio.getnframes()
                    rate = audio.getframerate()
                    samples = np.frombuffer(audio.readframes(frames), dtype="<i2")
                    result["duration_seconds"] = round(frames / rate, 2)
                    result["nonzero_samples"] = int(np.count_nonzero(samples))
                    result["generated"] = frames > 0 and bool(np.any(samples))
                    result["generated_chunks"] += 1
                    if "first_audio_ready_seconds" not in result:
                        result["first_audio_ready_seconds"] = round(time.monotonic() - started, 3)
            except Exception as exc:
                result["errors"].append(str(exc))

        def media_status(status):
            if status == QMediaPlayer.MediaStatus.EndOfMedia:
                result["played"] = True
                result["played_chunks"] += 1

        def caption_ready(path, text, seconds, backend):
            result["caption_matches"] += int(bool(text) and backend == result["backend"])

        worker.audio_ready.connect(audio_ready)
        worker.chunk_ready.connect(caption_ready)
        worker.error_received.connect(result["errors"].append)
        window.media_player.mediaStatusChanged.connect(media_status)
        window.media_player.errorOccurred.connect(lambda error, text: result["errors"].append(text))
        started = time.monotonic()

        def check_done():
            if time.monotonic() - started > 60 and not result["errors"]:
                result["errors"].append("Voice test timed out")
            drained = (result["played"] and worker not in window._workers
                       and not window.audio_queue and window.current_audio_path is None)
            if drained or result["errors"]:
                timer.stop()
                window.request_quit()

        timer = QTimer()
        timer.timeout.connect(check_done)
        timer.start(50)
        app.exec()
        print(json.dumps(result, ensure_ascii=True))
        return 0 if (result["generated"] and result["played"] and not result["errors"]
                     and result["generated_chunks"] == result["played_chunks"]
                     == result["caption_matches"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
