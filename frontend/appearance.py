"""Local appearance preferences, readable accents and a visible-only RGB edge."""

from PyQt6.QtCore import QEvent, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QConicalGradient, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from frontend.brand import ACCENT, ACCENT_HOVER
from frontend.design import STYLE

PRESETS = {"Mint": "#55ef9d", "Ocean": "#66cfff", "Violet": "#ba9fff", "Rose": "#ff9fc2", "Amber": "#ffcf78"}


def valid_color(value):
    color = QColor(value) if isinstance(value, str) else QColor()
    return color.name() if color.isValid() else "#55ef9d"


def readable_accent(value):
    """Keep a user's exact RGB choice for glow; readable controls get a lighter tint."""
    color = QColor(valid_color(value))
    return QColor.fromRgbF(*(max(.55, channel) for channel in (color.redF(), color.greenF(), color.blueF())))


def themed_style(value):
    accent = readable_accent(value)
    return STYLE.replace(ACCENT_HOVER, accent.lighter(115).name()).replace(ACCENT, accent.name()) + f"""
    #composer[focused="true"], #toolButton:checked {{ border-color: {accent.name()}; }}
    #navigationTab[selected="true"] {{ color: {accent.name()}; }}
    #eyebrow, QDialog #sectionTitle {{ color: {accent.name()}; }}
    QTabBar::tab:selected {{ border-bottom-color: {accent.name()}; }}
    #notchButton:focus {{ border: 1px solid {accent.name()}; border-top-left-radius: 0;
        border-top-right-radius: 0; border-bottom-left-radius: 14px; border-bottom-right-radius: 14px; }}
    """


class AccentEdge(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.color = "#55ef9d"
        self.rgb = False
        self.reduced = False
        self.phase = 0
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self._advance)
        parent.installEventFilter(self)
        self.setGeometry(parent.rect())
        self.show()

    def configure(self, color, rgb, reduced):
        self.color, self.rgb, self.reduced = valid_color(color), bool(rgb), bool(reduced)
        self._sync()
        self.update()

    def _sync(self):
        self.timer.stop()
        if self.rgb and not self.reduced and self.isVisible():
            self.timer.start()

    def _advance(self):
        self.phase = (self.phase + 1) % 360
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync()

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Resize:
            self.setGeometry(watched.rect())
            self.raise_()
        return False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.rgb:
            gradient = QConicalGradient(self.rect().center().toPointF(), self.phase)
            for stop, color in [(0, "#ff90bd"), (.25, "#aa9aff"), (.5, "#67dfff"), (.75, "#75ffb8"), (1, "#ff90bd")]:
                gradient.setColorAt(stop, QColor(color))
            pen = QPen(gradient, 1.5)
        else:
            color = QColor(self.color)
            color.setAlpha(85)
            pen = QPen(color, 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        radius = 16 if self.parentWidget().property("shell") != "chat" else 22
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), radius, radius)
        painter.end()
