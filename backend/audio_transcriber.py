import json
import logging
import queue
import threading

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from backend.speech_model import resolve_speech_model
from backend.voice_activity import VoiceActivity

SAMPLE_RATE = 16000


def input_devices():
    hosts = sd.query_hostapis()
    return [
        {"id": json.dumps([hosts[item["hostapi"]]["name"], item["name"]]),
         "name": f'{item["name"]} · {hosts[item["hostapi"]]["name"]}', "index": index}
        for index, item in enumerate(sd.query_devices()) if item["max_input_channels"] > 0
    ]


class AudioRecorder:
    def __init__(self, sample_rate=16000, *, device="", auto_stop=False,
                 threshold=0.012, silence_seconds=1.2, max_seconds=60.0):
        self.sample_rate = sample_rate
        self.frames = []
        self.is_recording = False
        self.stream = None
        self.device = device
        self.auto_stop = auto_stop
        self.activity = VoiceActivity(threshold, silence_seconds)
        self.finished = threading.Event()
        self.max_seconds = max_seconds
        self.capture_error = ""
        self._sample_count = 0
        self.endpoint = None
        self._endpoint_audio = queue.SimpleQueue()

    def prepare(self):
        from backend.speech_endpoint import SpeechEndpoint

        if self.sample_rate == SAMPLE_RATE:
            self.endpoint = SpeechEndpoint(self.activity.silence_seconds)

    def poll_endpoint(self):
        if self.endpoint is None:
            return
        while not self._endpoint_audio.empty():
            block = self._endpoint_audio.get_nowait()
            try:
                ended = self.endpoint.feed(block)
            finally:
                block.fill(0)
            if self.auto_stop and ended:
                self.finished.set()
                self.is_recording = False

    def _callback(self, indata, frames, time_info, status):
        if self.is_recording:
            if status or not np.isfinite(indata).all():
                self.capture_error = "Mikrofon akışı kesildi veya örnek kaybetti. Yeniden deneyin."
                self.finished.set()
                self.is_recording = False
                return
            remaining = max(0, int(self.max_seconds * self.sample_rate) - self._sample_count)
            indata = indata[:remaining]
            self.frames.append(indata.copy())
            self._sample_count += len(indata)
            ended = self.activity.feed(indata, self.sample_rate)
            if self.endpoint is not None:
                self._endpoint_audio.put(indata.reshape(-1).copy())
            heard_speech = self.endpoint.heard_speech if self.endpoint is not None else self.activity.heard_speech
            if ((self.auto_stop and self.endpoint is None and ended)
                    or self._sample_count >= int(self.max_seconds * self.sample_rate)
                    or (not heard_speech and self.activity.elapsed >= 10)):
                self.finished.set()
                self.is_recording = False

    def start(self):
        self.frames.clear()
        self.finished.clear()
        self.capture_error = ""
        self._sample_count = 0
        self.activity = VoiceActivity(self.activity.threshold, self.activity.silence_seconds)
        selected = None
        if self.device:
            selected = next((item["index"] for item in input_devices() if item["id"] == self.device), None)
            if selected is None:
                raise RuntimeError("Seçili mikrofon bulunamadı. Ayarlardan bağlı bir mikrofon seçin.")
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            callback=self._callback,
            device=selected,
            blocksize=int(self.sample_rate * 0.03),
        )
        try:
            self.is_recording = True
            self.stream.start()
        except Exception:
            self.is_recording = False
            self.stream.close()
            self.stream = None
            raise

    def stop(self) -> np.ndarray:
        self.is_recording = False
        if self.stream is not None:
            stream = self.stream
            self.stream = None
            try:
                stream.stop()
            finally:
                stream.close()

        if self.endpoint is not None:
            self.poll_endpoint()
        heard_speech = self.endpoint.heard_speech if self.endpoint is not None else self.activity.heard_speech
        audio = np.concatenate(self.frames, axis=0).flatten() if self.frames else np.array([], dtype=np.float32)
        for frame in self.frames:
            frame.fill(0)
        self.frames.clear()
        if self.endpoint is not None:
            self.endpoint.clear()
        if not heard_speech:
            audio.fill(0)
            return np.array([], dtype=np.float32)
        return audio


class WhisperTranscriber:
    def __init__(self, model_size='base', device='cpu', compute_type='int8'):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
        self.active_model_size = None

    def configure(self, model_size):
        if model_size != self.model_size:
            self.model_size = model_size
            self._model = None
            self.active_model_size = None

    def use_wake_model(self, model):
        if self.model_size == "base":
            self._model = model
            self.active_model_size = "base"

    def get_model(self):
        size = self.model_size
        try:
            directory = resolve_speech_model(size)
        except (OSError, RuntimeError):
            if size != "small":
                raise RuntimeError("Konuşma modeli hazır değil. Ayarlar → Ses → Giriş bölümünden modeli hazırlayın.") from None
            try:
                directory = resolve_speech_model("base")
                size = "base"
            except (OSError, RuntimeError):
                raise RuntimeError("Konuşma modeli hazır değil. Ayarlar → Ses → Giriş bölümünden modeli hazırlayın.") from None
        if self._model is None or self.active_model_size != size:
            self._model = WhisperModel(
                str(directory),
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=4,
                local_files_only=True,
            )
            self.active_model_size = size
            self._model.logger = logging.Logger("nexus.speech.private", level=logging.CRITICAL + 1)
        return self._model

    def transcribe(self, audio: np.ndarray, language: str = 'tr') -> str:
        if audio is None or len(audio) == 0:
            return ''

        values = np.asarray(audio, dtype=np.float32).reshape(-1).copy()
        if not np.isfinite(values).all():
            raise ValueError("Mikrofon verisi geçersiz. Yeniden deneyin.")
        values -= float(np.mean(values))
        level = float(np.sqrt(np.mean(values * values)))
        if level < 1e-5:
            values.fill(0)
            return ''
        gain = min(4.0, .08 / level, .95 / max(float(np.max(np.abs(values))), 1e-6))
        values *= gain
        try:
            model = self.get_model()
            segments, info = model.transcribe(
                audio=values,
                language=language,
                beam_size=5,
                temperature=0,
                vad_filter=True,
                vad_parameters={"threshold": .35, "min_silence_duration_ms": 300, "speech_pad_ms": 400},
                condition_on_previous_text=False,
            )
            return ' '.join(segment.text.strip() for segment in segments).strip()
        finally:
            values.fill(0)
