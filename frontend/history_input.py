from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLineEdit

from frontend.history import PromptHistory


class HistoryLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.history = PromptHistory(max_history=50)

    def add_to_history(self, text: str) -> None:
        self.history.add(text)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            text = self.history.get_previous()
            if text:
                self.setText(text)
                event.accept()
        elif event.key() == Qt.Key.Key_Down:
            text = self.history.get_next()
            self.setText(text)
            event.accept()
        else:
            super().keyPressEvent(event)