"""Speech-aware endpointing on the worker, never on the device callback."""

import numpy as np
from faster_whisper.vad import get_speech_timestamps, get_vad_model


class SpeechEndpoint:
    def __init__(self, silence_seconds=1.2):
        self.silence_seconds = max(.3, float(silence_seconds))
        self.heard_speech = False
        self.elapsed = self.silence = 0.0
        self.last_speech_end = 0.0
        self.samples = np.array([], dtype=np.float32)
        self.total = self.since_check = 0
        get_vad_model()  # Packaged local ONNX asset; no download.

    def feed(self, samples):
        values = np.asarray(samples, dtype=np.float32).reshape(-1)
        self.total += len(values)
        self.since_check += len(values)
        self.elapsed = self.total / 16000
        self.samples = np.concatenate((self.samples, values))[-40000:]
        if self.since_check < 2560:
            return False
        self.since_check = 0
        # Keep soft speech audible to the VAD without amplifying quiet noise
        # without limit. Context includes pauses and the beginning of words.
        audio = self.samples.copy()
        level = float(np.sqrt(np.mean(audio * audio)))
        audio *= min(4.0, .06 / max(level, 1e-6))
        try:
            segments = get_speech_timestamps(audio, threshold=.35, neg_threshold=.20,
                                            min_speech_duration_ms=160,
                                            min_silence_duration_ms=100, speech_pad_ms=0)
        finally:
            audio.fill(0)
        if segments:
            self.heard_speech = True
            end = (self.total - len(self.samples) + segments[-1]["end"]) / 16000
            self.last_speech_end = max(self.last_speech_end, end)
        self.silence = max(0.0, self.elapsed - self.last_speech_end)
        return self.heard_speech and self.silence >= self.silence_seconds

    def clear(self):
        self.samples.fill(0)
        self.samples = np.array([], dtype=np.float32)
