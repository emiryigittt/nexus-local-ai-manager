"""Render labelled EN/TR interface teasers from reviewed synthetic UI previews.

Uses existing PyQt6/numpy and optional PyAV, already installed with faster-whisper.
No model calls, microphone access, personal settings, or desktop capture.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import av
import numpy as np
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QImage, QPainter, QPen, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, FPS = 1600, 900, 24
ACCENT = "#55ef9d"
REPO = "github.com/emiryigittt/nexus-local-ai-manager"
COPY = {
    "en": {
        "label": "INTERFACE PREVIEW · SAMPLE CONTENT · NO LIVE MODEL RUN",
        "preview": "Windows · Development preview · Source installation",
        "scenes": [
            (6, "NEXUS", "Your local model.\nOne shortcut away.",
             "An open-source desktop assistant for Windows.", None,
             "Your local model. One shortcut away. Meet Nexus for Windows."),
            (9, "01 / YOUR MODEL", "Make your model\npart of your day.",
             "Connect Ollama, LM Studio or llama.cpp.\nOpen Nexus with Alt + Space.", "welcome",
             "Connect your existing local model and open Nexus with Alt + Space."),
            (9, "02 / YOUR WORK", "Bring context\nto the conversation.",
             "Ask questions, attach documents,\nand work in one compact window.", "response",
             "Ask questions and bring document context into your conversation. The answer shown is sample content."),
            (9, "03 / YOUR CONTROL", "Keep memory\nin your hands.",
             "Review, approve, edit or forget memories.\nAutomatic learning needs separate consent.", "privacy",
             "Control saved memory and give separate consent for automatic learning."),
            (8, "04 / YOUR VOICE", "Choose how\nyou talk to Nexus.",
             "Voice is optional. Choose local speech\nor consent-based cloud speech.", "voice-output",
             "Voice is optional. Choose a local speech engine or separately consent to cloud speech."),
            (7, "HELP SHAPE NEXUS", "Looking for\n10 early testers.",
             "Already using Windows and a local model?\nTry setup and one document workflow.", None,
             "Looking for ten Windows users to try setup and one document workflow. Visit the GitHub repository."),
        ],
    },
    "tr": {
        "label": "ARAYÜZ TANITIMI · ÖRNEK İÇERİK · CANLI MODEL ÇALIŞMASI DEĞİL",
        "preview": "Windows · Geliştirme önizlemesi · Kaynak koddan kurulum",
        "scenes": [
            (6, "NEXUS", "Yerel modelin.\nTek kısayol uzağında.",
             "Windows için açık kaynaklı masaüstü asistanı.", None,
             "Yerel modelin, tek kısayol uzağında. Windows için Nexus ile tanış."),
            (9, "01 / MODELİN", "Modelini günlük\nişlerine taşı.",
             "Ollama, LM Studio veya llama.cpp bağla.\nAlt + Space ile Nexus'u aç.", "welcome",
             "Çalışan yerel modelini bağla ve Alt + Space ile Nexus'u aç."),
            (9, "02 / İŞLERİN", "Sohbetine\nbağlam ekle.",
             "Sorunu sor, belgeni ekle,\ntek bir masaüstü penceresinde çalış.", "response",
             "Sorularını ve belge bağlamını sohbetine getir. Görünen yanıt örnek içeriktir."),
            (9, "03 / KONTROLÜN", "Hafızanın\nkontrolü sende.",
             "Kayıtları incele, onayla, düzenle veya unuttur.\nOtomatik öğrenme için ayrı izin ver.", "privacy",
             "Kayıtlı hafızayı yönet. Otomatik öğrenme için ayrı izin ver."),
            (8, "04 / SESİN", "Nasıl konuşacağını\nsen seç.",
             "Ses isteğe bağlı. Yerel ses motorunu\nveya izinli bulut sesini seç.", "voice-output",
             "Ses isteğe bağlı. Yerel ses motorunu veya ayrıca izin verdiğin bulut sesini seç."),
            (7, "NEXUS'U BİRLİKTE GELİŞTİRELİM", "İlk 10 kullanıcıyı\narıyoruz.",
             "Windows ve yerel model kullanıyorsan\nkurulumu ve bir belge akışını dene.", None,
             "Kurulumu ve bir belge akışını deneyecek ilk on Windows kullanıcısını arıyoruz. GitHub deposuna göz at."),
        ],
    },
}


def font(size: int, bold: bool = False) -> QFont:
    result = QFont("Segoe UI")
    result.setPixelSize(size)
    result.setWeight(QFont.Weight.DemiBold if bold else QFont.Weight.Normal)
    return result


def text(painter, rect, value, size, color="#f1f5f2", bold=False):
    painter.setFont(font(size, bold))
    painter.setPen(QColor(color))
    flags = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap
    bounds = painter.boundingRect(rect, int(flags), value)
    if bounds.height() > rect.height() + 2:
        raise ValueError(f"Text exceeds its frame: {value}")
    painter.drawText(rect, int(flags), value)


def render(language, index, progress, pictures, logo):
    copy = COPY[language]
    _, eyebrow, title, body, picture, _ = copy["scenes"][index]
    image = QImage(WIDTH, HEIGHT, QImage.Format.Format_RGB888)
    image.fill(QColor("#101614"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.setPen(QPen(QColor("#23372b"), 1))
    for x in range(0, WIDTH, 80):
        painter.drawLine(x, 0, x, HEIGHT)
    for y in range(0, HEIGHT, 80):
        painter.drawLine(0, y, WIDTH, y)
    painter.fillRect(QRectF(0, 0, WIDTH, 92), QColor("#101614"))
    logo.render(painter, QRectF(60, 28, 40, 40))
    text(painter, QRectF(115, 27, 200, 48), "nexus", 30, bold=True)
    text(painter, QRectF(940, 34, 600, 30), copy["preview"], 18, "#a1aaa5")
    entrance = min(1.0, progress / 0.6)
    painter.setOpacity(entrance)
    shift = 18 * (1 - entrance) ** 2
    if picture:
        text(painter, QRectF(70, 188 + shift, 600, 40), eyebrow, 21, ACCENT, True)
        text(painter, QRectF(70, 266 + shift, 610, 235), title, 58, bold=True)
        text(painter, QRectF(70, 530 + shift, 600, 170), body, 27, "#b9c7be")
        pixmap = pictures[picture]
        available = QRectF(735, 132 + shift, 805, 674)
        scaled = pixmap.scaled(int(available.width()), int(available.height()),
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        x = available.x() + (available.width() - scaled.width()) / 2
        y = available.y() + (available.height() - scaled.height()) / 2
        painter.drawPixmap(int(x), int(y), scaled)
    else:
        logo.render(painter, QRectF(70, 172 + shift, 104, 104))
        text(painter, QRectF(70, 308 + shift, 1400, 40), eyebrow, 23, ACCENT, True)
        text(painter, QRectF(70, 383 + shift, 1440, 220), title, 79, bold=True)
        text(painter, QRectF(70, 639 + shift, 1400, 96), body, 31, "#b9c7be")
        if index == len(copy["scenes"]) - 1:
            text(painter, QRectF(70, 755, 1440, 48), REPO, 28, ACCENT, True)
    painter.setOpacity(1)
    painter.fillRect(QRectF(0, HEIGHT - 61, WIDTH, 61), QColor("#17251c"))
    text(painter, QRectF(70, HEIGHT - 45, 1450, 30), copy["label"], 19, "#a9c8b4")
    total = sum(scene[0] for scene in copy["scenes"])
    elapsed = sum(scene[0] for scene in copy["scenes"][:index]) + progress
    painter.fillRect(QRectF(0, HEIGHT - 4, WIDTH * elapsed / total, 4), QColor(ACCENT))
    painter.end()
    return image


def timestamp(seconds):
    return f"00:{int(seconds) // 60:02}:{int(seconds) % 60:02},000"


def export(language, output):
    pictures = {}
    for name in ("welcome", "response", "privacy", "voice-output"):
        path = ROOT / "docs/assets/localization" / language / f"{name}.png"
        pictures[name] = QPixmap(str(path))
        if pictures[name].isNull():
            raise ValueError(f"Missing reviewed preview: {path}")
    logo = QSvgRenderer(str(ROOT / "frontend/assets/nexus-mark.svg"))
    path = output / f"nexus-intro-{language}.mp4"
    subtitles, elapsed = [], 0
    with av.open(str(path), "w", options={"movflags": "+faststart"}) as container:
        stream = container.add_stream("libx264", rate=FPS)
        stream.width, stream.height, stream.pix_fmt = WIDTH, HEIGHT, "yuv420p"
        stream.options = {"crf": "22", "preset": "fast"}
        frame_index = 0
        for index, scene in enumerate(COPY[language]["scenes"]):
            duration = scene[0]
            middle = render(language, index, min(2.0, duration / 2), pictures, logo)
            middle.save(str(output / f"{language}-scene-{index + 1}.png"))
            subtitles.append(f"{index + 1}\n{timestamp(elapsed)} --> {timestamp(elapsed + duration)}\n{scene[5]}\n")
            for number in range(duration * FPS):
                image = render(language, index, number / FPS, pictures, logo)
                bits = image.bits()
                bits.setsize(image.sizeInBytes())
                pixels = np.frombuffer(bits, dtype=np.uint8).reshape(HEIGHT, image.bytesPerLine())
                pixels = pixels[:, : WIDTH * 3].reshape(HEIGHT, WIDTH, 3)
                frame = av.VideoFrame.from_ndarray(pixels, format="rgb24")
                frame.pts = frame_index
                for packet in stream.encode(frame):
                    container.mux(packet)
                frame_index += 1
            elapsed += duration
            print(f"{language}: scene {index + 1}/6 encoded", flush=True)
        for packet in stream.encode():
            container.mux(packet)
    (output / f"nexus-intro-{language}.srt").write_text("\n".join(subtitles), encoding="utf-8")
    return {"file": path.name, "seconds": elapsed, "width": WIDTH, "height": HEIGHT,
            "fps": FPS, "audio": False, "live_model_run": False, "sample_content": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/launch")
    parser.add_argument("--language", choices=("en", "tr", "both"), default="both")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for name in ("segoeui.ttf", "seguisb.ttf"):
        if (fonts / name).exists():
            QFontDatabase.addApplicationFont(str(fonts / name))
    languages = ("en", "tr") if args.language == "both" else (args.language,)
    results = [export(language, args.output) for language in languages]
    (args.output / "manifest.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    app.quit()
    print(str(args.output.resolve()))


if __name__ == "__main__":
    main()
