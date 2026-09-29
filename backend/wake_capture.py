"""Continuous, bounded, RAM-only wake capture independent of model inference."""

import queue
import threading
import time

import numpy as np
import sounddevice as sd

from backend.audio_transcriber import input_devices
from backend.voice_activity import VoiceActivity


class WakeBuffer:
    """Four-second ring, silence-ended phrases, two-second overlap on long speech.

    Used only on the capture callback thread. No model/file/network calls here.
    """

    def __init__(self, threshold=0.012, sample_rate=16000):
        self.rate = sample_rate
        self.samples = np.zeros(4 * sample_rate, dtype=np.float32)
        self.activity = VoiceActivity(threshold, silence_seconds=0.5)
        self.position = self.size = self.active_samples = self.since_emit = 0

    def clear(self):
        self.samples.fill(0)
        self.position = self.size = self.active_samples = self.since_emit = 0
        floor = self.activity.noise_floor
        self.activity = VoiceActivity(self.activity.threshold, silence_seconds=0.5)
        self.activity.noise_floor = floor

    def snapshot(self):
        length = min(self.size, self.active_samples + int(0.3 * self.rate))
        start = (self.position - length) % len(self.samples)
        indices = (np.arange(length) + start) % len(self.samples)
        return self.samples[indices].copy()

    def feed(self, samples):
        values = np.asarray(samples, dtype=np.float32).reshape(-1)
        if len(values) > len(self.samples):
            raise ValueError("Oversized capture block")
        indices = (np.arange(len(values)) + self.position) % len(self.samples)
        self.samples[indices] = values
        self.position = (self.position + len(values)) % len(self.samples)
        self.size = min(len(self.samples), self.size + len(values))
        self.activity.feed(values, self.rate)
        if self.active_samples or self.activity.silence == 0:
            self.active_samples += len(values)
            self.since_emit += len(values)
        if self.activity.silence >= 0.5:
            clip = self.snapshot() if self.activity.heard_speech else None
            self.clear()  # Isolated clicks must not accumulate into speech.
            return clip
        if (self.activity.heard_speech and self.active_samples >= len(self.samples)
                and self.since_emit >= 2 * self.rate):
            self.since_emit = 0
            return self.snapshot()
        return None


class WakeCapture:
    """Own the device on a capture thread so cancellation also works during inference."""

    def __init__(self, device="", threshold=0.012):
        self.device = device
        self.buffer = WakeBuffer(threshold)
        self.pending = queue.Queue(maxsize=1)
        self.cancelled = threading.Event()
        self.ready = threading.Event()
        self.closed = threading.Event()
        self.error = False
        self.thread = None

    def _callback(self, indata, frames, time_info, status):
        if self.cancelled.is_set():
            return
        if status or not np.isfinite(indata).all():
            self.error = True
            self.cancel()
            return
        try:
            clip = self.buffer.feed(indata)
            if clip is not None:
                self.discard_pending()  # Keep newest audio, never an unbounded backlog.
                self.pending.put_nowait((time.monotonic(), clip))
        except Exception:
            self.error = True
            self.cancel()

    def discard_pending(self):
        try:
            _, clip = self.pending.get_nowait()
            clip.fill(0)
        except queue.Empty:
            pass

    def start(self):
        self.thread = threading.Thread(target=self._capture, name="nexus-wake-capture")
        self.thread.start()

    def _capture(self):
        stream = None
        try:
            if self.cancelled.is_set():
                return
            selected = None
            if self.device:
                selected = next((item["index"] for item in input_devices() if item["id"] == self.device), None)
                if selected is None:
                    raise RuntimeError("Selected microphone unavailable")
            stream = sd.InputStream(samplerate=16000, channels=1, dtype="float32",
                                    device=selected, blocksize=480, callback=self._callback)
            if self.cancelled.is_set():
                return
            stream.start()
            self.ready.set()
            while not self.cancelled.wait(0.05):
                if not stream.active:
                    raise RuntimeError("Microphone disconnected")
        except Exception:
            self.error = True
            self.cancel()
        finally:
            try:
                if stream is not None:
                    try:
                        stream.abort()
                    finally:
                        stream.close()
            except Exception:
                self.error = True
            finally:
                self.buffer.clear()
                self.discard_pending()
                self.ready.set()
                self.closed.set()

    def take(self, timeout=0.05):
        try:
            created, clip = self.pending.get(timeout=timeout)
        except queue.Empty:
            return None
        if self.cancelled.is_set() or time.monotonic() - created > 2.0:
            clip.fill(0)
            return None
        return clip

    def cancel(self):
        self.cancelled.set()

    def stop(self):
        self.cancel()
        if self.thread is not None:
            self.thread.join()
        self.discard_pending()
