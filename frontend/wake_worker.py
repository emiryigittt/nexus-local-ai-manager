"""Continuous ambient capture with cancellable, serial local inference."""

import threading
import time

from PyQt6.QtCore import QThread, pyqtSignal

from backend.wake_capture import WakeCapture


class WakeWordWorker(QThread):
    # Pending capture already expires after two seconds. Also bound inference:
    # an overloaded CPU must not open the assistant for an old utterance.
    MAX_INFERENCE_SECONDS = 6.0
    detected = pyqtSignal()
    state_changed = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, preferences, detector, capture=None):
        super().__init__()
        self.detector = detector
        self.language = preferences.language
        self.capture = capture or WakeCapture(
            device=preferences.voice_input_device, threshold=preferences.wake_word_threshold,
        )
        self._cancelled = threading.Event()
        self.detection_deadline = 0.0

    def cancel(self):
        self.requestInterruption()
        self._cancelled.set()
        self.capture.cancel()

    def run(self):
        audio = None
        phase = "model"
        try:
            if self._cancelled.is_set():
                return
            self.state_changed.emit("Hazırlanıyor · mikrofon kapalı")
            self.detector.language = self.language
            self.detector.prepare()  # Cached-only: no automatic download.
            if self._cancelled.is_set():
                return
            phase = "capture"
            self.capture.start()
            while not self.capture.ready.wait(0.05):
                if self._cancelled.is_set():
                    return
            if self.capture.error:
                raise RuntimeError("capture failed")
            self.state_changed.emit("Dinliyor · yerel mikrofon açık")
            while not self._cancelled.is_set():
                if self.capture.error:
                    raise RuntimeError("capture failed")
                audio = self.capture.take()
                if audio is None:
                    continue
                phase = "inference"
                started = time.monotonic()
                matched = self.detector.detects(audio)
                elapsed = time.monotonic() - started
                phase = "capture"
                if elapsed > self.MAX_INFERENCE_SECONDS:
                    self.state_changed.emit("Dinliyor · algılama gecikti, eski çağrı atlandı")
                    matched = False
                else:
                    self.state_changed.emit("Dinliyor · yerel mikrofon açık")
                if matched and not self._cancelled.is_set() and not self.capture.error:
                    self.detection_deadline = started + self.MAX_INFERENCE_SECONDS
                    self.capture.stop()  # Release before handing off to ordinary input.
                    if self.capture.error:
                        raise RuntimeError("capture failed during release")
                    if not self._cancelled.is_set() and time.monotonic() <= self.detection_deadline:
                        self.detected.emit()
                    break
                if audio is not None:
                    audio.fill(0)
                    audio = None
        except Exception:
            if not self._cancelled.is_set():
                # Never expose inference exceptions: they can contain ambient text.
                self.failed.emit({
                    "model": "Hey Nexus modeli hazır değil. Ayarlar → Ses bölümünden Modeli hazırla seçeneğini kullanıp yeniden deneyin.",
                    "capture": "Hey Nexus mikrofonu kullanamıyor. Ses ayarlarındaki cihazı ve Windows mikrofon iznini kontrol edin.",
                    "inference": "Hey Nexus ses algılaması durdu. Yerel modeli F2 ile kontrol edip yeniden deneyin.",
                }[phase])
        finally:
            if audio is not None:
                audio.fill(0)
            try:
                self.capture.stop()
            except Exception:
                pass
