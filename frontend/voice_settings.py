"""Voice preferences; device enumeration never opens a microphone stream."""

from PyQt6.QtMultimedia import QMediaDevices
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from backend.audio_transcriber import input_devices
from frontend.i18n import UiText
from frontend.wake_setup import WakeSetupPanel


class VoiceSettings(QWidget):
    def __init__(self, preferences, parent=None):
        super().__init__(parent)
        tr = UiText(preferences.language)
        self.ui_text = tr
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.sections = QTabWidget()
        self.sections.setObjectName("voiceSections")
        layout.addWidget(self.sections)

        def section(title):
            page = QWidget()
            form = QFormLayout(page)
            form.setContentsMargins(20, 22, 20, 22)
            form.setSpacing(16)
            form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
            self.sections.addTab(page, tr(title))
            return form

        input_form = section("Giriş")
        wake_form = section("Hey Nexus")
        output_form = section("Yanıt sesi")
        form = input_form
        self.input = QComboBox()
        self.output = QComboBox()
        self.input.addItem(tr("Sistem varsayılanı"), preferences.voice_input_device)
        self.output.addItem(tr("Sistem varsayılanı"), preferences.voice_output_device)
        form.addRow(tr("Mikrofon"), self.input)
        output_form.addRow(tr("Hoparlör"), self.output)
        self.mode = QComboBox()
        self.mode.addItem(tr("F2 ile başlat / durdur"), "toggle")
        self.mode.addItem(tr("F2 basılıyken konuş"), "push_to_talk")
        self.mode.addItem(tr("F2 ile başlat, sessizlikte bitir"), "vad")
        self.mode.setCurrentIndex(max(0, self.mode.findData(preferences.voice_input_mode)))
        form.addRow(tr("Sesli giriş"), self.mode)
        self.silence = QDoubleSpinBox()
        self.silence.setRange(0.3, 3.0)
        self.silence.setSingleStep(0.1)
        self.silence.setSuffix(tr(" sn"))
        self.silence.setValue(preferences.voice_silence_seconds)
        form.addRow(tr("Bitirme sessizliği"), self.silence)
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(0.1, 20.0)
        self.threshold.setSingleStep(0.1)
        self.threshold.setSuffix(" %")
        self.threshold.setValue(preferences.voice_threshold * 100)
        self.threshold.setToolTip(tr("Sessiz konuşmayı kaçırıyorsa azaltın; ortam gürültüsünü konuşma sayıyorsa artırın."))
        form.addRow(tr("Ses eşiği"), self.threshold)
        form = wake_form
        self.wake = QCheckBox(tr("Hey Nexus dinlemesine izin ver (deneysel)"))
        self.wake.setChecked(preferences.wake_word_enabled)
        form.addRow(self.wake)
        self.wake_startup = QCheckBox(tr("Nexus açılınca Hey Nexus dinlemesini başlat"))
        self.wake_startup.setChecked(preferences.wake_word_on_startup)
        self.wake_startup.setEnabled(self.wake.isChecked())
        self.wake.toggled.connect(self.wake_startup.setEnabled)
        form.addRow(self.wake_startup)
        wake_info = QLabel(tr(
            "İzin verirseniz arka planda kısa ses parçaları yalnızca yerel Whisper ile incelenir; "
            "kaydedilmez veya buluta gönderilmez. 'Hey Nexus' deyip duraklayın; pencere açılınca "
            "komutunuzu söyleyin. İşlemci kullanımı ve algılama gecikmesi olabilir. "
            "Penceredeki Hey Nexus düğmesinden veya sistem tepsisinden duraklatabilirsiniz. "
            "Yerel modeli aşağıdan mikrofon açmadan kontrol edebilir veya hazırlayabilirsiniz."
        ))
        wake_info.setWordWrap(True)
        wake_info.setObjectName("settingsNote")
        form.addRow(wake_info)
        self.wake_setup = WakeSetupPanel(preferences.language, self)
        form.addRow(self.wake_setup)
        self.microphone_status = QLabel()
        self.microphone_status.setWordWrap(True)
        self.microphone_status.setObjectName("settingsNote")
        input_form.addRow(self.microphone_status)
        self.input.currentIndexChanged.connect(self.update_microphone_status)
        self._input_ids = set()
        self._device_scan_failed = False
        form = output_form
        self.tts = QCheckBox(tr("Yanıtları seslendir"))
        self.tts.setChecked(preferences.tts_enabled)
        form.addRow(self.tts)
        self.backend = QComboBox()
        for label, value in (("Otomatik · yerel", "auto"), ("Supertonic · yerel", "supertonic"),
                             ("Windows sesi · yerel", "local"), ("Edge · bulut izni gerektirir", "edge")):
            self.backend.addItem(tr(label), value)
        self.backend.setCurrentIndex(max(0, self.backend.findData(preferences.tts_backend)))
        form.addRow(tr("Yanıt sesi"), self.backend)
        self.local_voice = QComboBox()
        for index in range(10):
            self.local_voice.addItem(tr("Yerel ses {number}", number=index + 1), index)
        self.local_voice.setCurrentIndex(max(0, self.local_voice.findData(preferences.tts_local_voice)))
        form.addRow(tr("Supertonic karakteri"), self.local_voice)
        self.edge_voice = QComboBox()
        for label, value in (("Ahmet · Türkçe", "tr-TR-AhmetNeural"), ("Emel · Türkçe", "tr-TR-EmelNeural"),
                             ("Aria · English", "en-US-AriaNeural"), ("Guy · English", "en-US-GuyNeural")):
            self.edge_voice.addItem(label, value)
        self.edge_voice.setCurrentIndex(max(0, self.edge_voice.findData(preferences.tts_edge_voice)))
        form.addRow(tr("Bulut karakteri"), self.edge_voice)
        self.speed = QDoubleSpinBox()
        self.speed.setRange(0.8, 1.3)
        self.speed.setSingleStep(0.05)
        self.speed.setValue(preferences.tts_speed)
        self.speed.setSuffix(" ×")
        form.addRow(tr("Konuşma hızı"), self.speed)
        self.steps = QComboBox()
        for label, value in (("Hızlı · 4 adım", 4), ("Dengeli · 6 adım", 6), ("Ayrıntılı · 8 adım", 8)):
            self.steps.addItem(tr(label), value)
        self.steps.setCurrentIndex(max(0, self.steps.findData(preferences.tts_steps)))
        form.addRow(tr("Yerel üretim"), self.steps)
        self.backend.currentIndexChanged.connect(self.update_backend_controls)
        self.steps.setToolTip(tr("Daha az adım üretimi hızlandırır; ses kalitesi değişebilir."))
        self.speed.setToolTip(tr("Supertonic ve Edge için geçerli; Windows sesi kendi hız ayarını kullanır."))
        self.update_backend_controls()
        self.status = QLabel(tr("Normal sesli giriş en fazla 60 saniyedir. Hey Nexus ayrı izin gerektirir."))
        self.status.setWordWrap(True)
        self.status.setObjectName("settingsNote")
        layout.addWidget(self.status)
        refresh = QPushButton(tr("Ses cihazlarını yenile"))
        refresh.clicked.connect(self.refresh)
        layout.addWidget(refresh)
        self.refresh()

    def update_backend_controls(self):
        backend = self.backend.currentData()
        self.local_voice.setEnabled(backend in {"auto", "supertonic"})
        self.steps.setEnabled(backend in {"auto", "supertonic"})
        self.edge_voice.setEnabled(backend == "edge")
        self.speed.setEnabled(backend != "local")

    def refresh(self):
        selected_input = self.input.currentData() or ""
        selected_output = self.output.currentData() or ""
        self.input.clear()
        self.output.clear()
        self.input.addItem(self.ui_text("Sistem varsayılanı"), "")
        self.output.addItem(self.ui_text("Sistem varsayılanı"), "")
        self._input_ids = set()
        self._device_scan_failed = False
        try:
            for item in input_devices():
                self._input_ids.add(item["id"])
                self.input.addItem(item["name"], item["id"])
        except Exception:
            self._device_scan_failed = True
            self.status.setText(self.ui_text("Mikrofonlar listelenemedi. Bağlantıyı kontrol edip yenileyin."))
        for device in QMediaDevices.audioOutputs():
            self.output.addItem(device.description(), bytes(device.id()).hex())
        for combo, value in ((self.input, selected_input), (self.output, selected_output)):
            if value and combo.findData(value) < 0:
                combo.addItem(self.ui_text("Önceki seçim (bağlı değil)"), value)
            combo.setCurrentIndex(max(0, combo.findData(value)))
        self.update_microphone_status()

    def update_microphone_status(self):
        selected = self.input.currentData()
        if self._device_scan_failed:
            source = "Mikrofon listesi okunamadı. Cihazları yenileyin."
        elif selected and selected not in self._input_ids:
            source = "Seçili mikrofon bağlı değil. Başka bir mikrofon seçin."
        elif not self._input_ids:
            source = "Mikrofon bulunamadı. Cihaz bağlayıp listeyi yenileyin."
        else:
            source = "Mikrofon listede görünüyor; Windows erişim izni ve ses alımı henüz test edilmedi."
        self.microphone_status.setText(self.ui_text(source))

    def apply(self, preferences):
        preferences.voice_input_device = self.input.currentData()
        preferences.voice_output_device = self.output.currentData()
        preferences.voice_input_mode = self.mode.currentData()
        preferences.voice_silence_seconds = self.silence.value()
        preferences.voice_threshold = self.threshold.value() / 100
        preferences.wake_word_enabled = self.wake.isChecked()
        preferences.wake_word_on_startup = self.wake.isChecked() and self.wake_startup.isChecked()
        preferences.tts_enabled = self.tts.isChecked()
        preferences.tts_backend = self.backend.currentData()
        preferences.tts_local_voice = self.local_voice.currentData()
        preferences.tts_edge_voice = self.edge_voice.currentData()
        preferences.tts_speed = self.speed.value()
        preferences.tts_steps = self.steps.currentData()
