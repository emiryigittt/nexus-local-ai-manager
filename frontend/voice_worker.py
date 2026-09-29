"""Background workers for local speech input and queued response speech."""

from __future__ import annotations

import os
import queue
import re
import tempfile
import threading
import time
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from backend.audio_speaker import SpeechSpeaker
from backend.audio_transcriber import AudioRecorder, WhisperTranscriber
from backend.speech_chunks import take_speech_chunks


def _clean_for_speech(text: str) -> str:
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"[`*_#>|~\[\]{}]", "", text)
    text = re.sub(r"https?://\S+", "", text)
    return re.sub(r"\s+", " ", text).strip()


class VoiceRecordWorker(QThread):
    recording_started = pyqtSignal()
    status_changed = pyqtSignal(str)
    text_ready = pyqtSignal(str)
    error_received = pyqtSignal(str)
    level_changed = pyqtSignal(float)

    def __init__(self, recorder=None, transcriber=None, *, language="tr"):
        super().__init__()
        self.recorder = recorder or AudioRecorder()
        self.transcriber = transcriber or WhisperTranscriber()
        self._stopped = threading.Event()
        self.language = language

    def run(self):
        try:
            if self.isInterruptionRequested():
                return
            self.recorder.start()
            if self.isInterruptionRequested():
                return
            self.status_changed.emit("Dinleniyor…")
            if not self._stopped.is_set():
                self.recording_started.emit()
            started = time.monotonic()
            while not self._stopped.wait(0.05):
                stream = getattr(self.recorder, "stream", None)
                if stream is not None and not stream.active:
                    raise RuntimeError("Mikrofon bağlantısı kesildi. Cihazı kontrol edip yeniden deneyin.")
                if hasattr(self.recorder, "activity"):
                    self.level_changed.emit(self.recorder.activity.level)
                if hasattr(self.recorder, "finished") and self.recorder.finished.is_set():
                    break
                if time.monotonic() - started >= getattr(self.recorder, "max_seconds", 60):
                    break
            audio = self.recorder.stop()
            if self.isInterruptionRequested():
                return
            if getattr(self.recorder, "capture_error", ""):
                raise RuntimeError(self.recorder.capture_error)
            if len(audio) == 0:
                self.text_ready.emit("")
                return
            self.status_changed.emit("Ses yerel Whisper ile çözümleniyor…")
            text = self.transcriber.transcribe(audio, language=self.language)
            if not self.isInterruptionRequested():
                self.text_ready.emit(text)
        except Exception as exc:
            if not self.isInterruptionRequested():
                self.error_received.emit(str(exc))
        finally:
            try:
                self.recorder.stop()
            except Exception:
                pass

    def stop_recording(self):
        self._stopped.set()

    def cancel(self):
        self.requestInterruption()
        self.stop_recording()


class VoiceSpeakWorker(QThread):
    """Synthesize a single block of speech."""

    audio_ready = pyqtSignal(str)

    def __init__(self, text: str, output_path: str | None = None):
        super().__init__()
        self.text = text
        self.output_path = output_path
        self.speaker = SpeechSpeaker()

    def run(self):
        clean_text = _clean_for_speech(self.text)
        if not clean_text:
            return
        path = self.output_path or _temporary_audio_path(self.speaker.file_suffix)
        if self.speaker.speak_to_file(clean_text, path):
            self.audio_ready.emit(path)


class StreamingVoiceWorker(QThread):
    """Generate sentence audio in order while the model is still responding."""

    audio_ready = pyqtSignal(str)
    error_received = pyqtSignal(str)
    chunk_ready = pyqtSignal(str, str, float, str)

    def __init__(self, backend=None):
        super().__init__()
        self.speaker = SpeechSpeaker(backend=backend)
        self.sentences: queue.Queue[str | None] = queue.Queue()
        self._finished_input = False

    def enqueue(self, sentence: str) -> None:
        cleaned = _clean_for_speech(sentence)
        if cleaned and not self._finished_input and not self.isInterruptionRequested():
            pieces, _ = take_speech_chunks(cleaned, flush=True)
            for piece in pieces:
                self.sentences.put(piece)

    def finish(self) -> None:
        if not self._finished_input:
            self._finished_input = True
            self.sentences.put(None)

    def stop(self) -> None:
        """Stop immediately when the owning window is closing.

        ``finish`` deliberately drains already queued sentences so normal
        playback remains ordered. During application shutdown we must not
        leave the QThread alive while Qt destroys its owner, otherwise Qt can
        abort the process with ``QThread: Destroyed while thread is still
        running``.
        """
        self.requestInterruption()
        self.sentences.put(None)

    def run(self):
        if self.speaker.backend == "supertonic":
            # Load weights while the LLM is preparing its first tokens.
            try:
                from backend.supertonic_speaker import _get_engine
                _get_engine()
            except Exception:
                pass  # Normal synthesis reports failure or the permitted local fallback.
        while True:
            sentence = self.sentences.get()
            if sentence is None or self.isInterruptionRequested():
                return
            path = _temporary_audio_path(self.speaker.file_suffix)
            delivered = False
            started = time.monotonic()
            try:
                if not self.speaker.speak_to_file(sentence, path):
                    raise RuntimeError(self.speaker.last_error or "Ses üretilemedi. Yerel ses motorunu kontrol edin.")
                if not self.isInterruptionRequested():
                    self.chunk_ready.emit(path, sentence, time.monotonic() - started, self.speaker.backend)
                    self.audio_ready.emit(path)
                    delivered = True
            except Exception as exc:
                if not self.isInterruptionRequested():
                    self.error_received.emit(str(exc))
                return
            finally:
                if not delivered:
                    try:
                        Path(path).unlink(missing_ok=True)
                    except OSError:
                        pass


def _temporary_audio_path(suffix: str) -> str:
    descriptor, path = tempfile.mkstemp(suffix=suffix)
    os.close(descriptor)
    return path
