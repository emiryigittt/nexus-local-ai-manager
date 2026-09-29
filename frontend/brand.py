"""Vector brand artwork shared by desktop, tray and export previews."""

from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtSvg import QSvgRenderer

ACCENT = "#55ef9d"
ACCENT_HOVER = "#8bf7b9"
MARK_PATH = Path(__file__).resolve().parent / "assets" / "nexus-mark.svg"


@lru_cache(maxsize=1)
def mark_source():
    return MARK_PATH.read_bytes()


@lru_cache(maxsize=1)
def ribbon_sources():
    sources = []
    for index in (0, 1):
        root = ElementTree.fromstring(mark_source())
        paths = root.findall("{http://www.w3.org/2000/svg}path")
        root.remove(paths[1 - index])
        sources.append(ElementTree.tostring(root))
    return tuple(sources)


def mark_pixmap(size, *, color=None):
    """Transparent vector mark. A solid tint is useful for inactive tray states."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    QSvgRenderer(mark_source()).render(painter, QRectF(0, 0, size, size))
    if color:
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(color))
    painter.end()
    return pixmap


def brand_pixmap(size, *, tile=True, active=None):
    """App tile or transparent logo; only explicit True means wake is listening."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    if tile:
        painter.setPen(QPen(QColor("#3c5b4b"), max(1, size / 96)))
        painter.setBrush(QColor("#1b3025"))
        inset = max(0.5, size / 128)
        painter.drawRoundedRect(QRectF(inset, inset, size - 2 * inset, size - 2 * inset),
                                size * 0.23, size * 0.23)
    painter.drawPixmap(0, 0, mark_pixmap(size, color="#a1aaa5" if active is False else None))
    if active is not None:
        radius = size * 0.115
        center = size * 0.81
        painter.setPen(QPen(QColor("#15231b"), max(1.2, size * 0.04)))
        painter.setBrush(QColor(ACCENT if active else "#56615b"))
        painter.drawEllipse(QRectF(center - radius, center - radius, 2 * radius, 2 * radius))
    painter.end()
    return pixmap


def brand_icon(*, tile=True, active=None):
    result = QIcon()
    for size in ((16, 24, 32, 48) if active is not None else (16, 24, 32, 48, 64, 128, 256)):
        result.addPixmap(brand_pixmap(size, tile=tile, active=active))
    return result
