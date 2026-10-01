"""50-second social film: high-density real Qt UI, directed camera and original audio.

Local synthetic fixtures only. No user data, network inference or microphone.
Reference footage is studied, never copied into the finished film. Built with
the installed PyQt6/PyAV/NumPy environment and the local FFmpeg CLI.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import tempfile
import textwrap
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

import av
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, FPS, SECONDS, RATE = 1080, 1920, 60, 50, 48000
SHOTS = [
    (0, 4, "Ekranında küçük.\nİşlerinde büyük.", "Nexus ile tanış.", "Ekranında küçük. İşlerinde büyük. Neksus'la tanış."),
    (4, 9, "Yaklaş.\nHazır.", "Araçların, tam ihtiyacın olduğunda.", "Ekranın üstünde durur. Yaklaştığında araçların açılır."),
    (9, 14, "Belgeni getir.", "Sorunu sor. Yerel modelinle çalış.", "Belgeni getir. Sorunu sor. Yerel modelinle çalış."),
    (14, 20, "Dağınık bilgiden\nnet adımlara.", "Önemli noktalar, tek bir sohbette.", "Önemli noktaları, tek bir sohbette toparla."),
    (20, 24, "İşine dön.", "Sohbetin ve taslağın yerinde kalır.", "Küçült. Çalışma alanın sana kalsın."),
    (24, 31, "Tam senlik.", "Rengini seç. Işığını ayarla.", "Rengini seç. Işığını ayarla. Neksus'u kendine uyarla."),
    (31, 37, "Biraz daha\ncanlı.", "Mini bot ya da kedi. Yol arkadaşını seç.", "Mini bot ya da kedi. Sana eşlik eden küçük bir yol arkadaşı."),
    (37, 44, "Hafızası var.\nKontrol sende.", "İncele. Onayla. Düzenle. Unuttur.", "Ne hatırlayacağını sen seç. İncele, onayla, düzenle."),
    (44, 50, "Yerel modelin.\nSenin Nexus'un.", "Windows için yerel AI asistanı.", "Yerel modelin. Senin Neksus'un. Projeyi GitHub'da keşfet."),
]
SHOTS_EN = [
    (0, 4, "Small on screen.\nBig on work.", "Meet Nexus.", "Small on screen. Big on work. Meet Nexus."),
    (4, 9, "Move closer.\nReady.", "Your tools, right when you need them.", "At the top of your screen. Ready when you move closer."),
    (9, 14, "Bring your\ndocument.", "Ask a question. Work with your local model.", "Bring your document. Ask your local model."),
    (14, 20, "From scattered notes\nto clear next steps.", "The key points, in one conversation.", "Turn scattered notes into clear next steps."),
    (20, 24, "Back to your work.", "Your conversation and draft stay with you.", "Collapse the panel. Keep your workspace."),
    (24, 31, "Make it yours.", "Pick your color. Set your glow.", "Pick your color. Set your glow. Make Nexus yours."),
    (31, 37, "A little more\nalive.", "Mini bot or cat. Choose your companion.", "A mini bot or a cat. Your little companion."),
    (37, 44, "It remembers.\nYou decide.", "Review. Approve. Edit. Forget.", "Choose what Nexus remembers. Review, approve and edit."),
    (44, 50, "Your local model.\nYour Nexus.", "A local AI companion for Windows.", "Your local model. Your Nexus. Explore the project on GitHub."),
]
VOICE_STARTS = [.65, 4.65, 9.65, 14.7, 20.5, 24.65, 31.25, 37.6, 44.9]
ANSWER = ("## Aurora için üç net öncelik\n\n"
          "1. **Güvenilir kayıt.** Eklediğin okuma öğesi, yeniden açınca korunmalı.\n\n"
          "2. **Klavye erişimi.** Ekleme, arama ve açma fare gerektirmemeli.\n\n"
          "3. **Açık çevrimdışı durumu.** Bağlantı yokken notlar okunabilir kalmalı.")
ANSWER_EN = ("## Three clear priorities for Aurora\n\n"
             "1. **Reliable saving.** Saved reading items should survive a restart.\n\n"
             "2. **Keyboard access.** Add, search and open items without a mouse.\n\n"
             "3. **A clear offline state.** Saved notes stay readable offline.")


def ease(value):
    value = max(0.0, min(1.0, value))
    # Zero velocity and acceleration at both ends: no abrupt camera starts.
    return value ** 3 * (value * (value * 6 - 15) + 10)


def lerp(a, b, value):
    return a + (b - a) * value


def read_audio(path):
    import soundfile as sf

    data, rate = sf.read(path, dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    if rate != RATE:
        mono = np.interp(np.arange(round(len(mono) * RATE / rate)) * rate / RATE,
                         np.arange(len(mono)), mono).astype(np.float32)
    return mono


def trim_voice(signal):
    window = 480
    padded = np.pad(signal, (0, (-len(signal)) % window))
    energies = np.sqrt(np.mean(padded.reshape(-1, window) ** 2, axis=1))
    active = np.flatnonzero(energies > .006)
    if not len(active):
        raise RuntimeError("Narration contains no audible speech")
    return signal[max(0, active[0] * window - 2400):min(len(signal), (active[-1] + 1) * window + 4800)]


def generate_narration(directory):
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["NEXUS_SUPERTONIC_MODEL_DIR"] = str(ROOT / "models/sherpa-onnx-supertonic-3-tts-int8-2026-05-11")
    os.environ["NEXUS_TTS_LANGUAGE"] = "tr"
    os.environ["NEXUS_SUPERTONIC_SPEAKER"] = "0"
    os.environ["NEXUS_SUPERTONIC_STEPS"] = "8"
    os.environ["NEXUS_SUPERTONIC_SPEED"] = "1.03"
    os.environ["NEXUS_TTS_THREADS"] = "4"
    with tempfile.TemporaryDirectory(prefix="nexus-film-voice-") as temporary:
        os.environ["NEXUS_DATA_DIR"] = temporary
        from backend.supertonic_speaker import synthesize_to_file

        records = []
        for index, shot in enumerate(SHOTS):
            path = directory / f"voice-{index + 1:02}.wav"
            if not path.exists() and not synthesize_to_file(shot[4], str(path)):
                raise RuntimeError("Local Turkish narration synthesis failed")
            signal = trim_voice(read_audio(path))
            duration = len(signal) / RATE
            available = shot[1] - VOICE_STARTS[index] - .12
            records.append({"scene": index + 1, "text": shot[4], "raw_seconds": round(duration, 3),
                            "available_seconds": round(available, 3), "speaker": "Supertonic stock voice 0"})
            print(f"Narration {index + 1}/9: {duration:.2f}s for {available:.2f}s", flush=True)
        (directory / "narration.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def original_music():
    """Original electronic score, deterministic synthesis; no third-party music."""
    mix = np.zeros((2, SECONDS * RATE), dtype=np.float32)
    rng = np.random.default_rng(2601001)
    beat = 60 / 108
    chords = [(164.81, 196., 246.94), (130.81, 164.81, 196.),
              (110., 130.81, 164.81), (146.83, 185., 220.)]

    def add(begin, signal, gain, pan=0.):
        start = int(begin * RATE)
        count = min(len(signal), mix.shape[1] - start)
        if count <= 0:
            return
        mix[0, start:start + count] += signal[:count] * gain * (1 - pan * .3)
        mix[1, start:start + count] += signal[:count] * gain * (1 + pan * .3)

    for bar in range(math.ceil(SECONDS / (beat * 4))):
        start = bar * beat * 4
        count = int(beat * 4.5 * RATE)
        t = np.arange(count) / RATE
        envelope = np.minimum(1, t / .45) * np.minimum(1, (count / RATE - t) / .5)
        pad = sum(np.sin(math.tau * f * t) + .15 * np.sin(math.tau * (f + .7) * t) for f in chords[bar % 4]) / 3
        add(start, pad * envelope, .04, (-1) ** bar * .5)
    for number in range(math.ceil(SECONDS / beat)):
        begin = number * beat
        chord = chords[(number // 4) % 4]
        if 3.5 <= begin <= 47.5:
            t = np.arange(int(.28 * RATE)) / RATE
            kick = np.sin(math.tau * (49 * t + 55 * (.018 * (1 - np.exp(-t / .018))))) * np.exp(-t * 19)
            add(begin, kick, .24)
            t = np.arange(int(beat * .8 * RATE)) / RATE
            bass = (np.sin(math.tau * chord[0] / 4 * t) + .25 * np.sin(math.tau * chord[0] / 2 * t))
            add(begin, bass * np.minimum(1, t / .012) * np.exp(-t * 5), .085)
            if number % 4 in {1, 3}:
                t = np.arange(int(.14 * RATE)) / RATE
                noise = rng.normal(0, 1, len(t)).astype(np.float32)
                add(begin, np.diff(noise, prepend=0) * np.exp(-t * 43), .024, .2)
        for half in range(2):
            stamp = begin + half * beat / 2
            t = np.arange(int(.32 * RATE)) / RATE
            note = chord[(number + half) % 3] * 2
            pluck = (np.sin(math.tau * note * t) + .22 * np.sin(math.tau * note * 2 * t))
            pluck *= np.minimum(1, t / .006) * np.exp(-t * 13)
            add(stamp, pluck, .038, (-1) ** number * .65)
            add(stamp + beat * .75, pluck, .009, (-1) ** (number + 1) * .65)
            if 6 < stamp < 47:
                t = np.arange(int(.07 * RATE)) / RATE
                noise = rng.normal(0, 1, len(t)).astype(np.float32)
                add(stamp, np.diff(noise, prepend=0) * np.exp(-t * 82), .006, (-1) ** half * .8)
    times = np.arange(mix.shape[1]) / RATE
    mix *= np.minimum(1, times / 1.3) * np.minimum(1, (SECONDS - times) / 1.6)
    return mix


def soft_effect(kind="transition"):
    """Original rounded low-mid impacts with dark stereo reflections; no sweep/noise."""
    count = int(1.15 * RATE)
    t = np.arange(count) / RATE
    base = {"transition": 98., "open": 147., "attachment": 196.,
            "success": 220., "collapse": 110., "listen": 174.6}[kind]
    attack = 1 - np.exp(-t / .006)
    phase = math.tau * (base * t + base * .25 * .022 * (1 - np.exp(-t / .022)))
    body = np.sin(phase) * np.exp(-t / .17)
    body += .32 * np.sin(math.tau * base * 2 * t) * np.exp(-t / .11)
    body += .14 * np.sin(math.tau * base * 3 * t) * np.exp(-t / .075)
    body += .22 * np.sin(math.tau * 73.4 * t) * np.exp(-t / .13)
    if kind in {"success", "attachment"}:
        delayed_t = np.maximum(0, t - .085)
        body += .3 * np.sin(math.tau * base * 1.5 * delayed_t) * np.exp(-delayed_t / .16) * (t >= .085)
    dry = np.tanh(body * attack) * .12
    result = np.stack([dry, dry]).astype(np.float32)
    # Individually darken the tails, leaving the center transient clean and warm.
    reflection = np.convolve(dry, np.ones(31) / 31, mode="same")
    for i, (delay, gain) in enumerate(((.075, .23), (.123, .18), (.193, .12), (.287, .085), (.411, .05), (.563, .025))):
        offset = int(delay * RATE)
        result[i % 2, offset:] += reflection[:-offset] * gain
        result[(i + 1) % 2, offset:] += reflection[:-offset] * gain * .65
    return result


def create_audio(directory, *, narration=True):
    import soundfile as sf

    music = original_music()
    voice = np.zeros(SECONDS * RATE, dtype=np.float32)
    for index, shot in enumerate(SHOTS):
        if not narration:
            break
        signal = trim_voice(read_audio(directory / f"voice-{index + 1:02}.wav"))
        limit = int((shot[1] - VOICE_STARTS[index] - .12) * RATE)
        ratio = max(.91, len(signal) / limit)
        if abs(ratio - 1.) > .005:
            # Give the short narration room to breathe, without changing pitch.
            if ratio > 1.35:
                raise RuntimeError(f"Narration {index + 1} needs a shorter script")
            source = directory / f"trimmed-{index}.wav"
            target = directory / f"fitted-{index}.wav"
            sf.write(source, signal, RATE)
            subprocess.run([shutil.which("ffmpeg"), "-v", "error", "-y", "-i", str(source),
                            "-af", f"atempo={ratio:.5f}", "-ar", str(RATE), str(target)], check=True)
            signal = read_audio(target)[:limit]
        energy = np.sqrt(np.mean(signal ** 2))
        signal *= min(4., .135 / max(.001, energy))
        signal = .8 * np.tanh(signal / .8)
        begin = int(VOICE_STARTS[index] * RATE)
        voice[begin:begin + len(signal)] += signal
    # Smooth 100 ms automatic music ducking; speech stays centered and readable.
    envelope = np.repeat(np.max(np.abs(voice[:len(voice) // 480 * 480].reshape(-1, 480)), axis=1), 480)
    kernel = np.ones(21) / 21
    smoothed = np.repeat(np.convolve(envelope[::480], kernel, mode="same"), 480)[:len(voice)]
    music *= np.where(smoothed > .035, .37, .85)
    mixed = music + np.stack([voice, voice])
    for stamp, name in [(5.7, "open"), (11., "attachment"), (18.8, "success"), (20.2, "collapse"),
                        (31.6, "listen"), (41.2, "success")]:
        signal = soft_effect(name)
        begin = int(stamp * RATE)
        mixed[:, begin:begin + signal.shape[1]] += signal * .8
    for stamp in (1.85, 4., 9., 14., 24., 31., 37., 44.):
        signal = soft_effect("transition")
        begin = int(stamp * RATE)
        mixed[:, begin:begin + signal.shape[1]] += signal * .7
    name = "voice-master" if narration else "music-master"
    raw, final = directory / f"{name}-raw.wav", directory / f"{name}.wav"
    sf.write(raw, mixed.T, RATE, subtype="PCM_24")
    ffmpeg = shutil.which("ffmpeg")
    first = subprocess.run([ffmpeg, "-hide_banner", "-i", str(raw), "-af",
                            "loudnorm=I=-16:TP=-3:LRA=7:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True, check=True)
    measured, _ = json.JSONDecoder().raw_decode(first.stderr[first.stderr.rfind("{"):])
    values = {key: measured[key] for key in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")}
    filter_value = (f"loudnorm=I=-16:TP=-3:LRA=7:measured_I={values['input_i']}:"
                    f"measured_TP={values['input_tp']}:measured_LRA={values['input_lra']}:"
                    f"measured_thresh={values['input_thresh']}:offset={values['target_offset']}:linear=true")
    subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(raw), "-af", filter_value,
                    "-ar", str(RATE), "-c:a", "pcm_s24le", str(final)], check=True)
    return final


class Capture:
    """Advance real widgets with a deterministic frame clock for smooth recording."""

    def __init__(self, app, temporary, language="tr"):
        from PyQt6.QtCore import QEasingCurve, QRect, Qt
        from PyQt6.QtWidgets import QHBoxLayout, QWidget

        from backend.memory import MemoryRepository
        from backend.user_settings import settings_store
        from frontend.app import SpotlightApp
        from frontend.companion import CompanionAvatar
        from frontend.memory_dialog import MemoryDialog
        from frontend.notch import NotchController
        from frontend.setup_dialog import SetupDialog

        self.app = app
        self.language = language
        self.shots = SHOTS_EN if language == "en" else SHOTS
        self.answer = ANSWER_EN if language == "en" else ANSWER
        preferences = settings_store.load()
        preferences.setup_complete = True
        preferences.reduced_motion = False
        preferences.language = language
        preferences.providers[0].selected_model = self.copy("Örnek yerel model", "Sample local model")
        settings_store.save(preferences)
        self.window = SpotlightApp()
        self.window._setup_prompted = True
        self.window.notch_controller.target_rect = lambda mode: QRect(0, 0, *NotchController.SIZES[mode])
        self.window.notch_controller.pointer_inside = lambda: True
        self.window.show()
        self.window.wake.timer.stop()
        self.window.speech_timer.stop()
        self.window.setWindowOpacity(1)
        self.window.fade_animation.stop()
        self.window.shell_transition.animation.setDuration(440)
        self.window.shell_transition.animation.setEasingCurve(QEasingCurve.Type.InOutQuint)
        self.settings = SetupDialog(parent=self.window)
        self.settings.resize(640, 760)
        self.settings.tabs.setCurrentIndex(3)
        self.repository = MemoryRepository(Path(temporary) / "film-memory.db")
        self.repository.add(self.copy("Kısa ve uygulanabilir yanıtları tercih eder.", "Prefers short, actionable answers."), "preference")
        self.repository.add(self.copy("Aurora: çevrimdışı okunabilen bir okuma listesi.", "Aurora: a reading list that works offline."), "goal")
        self.candidate, _ = self.repository.add_candidate(self.copy("Yanıtlarda önce üç net adım göster.", "Start each answer with three clear steps."), "instruction", "response.structure")
        self.memory = MemoryDialog(self.repository, parent=self.window, focus_memory_id=self.candidate)
        self.memory.resize(920, 680)
        self.cast = QWidget()
        self.cast.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QHBoxLayout(self.cast)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        self.robot, self.cat = CompanionAvatar(240), CompanionAvatar(240)
        self.cat.set_appearance("cat", "#ba9fff")
        layout.addWidget(self.robot)
        layout.addWidget(self.cat)
        self.cast.show()
        self.document = Path(temporary) / self.copy("aurora-proje.txt", "aurora-project.txt")
        self.document.write_text((ROOT / "docs/demo/project-brief.md").read_text(encoding="utf-8"), encoding="utf-8")
        self.fired = set()
        self.shell_start = 0.
        self.last_stage = -1
        self.animation_starts = {}
        app.processEvents()

    def copy(self, turkish, english):
        return english if self.language == "en" else turkish

    def once(self, name, condition, callback, moment):
        if condition and name not in self.fired:
            self.fired.add(name)
            callback()
            self.shell_start = moment

    def update(self, moment):
        from PyQt6.QtCore import QAbstractAnimation

        from frontend.companion import CompanionAvatar
        from frontend.micro_motion import RevealCurtain

        window = self.window
        stage = max(i for i, shot in enumerate(SHOTS) if moment >= shot[0])
        if stage != self.last_stage:
            self.last_stage = stage
            if stage == 1:
                window.set_shell_mode("notch")
            elif stage == 2:
                window.open_full_chat()
                window.show_welcome_state()
                window.input_line.setText(self.copy("Bu projenin üç önceliği nedir?", "What are the three priorities for this project?"))
            elif stage == 3:
                window._show_output()
                window.question_label.setText(self.copy("Aurora projesinin üç önceliğini çıkar.", "Find the three priorities for Aurora."))
                window.input_line.setText(self.copy("Sonra bunu haftalık plana dönüştür.", "Then turn this into a weekly plan."))
                window._response_complete = False
                window._refresh_visual_activity()
                window.update_status(self.copy("Örnek yanıt hazırlanıyor…", "Preparing a sample answer…"))
            elif stage == 4:
                window._response_complete = False
                window._refresh_visual_activity()
                window.collapse_to_notch()
            elif stage == 5:
                self.settings.show()
            elif stage == 6:
                self.settings.save()
                window.apply_appearance(self.settings.store.load())
                window.set_shell_mode("dock")
            elif stage == 7:
                self.memory.show()
            elif stage == 8:
                self.memory.close()
                window.set_shell_mode("notch")
            self.shell_start = moment

        self.once("hover", moment >= 5.7, window.notch_controller._open_preview, moment)
        self.once("pin", moment >= 7.3, window.pin_button.click, moment)
        self.once("document", moment >= 11., self._add_document, moment)
        if stage == 3:
            fraction = ease((moment - 14.5) / 3.5)
            wanted = self.answer[:int(len(self.answer) * fraction)]
            if window.streaming_text != wanted:
                window.streaming_text = wanted
                window._render_markdown(wanted)
        self.once("answer-ready", moment >= 18.8, window.complete_response, moment)
        self.once("background-ready", moment >= 22.5, window.complete_response, moment)
        self.once("violet", moment >= 25.5, lambda: self.settings.appearance.set_color("#ba9fff"), moment)
        self.once("ocean", moment >= 26.9, lambda: self.settings.appearance.set_color("#66cfff"), moment)
        self.once("rose", moment >= 28.2, lambda: self.settings.appearance.set_color("#ff9fc2"), moment)
        self.once("rgb", moment >= 29.1, lambda: self.settings.appearance.rgb.setChecked(True), moment)
        self.once("cat", moment >= 29.4, lambda: self.settings.appearance.character.setCurrentIndex(1), moment)
        self.once("approve", moment >= 41.2, self.memory.activate_button.click, moment)
        if stage == 6:
            mode = "idle" if moment < 32.1 else "listening" if moment < 33.8 else "thinking" if moment < 35.3 else "speaking"
            for avatar in (self.robot, self.cat, window.dock_avatar):
                avatar.set_mode(mode)
            window.dock_title.setText(window.ui_text({"idle": "Nexus hazır", "listening": "Nexus dinliyor", "thinking": "Nexus düşünüyor", "speaking": "Nexus konuşuyor"}[mode]))
        else:
            for avatar in (self.robot, self.cat):
                avatar.set_mode("idle")
        # Set real Qt property animations to exact frame time. The application UI
        # remains the renderer; editorial camera movement is added separately.
        elapsed = max(0, int((moment - self.shell_start) * 1000))
        if window.shell_transition.animation.state() == QAbstractAnimation.State.Running:
            window.shell_transition.animation.pause()
        if window.shell_transition.animation.state() == QAbstractAnimation.State.Paused:
            window.shell_transition.animation.setCurrentTime(min(440, elapsed))
        if elapsed >= 440:
            window.shell_transition.finish()
        self.app.processEvents()
        for parent in (window, self.settings, self.cast):
            for avatar in parent.findChildren(CompanionAvatar):
                avatar.blink_timer.stop()
                avatar.ambient_animation.stop()
                avatar.blink_animation.stop()
                if avatar.mode in avatar.DURATIONS and avatar.mode != "entrance":
                    avatar.phase = (moment * 1000 % avatar.DURATIONS[avatar.mode]) / avatar.DURATIONS[avatar.mode]
                elif avatar.mode == "entrance":
                    avatar.phase = min(1., elapsed / 650)
                avatar.ambient_phase = moment % 5.6 / 5.6
                cycle = moment % 4.6
                avatar.blink = min(1., cycle / .38) if cycle < .38 else 0.
                if avatar.reaction:
                    marker = (id(avatar), avatar.reaction)
                    self.animation_starts.setdefault(marker, moment)
                    avatar.reaction_animation.setCurrentTime(min(900, int((moment - self.animation_starts[marker]) * 1000)))
        for parent in (window, self.settings):
            for curtain in parent.findChildren(RevealCurtain):
                curtain.opacity = 0.
        for edge in (window.accent_edge, self.settings.appearance.edge):
            edge.timer.stop()
            edge.phase = (moment * 24) % 360
        window.notch_controller.stop()
        return stage

    def _add_document(self):
        with patch("frontend.app.request_json", return_value={"id": "fictional-film-document"}):
            self.window.add_local_document(self.document)
        self.window.input_line.setText(self.copy("Bu projenin üç önceliği nedir?", "What are the three priorities for this project?"))

    def close(self):
        self.settings.close()
        self.memory.close()
        self.cast.close()
        self.window.close()
        self.app.processEvents()


def font(size, bold=False):
    from PyQt6.QtGui import QFont

    result = QFont("Segoe UI")
    result.setPixelSize(size)
    result.setWeight(QFont.Weight.DemiBold if bold else QFont.Weight.Normal)
    return result


def transparent_widget(widget):
    """Render widget paint and children without the native window palette."""
    from PyQt6.QtCore import QPoint, Qt
    from PyQt6.QtGui import QImage, QPainter, QRegion
    from PyQt6.QtWidgets import QWidget

    image = QImage(widget.width() * 2, widget.height() * 2, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.scale(2, 2)
    widget.render(painter, QPoint(), QRegion(), QWidget.RenderFlag.DrawChildren)
    painter.end()
    return image


def text(painter, rect, value, size, color="#f0f4f7", *, bold=False, center=False):
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QColor

    painter.setFont(font(size, bold))
    painter.setPen(QColor(color))
    flags = Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap
    flags |= Qt.AlignmentFlag.AlignHCenter if center else Qt.AlignmentFlag.AlignLeft
    bounds = painter.boundingRect(rect, int(flags), value)
    if bounds.height() > rect.height() + 3:
        raise ValueError(f"Film text exceeds frame: {value}")
    painter.drawText(rect, int(flags), value)


def wallpaper(painter, bounds, moment, color="#55ef9d"):
    """Original flowing vector ribbons; not Microsoft's or the reference's wallpaper."""
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QColor, QLinearGradient, QPainterPath, QPen, QRadialGradient

    painter.fillRect(bounds, QColor("#0c1520"))
    glow = QRadialGradient(bounds.width() * .72, bounds.height() * .46, bounds.width() * .76)
    tint = QColor(color)
    tint.setAlpha(65)
    glow.setColorAt(0, tint)
    glow.setColorAt(1, QColor(4, 8, 17, 0))
    painter.fillRect(bounds, glow)
    for index in range(12):
        offset = index * 34
        shift = math.sin(moment * .17 + index * .12) * 12
        path = QPainterPath()
        path.moveTo(-160, bounds.height() * .88 + offset)
        path.cubicTo(bounds.width() * .22, bounds.height() * .92 - offset * .9,
                     bounds.width() * .22, bounds.height() * .28 + offset * .55,
                     bounds.width() * .7 + shift, bounds.height() * .48 + offset * .32)
        path.cubicTo(bounds.width() * .94, bounds.height() * .6 + offset * .45,
                     bounds.width() * 1.1, bounds.height() * .24 - offset * .3,
                     bounds.width() * 1.2, bounds.height() * .21 - offset * .25)
        pen_color = QColor(color)
        pen_color.setAlpha(80 - index * 4)
        gradient = QLinearGradient(0, bounds.height(), bounds.width(), 0)
        gradient.setColorAt(0, QColor("#123a42"))
        gradient.setColorAt(.47, pen_color)
        gradient.setColorAt(1, QColor("#121b37"))
        painter.setPen(QPen(gradient, 44))
        painter.drawPath(path)
        shine = QColor(color)
        shine.setAlpha(60 - index * 3)
        painter.setPen(QPen(shine, 1.1))
        painter.drawPath(path)
    painter.setPen(QPen(QColor(160, 190, 200, 12), 1))
    for index in range(4):
        radius = 210 + index * 45
        painter.drawEllipse(QRectF(bounds.width() * .76 - radius, bounds.height() * .23 - radius,
                                  radius * 2, radius * 2))


def desktop(capture, moment, stage):
    from PyQt6.QtCore import QRectF, Qt
    from PyQt6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen

    image = QImage(2800, 2000, QImage.Format.Format_RGB888)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.scale(2, 2)
    wallpaper(painter, QRectF(0, 0, 1400, 1000), moment, "#ba9fff" if stage >= 5 else "#55ef9d")
    if stage == 4:
        painter.setBrush(QColor(11, 18, 25, 180))
        painter.setPen(QPen(QColor(144, 184, 195, 40), 1))
        painter.drawRoundedRect(QRectF(210, 220, 980, 500), 22, 22)
        text(painter, QRectF(245, 255, 900, 44), capture.copy("Bugünün odağı", "Today's focus"), 25, "#97b2bd", bold=True)
        text(painter, QRectF(245, 330, 900, 105), capture.copy("Daha az dağınıklık.\nDaha çok odak.", "Less clutter.\nMore focus."), 30, "#688691")
        for row, value in enumerate((capture.copy("Aurora / proje notları", "Aurora / project notes"),
                                     capture.copy("Haftanın öncelikleri", "This week's priorities"),
                                     capture.copy("Okuma listem", "My reading list"))):
            y = 460 + row * 62
            painter.setPen(QPen(QColor("#3b6470"), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(246, y + 2, 19, 19), 4, 4)
            text(painter, QRectF(283, y, 780, 35), value, 18, "#8ca6b0")
    if stage == 5:
        pixmap = capture.settings.grab()
        target = QRectF(380, 0, 640, capture.settings.height())
    elif stage == 7:
        pixmap = capture.memory.grab()
        target = QRectF(240, 20, 920, 680)
    else:
        pixmap = capture.window.grab()
        target = QRectF((1400 - capture.window.width()) / 2, 0,
                        capture.window.width(), capture.window.height())
    painter.drawPixmap(target, pixmap, QRectF(0, 0, pixmap.width(), pixmap.height()))
    if stage == 2 and moment < 11.4:
        progress = ease((moment - 9.5) / 1.5)
        x, y = lerp(1060, 540, progress), lerp(470, 550, progress)
        painter.save()
        painter.translate(x, y)
        painter.rotate(lerp(9, -3, progress))
        painter.setPen(QPen(QColor("#a4d8ba"), 1))
        painter.setBrush(QColor("#152c2c"))
        painter.drawRoundedRect(QRectF(-125, -58, 250, 116), 15, 15)
        painter.setPen(QPen(QColor("#a4d8ba"), 2))
        painter.drawRoundedRect(QRectF(-99, -28, 28, 37), 4, 4)
        painter.drawLine(-92, -16, -79, -16)
        painter.drawLine(-92, -7, -79, -7)
        text(painter, QRectF(-53, -26, 165, 55), capture.copy("aurora-proje.txt\nÖrnek belge", "aurora-project.txt\nSample document"), 17, "#d8ede7", bold=True)
        painter.restore()
    # Editorial cursor highlights real controls, with finite click rings.
    cursor = None
    click = None
    if stage == 1:
        cursor = (lerp(965, 737, ease((moment - 4.5) / 1.2)), lerp(177, 24, ease((moment - 4.5) / 1.2)))
        if moment > 6.7:
            cursor = (lerp(737, 884, ease((moment - 6.7) / .5)), lerp(24, 52, ease((moment - 6.7) / .5)))
        click = 7.3
    elif stage == 7:
        cursor = (925, 614)
        click = 41.2
    if cursor:
        x, y = cursor
        if click is not None and click <= moment < click + .5:
            phase = (moment - click) / .5
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(160, 245, 193, int(210 * (1 - phase))), 2))
            painter.drawEllipse(QRectF(x - phase * 25, y - phase * 25, phase * 50, phase * 50))
        path = QPainterPath()
        path.moveTo(x, y)
        path.lineTo(x + 4, y + 23)
        path.lineTo(x + 11, y + 17)
        path.lineTo(x + 20, y + 19)
        path.closeSubpath()
        painter.setBrush(QColor("#f7faf9"))
        painter.setPen(QPen(QColor("#183333"), 1.5))
        painter.drawPath(path)
    painter.end()
    return image


def camera(stage, moment):
    """Logical desktop coordinates, with eased zooms rather than static screenshots."""
    progress = moment - SHOTS[stage][0]
    if stage == 0:
        width, x, y = lerp(900, 630, ease(progress / 4)), 700, 185
    elif stage == 1:
        width, x, y = lerp(630, 560, ease(progress / 4.4)), 700, lerp(185, 165, ease(progress / 4.4))
    elif stage == 2:
        width, x, y = lerp(970, 920, ease(progress / 5)), 700, 335
    elif stage == 3:
        width, x, y = lerp(850, 690, ease(progress / 5)), 650, 330
    elif stage == 4:
        width, x, y = lerp(630, 1120, ease(progress / 3.5)), 700, lerp(160, 440, ease(progress / 3.5))
    elif stage == 5:
        width, x, y = lerp(680, 620, ease(progress / 5)), 700, 365
    elif stage == 7:
        width = lerp(1020, 660, ease(progress / 6))
        x = lerp(700, 815, ease(progress / 6))
        y = lerp(360, 435, ease(progress / 6))
    else:
        width, x, y = 720, 700, 320
    top = 0 if stage in {0, 1, 4} else max(0, y - width * (770 / 916) / 2)
    return x - width / 2, top, width, width * (770 / 916)


def draw_caption_layer(painter, stage, moment, language, *, parts=("headline", "footer")):
    """Keep editorial text independent of the native UI's shot dissolve."""
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QColor

    shots = SHOTS_EN if language == "en" else SHOTS
    local = moment - shots[stage][0]
    opacity = ease(local / .44)
    if stage < len(shots) - 1:
        opacity = min(opacity, 1 - ease((moment - shots[stage][1] + .18) / .18))
    shift = 34 * (1 - ease(local / .65))
    accent = "#ba9fff" if stage >= 5 else "#55ef9d"
    painter.setOpacity(opacity)
    if "headline" in parts:
        text(painter, QRectF(82, 292 + shift, 916, 236), shots[stage][2], 76, bold=True)
    if "footer" in parts:
        text(painter, QRectF(82, 1482 + shift * .5, 916, 112), shots[stage][3], 34, "#c4d7de")
        if stage == 8:
            text(painter, QRectF(82, 1596, 916, 86), "github.com/emiryigittt/\nnexus-local-ai-manager", 29, accent, bold=True)
        else:
            for index in range(9):
                color = QColor(accent if index == stage else "#3c5463")
                painter.fillRect(QRectF(82 + index * 38, 1624, 25, 3), color)
    painter.setOpacity(1)


def frame(capture, moment):
    from PyQt6.QtCore import QPointF, QRectF, Qt
    from PyQt6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QRadialGradient
    from PyQt6.QtSvg import QSvgRenderer

    stage = capture.update(moment)
    image = QImage(WIDTH, HEIGHT, QImage.Format.Format_RGB888)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    wallpaper(painter, QRectF(0, 0, WIDTH, HEIGHT), moment, "#ba9fff" if stage >= 5 else "#55ef9d")
    painter.fillRect(QRectF(0, 0, WIDTH, HEIGHT), QColor(4, 8, 15, 120))
    accent = "#ba9fff" if stage >= 5 else "#55ef9d"
    mark = QSvgRenderer(str(ROOT / "frontend/assets/nexus-mark.svg"))
    mark.render(painter, QRectF(82, 160, 44, 44))
    text(painter, QRectF(144, 158, 500, 60), "nexus", 42, bold=True)
    text(painter, QRectF(800, 177, 198, 40), "WINDOWS / LOCAL AI", 18, "#9cb9c6")
    local = moment - SHOTS[stage][0]
    draw_caption_layer(painter, stage, moment, capture.language, parts=("headline",))
    viewport = QRectF(82, 620, 916, 770)
    # Soft editorial depth, a gently moving camera, and ample readable UI pixels.
    for index in range(9, 0, -1):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 9))
        painter.drawRoundedRect(viewport.adjusted(-index * 3, -index * 2, index * 3, index * 4), 34, 34)
    painter.save()
    painter.translate(viewport.center())
    tilt = math.sin(moment * .4) * .38
    painter.rotate(tilt)
    painter.translate(-viewport.center())
    clip = QPainterPath()
    clip.addRoundedRect(viewport, 30, 30)
    painter.setClipPath(clip)
    if stage in {6, 8}:
        painter.fillRect(viewport, QColor("#0c1720"))
        halo = QRadialGradient(QPointF(540, 940), 440)
        halo.setColorAt(0, QColor(186, 159, 255, 80))
        halo.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(viewport, halo)
        if stage == 6:
            cast = transparent_widget(capture.cast)
            width = lerp(850, 980, ease(local / 5))
            painter.drawImage(QRectF(540 - width / 2, 716, width, width * cast.height() / cast.width()), cast)
            mode = (capture.copy("HAZIR", "READY") if moment < 32.1 else
                    capture.copy("DİNLİYOR", "LISTENING") if moment < 33.8 else
                    capture.copy("DÜŞÜNÜYOR", "THINKING") if moment < 35.3 else capture.copy("KONUŞUYOR", "SPEAKING"))
            text(painter, QRectF(152, 1188, 776, 65), mode, 29, accent, bold=True, center=True)
            text(painter, QRectF(152, 1274, 776, 64), capture.copy("Gerçek durumlara tepki veren animasyonlar", "Animations that follow the app's activity"), 24, "#a8c3cc", center=True)
        else:
            mark.render(painter, QRectF(430, 670, 220, 220))
            text(painter, QRectF(130, 936, 820, 180), "Nexus", 122, bold=True, center=True)
            text(painter, QRectF(146, 1113, 788, 64), "Ollama  /  LM Studio  /  llama.cpp", 27, "#b8d0da", center=True)
            painter.setPen(QPen(QColor("#658277"), 1))
            painter.setBrush(QColor("#172e2b"))
            painter.drawRoundedRect(QRectF(213, 1204, 654, 84), 20, 20)
            text(painter, QRectF(233, 1225, 568, 55), capture.copy("GitHub'da projeyi keşfet", "Explore the project on GitHub"), 29, "#c6f6de", bold=True, center=True)
            painter.setPen(QPen(QColor("#c6f6de"), 2.2))
            painter.drawLine(796, 1260, 812, 1244)
            painter.drawLine(800, 1244, 812, 1244)
            painter.drawLine(812, 1244, 812, 1256)
    elif stage == 0 and moment < 1.85:
        painter.fillRect(viewport, QColor("#0c1720"))
        halo = QRadialGradient(QPointF(540, 945), 410)
        halo.setColorAt(0, QColor(85, 239, 157, 50))
        halo.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(viewport, halo)
        avatar = transparent_widget(capture.robot)
        scale = lerp(650, 540, ease(moment / 1.85))
        painter.drawImage(QRectF(540 - scale / 2, 645, scale, scale), avatar)
        text(painter, QRectF(152, 1225, 776, 65), capture.copy("Yerel modelin, masaüstünde.", "Your local model, on your desktop."), 30, accent, bold=True, center=True)
    elif stage == 3:
        painter.fillRect(viewport, QColor("#111416"))
        painter.setOpacity(.15)
        halo = QRadialGradient(QPointF(880, 860), 420)
        halo.setColorAt(0, QColor("#55ef9d"))
        halo.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(viewport, halo)
        painter.setOpacity(1)
        text(painter, QRectF(130, 670, 820, 65), capture.copy("AURORA / ÖRNEK BELGE", "AURORA / SAMPLE DOCUMENT"), 24, accent, bold=True)
        output = capture.window.output_browser.grab().toImage()
        scale = min(824 / (output.width() / 2), 525 / (output.height() / 2))
        painter.drawImage(QRectF(130, 776, output.width() / 2 * scale, output.height() / 2 * scale), output)
        hero = transparent_widget(capture.window.activity_logo)
        painter.drawImage(QRectF(842, 668, 95, 95), hero)
        text(painter, QRectF(130, 1310, 824, 45), capture.copy("Belgenin içinden üç somut öncelik.", "Three concrete priorities from your document."), 25, "#9fbdbb")
    else:
        rendered = desktop(capture, moment, stage)
        x, y, width, height = camera(stage, moment)
        painter.drawImage(viewport, rendered, QRectF(x * 2, y * 2, width * 2, height * 2))
    painter.restore()
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor(177, 211, 224, 55), 1.5))
    painter.drawRoundedRect(viewport, 30, 30)
    draw_caption_layer(painter, stage, moment, capture.language, parts=("footer",))
    text(painter, QRectF(82, 1718, 916, 70), capture.copy("Gerçek arayüz · örnek içerik ve durumlar\nWindows için geliştirme önizlemesi", "Real interface · sample content and activity\nDevelopment preview for Windows"), 21, "#8eaebd")
    painter.end()
    return image


class FilmDirector:
    """Blend native UI shots through a gently eased 550 ms depth transition."""

    def __init__(self):
        self.key = None
        self.previous = None
        self.outgoing = None
        self.start = 0.

    def compose(self, image, stage, moment):
        from PyQt6.QtCore import QRectF
        from PyQt6.QtGui import QPainter

        key = (stage, stage == 0 and moment < 1.85)
        if key != self.key:
            self.outgoing = self.previous
            self.key = key
            self.start = moment
        result = image
        if self.outgoing is not None and moment - self.start < .55:
            progress = ease((moment - self.start) / .55)
            result = image.copy()
            painter = QPainter(result)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            region = QRectF(63, 588, 954, 832)
            painter.setClipRect(region)
            # Start with the outgoing page at full opacity, so alpha never dips
            # through black. Dissolve the incoming camera view with a subtle
            # settling zoom; the persistent logo/header remains steady.
            painter.drawImage(0, 0, self.outgoing)
            painter.setOpacity(progress)
            scale = 1 + .014 * (1 - progress)
            painter.drawImage(QRectF((WIDTH - WIDTH * scale) / 2, (HEIGHT - HEIGHT * scale) / 2,
                                    WIDTH * scale, HEIGHT * scale), image)
            painter.end()
        self.previous = image
        return result


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    return f"00:{milliseconds // 60000:02}:{milliseconds // 1000 % 60:02},{milliseconds % 1000:03}"


def polish_cached_captions(work, language):
    """Refresh only caption bands around cuts while preserving the filmed UI."""
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QColor, QImage, QPainter

    source = work / "social-picture.mp4"
    target = work / "social-picture-polished.mp4"
    with av.open(str(source)) as incoming, av.open(str(target), "w") as outgoing:
        stream = outgoing.add_stream("libx264", rate=FPS)
        stream.width, stream.height, stream.pix_fmt = WIDTH, HEIGHT, "yuv420p"
        stream.options = {"crf": "16", "preset": "fast", "threads": "4"}
        stream.codec_context.color_primaries = 1
        stream.codec_context.color_trc = 1
        stream.codec_context.colorspace = 1
        for index, decoded in enumerate(incoming.decode(video=0)):
            moment = index / FPS
            stage = max(i for i, shot in enumerate(SHOTS) if moment >= shot[0])
            pixels = decoded.to_ndarray(format="rgb24")
            image = QImage(pixels.tobytes(), WIDTH, HEIGHT, WIDTH * 3, QImage.Format.Format_RGB888).copy()
            if any(begin - .18 <= moment <= begin + .55 for begin, *_ in SHOTS[1:]):
                clean = QImage(WIDTH, HEIGHT, QImage.Format.Format_RGB888)
                layer = QPainter(clean)
                layer.setRenderHint(QPainter.RenderHint.Antialiasing)
                wallpaper(layer, QRectF(0, 0, WIDTH, HEIGHT), moment, "#ba9fff" if stage >= 5 else "#55ef9d")
                layer.fillRect(QRectF(0, 0, WIDTH, HEIGHT), QColor(4, 8, 15, 120))
                draw_caption_layer(layer, stage, moment, language)
                layer.end()
                painter = QPainter(image)
                for region in (QRectF(0, 265, WIDTH, 323), QRectF(0, 1430, WIDTH, 260)):
                    painter.drawImage(region, clean, region)
                painter.end()
            array = np.frombuffer(image.constBits().asstring(image.sizeInBytes()), dtype=np.uint8)
            array = array.reshape(HEIGHT, image.bytesPerLine())[:, :WIDTH * 3].reshape(HEIGHT, WIDTH, 3)
            picture = av.VideoFrame.from_ndarray(array, format="rgb24").reformat(format="yuv420p", dst_colorspace="ITU709")
            picture.pts, picture.time_base = index, Fraction(1, FPS)
            for packet in stream.encode(picture):
                outgoing.mux(packet)
        for packet in stream.encode():
            outgoing.mux(packet)
    # Keep the previous picture recoverable; these are explicit workspace files.
    source.replace(work / "social-picture-before-caption-polish.mp4")
    target.replace(source)


def render(args):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["QT_SCALE_FACTOR"] = "2"
    os.environ["NEXUS_TTS_ENABLED"] = "0"
    from PyQt6.QtGui import QFontDatabase
    from PyQt6.QtWidgets import QApplication

    args.output.mkdir(parents=True, exist_ok=True)
    work = ROOT / "build/social-film-v2" / args.language
    work.mkdir(parents=True, exist_ok=True)
    if args.narration and args.language != "tr":
        raise ValueError("Narration is Turkish only; the bilingual films use music and effects")
    if args.polish_captions:
        app = QApplication([])
        fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for name in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf"):
            QFontDatabase.addApplicationFont(str(fonts / name))
        polish_cached_captions(work, args.language)
        finish(work, args.output, narration=False, language=args.language)
        return
    if args.narration:
        generate_narration(work)
    if args.remix_only:
        finish(work, args.output, narration=args.narration, language=args.language)
        return
    with tempfile.TemporaryDirectory(prefix="nexus-film-ui-") as temporary:
        os.environ["NEXUS_DATA_DIR"] = temporary
        # Narration imports the preference module before its separate temp folder
        # closes. Rebind the store to this recording's isolated folder.
        import backend.user_settings as recording_preferences

        recording_preferences.settings_store = recording_preferences.SettingsStore()
        app = QApplication([])
        app.setQuitOnLastWindowClosed(False)
        fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for name in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf"):
            if (fonts / name).exists():
                QFontDatabase.addApplicationFont(str(fonts / name))
        capture = Capture(app, temporary, args.language)
        if args.preview:
            reviews = {int(moment * FPS): moment for moment in (1., 2.2, 7.7, 12.4, 17.7, 22.8, 29.9, 35.7, 42., 47.5)}
            for index in range(FPS * SECONDS):
                moment = index / FPS
                capture.update(moment)
                if index in reviews:
                    frame(capture, moment).save(str(work / f"review-{reviews[index]:04.1f}.png"))
            capture.close()
            print(work.resolve(), flush=True)
            return
        raw_video = work / "social-picture.mp4"
        director = FilmDirector()
        with av.open(str(raw_video), "w") as container:
            stream = container.add_stream("libx264", rate=FPS)
            stream.width, stream.height, stream.pix_fmt = WIDTH, HEIGHT, "yuv420p"
            stream.options = {"crf": "16", "preset": "medium", "threads": "4"}
            stream.codec_context.color_primaries = 1
            stream.codec_context.color_trc = 1
            stream.codec_context.colorspace = 1
            previous = -1
            for index in range(SECONDS * FPS):
                moment = index / FPS
                image = frame(capture, moment)
                image = director.compose(image, capture.last_stage, moment)
                if capture.last_stage != previous:
                    previous = capture.last_stage
                    print(f"Picture {previous + 1}/9, {SHOTS[previous][0]}–{SHOTS[previous][1]}s", flush=True)
                if index in {int(value * FPS) for value in (2.2, 7.7, 12.4, 17.7, 22.8, 29.9, 35.7, 42., 47.5)}:
                    image.save(str(args.output / f"nexus-film-{args.language}-scene-{previous + 1:02}.png"))
                if index == FPS:
                    image.save(str(args.output / f"nexus-social-cover-{args.language}.png"))
                pixels = np.frombuffer(image.constBits().asstring(image.sizeInBytes()), dtype=np.uint8)
                pixels = pixels.reshape(HEIGHT, image.bytesPerLine())[:, :WIDTH * 3].reshape(HEIGHT, WIDTH, 3)
                picture = av.VideoFrame.from_ndarray(pixels, format="rgb24")
                picture = picture.reformat(format="yuv420p", dst_colorspace="ITU709")
                picture.pts, picture.time_base = index, Fraction(1, FPS)
                for packet in stream.encode(picture):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)
        capture.close()
    finish(work, args.output, narration=args.narration, language=args.language)


def finish(work, output, *, narration, language="tr"):
    raw_video = work / "social-picture.mp4"
    if not raw_video.exists():
        raise FileNotFoundError("Render the film before remixing its soundtrack")
    soundtrack = create_audio(work, narration=narration)
    name = f"nexus-social-film-{language}-50s-v2.mp4"
    result = output / name
    subprocess.run([shutil.which("ffmpeg"), "-v", "error", "-y", "-i", str(raw_video), "-i", str(soundtrack),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
                    "-movflags", "+faststart", "-t", str(SECONDS), str(result)], check=True)
    subtitles = []
    for i, (begin, end, title, body, spoken) in enumerate(SHOTS_EN if language == "en" else SHOTS, 1):
        words = spoken.replace("Neksus", "Nexus") if narration else title.replace("\n", " ") + " " + body
        subtitles.append(f"{i}\n{timestamp(begin)} --> {timestamp(end)}\n{textwrap.fill(words, width=45)}\n")
    result.with_suffix(".srt").write_text("\n".join(subtitles), encoding="utf-8")
    metadata = {"file": name, "language": language, "version": 2, "width": WIDTH, "height": HEIGHT, "fps": FPS, "seconds": SECONDS,
                "actual_ui": "2x density Qt widgets, deterministic native animation properties",
                "content": "fictional Aurora fixture; no live model inference or microphone capture",
                "audio": "original electronic score, rounded low-mid impacts with dark stereo echoes; no page sweep" + (", local Supertonic Turkish stock narration" if narration else ""),
                "motion": "quintic camera easing, paused deterministic native window animation at 440 ms, 550 ms UI dissolves with independent caption fades",
                "reference": "motion pacing and low-mid sound character only; no copied video or audio", "publicly_posted": False}
    result.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(result.resolve(), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/launch/social-film-v2")
    parser.add_argument("--language", choices=("tr", "en"), default="tr")
    parser.add_argument("--polish-captions", action="store_true", help="Polish independent caption motion in an existing picture")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--narration", action="store_true")
    parser.add_argument("--remix-only", action="store_true", help="Reuse the rendered picture for an alternative soundtrack")
    render(parser.parse_args())


if __name__ == "__main__":
    main()
