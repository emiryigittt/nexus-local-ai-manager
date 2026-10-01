import sys
import wave
from types import SimpleNamespace

import numpy as np
import pytest

from backend import supertonic_speaker as speaker
from backend.user_settings import UserPreferences


def configure(monkeypatch, samples, rate=24000):
    engine = SimpleNamespace(generate=lambda *args: SimpleNamespace(samples=samples, sample_rate=rate))
    monkeypatch.setattr(speaker, "_get_engine", lambda: engine)
    monkeypatch.setattr("backend.user_settings.settings_store.load", UserPreferences.defaults)
    monkeypatch.setitem(sys.modules, "sherpa_onnx", SimpleNamespace(
        GenerationConfig=lambda: SimpleNamespace(extra={}),
    ))


def test_generated_wave_is_mono_pcm16_and_clips_overflow(monkeypatch, tmp_path):
    configure(monkeypatch, [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5])
    path = tmp_path / "voice.wav"
    assert speaker.synthesize_to_file("Merhaba", str(path))
    with wave.open(str(path), "rb") as audio:
        assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (1, 2, 24000)
        assert audio.getnframes() == 7
        assert np.frombuffer(audio.readframes(7), dtype="<i2").tolist() == [
            -32768, -32768, -16384, 0, 16384, 32767, 32767,
        ]


@pytest.mark.parametrize("samples,rate", [([], 24000), ([float("nan")], 24000), ([float("inf")], 24000), ([[0.1]], 24000), ([0.1], 0)])
def test_invalid_generated_audio_is_not_written(monkeypatch, tmp_path, samples, rate):
    configure(monkeypatch, samples, rate)
    path = tmp_path / "invalid.wav"
    assert not speaker.synthesize_to_file("Merhaba", str(path))
    assert not path.exists()
