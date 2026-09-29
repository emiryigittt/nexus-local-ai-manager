import numpy as np

from backend.audio_transcriber import WhisperTranscriber


class FakeSegment:
    def __init__(self, text):
        self.text = text


class FakeWhisperModel:
    created = 0

    def __init__(self, model_size, device, compute_type):
        self.configuration = (model_size, device, compute_type)
        FakeWhisperModel.created += 1

    def transcribe(self, audio, language, beam_size, vad_filter, vad_parameters, condition_on_previous_text):
        assert len(audio) == 3
        assert language == "tr"
        assert beam_size == 5
        assert vad_filter is True
        assert vad_parameters["min_silence_duration_ms"] == 500
        assert condition_on_previous_text is False
        return [FakeSegment(" Merhaba "), FakeSegment(" Nexus ")], object()


def test_whisper_transcriber_is_local_lazy_and_reused(monkeypatch):
    FakeWhisperModel.created = 0
    monkeypatch.setattr("backend.audio_transcriber.WhisperModel", FakeWhisperModel)
    transcriber = WhisperTranscriber(model_size="base", device="cpu", compute_type="int8")

    assert transcriber._model is None
    assert transcriber.transcribe(np.array([0.1, 0.2, 0.3], dtype=np.float32)) == "Merhaba Nexus"
    assert transcriber.transcribe(np.array([0.1, 0.2, 0.3], dtype=np.float32)) == "Merhaba Nexus"
    assert FakeWhisperModel.created == 1
