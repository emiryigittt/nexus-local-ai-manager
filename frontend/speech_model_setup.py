"""Explicit download and offline validation of the selected speech model."""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from frontend.i18n import UiText
from frontend.setup_task import SetupTask


class SpeechModelSetupPanel(QWidget):
    def __init__(self, selection, language="tr", parent=None):
        super().__init__(parent)
        self.selection = selection
        self.tr = UiText(language)
        self.task = SetupTask(self)
        self.task.event_received.connect(self.progress)
        self.task.completed.connect(self.completed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.status = QLabel(self.tr("Konuşma modeli yerelde çalışır. Hazırlama işlemi mikrofonu açmaz."))
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        row = QHBoxLayout()
        self.check = QPushButton(self.tr("Modeli kontrol et"))
        self.prepare = QPushButton(self.tr("Konuşma modelini hazırla…"))
        self.cancel = QPushButton(self.tr("İşlemi durdur"))
        self.cancel.setEnabled(False)
        self.check.clicked.connect(lambda: self.start())
        self.prepare.clicked.connect(self.confirm_download)
        self.cancel.clicked.connect(self.stop)
        for button in (self.check, self.prepare, self.cancel):
            row.addWidget(button)
        layout.addLayout(row)
        selection.currentIndexChanged.connect(self.selection_changed)

    def selection_changed(self):
        self.status.setText(self.tr("Seçili modeli kontrol edin veya hazırlayın. Sesiniz buluta gönderilmez."))

    def confirm_download(self):
        if self.task.busy:
            return
        answer = QMessageBox.question(self, self.tr("Konuşma modelini hazırla"), self.tr(
            "Seçili Whisper modeli Hugging Face üzerinden indirilir; internet ve yüzlerce MB disk alanı kullanabilir. "
            "İndirme sonrası konuşmalar yerelde çözümlenir. Mikrofon açılmaz, ses gönderilmez. Devam edilsin mi?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.start(download=True)

    def start(self, *, download=False):
        if self.task.busy:
            return
        self.preparing_size = self.selection.currentData()
        self.set_busy(True)
        self.status.setText(self.tr("Konuşma modeli hazırlanıyor… Mikrofon kapalı."))
        arguments = ["--model", self.preparing_size] + (["--download"] if download else [])
        self.task.start("prepare-speech", "setup_speech_model.py", arguments, timeout=15 * 60 * 1000)

    def set_busy(self, busy):
        self.selection.setEnabled(not busy)
        self.check.setEnabled(not busy)
        self.prepare.setEnabled(not busy)
        self.cancel.setEnabled(busy)

    def progress(self, event):
        messages = {"checking": "Yerel önbellek kontrol ediliyor… Mikrofon kapalı.",
                    "downloading": "Konuşma modeli indiriliyor… Mikrofon kapalı.",
                    "validating": "Model çevrimdışı yüklenerek doğrulanıyor… Mikrofon kapalı."}
        if event.get("stage") in messages:
            self.status.setText(self.tr(messages[event["stage"]]))

    def completed(self, success):
        self.set_busy(False)
        if self.task.cancelled:
            message = "Hazırlama durduruldu. Mikrofon kapalı; kısmi indirme önbellekte kalabilir."
        elif success:
            message = "Seçili konuşma modeli hazır. Kaydet düğmesiyle seçiminizi uygulayın."
        else:
            message = "Konuşma modeli hazır değil. Hazırla seçeneğini kullanın; internet ve disk alanını kontrol edin."
        self.status.setText(self.tr(message))

    def stop(self):
        return self.task.stop()
