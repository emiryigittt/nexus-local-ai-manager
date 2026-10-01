"""RGB controls and character selection with an isolated, immediate visual preview."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from frontend.appearance import PRESETS, AccentEdge, themed_style, valid_color
from frontend.companion import CompanionAvatar
from frontend.design import settings_card
from frontend.sound_feedback import SoundFeedback


class AppearanceSettings(QWidget):
    def __init__(self, preferences, ui):
        super().__init__()
        self.ui = ui
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        color_card = settings_card(root, ui("Renk ve RGB"))
        note = QLabel(ui("Rengini seç. Karakteri ve ışığı önizlemede hemen gör."))
        note.setWordWrap(True)
        note.setObjectName("settingsNote")
        color_card.addWidget(note)
        self.preview = QFrame()
        self.preview.setObjectName("container")
        self.preview.setProperty("shell", "dock")
        row = QHBoxLayout(self.preview)
        self.avatar = CompanionAvatar(84)
        row.addWidget(self.avatar)
        words = QVBoxLayout()
        title = QLabel("Nexus")
        title.setObjectName("dockTitle")
        words.addWidget(title)
        words.addWidget(QLabel(ui("Senin rengin. Senin asistanın.")))
        row.addLayout(words, 1)
        color_card.addWidget(self.preview)
        self.edge = AccentEdge(self.preview)
        presets = QHBoxLayout()
        for name, color in PRESETS.items():
            button = QPushButton(ui(name))
            button.setStyleSheet(f"border-bottom: 3px solid {color}; padding: 7px 4px;")
            button.clicked.connect(lambda checked=False, color=color: self.set_color(color))
            presets.addWidget(button)
        color_card.addLayout(presets)
        channels = QHBoxLayout()
        self.channels = []
        for name in ("R", "G", "B"):
            channels.addWidget(QLabel(name))
            channel = QSpinBox()
            channel.setRange(0, 255)
            channel.setAccessibleName(ui("Renk kanalı") + " " + name)
            channel.valueChanged.connect(self.refresh_preview)
            channels.addWidget(channel)
            self.channels.append(channel)
        picker = QPushButton(ui("Renk seç…"))
        picker.clicked.connect(self.choose_color)
        channels.addWidget(picker)
        color_card.addLayout(channels)
        self.rgb = QCheckBox(ui("Yavaş RGB kenar ışığı"))
        self.rgb.setChecked(preferences.rgb_enabled)
        self.rgb.toggled.connect(self.refresh_preview)
        color_card.addWidget(self.rgb)
        self.hex_label = QLabel()
        self.hex_label.setObjectName("settingsNote")
        color_card.addWidget(self.hex_label)
        pet_card = settings_card(root, ui("Yol arkadaşın"))
        form = QFormLayout()
        self.character = QComboBox()
        self.character.addItem(ui("Mini bot"), "robot")
        self.character.addItem(ui("Nexus kedisi"), "cat")
        self.character.setCurrentIndex(max(0, self.character.findData(preferences.companion_style)))
        self.character.currentIndexChanged.connect(self.refresh_preview)
        form.addRow(ui("Karakter"), self.character)
        pet_card.addLayout(form)
        hello = QPushButton(ui("Karakteri selamla"))
        hello.clicked.connect(lambda: self.avatar.react("success"))
        pet_card.addWidget(hello, alignment=Qt.AlignmentFlag.AlignLeft)
        description = QLabel(ui("Göz kırpar, dinler, düşünür ve konuşur. Uygulamanın gerçek durumunu takip eder."))
        description.setWordWrap(True)
        description.setObjectName("settingsNote")
        pet_card.addWidget(description)
        sound_card = settings_card(root, ui("Küçük sesler"))
        self.sounds = QCheckBox(ui("Arayüz ses efektlerini aç"))
        self.sounds.setChecked(preferences.ui_sounds_enabled)
        sound_card.addWidget(self.sounds)
        sound_row = QHBoxLayout()
        sound_row.addWidget(QLabel(ui("Ses düzeyi")))
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(preferences.ui_sound_volume)
        self.volume.setAccessibleName(ui("Ses düzeyi"))
        sound_row.addWidget(self.volume, 1)
        self.volume_label = QLabel()
        sound_row.addWidget(self.volume_label)
        sample = QPushButton(ui("Sesi dene"))
        self.sound_preview = SoundFeedback(self)
        sample.clicked.connect(self.play_sample)
        sound_row.addWidget(sample)
        sound_card.addLayout(sound_row)
        self.volume.valueChanged.connect(lambda value: self.volume_label.setText(f"%{value}"))
        self.volume_label.setText(f"%{self.volume.value()}")
        quiet = QLabel(ui("Fareyle üzerine gelince ses çıkmaz. Sesler isteğe bağlıdır; konuşma sesi ayrı ayarlanır."))
        quiet.setWordWrap(True)
        quiet.setObjectName("settingsNote")
        sound_card.addWidget(quiet)
        self.reduced = preferences.reduced_motion
        self.set_color(preferences.accent_color)
        root.addStretch()

    def color(self):
        return QColor(*(channel.value() for channel in self.channels)).name()

    def set_color(self, value):
        color = QColor(valid_color(value))
        for control, channel in zip(self.channels, (color.red(), color.green(), color.blue()), strict=True):
            control.blockSignals(True)
            control.setValue(channel)
            control.blockSignals(False)
        self.refresh_preview()

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.color()), self, self.ui("Renk seç…"))
        if color.isValid():
            self.set_color(color.name())

    def refresh_preview(self, *args):
        if not hasattr(self, "reduced"):
            return
        color = self.color()
        self.preview.setStyleSheet(themed_style(color))
        self.avatar.set_appearance(self.character.currentData(), color)
        self.avatar.set_reduced_motion(self.reduced)
        self.edge.configure(color, self.rgb.isChecked(), self.reduced)
        self.edge.raise_()
        self.hex_label.setText(color.upper() + " · " + self.ui("Hareketi azalt açıkken RGB ışığı sabit kalır."))

    def set_reduced_motion(self, value):
        self.reduced = bool(value)
        self.refresh_preview()

    def play_sample(self):
        self.sound_preview.configure(True, self.volume.value())
        self.sound_preview.play("success", preview=True)

    def hideEvent(self, event):
        self.sound_preview.stop()
        super().hideEvent(event)

    def apply(self, preferences):
        preferences.accent_color = self.color()
        preferences.rgb_enabled = self.rgb.isChecked()
        preferences.companion_style = str(self.character.currentData())
        preferences.ui_sounds_enabled = self.sounds.isChecked()
        preferences.ui_sound_volume = self.volume.value()
