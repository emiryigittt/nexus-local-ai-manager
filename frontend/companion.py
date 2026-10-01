"""A visible companion stage with calm breathing, blinks and finite reactions."""

import math

from PyQt6.QtCore import QPointF, QPropertyAnimation, QRectF, Qt, QTimer, pyqtProperty
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPen, QPolygonF, QRadialGradient

from frontend.motion import MotionLogo


class CompanionAvatar(MotionLogo):
    DURATIONS = {**MotionLogo.DURATIONS, "speaking": 1050}

    def __init__(self, size=84, parent=None):
        super().__init__(size, tile=False, parent=parent)
        self.reaction = ""
        self._reaction_phase = 1.0
        self._blink = 0.0
        self._ambient_phase = 0.0
        self.ambient_enabled = True
        self.character = "robot"
        self.accent = QColor("#55ef9d")
        self.ambient_animation = QPropertyAnimation(self, b"ambient_phase", self)
        self.ambient_animation.setDuration(5600)
        self.ambient_animation.setLoopCount(-1)
        self.ambient_animation.setStartValue(0.0)
        self.ambient_animation.setEndValue(1.0)
        self.reaction_animation = QPropertyAnimation(self, b"reaction_phase", self)
        self.reaction_animation.setStartValue(0.0)
        self.reaction_animation.setEndValue(1.0)
        self.reaction_animation.finished.connect(self._reaction_finished)
        self.blink_animation = QPropertyAnimation(self, b"blink", self)
        self.blink_animation.setDuration(380)
        self.blink_animation.setStartValue(0.0)
        self.blink_animation.setEndValue(1.0)
        self.blink_animation.finished.connect(self._schedule_blink)
        self.blink_timer = QTimer(self)
        self.blink_timer.setSingleShot(True)
        self.blink_timer.timeout.connect(self.blink_animation.start)

    def set_appearance(self, character, color):
        self.character = character if character in {"robot", "cat"} else "robot"
        tint = QColor(color)
        self.accent = tint if tint.isValid() else QColor("#55ef9d")
        self.update()

    @pyqtProperty(float)
    def ambient_phase(self):
        return self._ambient_phase

    @ambient_phase.setter
    def ambient_phase(self, value):
        self._ambient_phase = value
        self.update()

    @pyqtProperty(float)
    def reaction_phase(self):
        return self._reaction_phase

    @reaction_phase.setter
    def reaction_phase(self, value):
        self._reaction_phase = value
        self.update()

    @pyqtProperty(float)
    def blink(self):
        return self._blink

    @blink.setter
    def blink(self, value):
        self._blink = value
        self.update()

    def react(self, kind):
        if kind not in {"success", "attachment", "error"}:
            raise ValueError("Unknown companion reaction")
        self.reaction_animation.stop()
        self.reaction = kind
        self.reaction_phase = 0.0
        if self.reduced or not self.isVisible():
            self._reaction_finished()
            return
        self.reaction_animation.setDuration(900 if kind != "error" else 600)
        self.reaction_animation.start()

    def _reaction_finished(self):
        self.reaction = ""
        self.reaction_phase = 1.0

    def _schedule_blink(self):
        self.blink_timer.stop()
        if self.isVisible() and not self.reduced and self.mode == "idle":
            self.blink_timer.start(4600)

    def _sync(self):
        super()._sync()
        if hasattr(self, "blink_timer"):
            self._schedule_blink()
            if self.mode != "idle":
                self.blink_animation.stop()
                self.blink = 0.0
            self._sync_ambient()

    def _sync_ambient(self):
        self.ambient_animation.stop()
        if self.isVisible() and not self.reduced and self.mode == "idle" and self.ambient_enabled:
            self.ambient_animation.start()

    def _settled(self):
        super()._settled()
        self._schedule_blink()
        self._sync_ambient()

    def set_reduced_motion(self, reduced):
        super().set_reduced_motion(reduced)
        if reduced:
            self.reaction_animation.stop()
            self.ambient_animation.stop()
            self.blink_animation.stop()
            self.blink_timer.stop()
            self._reaction_finished()
            self.blink = 0.0

    def hideEvent(self, event):
        self.reaction_animation.stop()
        self.ambient_animation.stop()
        self.blink_animation.stop()
        self.blink_timer.stop()
        self._reaction_finished()
        self.blink = 0.0
        super().hideEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(self.width() / 84, self.height() / 84)
        active = self.mode in {"listening", "thinking", "speaking"}
        phase = 0.0 if self.reduced else self.phase
        wave = math.sin(phase * math.tau) if active else 0.0
        breath = math.sin(self.ambient_phase * math.tau) if self.mode == "idle" and not self.reduced else 0.0
        error = self.reaction == "error"
        tint = QColor("#e9b877" if error else {"thinking": "#91b6ff", "speaking": "#baa6ff"}.get(self.mode, self.accent.name()))
        halo = QRadialGradient(42, 43, 41)
        center = QColor(tint)
        center.setAlpha(108 if active or self.reaction else int(54 + breath * 10))
        halo.setColorAt(0, center)
        halo.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(halo)
        painter.drawEllipse(QRectF(1, 2, 82, 82))
        if self.mode == "listening":
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for offset in (0.0, .5):
                progress = (phase + offset) % 1
                color = QColor(tint)
                color.setAlpha(int(165 * (1 - progress)))
                painter.setPen(QPen(color, 1.8))
                radius = 27 + 13 * progress
                painter.drawEllipse(QRectF(42 - radius, 43 - radius, radius * 2, radius * 2))
        elif self.mode == "thinking":
            painter.setPen(Qt.PenStyle.NoPen)
            for index in range(5):
                angle = phase * math.tau + index * .42
                color = QColor(tint)
                color.setAlpha(235 - index * 40)
                painter.setBrush(color)
                painter.drawEllipse(QRectF(39.5 + math.cos(angle) * 33, 40.5 + math.sin(angle) * 32, 5, 5))
        reaction_wave = math.sin(self.reaction_phase * math.pi)
        lift = -9 * reaction_wave if self.reaction in {"success", "attachment"} else wave * 2 + breath * 1.8
        shake = math.sin(self.reaction_phase * math.tau * 3) * 4 * (1 - self.reaction_phase) if error else 0
        painter.save()
        painter.translate(42 + shake, 43 + lift)
        if self.mode == "entrance" and not self.reduced:
            scale = .75 + .25 * (1 - (1 - phase) ** 3)
            painter.scale(scale, scale)
        painter.rotate(wave * 3 if self.mode == "thinking" else reaction_wave * -5)
        painter.translate(-42, -43)
        gradient = QLinearGradient(17, 22, 67, 63)
        gradient.setColorAt(0, QColor("#f5fff9"))
        body = QColor.fromRgbF(*(.72 + .24 * channel for channel in
                                (self.accent.redF(), self.accent.greenF(), self.accent.blueF())))
        gradient.setColorAt(1, body)
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor("#86bba0"), .7))
        if self.character == "cat":
            for points in ([(19, 32), (20, 13), (37, 25)], [(47, 25), (64, 13), (65, 32)]):
                painter.drawPolygon(QPolygonF([QPointF(x, y) for x, y in points]))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#f3b3c5"))
            for points in ([(23, 26), (24, 18), (31, 25)], [(53, 25), (60, 18), (61, 26)]):
                painter.drawPolygon(QPolygonF([QPointF(x, y) for x, y in points]))
            painter.setBrush(gradient)
            painter.setPen(QPen(QColor("#86bba0"), .7))
        painter.drawRoundedRect(QRectF(17, 22, 50, 41), 15, 15)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#223e33"))
        blink = 1 - math.sin(self.blink * math.pi) ** 8 if not self.reduced else 1
        height = max(1.1, (7 + (wave if self.mode == "listening" else 0)) * blink)
        gaze = wave * 1.8 if self.mode == "thinking" else 0
        for x in (31, 49):
            painter.drawRoundedRect(QRectF(x + gaze, 40 - height / 2, 4, height), 2, 2)
        painter.setPen(QPen(QColor("#5b9679"), 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        if self.mode == "speaking":
            painter.setBrush(QColor("#365c49"))
            painter.drawEllipse(QRectF(37, 49 - abs(wave) * 2, 10, 2 + abs(wave) * 5))
        elif error:
            painter.drawLine(38, 51, 46, 51)
        else:
            painter.drawArc(QRectF(37, 44, 10, 7), 200 * 16, 140 * 16)
        if self.character == "cat":
            painter.setPen(QPen(QColor("#658a83"), 1, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for y in (47, 51):
                painter.drawLine(20, y, 30, y - 1)
                painter.drawLine(54, y - 1, 64, y)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#d484a3"))
            painter.drawEllipse(QRectF(40, 44, 4, 3))
        else:
            painter.setPen(QPen(QColor("#183629"), 2))
            painter.setBrush(tint if active or self.reaction else QColor("#365c49"))
            painter.drawEllipse(QRectF(58, 20, 10, 10))
        painter.restore()
        if self.reaction in {"success", "attachment"}:
            painter.setPen(QPen(QColor(150, 241, 183, int(240 * (1 - self.reaction_phase))), 2))
            for index in range(7):
                angle = index * math.tau / 7
                radius = 27 + self.reaction_phase * 16
                x, y = 42 + math.cos(angle) * radius, 43 + math.sin(angle) * radius
                painter.drawLine(int(x - 2), int(y), int(x + 2), int(y))
                painter.drawLine(int(x), int(y - 2), int(x), int(y + 2))
        if self.mode == "speaking":
            painter.setPen(QPen(tint, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for index in range(5):
                height = 2 + abs(math.sin(phase * math.tau + index * .8)) * 6
                painter.drawLine(int(30 + index * 6), int(73 - height / 2), int(30 + index * 6), int(73 + height / 2))
        painter.end()
