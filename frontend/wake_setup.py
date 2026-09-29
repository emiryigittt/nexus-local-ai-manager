"""Explicit, cancellable model preparation without opening a microphone."""

import json
import sys
from pathlib import Path

from PyQt6.QtCore import QProcess, QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from frontend.i18n import UiText


class WakeSetupPanel(QWidget):
    def __init__(self, language="tr", parent=None):
        super().__init__(parent)
        self.tr = UiText(language)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.status = QLabel(self.tr("Yerel model henüz kontrol edilmedi. Bu kontrol mikrofonu açmaz."))
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        row = QHBoxLayout()
        self.check = QPushButton(self.tr("Modeli kontrol et"))
        self.download = QPushButton(self.tr("Modeli hazırla…"))
        self.cancel = QPushButton(self.tr("İşlemi durdur"))
        self.cancel.setEnabled(False)
        for button in (self.check, self.download, self.cancel):
            row.addWidget(button)
        layout.addLayout(row)
        self.check.clicked.connect(lambda: self.start())
        self.download.clicked.connect(self.confirm_download)
        self.cancel.clicked.connect(self.stop)
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(lambda: self.process.readAllStandardError())
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        self.timeout = QTimer(self)
        self.timeout.setSingleShot(True)
        self.timeout.setInterval(5 * 60 * 1000)
        self.timeout.timeout.connect(self.timed_out)
        self.buffer = b""
        self.stage = ""
        self.cancelled = False
        self.expired = False
        self.download_requested = False

    @property
    def busy(self):
        return self.process.state() != QProcess.ProcessState.NotRunning

    def confirm_download(self):
        if self.busy:
            return
        answer = QMessageBox.question(
            self, self.tr("Yerel ses modelini hazırla"),
            self.tr("Whisper base dosyaları Hugging Face (Systran/faster-whisper-base) üzerinden indirilebilir. "
                    "İnternet ve disk alanı kullanılır. Mikrofon açılmaz; ses veya sohbet gönderilmez. "
                    "Bu işlem dinleme izni vermez. İptalde önbellekte kısmi dosyalar kalabilir. Devam edilsin mi?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.start(download=True)

    def start(self, *, download=False):
        if self.busy:
            return
        self.cancelled = self.expired = False
        self.download_requested = download
        self.buffer = b""
        self.stage = ""
        self.set_busy(True)
        self.status.setText(self.tr("Model hazırlanıyor… Mikrofon kapalı."))
        script = Path(__file__).resolve().parents[1] / "scripts" / "setup_wake_model.py"
        self.process.setProgram(sys.executable)
        self.process.setArguments([str(script)] + (["--download"] if download else []))
        self.timeout.start()
        self.process.start()

    def set_busy(self, busy):
        self.check.setEnabled(not busy)
        self.download.setEnabled(not busy)
        self.cancel.setEnabled(busy)

    def read_output(self):
        self.buffer += bytes(self.process.readAllStandardOutput())
        for line in self.buffer.split(b"\n")[:-1]:
            try:
                event = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                continue
            if not isinstance(event, dict):
                continue
            stage = event.get("stage")
            messages = {
                "checking": "Yerel önbellek kontrol ediliyor… Mikrofon kapalı.",
                "downloading": "Model dosyaları indiriliyor… Mikrofon kapalı.",
                "validating": "Model çevrimdışı yüklenerek doğrulanıyor… Mikrofon kapalı.",
                "ready": "Model doğrulandı; dinleme izni ayrı verilir. Mikrofon erişimi test edilmedi.",
                "failed": self.failure_message(),
            }
            if isinstance(stage, str) and stage in messages and not self.cancelled:
                self.stage = stage
                # Success is shown only after a clean process exit.
                if stage != "ready":
                    self.status.setText(self.tr(messages[stage]))
        self.buffer = self.buffer.rsplit(b"\n", 1)[-1][-4096:]

    def finished(self, exit_code, exit_status):
        self.read_output()
        self.timeout.stop()
        self.set_busy(False)
        if self.expired:
            source = "Model hazırlığı zaman aşımına uğradı. Yeniden deneyebilirsiniz."
        elif self.cancelled:
            source = "İşlem durduruldu. Dinleme izinleri değişmedi; kısmi indirme önbellekte kalabilir."
        elif exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit and self.stage == "ready":
            source = "Model doğrulandı; dinleme izni ayrı verilir. Mikrofon erişimi test edilmedi."
        else:
            source = self.failure_message()
        self.status.setText(self.tr(source))

    def failure_message(self):
        if self.download_requested:
            return "Model hazırlanamadı. İnternet, disk alanı ve model önbelleğini kontrol edip yeniden deneyin."
        return "Yerel model bulunamadı veya yüklenemedi. Modeli hazırla seçeneğini kullanabilirsiniz."

    def process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.timeout.stop()
            self.set_busy(False)
            self.status.setText(self.tr("Model kontrolü başlatılamadı. Nexus kurulumunu kontrol edin."))

    def stop(self):
        self.cancelled = True
        self.timeout.stop()
        if self.busy:
            self.process.kill()

    def timed_out(self):
        self.expired = True
        self.stop()

    def stop_and_wait(self):
        """A dialog must not leave a download process behind when it is dismissed."""
        if self.busy:
            self.stop()
            self.process.waitForFinished(1000)
        return not self.busy
