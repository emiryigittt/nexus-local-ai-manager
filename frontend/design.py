"""Nexus visual language: calm graphite, warm text, restrained mint accents."""

from PyQt6.QtCore import QEvent, QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout

from frontend.brand import ACCENT, ACCENT_HOVER, brand_icon


def icon(name, color="#bfc3c7"):
    """Small vector-like line icons, independent of symbol/emoji font support."""
    if name == "logo":
        return brand_icon(tile=False)
    pixmap = QPixmap(48, 48)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(2, 2)
    painter.setPen(QPen(QColor(color), 1.6, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    if name == "mic":
        painter.drawRoundedRect(9, 3, 6, 12, 3, 3)
        painter.drawArc(6, 6, 12, 12, 180 * 16, 180 * 16)
        painter.drawLine(12, 18, 12, 21)
        painter.drawLine(9, 21, 15, 21)
    elif name == "send":
        painter.drawLine(12, 19, 12, 5)
        painter.drawLine(6, 11, 12, 5)
        painter.drawLine(12, 5, 18, 11)
    elif name == "history":
        painter.drawEllipse(4, 4, 16, 16)
        painter.drawLine(12, 7, 12, 12)
        painter.drawLine(12, 12, 16, 14)
    elif name == "settings":
        for x, y in ((6, 8), (12, 16), (18, 10)):
            painter.drawLine(x, 4, x, 20)
            painter.setBrush(QColor("#1c1e22"))
            painter.drawEllipse(x - 2, y - 2, 4, 4)
    elif name == "hide":
        painter.drawLine(6, 12, 18, 12)
    elif name == "plus":
        painter.drawLine(12, 5, 12, 19)
        painter.drawLine(5, 12, 19, 12)
    elif name == "web":
        painter.drawEllipse(3, 3, 18, 18)
        painter.drawEllipse(8, 3, 8, 18)
        painter.drawLine(3, 12, 21, 12)
    elif name == "copy":
        painter.drawRoundedRect(8, 8, 12, 13, 2, 2)
        painter.drawLine(4, 16, 4, 3)
        painter.drawLine(4, 3, 16, 3)
    else:
        for x in (5, 12, 19):
            painter.drawEllipse(x - 1, 11, 2, 2)
    painter.end()
    return QIcon(pixmap)


def button(name, tooltip, callback, text="", primary=False):
    widget = QPushButton(text)
    widget.setIcon(icon(name, "#142820" if primary else "#bfc3c7"))
    widget.setIconSize(QSize(20, 20))
    widget.setObjectName("sendButton" if primary else "toolButton")
    widget.setToolTip(tooltip)
    widget.setAccessibleName(tooltip)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    widget.setMinimumHeight(36)
    if not text:
        widget.setFixedSize(36, 36)
    widget.clicked.connect(callback)
    return widget


class StatusLabel(QLabel):
    """Bound long provider names/errors so status never pushes controls off screen."""

    def __init__(self, text=""):
        super().__init__()
        self.full_text = ""
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setMinimumWidth(40)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setText(text)

    def setText(self, text):
        self.full_text = text
        self.setToolTip(text)
        self._elide()

    def _elide(self):
        super().setText(self.fontMetrics().elidedText(self.full_text, Qt.TextElideMode.ElideRight, self.width()))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._elide()


class ComposerFrame(QFrame):
    """Visible keyboard focus without changing editor shortcuts or input behavior."""

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.FocusIn, QEvent.Type.FocusOut):
            self.setProperty("focused", event.type() == QEvent.Type.FocusIn)
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()
        return super().eventFilter(watched, event)


class ActionCard(QPushButton):
    """A single keyboard/click target with a title, hint and drawn icon."""

    def __init__(self, name, title, description, shortcut, callback, ui):
        super().__init__()
        self.setObjectName("actionCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(112)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(5)
        top = QHBoxLayout()
        mark = QLabel()
        mark.setPixmap(icon(name, ACCENT).pixmap(20, 20))
        top.addWidget(mark)
        top.addStretch()
        key = QLabel(shortcut)
        key.setObjectName("cardShortcut")
        top.addWidget(key)
        layout.addLayout(top)
        heading = QLabel()
        heading.setObjectName("cardTitle")
        ui.bind(heading, "setText", title)
        layout.addWidget(heading)
        hint = QLabel()
        hint.setObjectName("cardDescription")
        ui.bind(hint, "setText", description)
        layout.addWidget(hint)
        for child in self.findChildren(QLabel):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        ui.bind(self, "setAccessibleName", title)
        ui.bind(self, "setAccessibleDescription", description)
        ui.bind(self, "setToolTip", title)
        self.clicked.connect(callback)


def settings_card(parent_layout, title):
    card = QFrame()
    card.setObjectName("settingsCard")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(14)
    heading = QLabel(title)
    heading.setObjectName("sectionTitle")
    layout.addWidget(heading)
    parent_layout.addWidget(card)
    return layout


STYLE = """
QWidget { color: #ecebea; font-family: 'Segoe UI'; font-size: 13px; }
#outer, #header, #content, #welcome, #footer { background: transparent; }
#container { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #202426,stop:0.5 #191c1f,stop:1 #191c1f);
    border: 1px solid #3c4245; border-radius: 24px; }
#brand { color: #f3f1ed; font-size: 16px; font-weight: 600; }
#brandNote { color: #8f959d; font-size: 11px; }
#heroMark { background: transparent; border: none; }
#welcomeTitle { color: #f1efeb; font-size: 34px; font-weight: 600; }
#subtitle { color: #a0a4ab; font-size: 14px; }
#eyebrow { color: #83dbaa; font-size: 11px; font-weight: 600; }
#actionCard { background: #23282b; border: 1px solid #394145; border-radius: 14px; }
#actionCard:hover { background: #2b3631; border-color: #708f7c; }
#actionCard:pressed { background: #34473a; }
#actionCard:focus { border: 2px solid @accent; }
#actionCard QLabel { background: transparent; border: none; }
#cardTitle { color: #e6e9e7; font-size: 13px; font-weight: 600; }
#cardDescription { color: #a1aba8; font-size: 11px; }
#cardShortcut { color: #a1aba8; font-size: 10px; }
#suggestion { background: #222529; border: 1px solid #34383e; border-radius: 11px;
    text-align: left; padding: 12px 16px; color: #d9dbdd; }
#suggestion:hover { background: #2b3033; border-color: #6b897a; }
#suggestion:focus { border-color: #a4d5b9; }
#composer { background: #252b2e; border: 1px solid #4d5858; border-radius: 18px; }
#composer[focused="true"] { border: 1px solid #9abea7; background: #272f31; }
HistoryLineEdit { color: #f0eeeb; background: transparent; border: none; padding: 6px 0;
    font-size: 17px; selection-background-color: #3b6851; }
HistoryLineEdit:disabled { color: #888e96; }
#toolButton { color: #bfc3c7; background: transparent; border: 1px solid transparent;
    border-radius: 8px; padding: 5px 8px; }
#toolButton:hover { background: #363b40; color: #f5f4f0; }
#toolButton:focus { border-color: #95c6aa; }
#toolButton:checked { background: #3e5548; border-color: #92caaa; }
#sendButton { background: @accent; border: none; border-radius: 10px; }
#sendButton:hover { background: @accentHover; }
#sendButton:focus { border: 2px solid #edf9f1; }
#sendButton:disabled { background: #404a43; }
#contextButton { color: #b1b8bd; background: transparent; border: none; text-align: left;
    padding: 5px 0; font-size: 11px; }
#contextButton:hover { color: #c5e5d0; }
#contextButton:focus, #wakeButton:focus { border: 1px solid #a4d5b9; border-radius: 5px; }
#output { background: transparent; color: #e4e3e0; border: none;
    selection-background-color: #3b6851; padding: 0; font-size: 15px; }
#responseHeading { color: #a5c9b5; font-size: 12px; font-weight: 600; }
#modelStatus { color: #939aa1; font-size: 11px; }
#localBadge { color: #b4d5bf; font-size: 9px; font-weight: 600; background: #26342c;
    border: 1px solid #3b5244; border-radius: 5px; padding: 4px 7px; }
#localBadge[mode="cloud"] { color: #efc57d; }
#localBadge[mode="private"] { color: #b9bfdc; }
#wakeButton { background: transparent; border: none; font-size: 10px; padding: 4px; }
#stopButton { background: #38282c; color: #f0b1ba; border: 1px solid #65404a;
    border-radius: 8px; padding: 5px 9px; }
#footerHint { color: #92999f; font-size: 11px; }
QMenu { background: #26292e; color: #e8e7e4; border: 1px solid #464c53; padding: 6px; }
QMenu::item { padding: 9px 22px 9px 12px; border-radius: 5px; }
QMenu::item:selected { background: #3b4942; }
QMenu::separator { height: 1px; background: #40464c; margin: 5px; }
QToolTip { color: #f0eeeb; background: #292d31; border: 1px solid #4a535b; padding: 7px; }
QScrollBar:vertical { background: transparent; width: 6px; margin: 3px; }
QScrollBar::handle:vertical { background: #495057; border-radius: 3px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QDialog { background: #191b1e; }
QDialog QLabel { background: transparent; }
QDialog QScrollArea, QDialog QScrollArea > QWidget > QWidget { background: #191b1e; border: none; }
QDialog QLineEdit, QDialog QComboBox, QDialog QDoubleSpinBox, QDialog QListWidget,
QDialog QTextEdit { background: #25292e; color: #e8e7e4; border: 1px solid #454c54;
    border-radius: 6px; padding: 7px; selection-background-color: #3b6851; }
QDialog QPushButton { background: #30363b; border: 1px solid #48535a; border-radius: 7px; padding: 8px 12px; }
QDialog QPushButton:hover { background: #3b4942; }
QDialog QPushButton:disabled { color: #7e888e; background: #252a2e; border-color: #353c41; }
QDialog QPushButton:focus, QDialog QComboBox:focus, QDialog QLineEdit:focus,
QDialog QDoubleSpinBox:focus { border-color: @accent; }
QDialog QPushButton[primary="true"] { background: @accent; color: #142820; border-color: @accent; font-weight: 600; }
QDialog QPushButton[primary="true"]:hover { background: @accentHover; }
QDialog #settingsCard { background: #22272a; border: 1px solid #394246; border-radius: 14px; }
QDialog #sectionTitle { color: #c4dccd; font-size: 12px; font-weight: 600; }
QDialog #settingsNote { color: #a3adb3; font-size: 12px; }
QDialog QGroupBox { border: 1px solid #3c444b; border-radius: 10px; margin-top: 16px; padding: 14px; }
QDialog QGroupBox::title { subcontrol-origin: margin; left: 12px; color: #b4d4c1; }
QDialog QCheckBox { spacing: 8px; padding: 5px 0; }
QDialog #dialogTitle { font-size: 23px; font-weight: 600; }
QTabWidget::pane { border: none; border-top: 1px solid #363e44; }
QTabBar::tab { background: transparent; color: #9fa7ae; padding: 10px 20px;
    border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #c6e4d1; border-bottom-color: #a8cdb7; }
QTabBar::tab:hover { color: #e4f0e8; background: #272f2d; }
QTabBar::tab:focus { border-color: @accent; }
#voiceSections::pane { border: 1px solid #394246; border-radius: 12px; background: #22272a; }
#voiceSections QTabBar::tab { padding: 10px 15px; margin: 0 4px 8px 0; border: 1px solid #394246;
    border-radius: 8px; background: #23282b; }
#voiceSections QTabBar::tab:selected { color: #d4ebdd; background: #34473b; border-color: #6b8d77; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #6c757c;
    border-radius: 4px; background: #25292e; }
QCheckBox::indicator:checked { background: @accent; border: 3px solid #397f57; }
""".replace("@accentHover", ACCENT_HOVER).replace("@accent", ACCENT)
