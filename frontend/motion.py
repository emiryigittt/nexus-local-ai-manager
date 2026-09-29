"""Small, state-driven vector animations; no playback files or background timers."""

import math

from PyQt6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    Qt,
    pyqtProperty,
)
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QWidget

from frontend.brand import ACCENT, ribbon_sources


class MotionLogo(QWidget):
    DURATIONS = {"entrance": 650, "listening": 2200, "thinking": 1600}

    def __init__(self, size=52, *, tile=True, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.tile = tile
        self.mode = "idle"
        self.reduced = False
        self._phase = 1.0
        self.layers = [QSvgRenderer(source, self) for source in ribbon_sources()]
        self.animation = QPropertyAnimation(self, b"phase", self)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.Linear)
        self.animation.finished.connect(self._settled)

    @pyqtProperty(float)
    def phase(self):
        return self._phase

    @phase.setter
    def phase(self, value):
        self._phase = max(0.0, min(1.0, value))
        self.update()

    def set_mode(self, mode):
        if mode not in {"idle", "entrance", "listening", "thinking"}:
            raise ValueError("Unknown visual activity")
        if mode == self.mode:
            return
        self.animation.stop()
        self.mode = mode
        self.phase = 1.0 if mode in {"idle", "entrance"} else 0.0
        self._sync()

    def reveal(self):
        if self.mode in {"idle", "entrance"} and not self.reduced:
            self.mode = "idle"
            self.set_mode("entrance")

    def set_reduced_motion(self, reduced):
        self.reduced = bool(reduced)
        self.animation.stop()
        self.phase = 1.0 if self.mode == "entrance" else 0.0
        self._sync()

    def _sync(self):
        if self.reduced or not self.isVisible() or self.mode == "idle":
            return
        if self.animation.state() != QAbstractAnimation.State.Running:
            self.animation.setDuration(self.DURATIONS[self.mode])
            self.animation.setLoopCount(1 if self.mode == "entrance" else -1)
            self.animation.start()

    def _settled(self):
        if self.mode == "entrance":
            self.mode = "idle"
            self.phase = 1.0

    def showEvent(self, event):
        super().showEvent(event)
        self._sync()

    def hideEvent(self, event):
        self.animation.stop()
        super().hideEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = self.width()
        if self.tile:
            painter.setPen(QPen(QColor("#3c5b4b"), 1))
            painter.setBrush(QColor("#1b3025"))
            painter.drawRoundedRect(QRectF(1, 1, size - 2, size - 2), size * .23, size * .23)
        phase = 0.0 if self.reduced else self.phase
        if self.mode in {"listening", "thinking"}:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            color = QColor(ACCENT)
            pulse = .5 - .5 * math.cos(phase * math.tau)
            color.setAlphaF(.3 + .45 * pulse if self.mode == "listening" else .75)
            painter.setPen(QPen(color, 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            ring = QRectF(2, 2, size - 4, size - 4)
            if self.mode == "listening":
                painter.drawRoundedRect(ring, size * .25, size * .25)
            else:
                painter.drawArc(ring, int(-phase * 360 * 16), 100 * 16)
        progress = 1 - (1 - phase) ** 3
        separation = size * .12 * (1 - progress) if self.mode == "entrance" and not self.reduced else 0
        painter.setOpacity(.35 + .65 * progress if separation else 1)
        inset = size * .12 if self.mode == "thinking" else 0
        for layer, sign in zip(self.layers, (-1, 1), strict=True):
            layer.render(painter, QRectF(inset + sign * separation, inset + sign * separation,
                                        size - 2 * inset, size - 2 * inset))
        painter.end()
