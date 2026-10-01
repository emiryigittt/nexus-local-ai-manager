"""Short UI transitions; persistent movement exists only during visible activity."""

import math

from PyQt6.QtCore import (
    QEasingCurve,
    QEvent,
    QObject,
    QPointF,
    QPropertyAnimation,
    QRect,
    QRectF,
    Qt,
    QVariantAnimation,
    pyqtProperty,
)
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QPushButton, QWidget

from frontend.motion import MotionLogo


class MotionButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.reduced = False
        self._hover_progress = 0.0
        self._ripple_progress = 1.0
        self.ripple_origin = QPointF()
        self.hover_animation = QPropertyAnimation(self, b"hover_progress", self)
        self.hover_animation.setDuration(130)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.ripple_animation = QPropertyAnimation(self, b"ripple_progress", self)
        self.ripple_animation.setDuration(330)
        self.ripple_animation.setStartValue(0.0)
        self.ripple_animation.setEndValue(1.0)
        self.pressed.connect(self._ripple)

    @pyqtProperty(float)
    def hover_progress(self):
        return self._hover_progress

    @hover_progress.setter
    def hover_progress(self, value):
        self._hover_progress = value
        self.update()

    @pyqtProperty(float)
    def ripple_progress(self):
        return self._ripple_progress

    @ripple_progress.setter
    def ripple_progress(self, value):
        self._ripple_progress = value
        self.update()

    def _hover(self, target):
        self.hover_animation.stop()
        if self.reduced:
            self.hover_progress = 0
        else:
            self.hover_animation.setStartValue(self.hover_progress)
            self.hover_animation.setEndValue(target)
            self.hover_animation.start()

    def _ripple(self):
        if self.reduced or not self.isVisible():
            return
        if self.ripple_origin.isNull():
            self.ripple_origin = QPointF(self.rect().center())
        self.ripple_animation.stop()
        self.ripple_animation.start()

    def mousePressEvent(self, event):
        self.ripple_origin = event.position()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        super().enterEvent(event)
        self._hover(1)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._hover(0)

    def set_reduced_motion(self, reduced):
        self.reduced = bool(reduced)
        if reduced:
            self.hover_animation.stop()
            self.ripple_animation.stop()
            self.hover_progress = 0
            self.ripple_progress = 1

    def hideEvent(self, event):
        self.hover_animation.stop()
        self.ripple_animation.stop()
        self.hover_progress = 0
        self.ripple_progress = 1
        super().hideEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.reduced or not self.isEnabled():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        from PyQt6.QtGui import QPainterPath

        path = QPainterPath()
        path.addRoundedRect(bounds, 9, 9)
        painter.setClipPath(path)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(145, 225, 175, int(16 * self.hover_progress)))
        painter.drawPath(path)
        if self.ripple_progress < 1:
            painter.setBrush(QColor(145, 225, 175, int(52 * (1 - self.ripple_progress))))
            radius = max(self.width(), self.height()) * self.ripple_progress
            painter.drawEllipse(self.ripple_origin, radius, radius)
        painter.end()


class RevealCurtain(QWidget):
    def __init__(self, target):
        super().__init__(target)
        self._opacity = 1.0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setGeometry(target.rect())
        target.installEventFilter(self)
        self.animation = QPropertyAnimation(self, b"opacity", self)
        self.animation.setDuration(140)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.dismiss)
        self.show()
        self.raise_()

    @pyqtProperty(float)
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.update()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Resize:
            self.setGeometry(watched.rect())
        return False

    def dismiss(self):
        self.animation.stop()
        self.parentWidget().removeEventFilter(self)
        self.hide()
        self.deleteLater()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(17, 20, 22, int(255 * self.opacity)))
        painter.end()


class ShellTransition(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.reduced = False
        self.target = None
        self.cover = None
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(230)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.valueChanged.connect(self._geometry)
        self.animation.finished.connect(self._reveal)

    def _geometry(self, rect):
        self.window.setFixedSize(rect.size())
        self.window.move(rect.topLeft())

    def start(self, rect, content):
        self.animation.stop()
        self._remove_cover()
        self.target = QRect(rect)
        if self.reduced or not self.window.isVisible():
            self._geometry(rect)
            return
        self.cover = RevealCurtain(content)
        self.animation.setStartValue(self.window.geometry())
        self.animation.setEndValue(rect)
        self.animation.start()

    def _remove_cover(self):
        if self.cover is not None:
            from PyQt6 import sip

            if not sip.isdeleted(self.cover):
                self.cover.dismiss()
            self.cover = None

    def _reveal(self):
        if self.cover is not None:
            self.cover.animation.start()

    def finish(self):
        self.animation.stop()
        if self.target is not None:
            self._geometry(self.target)
        self._remove_cover()

    def set_reduced_motion(self, reduced):
        self.reduced = bool(reduced)
        if reduced:
            self.finish()


class ActivityDots(MotionLogo):
    """A rhythm indicator, not microphone amplitude or a model progress percentage."""

    DURATIONS = {**MotionLogo.DURATIONS, "speaking": 1000}

    def __init__(self):
        super().__init__(18, tile=False)
        self.setFixedSize(42, 18)

    def set_mode(self, mode):
        super().set_mode(mode)
        self.setVisible(mode in {"thinking", "listening", "speaking"})

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        for index in range(3):
            wave = 0 if self.reduced else math.sin(self.phase * math.tau - index * .9)
            painter.setBrush(QColor(150, 229, 179, int(150 + 90 * max(0, wave))))
            painter.drawEllipse(QRectF(4 + index * 12, 7 - wave * 2, 5, 5))
        painter.end()


class DropTarget(QWidget):
    def __init__(self, parent, text):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.text = text
        self.reduced = False
        self._phase = 0.0
        self.animation = QPropertyAnimation(self, b"phase", self)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setDuration(1200)
        self.animation.setLoopCount(-1)
        self.hide()

    @pyqtProperty(float)
    def phase(self):
        return self._phase

    @phase.setter
    def phase(self, value):
        self._phase = value
        self.update()

    def set_reduced_motion(self, reduced):
        self.reduced = bool(reduced)
        self.animation.stop()
        self.phase = 0.0
        if not reduced and self.isVisible():
            self.animation.start()

    def showEvent(self, event):
        self.setGeometry(self.parentWidget().rect())
        self.raise_()
        if not self.reduced:
            self.animation.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self.animation.stop()
        super().hideEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(17, 29, 23, 235))
        painter.setPen(QPen(QColor(145, 225, 175, int(180 + 60 * math.sin(self.phase * math.pi))),
                            2, Qt.PenStyle.DashLine))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(22, 22, -22, -22), 17, 17)
        painter.setPen(QColor("#d4f5e1"))
        painter.drawText(self.rect().adjusted(34, 34, -34, -34), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.text)
        painter.end()
