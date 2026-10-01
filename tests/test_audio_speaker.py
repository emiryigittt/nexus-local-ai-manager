from backend.audio_speaker import SpeechSpeaker


class FakeEngine:
    def __init__(self):
        self.output_path = None

    def setProperty(self, _name, _value):
        pass

    def save_to_file(self, _text, output_path):
        self.output_path = output_path

    def runAndWait(self):
        with open(self.output_path, "wb") as output:
            output.write(b"RIFF-local-audio" + b"\x00" * 64)

    def stop(self):
        pass


def test_speaker_uses_local_engine(monkeypatch, tmp_path):
    monkeypatch.setattr("backend.audio_speaker.pyttsx3.init", FakeEngine)
    output_path = tmp_path / "speech.wav"

    assert SpeechSpeaker(backend="local").speak_to_file("Merhaba Nexus", str(output_path))
    assert output_path.read_bytes().startswith(b"RIFF")


def test_speaker_ignores_empty_text(tmp_path):
    assert not SpeechSpeaker(backend="local").speak_to_file(
        "  ", str(tmp_path / "speech.wav")
    )


def test_edge_backend_is_explicit_and_uses_mp3():
    speaker = SpeechSpeaker(backend="edge")

    assert speaker.backend == "edge"
    assert speaker.file_suffix == ".mp3"


def test_unknown_backend_falls_back_to_local():
    speaker = SpeechSpeaker(backend="unknown")

    assert speaker.backend == "local"
    assert speaker.file_suffix == ".wav"


def test_supertonic_backend_uses_wave_audio():
    speaker = SpeechSpeaker(backend="supertonic")

    assert speaker.backend == "supertonic"
    assert speaker.file_suffix == ".wav"


def test_auto_backend_prefers_installed_supertonic(monkeypatch):
    monkeypatch.setattr("backend.supertonic_speaker.runtime_is_ready", lambda: True)

    assert SpeechSpeaker(backend="auto").backend == "supertonic"


def test_auto_backend_skips_model_files_without_runtime_packages(monkeypatch):
    from backend.supertonic_speaker import runtime_is_ready

    monkeypatch.setattr("backend.supertonic_speaker.model_is_ready", lambda: True)
    monkeypatch.setattr("backend.supertonic_speaker.importlib.util.find_spec", lambda name: None)
    assert not runtime_is_ready()
    assert SpeechSpeaker(backend="auto").backend == "local"


def test_auto_voice_falls_back_locally_if_neural_synthesis_fails(monkeypatch, tmp_path):
    monkeypatch.setattr("backend.supertonic_speaker.runtime_is_ready", lambda: True)
    monkeypatch.setattr("backend.supertonic_speaker.synthesize_to_file", lambda *args: False)
    monkeypatch.setattr("backend.audio_speaker.pyttsx3.init", FakeEngine)
    speaker = SpeechSpeaker(backend="auto")
    assert speaker.speak_to_file("Test", str(tmp_path / "fallback.wav"))
    assert speaker.backend == "local"


def test_explicit_neural_voice_reports_missing_engine(monkeypatch, tmp_path):
    monkeypatch.setattr("backend.supertonic_speaker.synthesize_to_file", lambda *args: False)
    speaker = SpeechSpeaker(backend="supertonic")
    assert not speaker.speak_to_file("Test", str(tmp_path / "missing.wav"))
    assert "Ayarlar" in speaker.last_error and "Yanıt sesi" in speaker.last_error


def test_cloud_speech_never_runs_without_saved_consent(monkeypatch, tmp_path):
    from backend.user_settings import UserPreferences

    monkeypatch.setattr("backend.user_settings.settings_store.load", UserPreferences.defaults)
    speaker = SpeechSpeaker(backend="edge")

    def forbidden(*args):
        raise AssertionError("No cloud request without consent")

    monkeypatch.setattr(speaker, "_edge_to_file", forbidden)
    assert not speaker.speak_to_file("Private test", str(tmp_path / "never.mp3"))


def test_edge_uses_saved_voice_and_rate_only_after_consent(monkeypatch, tmp_path):

    from backend.user_settings import UserPreferences

    preferences = UserPreferences.defaults()
    preferences.cloud_speech_consent = True
    preferences.tts_edge_voice = "tr-TR-EmelNeural"
    preferences.tts_speed = 1.1
    monkeypatch.setattr("backend.user_settings.settings_store.load", lambda: preferences)
    monkeypatch.delenv("NEXUS_EDGE_TTS_VOICE", raising=False)
    calls = []

    class Communicate:
        def __init__(self, text, voice, *, rate, boundary):
            assert boundary == "WordBoundary"
            calls.append((text, voice, rate))

        async def stream(self):
            yield {"type": "audio", "data": b"synthetic"}
            yield {"type": "WordBoundary", "offset": 1_000_000, "duration": 2_000_000, "text": "Test"}

    monkeypatch.setattr("backend.audio_speaker.edge_tts.Communicate", Communicate)
    speaker = SpeechSpeaker(backend="edge")
    assert speaker.speak_to_file("Test", str(tmp_path / "test.mp3"))
    assert calls == [("Test", "tr-TR-EmelNeural", "+10%")]
    assert speaker.last_word_timings == [(100, 300, "Test")]


def test_edge_supports_older_communicate_without_boundary_parameter(monkeypatch, tmp_path):
    from backend.user_settings import UserPreferences

    preferences = UserPreferences.defaults()
    preferences.cloud_speech_consent = True
    monkeypatch.setattr("backend.user_settings.settings_store.load", lambda: preferences)

    class Communicate:
        def __init__(self, text, voice, *, rate):
            pass

        async def stream(self):
            yield {"type": "audio", "data": b"synthetic"}
            yield {"type": "WordBoundary", "offset": 0, "duration": 1_000_000, "text": "Test"}

    monkeypatch.setattr("backend.audio_speaker.edge_tts.Communicate", Communicate)
    speaker = SpeechSpeaker(backend="edge")
    assert speaker.speak_to_file("Test", str(tmp_path / "older.mp3"))
    assert speaker.last_word_timings == [(0, 100, "Test")]
