"""Search and select locally stored conversations."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)

from backend.conversations import ConversationRepository, conversation_repository


class HistoryDialog(QDialog):
    def __init__(self, repository: ConversationRepository = conversation_repository, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.selected_conversation_id: str | None = None
        self.setWindowTitle("Konuşma geçmişi")
        self.setMinimumSize(560, 430)
        layout = QVBoxLayout(self)
        title = QLabel("Yerel konuşmalar")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Konuşmalarda ara…")
        self.search.textChanged.connect(self.refresh)
        layout.addWidget(self.search)
        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self.open_selected)
        layout.addWidget(self.list, 1)
        buttons = QHBoxLayout()
        delete = QPushButton("Sil")
        delete.clicked.connect(self.delete_selected)
        buttons.addWidget(delete)
        buttons.addStretch()
        close = QPushButton("Kapat")
        close.clicked.connect(self.reject)
        buttons.addWidget(close)
        open_button = QPushButton("Aç")
        open_button.clicked.connect(self.open_selected)
        buttons.addWidget(open_button)
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        for conversation in self.repository.list(self.search.text().strip()):
            pin = "★ " if conversation["pinned"] else ""
            self.list.addItem(f"{pin}{conversation['title']}")
            self.list.item(self.list.count() - 1).setData(
                Qt.ItemDataRole.UserRole, conversation["id"]
            )

    def open_selected(self) -> None:
        item = self.list.currentItem()
        if item:
            self.selected_conversation_id = item.data(Qt.ItemDataRole.UserRole)
            self.accept()

    def delete_selected(self) -> None:
        item = self.list.currentItem()
        if item and self.repository.delete(item.data(Qt.ItemDataRole.UserRole)):
            self.refresh()
