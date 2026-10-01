"""Top-edge anchor and delayed hover preview; never activates the editor on hover."""

from PyQt6.QtCore import QObject, QRect, QTimer
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication


class NotchController(QObject):
    SIZES = {"notch": (180, 36), "dock": (460, 188), "chat": (800, 640)}

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.pinned = False
        self.open_timer = QTimer(self)
        self.open_timer.setSingleShot(True)
        self.open_timer.setInterval(160)
        self.open_timer.timeout.connect(self._open_preview)
        self.close_timer = QTimer(self)
        self.close_timer.setSingleShot(True)
        self.close_timer.setInterval(350)
        self.close_timer.timeout.connect(self._close_preview)
        self.screen = window.screen() or QApplication.primaryScreen()
        self.screen.availableGeometryChanged.connect(self.reanchor)
        QApplication.instance().screenRemoved.connect(self._screen_removed)

    @classmethod
    def anchored_rect(cls, available, mode):
        width, height = cls.SIZES[mode]
        width = min(width, max(1, available.width() - (32 if mode == "chat" else 0)))
        height = min(height, max(1, available.height() - (32 if mode == "chat" else 0)))
        return QRect(available.left() + (available.width() - width) // 2,
                     available.top(), width, height)

    def target_rect(self, mode):
        if self.screen not in QApplication.screens():
            self.screen = QApplication.primaryScreen()
        return self.anchored_rect(self.screen.availableGeometry(), mode)

    def reanchor(self, *args):
        if self.window._shell_mode is not None and not self.window._quitting:
            self.window.shell_transition.finish()
            rect = self.target_rect(self.window._shell_mode)
            self.window.shell_transition.target = rect
            self.window.shell_transition._geometry(rect)

    def _screen_removed(self, screen):
        if screen is self.screen:
            self.screen = QApplication.primaryScreen()
            self.screen.availableGeometryChanged.connect(self.reanchor)
            self.reanchor()

    def pointer_inside(self):
        return self.window.geometry().contains(QCursor.pos())

    def enter(self):
        self.close_timer.stop()
        if self.window._shell_mode == "notch":
            self.open_timer.start()

    def leave(self):
        self.open_timer.stop()
        if self.window._shell_mode == "dock" and not self.pinned:
            self.close_timer.start()

    def _open_preview(self):
        if (self.window.isVisible() and self.window._shell_mode == "notch"
                and self.pointer_inside() and QApplication.activeModalWidget() is None):
            self.window.set_shell_mode("dock", transient=True)

    def _close_preview(self):
        if self.window._shell_mode != "dock" or self.pinned or not self.window.isVisible():
            return
        if QApplication.activeModalWidget() is not None:
            self.close_timer.start()
        elif not self.pointer_inside():
            self.window.set_shell_mode("notch")

    def mode_changed(self, mode, transient):
        self.stop()
        self.pinned = mode == "dock" and not transient
        self._sync_pin()

    def toggle_pin(self):
        self.pinned = not self.pinned
        self._sync_pin()
        if not self.pinned and not self.pointer_inside():
            self.leave()

    def _sync_pin(self):
        self.window.pin_button.setChecked(self.pinned)
        description = self.window.ui_text("Sabitlemeyi kaldır" if self.pinned else "Mini paneli sabitle")
        self.window.pin_button.setToolTip(description)
        self.window.pin_button.setAccessibleName(description)

    def stop(self):
        self.open_timer.stop()
        self.close_timer.stop()
