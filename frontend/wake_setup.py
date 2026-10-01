"""Model preparation and an explicitly triggered, bounded microphone check."""

import json
import sys
from dataclasses import replace
from pathlib import Path

from PyQt6.QtCore import QProcess, QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from backend.runtime import frozen
from backend.user_settings import settings_store
from backend.wake_word import LocalWakeDetector
from frontend.i18n import UiText
from frontend.setup_task import SetupTask
from frontend.wake_worker import WakeWordWorker


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
        self.microphone_test = QPushButton(self.tr("Çağrıyı dene (5 sn)"))
        self.microphone_test.setToolTip(self.tr("Yalnızca tıklayınca mikrofon beş saniye açılır. Hey Nexus deyip durakla. Ses kaydedilmez veya gönderilmez."))
        self.microphone_test.clicked.connect(self.start_microphone_test)
        layout.addWidget(self.microphone_test)
        self.test_worker = None
        self.test_owner = None
        self.test_start_timer = QTimer(self)
        self.test_start_timer.setSingleShot(True)
        self.test_start_timer.setInterval(50)
        self.test_start_timer.timeout.connect(self.start_test_worker)
        self.test_found = False
        self.test_error = ""
        self.test_timer = QTimer(self)
        self.test_timer.setSingleShot(True)
        self.test_timer.setInterval(5000)
        self.test_timer.timeout.connect(self.stop_microphone_test)
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
        self.frozen_task = SetupTask(self) if frozen() else None
        if self.frozen_task:
            self.frozen_task.event_received.connect(self.consume_event)
            self.frozen_task.completed.connect(lambda success: self.finished(0 if success else 1, QProcess.ExitStatus.NormalExit))

    @property
    def busy(self):
        if self.test_worker:
            return True
        if self.frozen_task:
            return self.frozen_task.busy
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
        if self.frozen_task:
            self.frozen_task.start("prepare-whisper", "setup_wake_model.py", ["--download"] if download else [], timeout=5 * 60 * 1000)
            return
        script = Path(__file__).resolve().parents[1] / "scripts" / "setup_wake_model.py"
        self.process.setProgram(sys.executable)
        self.process.setArguments([str(script)] + (["--download"] if download else []))
        self.timeout.start()
        self.process.start()

    def set_busy(self, busy):
        self.check.setEnabled(not busy)
        self.download.setEnabled(not busy)
        self.cancel.setEnabled(busy)
        self.microphone_test.setEnabled(not busy)

    def start_microphone_test(self):
        if self.busy:
            return
        preferences = settings_store.load()
        owner = self.parent()
        if hasattr(owner, "input"):
            preferences = replace(preferences, voice_input_device=owner.input.currentData() or "",
                                  wake_word_threshold=owner.wake_threshold.value() / 100)
        self.test_threshold = preferences.wake_word_threshold
        self.test_found, self.test_error = False, ""
        owner = self.parent()
        while owner is not None and not hasattr(owner, "_track_worker"):
            owner = owner.parent()
        self.test_owner = owner
        detector = owner.wake.detector if owner else LocalWakeDetector()
        worker = WakeWordWorker(preferences, detector)
        # Track the diagnostic during application shutdown as well as closing
        # settings. Wait for ambient capture to release the same microphone.
        worker.setParent(self)
        self.test_worker = worker
        worker.state_changed.connect(self.test_state)
        worker.detected.connect(self.test_detected)
        worker.failed.connect(self.test_failed)
        worker.finished.connect(self.test_finished)
        if owner:
            owner._track_worker(worker)
            owner.wake.stop_worker()
        self.set_busy(True)
        self.status.setText(self.tr("Model hazırlanıyor… Mikrofon kapalı."))
        self.timeout.start(15_000)  # Also bound model preparation before capture.
        self.start_test_worker()

    def start_test_worker(self):
        worker = self.test_worker
        if worker is None:
            return
        if self.test_owner and self.test_owner._quitting:
            worker.cancel()
        if (not worker.isInterruptionRequested() and self.test_owner
                and self.test_owner.wake.worker is not None):
            self.test_start_timer.start()
            return
        worker.start()

    def test_state(self, state):
        if (self.test_worker and not self.test_worker.isInterruptionRequested()
                and state.startswith("Dinliyor") and not self.test_timer.isActive()):
            self.test_timer.start()
            self.status.setText(self.tr("Mikrofon açık · şimdi Hey Nexus deyip durakla. Test beş saniyede biter."))

    def test_detected(self):
        self.test_found = True

    def test_failed(self, message):
        self.test_error = message

    def stop_microphone_test(self):
        if self.test_worker:
            self.test_worker.cancel()

    def test_finished(self):
        worker, self.test_worker = self.test_worker, None
        self.test_start_timer.stop()
        self.test_timer.stop()
        self.timeout.stop()
        self.set_busy(False)
        if self.test_error:
            self.status.setText(self.tr(self.test_error))
        elif self.test_found:
            self.status.setText(self.tr("Hey Nexus algılandı. Test tamamlandı; mikrofon kapalı."))
        elif getattr(worker.capture, "peak_level", 0) < self.test_threshold:
            self.status.setText(self.tr("Ses eşiğine ulaşılmadı. Doğru mikrofonu seç veya Çağrı ses eşiğini azaltıp tekrar dene. Mikrofon kapalı."))
        else:
            self.status.setText(self.tr("Ses geldi ama çağrı algılanmadı. Hey Nexus deyip kısa bir duraklama yaparak tekrar dene. Mikrofon kapalı."))
        worker.deleteLater()

    def read_output(self):
        self.buffer += bytes(self.process.readAllStandardOutput())
        for line in self.buffer.split(b"\n")[:-1]:
            try:
                event = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                continue
            if not isinstance(event, dict):
                continue
            self.consume_event(event)
        self.buffer = self.buffer.rsplit(b"\n", 1)[-1][-4096:]

    def consume_event(self, event):
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
        self.stop_microphone_test()
        if self.frozen_task:
            self.frozen_task.stop()
            return
        if self.busy:
            self.process.kill()

    def timed_out(self):
        self.expired = True
        self.stop()

    def stop_and_wait(self):
        """A dialog must not leave a download process behind when it is dismissed."""
        if self.test_worker:
            self.test_worker.cancel()
            if self.test_start_timer.isActive():
                self.test_start_timer.stop()
                self.start_test_worker()  # Cancelled worker exits without capture.
            if not self.test_worker.wait(1500):
                return False
        if self.busy:
            self.stop()
            self.process.waitForFinished(1000)
        return not self.busy or (self.test_worker is not None and not self.test_worker.isRunning())
