import numpy as np
import pytest

from backend.audio_transcriber import WhisperTranscriber


class FakeSegment:
    def __init__(self, text):
        self.text = text


class FakeWhisperModel:
    created = 0

    def __init__(self, model_size, device, compute_type, **options):
        assert options == {"cpu_threads": 4, "local_files_only": True}
        self.configuration = (model_size, device, compute_type)
        FakeWhisperModel.created += 1

    def transcribe(self, audio, language, beam_size, vad_filter, vad_parameters, condition_on_previous_text, temperature):
        assert len(audio) == 3
        assert language == "tr"
        assert beam_size == 5 and temperature == 0
        assert vad_filter is True
        assert vad_parameters["min_silence_duration_ms"] == 300
        assert vad_parameters["speech_pad_ms"] == 400
        assert condition_on_previous_text is False
        return [FakeSegment(" Merhaba "), FakeSegment(" Nexus ")], object()


def test_whisper_transcriber_is_local_lazy_and_reused(monkeypatch):
    FakeWhisperModel.created = 0
    monkeypatch.setattr("backend.audio_transcriber.WhisperModel", FakeWhisperModel)
    monkeypatch.setattr("backend.audio_transcriber.resolve_speech_model", lambda size: "/synthetic/" + size)
    transcriber = WhisperTranscriber(model_size="base", device="cpu", compute_type="int8")

    assert transcriber._model is None
    assert transcriber.transcribe(np.array([0.1, 0.2, 0.3], dtype=np.float32)) == "Merhaba Nexus"
    assert transcriber.transcribe(np.array([0.1, 0.2, 0.3], dtype=np.float32)) == "Merhaba Nexus"
    assert FakeWhisperModel.created == 1


def test_small_falls_back_offline_then_switches_when_prepared(monkeypatch):
    prepared = []

    def resolve(size):
        if size == "small" and not prepared:
            raise FileNotFoundError("Not cached")
        return "/synthetic/" + size

    monkeypatch.setattr("backend.audio_transcriber.resolve_speech_model", resolve)
    monkeypatch.setattr("backend.audio_transcriber.WhisperModel", FakeWhisperModel)
    transcriber = WhisperTranscriber(model_size="small")
    transcriber.get_model()
    assert transcriber.active_model_size == "base"
    base = transcriber._model
    prepared.append(True)
    transcriber.get_model()
    assert transcriber.active_model_size == "small" and transcriber._model is not base


def test_empty_or_invalid_audio_never_loads_model(monkeypatch):
    transcriber = WhisperTranscriber()
    monkeypatch.setattr(transcriber, "get_model", lambda: pytest.fail("No model for invalid audio"))
    assert transcriber.transcribe(np.zeros(16000, dtype=np.float32)) == ""
    with pytest.raises(ValueError, match="geçersiz"):
        transcriber.transcribe(np.array([float("nan")]))


def test_preprocessing_preserves_source_and_bounds_gain(monkeypatch):
    source = np.array([-.01, .005, .015], dtype=np.float32)
    original = source.copy()
    retained = []

    def transcribe(**kwargs):
        retained.append(kwargs["audio"])
        assert abs(float(kwargs["audio"].mean())) < 1e-6
        assert np.max(np.abs(kwargs["audio"])) <= .07
        return [FakeSegment("Konuşma")], None

    from types import SimpleNamespace

    model = SimpleNamespace(transcribe=transcribe)
    transcriber = WhisperTranscriber()
    monkeypatch.setattr(transcriber, "get_model", lambda: model)
    assert transcriber.transcribe(source) == "Konuşma"
    assert np.array_equal(source, original)
    assert not np.any(retained[0])
