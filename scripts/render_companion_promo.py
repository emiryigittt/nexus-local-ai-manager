"""A portrait/landscape promo of actual Qt motion, fictional data and original audio.

The app, hover timers, RGB, character and memory approval really run. Model output,
listening and speaking poses are simulated and disclosed on every frame.
"""

import argparse
import json
import math
import os
import tempfile
import time
import wave
from fractions import Fraction
from pathlib import Path

import av
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FPS, SECONDS, RATE = 24, 36, 48000
SCENES = [
    (0, 3, "Az yer kaplar.\nÇok şey yapar.", "Ekranın üstünde küçük bir Nexus.\nÇalışma alanın sana kalsın."),
    (3, 7, "Yaklaş.\nAraçların burada.", "Üzerine gelince mini panel açılır.\nFare uzaklaşınca küçülür; istersen sabitle."),
    (7, 12, "Bir tıkla\nsohbete geç.", "Çalışan yerel modeline bağlan.\nSorularını ve belgelerini beraber getir."),
    (12, 15, "Küçülür.\nİşini sürdürür.", "Görünüm değişse de taslağın ve\nsohbetin yerinde kalır."),
    (15, 21, "Nexus'u\nkendine uyarla.", "RGB renkleri, yavaş kenar ışığı\nve seçilebilir yol arkadaşın."),
    (21, 25, "Küçük bir\nyol arkadaşı.", "Göz kırpar. Dinler. Düşünür. Konuşur.\nKısa ses efektleri de senin kontrolünde."),
    (25, 30, "Neyi hatırlasın?\nKarar senin.", "Hafıza önerilerini incele, onayla,\ndüzenle veya unuttur."),
    (30, 36, "Yerel modelin.\nSenin Nexus'un.", "Windows için geliştirme önizlemesi.\nOllama · LM Studio · llama.cpp"),
]


def soundtrack():
    signal = np.zeros(SECONDS * RATE, dtype=np.float32)
    # An original, quiet pulse and pad; no third-party recording or music sample.
    chords = [(220, 261.63, 329.63), (174.61, 220, 261.63), (196, 246.94, 293.66)]
    for beat in range(SECONDS * 2):
        start = beat * RATE // 2
        count = min(RATE, len(signal) - start)
        times = np.arange(count) / RATE
        note = chords[(beat // 8) % 3][beat % 3] * (2 if beat % 2 else 1)
        envelope = (1 - np.exp(-times * 22)) * np.exp(-times * 4)
        signal[start:start + count] += .035 * np.sin(math.tau * note * times) * envelope
    for second, name in [(7, "open"), (12, "collapse"), (14, "success"), (21, "listen"), (28, "success")]:
        with wave.open(str(ROOT / "frontend/assets/sounds" / f"{name}.wav")) as sound:
            raw = np.frombuffer(sound.readframes(sound.getnframes()), dtype="<i2").astype(np.float32) / 32768
            resampled = np.interp(np.arange(int(len(raw) * RATE / sound.getframerate())) * sound.getframerate() / RATE,
                                  np.arange(len(raw)), raw)
        begin = second * RATE
        signal[begin:begin + len(resampled)] += resampled * .28
    signal *= np.minimum(1, np.arange(len(signal)) / RATE)
    signal *= np.minimum(1, (len(signal) - np.arange(len(signal))) / RATE)
    return np.stack([signal, signal])


def draw_text(painter, rect, value, size, color="#f0f5f4", bold=False):
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QColor, QFont

    font = QFont("Segoe UI")
    font.setPixelSize(size)
    font.setWeight(QFont.Weight.DemiBold if bold else QFont.Weight.Normal)
    painter.setFont(font)
    painter.setPen(QColor(color))
    flags = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap
    bounds = painter.boundingRect(rect, int(flags), value)
    if bounds.height() > rect.height() + 3:
        raise ValueError(f"Promo text exceeds its frame: {value}")
    painter.drawText(rect, int(flags), value)


def export(output, landscape=False):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["NEXUS_TTS_ENABLED"] = "0"
    from PyQt6.QtCore import QPointF, QRectF
    from PyQt6.QtGui import (
        QColor,
        QFontDatabase,
        QImage,
        QPainter,
        QPainterPath,
        QPen,
        QRadialGradient,
    )
    from PyQt6.QtWidgets import QApplication

    with tempfile.TemporaryDirectory(prefix="nexus-companion-promo-") as temporary:
        os.environ["NEXUS_DATA_DIR"] = temporary
        from backend.memory import MemoryRepository
        from backend.user_settings import settings_store
        from frontend.app import SpotlightApp
        from frontend.memory_dialog import MemoryDialog
        from frontend.setup_dialog import SetupDialog

        app = QApplication.instance() or QApplication([])
        app.setQuitOnLastWindowClosed(False)
        fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for name in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf"):
            if (fonts / name).exists():
                QFontDatabase.addApplicationFont(str(fonts / name))
        preferences = settings_store.load()
        preferences.setup_complete = True
        preferences.reduced_motion = False
        preferences.providers[0].selected_model = "Örnek yerel model"
        settings_store.save(preferences)
        window = SpotlightApp()
        pointer = {"inside": False}
        window.notch_controller.pointer_inside = lambda: pointer["inside"]
        window.show()
        window.wake.timer.stop()
        repository = MemoryRepository(Path(temporary) / "fictional-memory.db")
        repository.add("Kısa ve uygulanabilir yanıtları tercih eder.", "preference")
        repository.add("Nexus: kullanımı kolay bir yerel asistan.", "goal")
        candidate, _ = repository.add_candidate("Önce en önemli üç adımı göster.", "instruction", "response.structure")
        settings_dialog = None
        memory_dialog = None
        stage = -1
        approved = False
        frame_shots = {1: "notch", 5: "hover", 10: "chat", 14: "busy-notch", 19: "rgb", 23: "pet", 27: "memory", 33: "outro"}
        captured = set()
        width, height = (1920, 1080) if landscape else (1080, 1920)
        filename = "nexus-promo-landscape-tr.mp4" if landscape else "nexus-promo-reels-tr.mp4"
        path = output / filename
        music = soundtrack()
        with av.open(str(path), "w", options={"movflags": "+faststart"}) as container:
            video = container.add_stream("libx264", rate=FPS)
            video.width, video.height, video.pix_fmt = width, height, "yuv420p"
            video.options = {"crf": "20", "preset": "veryfast"}
            audio = container.add_stream("aac", rate=RATE)
            audio.layout = "stereo"
            audio.bit_rate = 128000
            began = time.perf_counter()
            for index in range(FPS * SECONDS):
                moment = index / FPS
                current = max(i for i, scene in enumerate(SCENES) if moment >= scene[0])
                if current != stage:
                    stage = current
                    print(f"{filename}: scene {stage + 1}/{len(SCENES)}", flush=True)
                    if stage == 1:
                        pointer["inside"] = True
                        window.notch_controller.enter()
                    elif stage == 2:
                        window.open_full_chat()
                        pointer["inside"] = False
                        window._show_output()
                        window.input_line.setText("Sonra bunu haftalık plana dönüştür.")
                        window.question_label.setText("Daha odaklı çalışmak için nereden başlayayım?")
                        window._response_complete = False
                        window._refresh_visual_activity()
                        window.update_status("Örnek yanıt hazırlanıyor…")
                        window.append_response("## Küçük adımlar, daha net bir gün\n\nÖnce bugün fark yaratacak **bir işi** seç.\n\n1. Bildirimlerini kısa süreli kapat.\n2. 45 dakikalık bir odak aralığı ayır.\n3. Gün sonunda yarının ilk adımını yaz.")
                    elif stage == 3:
                        window.collapse_to_notch()
                    elif stage == 4:
                        settings_dialog = SetupDialog(parent=window)
                        settings_dialog.tabs.setCurrentIndex(3)
                        settings_dialog.show()
                    elif stage == 5:
                        settings_dialog.save()
                        preferences = settings_store.load()
                        window.apply_appearance(preferences)
                        window.set_shell_mode("dock")
                        window._recording_ready = True
                        window._refresh_visual_activity()
                    elif stage == 6:
                        window._recording_ready = False
                        window._refresh_visual_activity()
                        memory_dialog = MemoryDialog(repository, parent=window, focus_memory_id=candidate)
                        memory_dialog.show()
                    elif stage == 7:
                        memory_dialog.close()
                        window.set_shell_mode("notch")
                        window.notch_avatar.set_mode("idle")
                if stage == 3 and moment >= 14 and not window._response_complete:
                    window.complete_response()
                if stage == 4:
                    if moment >= 17:
                        settings_dialog.appearance.set_color("#ba9fff")
                    if moment >= 18:
                        settings_dialog.appearance.character.setCurrentIndex(1)
                        settings_dialog.appearance.rgb.setChecked(True)
                if stage == 5 and moment >= 23:
                    window._recording_ready = False
                    window.dock_avatar.set_mode("speaking")
                    window.dock_title.setText("Nexus konuşuyor")
                    window.dock_status.setText("Örnek seslendirme durumu")
                if stage == 6 and moment >= 28 and not approved:
                    memory_dialog.activate_button.click()
                    approved = True
                delay = began + index / FPS - time.perf_counter()
                if delay > 0:
                    time.sleep(delay)
                app.processEvents()
                canvas = QImage(width, height, QImage.Format.Format_RGB888)
                canvas.fill(QColor("#0b0e13"))
                painter = QPainter(canvas)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                tint = "#ba9fff" if stage >= 4 else "#55ef9d"
                gradient = QRadialGradient(width * .9, height * .35, width * .85)
                center = QColor(tint)
                center.setAlpha(28)
                gradient.setColorAt(0, center)
                gradient.setColorAt(1, QColor(0, 0, 0, 0))
                painter.fillRect(canvas.rect(), gradient)
                painter.setPen(QPen(QColor("#1a2027"), 1))
                for y in range(0, height, 96):
                    painter.drawLine(0, y, width, y)
                progress = moment - SCENES[stage][0]
                entrance = min(1, progress / .45)
                shift = 24 * (1 - entrance) ** 3
                painter.setOpacity(entrance)
                draw_text(painter, QRectF(72, 64, 650, 60), "nexus / WINDOWS COMPANION", 27, tint, True)
                title_rect = QRectF(72, 165 + shift, 936, 270) if not landscape else QRectF(76, 228 + shift, 680, 260)
                draw_text(painter, title_rect, SCENES[stage][2], 84 if not landscape else 74, bold=True)
                body_rect = QRectF(72, 1440 + shift, 940, 180) if not landscape else QRectF(76, 565 + shift, 650, 165)
                draw_text(painter, body_rect, SCENES[stage][3], 34 if not landscape else 31, "#aebdc5")
                painter.setOpacity(1)
                desktop = QRectF(48, 535, 984, 750) if not landscape else QRectF(825, 142, 1035, 756)
                painter.setBrush(QColor("#141b22"))
                painter.setPen(QPen(QColor("#34414a"), 2))
                painter.drawRoundedRect(desktop, 20, 20)
                painter.save()
                clip = QPainterPath()
                clip.addRoundedRect(desktop.adjusted(1, 1, -1, -1), 19, 19)
                painter.setClipPath(clip)
                # Generic illustrative wallpaper, not a captured user's desktop.
                draw_text(painter, desktop.adjusted(130, 290, -70, -100), "Çalışma alanın\nsana kalsın.", 46, "#3c4b56", True)
                pixmap = window.grab()
                if stage == 4:
                    pixmap = settings_dialog.grab()
                elif stage == 6:
                    pixmap = memory_dialog.grab()
                if stage in {4, 6}:
                    scale = min((desktop.width() - 48) / pixmap.width(), (desktop.height() - 32) / pixmap.height())
                    destination = QRectF(desktop.center().x() - pixmap.width() * scale / 2,
                                         desktop.top() + 16, pixmap.width() * scale, pixmap.height() * scale)
                else:
                    scale = min(1, (desktop.width() - 60) / 800)
                    destination = QRectF(desktop.center().x() - pixmap.width() * scale / 2,
                                         desktop.top(), pixmap.width() * scale, pixmap.height() * scale)
                painter.drawPixmap(destination.toRect(), pixmap)
                if stage in {1, 2}:
                    cursor_x = desktop.center().x() + 48
                    cursor_y = desktop.top() + 22
                    if stage == 1:
                        cursor_x += 170 * (1 - min(1, progress / .4))
                        cursor_y += 90 * (1 - min(1, progress / .4))
                    painter.setOpacity(max(0, 1 - max(0, progress - 1)))
                    cursor = QPainterPath(QPointF(cursor_x, cursor_y))
                    cursor.lineTo(cursor_x + 4, cursor_y + 26)
                    cursor.lineTo(cursor_x + 11, cursor_y + 20)
                    cursor.lineTo(cursor_x + 21, cursor_y + 22)
                    cursor.closeSubpath()
                    painter.setPen(QPen(QColor("#101318"), 2))
                    painter.setBrush(QColor("#f0f3f5"))
                    painter.drawPath(cursor)
                    painter.setOpacity(1)
                painter.restore()
                small_y = 1330 if not landscape else 936
                draw_text(painter, QRectF(72, small_y, width - 120, 40), "ÜST ŞERİT   /   SOHBET   /   RGB   /   KİŞİSEL HAFIZA", 21, tint, True)
                if stage == 7:
                    draw_text(painter, QRectF(72, 1650 if not landscape else 790, 740, 90),
                              "GitHub'da keşfet\nemiryigittt/nexus-local-ai-manager", 25, tint, True)
                label_y = height - 95
                draw_text(painter, QRectF(72, label_y, width - 130, 58),
                          "Gerçek arayüz · örnek içerik ve durumlar\nCanlı model veya mikrofon kaydı değildir.", 20, "#8396a2")
                painter.fillRect(QRectF(0, height - 4, width * moment / SECONDS, 4), QColor(tint))
                painter.end()
                second = int(moment)
                if second in frame_shots and second not in captured:
                    canvas.save(str(output / f"{path.stem}-{frame_shots[second]}.png"))
                    captured.add(second)
                pixels = np.frombuffer(canvas.constBits().asstring(canvas.sizeInBytes()), dtype=np.uint8)
                pixels = pixels.reshape(height, canvas.bytesPerLine())[:, :width * 3].reshape(height, width, 3)
                frame = av.VideoFrame.from_ndarray(pixels, format="rgb24")
                frame.pts, frame.time_base = index, Fraction(1, FPS)
                for packet in video.encode(frame):
                    container.mux(packet)
                count = RATE // FPS
                audio_frame = av.AudioFrame.from_ndarray(np.ascontiguousarray(music[:, index * count:(index + 1) * count]),
                                                        format="fltp", layout="stereo")
                audio_frame.sample_rate, audio_frame.pts, audio_frame.time_base = RATE, index * count, Fraction(1, RATE)
                for packet in audio.encode(audio_frame):
                    container.mux(packet)
            for stream in (video, audio):
                for packet in stream.encode():
                    container.mux(packet)
        if settings_dialog:
            settings_dialog.close()
        if memory_dialog:
            memory_dialog.close()
        window.close()
        app.processEvents()
        captions = []
        for i, (start, end, title, body) in enumerate(SCENES, 1):
            captions.append(f"{i}\n00:00:{start:02},000 --> 00:00:{end:02},000\n{title.replace(chr(10), ' ')}\n{body.replace(chr(10), ' ')}\n")
        path.with_suffix(".srt").write_text("\n".join(captions), encoding="utf-8")
        result = {"file": filename, "width": width, "height": height, "fps": FPS, "seconds": SECONDS,
                  "audio": "original synthesized music and Nexus chimes", "sample_content": True, "live_inference": False,
                  "recording": "actual offscreen Qt animations; generic illustrative desktop"}
        path.with_suffix(".json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(path.resolve(), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/launch")
    parser.add_argument("--landscape", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    export(args.output, args.landscape)


if __name__ == "__main__":
    main()
