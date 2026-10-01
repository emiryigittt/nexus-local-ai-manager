"""Optional, brief local chimes. No sounds on hover, streaming chunks or wake polling."""

import time

from PyQt6.QtCore import QObject, QUrl
from PyQt6.QtMultimedia import QSoundEffect

from backend.runtime import resource_root


class SoundFeedback(QObject):
    NAMES = {"open", "collapse", "success", "attachment", "error", "listen"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled = False
        self.volume = .2
        self.effects = {}
        self.last_play = -1.0

    def configure(self, enabled, volume):
        self.enabled = bool(enabled)
        self.volume = max(0, min(100, int(volume))) / 100
        for effect in self.effects.values():
            effect.setVolume(self.volume)
        if not self.enabled:
            self.stop()

    def play(self, name, *, preview=False):
        if name not in self.NAMES or (not preview and not self.enabled) or not self.volume:
            return False
        if time.monotonic() - self.last_play < .15:
            return False
        path = resource_root() / "frontend/assets/sounds" / f"{name}.wav"
        if not path.is_file():
            return False
        self.stop()
        effect = self.effects.get(name)
        if effect is None:
            effect = QSoundEffect(self)
            effect.setSource(QUrl.fromLocalFile(str(path)))
            effect.setLoopCount(1)
            self.effects[name] = effect
        effect.setVolume(self.volume)
        effect.play()
        self.last_play = time.monotonic()
        return True

    def stop(self):
        for effect in self.effects.values():
            effect.stop()
