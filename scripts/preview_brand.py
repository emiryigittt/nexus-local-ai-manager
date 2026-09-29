"""Render the actual vector logo and native app icons; no user data or AI mockups."""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QColor, QFont, QFontDatabase, QPainter, QPen, QPixmap
    from PyQt6.QtWidgets import QApplication

    from frontend.brand import ACCENT, brand_pixmap, mark_pixmap

    app = QApplication([])
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for name in ("segoeui.ttf", "seguisb.ttf"):
        if (fonts / name).exists():
            QFontDatabase.addApplicationFont(str(fonts / name))
    args.output.mkdir(parents=True, exist_ok=True)
    canvas = QPixmap(1040, 590)
    canvas.fill(QColor("#141b18"))
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    def text(x, y, value, size, color="#e7f3eb", bold=False):
        font = QFont("Segoe UI")
        font.setPixelSize(size)
        font.setWeight(QFont.Weight.DemiBold if bold else QFont.Weight.Normal)
        painter.setFont(font)
        painter.setPen(QColor(color))
        painter.drawText(x, y, value)

    text(48, 52, "NEXUS  /  LINKED RIBBONS", 13, "#93b7a1", True)
    painter.drawPixmap(58, 96, mark_pixmap(236))
    text(344, 208, "nexus", 88, bold=True)
    text(350, 249, "Your local model. One shortcut away.", 18, "#a9b9af")
    for index, color in enumerate((ACCENT, "#16bb75", "#9affbc")):
        painter.setBrush(QColor(color))
        painter.setPen(QPen(QColor(color), 1))
        painter.drawRoundedRect(QRectF(350 + 170 * index, 292, 28, 28), 8, 8)
        text(389 + 170 * index, 312, color.upper(), 14, "#a9b9af")
    painter.setPen(QPen(QColor("#304238"), 1))
    painter.drawLine(48, 370, 992, 370)
    text(48, 410, "APP ICON", 11, "#93b7a1", True)
    painter.drawPixmap(48, 432, brand_pixmap(96))
    text(220, 410, "SMALL SIZES", 11, "#93b7a1", True)
    for x, size in ((220, 16), (284, 24), (360, 32), (450, 64)):
        painter.drawPixmap(x, 480 - size // 2, mark_pixmap(size))
        text(x, 535, f"{size}px", 12, "#93b7a1")
    text(646, 410, "TRAY STATES", 11, "#93b7a1", True)
    painter.drawPixmap(646, 447, brand_pixmap(48, active=False))
    painter.drawPixmap(806, 447, brand_pixmap(48, active=True))
    text(646, 525, "Paused", 13, "#93b7a1")
    text(806, 525, "Listening", 13, "#93b7a1")
    painter.end()
    for name, pixmap in (("brand-board.png", canvas), ("nexus-mark.png", mark_pixmap(512)),
                         ("nexus-app.png", brand_pixmap(512))):
        if not pixmap.save(str(args.output / name)):
            raise RuntimeError(f"Could not save {name}")
    app.processEvents()
    print(args.output.resolve())


if __name__ == "__main__":
    main()
