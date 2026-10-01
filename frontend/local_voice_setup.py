"""Explicit download and progress for optional local response speech."""

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from frontend.setup_task import SetupTask


class LocalVoiceSetupPanel(QWidget):
    def __init__(self, language="tr", parent=None):
        super().__init__(parent)
        self.english = language == "en"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.status = QLabel(self.t("Yerel yanıt sesi isteğe bağlıdır. Windows sesi indirme gerektirmez.", "Local neural speech is optional. Windows speech needs no download."))
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)
        row = QHBoxLayout()
        self.check = QPushButton(self.t("Sesi kontrol et", "Check voice"))
        self.download = QPushButton(self.t("Sesi hazırla…", "Prepare voice…"))
        self.cancel = QPushButton(self.t("İşlemi durdur", "Stop"))
        self.cancel.setEnabled(False)
        for control in (self.check, self.download, self.cancel):
            row.addWidget(control)
        layout.addLayout(row)
        self.task = SetupTask(self)
        self.task.event_received.connect(self.receive)
        self.task.completed.connect(self.finished)
        self.check.clicked.connect(lambda: self.start(False))
        self.download.clicked.connect(self.confirm_download)
        self.cancel.clicked.connect(self.task.stop)
        self.stage = ""

    def t(self, tr, en):
        return en if self.english else tr

    def confirm_download(self):
        answer = QMessageBox.question(self, "Supertonic", self.t(
            "Yerel yanıt sesi için sherpa-onnx GitHub deposundan Supertonic model dosyaları indirilecek. İnternet ve disk alanı kullanılır; sohbet veya ses kaydı gönderilmez. Modelin OpenRAIL-M koşulları geçerlidir. Devam edilsin mi?",
            "Download Supertonic model files from sherpa-onnx on GitHub for local speech? This uses internet and disk space; no chats or recordings are sent. The model's OpenRAIL-M terms apply."),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.start(True)

    def start(self, download=False):
        if self.task.busy:
            return
        self.stage = ""
        self.progress.setRange(0, 0)
        self.progress.show()
        self.status.setText(self.t("Yerel ses hazırlanıyor…", "Preparing local speech…"))
        self.check.setEnabled(False)
        self.download.setEnabled(False)
        self.cancel.setEnabled(True)
        self.task.start("prepare-voice", "setup_local_tts.py", ["--download"] if download else [], timeout=15 * 60 * 1000)

    def receive(self, event):
        self.stage = event.get("stage", "")
        percent = event.get("percent")
        if isinstance(percent, int):
            self.progress.setRange(0, 100)
            self.progress.setValue(max(0, min(100, percent)))
        elif self.stage in {"extracting", "validating"}:
            self.progress.setRange(0, 0)
        messages = {
            "checking": ("Ses dosyaları kontrol ediliyor…", "Checking voice files…"),
            "downloading": ("Ses dosyaları indiriliyor…", "Downloading voice files…"),
            "extracting": ("Ses dosyaları açılıyor…", "Extracting voice files…"),
            "validating": ("Ses motoru çevrimdışı doğrulanıyor…", "Validating the speech engine offline…"),
        }
        if self.stage in messages:
            self.status.setText(self.t(*messages[self.stage]))

    def finished(self, success):
        self.progress.hide()
        self.check.setEnabled(True)
        self.download.setEnabled(True)
        self.cancel.setEnabled(False)
        if self.task.cancelled:
            message = ("İşlem durduruldu. Kısmi indirme diskte kalabilir.", "Stopped. A partial download may remain on disk.")
        elif success:
            message = ("Yerel ses hazır. Supertonic seçip Yanıtları seslendir'i açabilirsin.", "Local speech is ready. Select Supertonic and enable Read responses aloud.")
        elif self.stage == "runtime_missing":
            message = ("Bu kaynak kurulumunda ses bileşenleri eksik. Windows kurulum paketi bu bileşenleri içerir.", "Speech components are missing in this source installation. The Windows installer includes them.")
        else:
            message = ("Ses hazır değil. Sesi hazırla'yı kullan veya internet ve disk alanını kontrol edip yeniden dene.", "Voice is not ready. Use Prepare voice, or check internet and disk space and retry.")
        self.status.setText(self.t(*message))

    def stop_and_wait(self):
        return self.task.stop()
