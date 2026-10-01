"""Wake listener lifecycle, consent checks, and exclusive microphone handoff."""

import time

from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from backend.user_settings import settings_store
from backend.wake_word import LocalWakeDetector
from frontend.brand import ACCENT, brand_icon
from frontend.wake_worker import WakeWordWorker


class WakeController(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.worker = None
        self.detector = LocalWakeDetector()
        preferences = settings_store.load()
        self.consented = preferences.wake_word_enabled
        self.enabled = preferences.wake_word_enabled and preferences.wake_word_on_startup
        self.snooze_until = 0.0
        self.cooldown_until = 0.0
        self.pending = None
        self.detected = False
        self.closed = False
        self.error = ""
        self.state = "Kapalı"
        self.tray = QSystemTrayIcon(self)
        self._tray_active = None
        self.menu = QMenu(window)
        self.status_action = self.menu.addAction("Hey Nexus · Kapalı")
        self.status_action.setEnabled(False)
        self.toggle_action = self.menu.addAction("Hey Nexus: devam et", self.toggle)
        self.snooze_action = self.menu.addAction("15 dakika ertele", self.snooze)
        self.menu.addSeparator()
        self.show_action = self.menu.addAction("Nexus'u göster", self.show_window)
        self.settings_action = self.menu.addAction("Ayarlar", window.open_settings)
        self.quit_action = self.menu.addAction("Çıkış", window.request_quit)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._activated)
        self._set_state("Kapalı")
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.tick)
        self.timer.start()

    def _activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()

    def show_window(self):
        self.window.open_full_chat()

    def _set_state(self, state):
        tr = self.window.ui_text
        self.window.wake_button.setVisible(settings_store.load().wake_word_enabled)
        self.state = state
        listening = state.startswith("Dinliyor")
        self.window.set_wake_visual(listening)
        self.window.wake_button.setText(tr("● Hey Nexus · Dinliyor" if listening else "○ Hey Nexus · Beklemede"))
        if not self.enabled:
            self.window.wake_button.setText(tr("○ Hey Nexus · Kapalı"))
        if self.error:
            self.window.wake_button.setText(tr("○ Hey Nexus · Kontrol gerekli"))
        self.window.wake_button.setToolTip(tr("Hey Nexus · {state}\nTıkla: duraklat / devam et", state=tr(state)))
        self.window.wake_button.setAccessibleDescription(self.window.wake_button.toolTip())
        self.window.wake_button.setStyleSheet(f"color: {ACCENT}" if listening else "color: #a1a1aa")
        self.status_action.setText(f"Hey Nexus · {tr(state)}")
        self.toggle_action.setText(tr("Hey Nexus: duraklat" if self.enabled else "Hey Nexus: devam et"))
        for action, source in ((self.snooze_action, "15 dakika ertele"),
                               (self.show_action, "Nexus'u göster"),
                               (self.settings_action, "Ayarlar"), (self.quit_action, "Çıkış")):
            action.setText(tr(source))
        self.tray.setToolTip(f"Nexus · Hey Nexus: {tr(state)}")
        if listening != self._tray_active:
            self.tray.setIcon(brand_icon(active=listening))
            self._tray_active = listening

    def busy(self):
        window = self.window
        return bool(
            window._quitting or QApplication.activeModalWidget()
            or window.voice_record_worker or window.worker
            or window.stream_voice_worker or window.current_audio_path or window.audio_queue
        )

    def allowed(self):
        return bool(not self.closed and self.enabled and settings_store.load().wake_word_enabled
                    and time.monotonic() >= self.snooze_until)

    def stop_worker(self):
        self.detected = False  # A UI stop invalidates any queued wake handoff.
        if self.worker:
            self.worker.cancel()
            self._set_state("Durduruluyor")

    def reconfigure(self):
        self.stop_worker()
        self.pending = None
        self.detected = False
        consented = settings_store.load().wake_word_enabled
        if not consented:
            self.enabled = False
            self.snooze_until = 0.0
            self.error = ""
        elif not self.consented:
            # Only a new explicit grant starts listening. Saving unrelated
            # settings must not undo pause, snooze or a failed-device stop.
            self.enabled = True
            self.snooze_until = 0.0
            self.error = ""
        self.consented = consented
        self.tick()

    def toggle(self):
        if not settings_store.load().wake_word_enabled:
            self.window.open_settings()
            return
        self.enabled = time.monotonic() < self.snooze_until or not self.enabled
        self.error = ""
        self.snooze_until = 0.0
        self.pending = None
        self.detected = False
        self.tick()

    def snooze(self):
        self.snooze_until = time.monotonic() + 15 * 60
        self.pending = None
        self.detected = False
        self.tick()

    def cancel_pending(self):
        self.pending = None
        self.detected = False
        self.cooldown_until = time.monotonic() + 4

    def defer_microphone(self, callback):
        """Return True when a worker must release its microphone before F2 starts."""
        if self.worker is None:
            return False
        self.pending = callback
        self.detected = False
        self.stop_worker()
        return True

    def tick(self):
        if self.closed:
            return
        if not self.allowed() or self.busy() or self.pending:
            self.stop_worker()
            if not self.worker:
                state = self.error or ("15 dakika ertelendi" if time.monotonic() < self.snooze_until
                                       else "Duraklatıldı" if not self.allowed() else "Asistan meşgul")
                self._set_state(state)
            return
        if time.monotonic() < self.cooldown_until:
            if not self.worker:
                self._set_state("Bekleme süresi")
            return
        # Without a tray there must be a visible window indicator.
        if not self.window.isVisible() and not self.tray.isVisible():
            self.stop_worker()
            if not self.worker:
                self._set_state("Görünür gösterge bekleniyor")
            return
        if self.worker is None:
            worker = WakeWordWorker(settings_store.load(), self.detector)
            self.worker = worker
            worker.state_changed.connect(lambda state: self._worker_state(worker, state))
            worker.detected.connect(lambda: self._detected(worker))
            worker.failed.connect(lambda message: self._failed(worker, message))
            worker.finished.connect(lambda: self._finished(worker))
            self.window._track_worker(worker)
            worker.start()

    def _worker_state(self, worker, state):
        if self.worker is worker and not worker.isInterruptionRequested():
            self._set_state(state)

    def _detected(self, worker):
        if (self.worker is worker and not worker.isInterruptionRequested()
                and self.allowed() and not self.busy() and self._has_indicator()
                and self._fresh_detection(worker)):
            self.detected = True

    def _has_indicator(self):
        return self.window.isVisible() or self.tray.isVisible()

    @staticmethod
    def _fresh_detection(worker):
        # Queued Qt signals can arrive long after inference if the UI was busy.
        return time.monotonic() <= getattr(worker, "detection_deadline", 0.0)

    def _failed(self, worker, message):
        if self.worker is worker and not worker.isInterruptionRequested():
            self.enabled = False  # No automatic retry loop on a broken device/model.
            self.error = message
            self._set_state(message)

    def _finished(self, worker):
        if self.worker is not worker:
            return
        self.worker = None
        callback, self.pending = self.pending, None
        detected, self.detected = self.detected, False
        self.cooldown_until = time.monotonic() + 4
        if self.closed or self.window._quitting:
            return
        if callback:
            if self.window.isVisible() and not QApplication.activeModalWidget():
                callback()
        elif (detected and not worker.isInterruptionRequested() and self.allowed()
              and not self.busy() and self._has_indicator() and self._fresh_detection(worker)):
            self.show_window()
            self.window.toggle_voice_recording(wake_triggered=True)
        self.tick()

    def close(self):
        self.closed = True
        self.timer.stop()
        self.pending = None
        self.detected = False
        self.stop_worker()
        self.tray.hide()
