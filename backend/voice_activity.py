"""Energy-based speech gating for explicitly started, bounded microphone sessions."""

import math

import numpy as np


class VoiceActivity:
    def __init__(self, threshold=0.012, silence_seconds=1.2, min_speech_seconds=0.2):
        self.threshold = min(0.2, max(0.001, float(threshold)))
        self.silence_seconds = max(0.3, float(silence_seconds))
        self.min_speech_seconds = min_speech_seconds
        self.speech_seconds = 0.0
        self.silence = 0.0
        self.elapsed = 0.0
        self.noise_floor = 0.0
        self.level = 0.0

    @property
    def heard_speech(self):
        return self.speech_seconds >= self.min_speech_seconds

    def feed(self, samples, sample_rate):
        duration = len(samples) / sample_rate
        self.elapsed += duration
        self.level = math.sqrt(float(np.mean(np.square(samples)))) if len(samples) else 0.0
        if not math.isfinite(self.level):
            self.level = 0.0
        cutoff = max(self.threshold, self.noise_floor * 3)
        if self.level >= cutoff:
            self.speech_seconds += duration
            self.silence = 0.0
        else:
            self.silence += duration
            self.noise_floor = self.noise_floor * 0.95 + self.level * 0.05
        return self.heard_speech and self.silence >= self.silence_seconds
