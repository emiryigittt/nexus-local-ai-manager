import json
import threading

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

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

    def _callback(self, indata, frames, time_info, status):
        if self.is_recording:
            if status:
                self.capture_error = "Mikrofon akışı kesildi veya örnek kaybetti. Yeniden deneyin."
                self.finished.set()
                self.is_recording = False
                return
            remaining = max(0, int(self.max_seconds * self.sample_rate) - self._sample_count)
            indata = indata[:remaining]
            self.frames.append(indata.copy())
            self._sample_count += len(indata)
            ended = self.activity.feed(indata, self.sample_rate)
            if ((self.auto_stop and ended) or self._sample_count >= int(self.max_seconds * self.sample_rate)
                    or (not self.activity.heard_speech and self.activity.elapsed >= 10)):
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

        if not self.frames:
            return np.array([])

        audio = np.concatenate(self.frames, axis=0).flatten()
        self.frames.clear()
        if not self.activity.heard_speech:
            return np.array([], dtype=np.float32)
        return audio


class WhisperTranscriber:
    def __init__(self, model_size='base', device='cpu', compute_type='int8'):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def get_model(self):
        if self._model is None:
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
        return self._model

    def transcribe(self, audio: np.ndarray, language: str = 'tr') -> str:
        if audio is None or len(audio) == 0:
            return ''

        model = self.get_model()
        segments, info = model.transcribe(
            audio=audio,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
            condition_on_previous_text=False,
        )

        return ' '.join(segment.text.strip() for segment in segments).strip()
