"""User-facing control center for Nexus Memory 2.0."""

from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from backend.memory import MEMORY_TYPES, MemoryRepository, memory_repository
from backend.memory_jobs import MemoryJobStatus
from backend.user_settings import settings_store


class MemoryDialog(QDialog):
    def __init__(
        self,
        repository: MemoryRepository = memory_repository,
        parent=None,
        focus_memory_id: str | None = None,
    ):
        super().__init__(parent)
        self.repository = repository
        self._memories: list[dict] = []
        self.setWindowTitle("Nexus · Kişisel Hafıza")
        self.setMinimumSize(860, 620)

        root = QVBoxLayout(self)
        title = QLabel("Kişiselleştirme · Hafıza")
        title.setObjectName("dialogTitle")
        root.addWidget(title)
        explanation = QLabel(
            "Nexus'un bildiği her şey yerel olarak saklanır. Aday kayıtlar, siz "
            "etkinleştirene kadar cevaplarda kullanılmaz."
        )
        explanation.setWordWrap(True)
        root.addWidget(explanation)
        self.learning_status = QLabel()
        self.learning_status.setWordWrap(True)
        root.addWidget(self.learning_status)

        summary_form = QFormLayout()
        self.summary = QTextEdit()
        self.summary.setPlaceholderText("Nexus'un sizi nasıl tanıması gerektiğinin kısa özeti…")
        self.summary.setMaximumHeight(88)
        self.summary.setPlainText(repository.profile_summary())
        summary_form.addRow("Hafıza özeti", self.summary)
        root.addLayout(summary_form)

        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Hafızada ara…")
        self.search.textChanged.connect(self.refresh)
        filters.addWidget(self.search, 1)
        self.type_filter = QComboBox()
        self.type_filter.addItem("Tüm türler", "")
        for value in sorted(MEMORY_TYPES):
            self.type_filter.addItem(value, value)
        self.type_filter.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.type_filter)
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm durumlar", "")
        for value in ("candidate", "active", "superseded", "disabled"):
            self.status_filter.addItem(value, value)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.status_filter)
        root.addLayout(filters)

        splitter = QSplitter()
        self.list = QListWidget()
        self.list.currentItemChanged.connect(self.load_selected)
        splitter.addWidget(self.list)

        editor = QWidget()
        editor_layout = QVBoxLayout(editor)
        form = QFormLayout()
        self.content = QTextEdit()
        self.content.setMinimumHeight(110)
        form.addRow("İçerik", self.content)
        self.memory_type = QComboBox()
        for value in sorted(MEMORY_TYPES):
            self.memory_type.addItem(value, value)
        form.addRow("Tür", self.memory_type)
        self.scope = QComboBox()
        self.scope.addItem("Global", "global")
        self.scope.addItem("Proje", "project")
        form.addRow("Kapsam", self.scope)
        self.project_id = QLineEdit()
        form.addRow("Proje kimliği", self.project_id)
        self.status = QComboBox()
        for value in ("candidate", "active", "superseded", "disabled"):
            self.status.addItem(value, value)
        form.addRow("Durum", self.status)
        self.confidence = QDoubleSpinBox()
        self.confidence.setRange(0, 1)
        self.confidence.setSingleStep(0.05)
        form.addRow("Güven", self.confidence)
        self.importance = QDoubleSpinBox()
        self.importance.setRange(0, 1)
        self.importance.setSingleStep(0.05)
        form.addRow("Önem", self.importance)
        self.pinned = QCheckBox("Her zaman önceliklendir")
        form.addRow("Sabitle", self.pinned)
        self.source = QLabel("—")
        self.source.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow("Kaynak", self.source)
        editor_layout.addLayout(form)

        actions = QHBoxLayout()
        save = QPushButton("Değişiklikleri kaydet")
        save.clicked.connect(self.save_selected)
        actions.addWidget(save)
        activate = QPushButton("Adayı etkinleştir")
        activate.clicked.connect(self.activate_selected)
        actions.addWidget(activate)
        delete = QPushButton("Unut")
        delete.clicked.connect(self.delete_selected)
        actions.addWidget(delete)
        editor_layout.addLayout(actions)
        splitter.addWidget(editor)
        splitter.setSizes([330, 500])
        root.addWidget(splitter, 1)

        footer = QHBoxLayout()
        self.counts = QLabel()
        footer.addWidget(self.counts)
        footer.addStretch()
        refresh = QPushButton("Yenile")
        refresh.setToolTip("Arka plandaki hafıza işleminin durumunu ve yeni adayları getirir.")
        refresh.clicked.connect(self.refresh)
        footer.addWidget(refresh)
        export = QPushButton("JSON dışa aktar")
        export.clicked.connect(self.export_json)
        footer.addWidget(export)
        delete_all = QPushButton("Tüm hafızayı sil")
        delete_all.clicked.connect(self.delete_everything)
        footer.addWidget(delete_all)
        close = QPushButton("Kapat")
        close.clicked.connect(self.accept)
        footer.addWidget(close)
        root.addLayout(footer)
        self.refresh()
        if focus_memory_id:
            self.focus_memory(focus_memory_id)

    def _selected_id(self) -> str | None:
        item = self.list.currentItem()
        return str(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def focus_memory(self, memory_id: str) -> None:
        for index in range(self.list.count()):
            item = self.list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == memory_id:
                self.list.setCurrentItem(item)
                return

    def refresh(self) -> None:
        preferences = settings_store.load()
        job = MemoryJobStatus(self.repository.path).latest()
        detail = "Henüz bir otomatik hafıza işlemi yok."
        if job:
            detail = {
                "running": "Son işlem başladı; sonuç henüz kaydedilmedi. Uygulama kapandıysa işlem yarım kalmış olabilir.",
                "completed": f"Son işlem: {job['count']} yeni aday. Adayları seçip etkinleştirin.",
                "failed": "Son işlem başarısız: model bağlantısını ve JSON desteğini kontrol edin.",
                "model_unavailable": "Hafıza kaydedilemedi: yerel model sunucusuna ulaşılamıyor.",
                "timeout": "Hafıza çıkarma zaman aşımına uğradı; model yükünü kontrol edin.",
                "invalid_output": "Hafıza kaydedilemedi: model beklenen JSON biçimini döndürmedi.",
                "cancelled": "Son işlem iptal edildi.",
            }.get(job["state"], "")
        self.learning_status.setText(
            f"Hafızayı kullanma: {'açık' if preferences.memory_enabled else 'kapalı'} · "
            f"Otomatik aday çıkarma: {'açık' if preferences.memory_auto_learn else 'kapalı'}\n{detail}"
        )
        selected_id = self._selected_id()
        query = self.search.text().strip().casefold()
        type_filter = str(self.type_filter.currentData() or "")
        status_filter = str(self.status_filter.currentData() or "")
        self._memories = self.repository.list()
        self.list.clear()
        for memory in self._memories:
            if query and query not in str(memory["content"]).casefold():
                continue
            if type_filter and memory["memory_type"] != type_filter:
                continue
            if status_filter and memory["status"] != status_filter:
                continue
            prefix = "★ " if memory["pinned"] else ""
            item_text = f"{prefix}{memory['content'][:72]}\n{memory['memory_type']} · {memory['status']}"
            self.list.addItem(item_text)
            item = self.list.item(self.list.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, memory["id"])
            if memory["id"] == selected_id:
                self.list.setCurrentItem(item)
        active = sum(item["status"] == "active" for item in self._memories)
        candidates = sum(item["status"] == "candidate" for item in self._memories)
        self.counts.setText(f"{len(self._memories)} kayıt · {active} aktif · {candidates} aday")
        if not self.list.currentItem() and self.list.count():
            self.list.setCurrentRow(0)

    def load_selected(self) -> None:
        memory_id = self._selected_id()
        memory = next((item for item in self._memories if item["id"] == memory_id), None)
        if not memory:
            return
        self.content.setPlainText(str(memory["content"]))
        self.memory_type.setCurrentIndex(self.memory_type.findData(memory["memory_type"]))
        self.scope.setCurrentIndex(self.scope.findData(memory["scope"]))
        self.project_id.setText(str(memory.get("project_id") or ""))
        self.status.setCurrentIndex(self.status.findData(memory["status"]))
        self.confidence.setValue(float(memory["confidence"]))
        self.importance.setValue(float(memory["importance"]))
        self.pinned.setChecked(bool(memory["pinned"]))
        source = memory.get("source_conversation_id") or "Elle kaydedildi"
        self.source.setText(str(source))

    def save_selected(self) -> None:
        memory_id = self._selected_id()
        if not memory_id:
            self.repository.set_profile_summary(self.summary.toPlainText())
            return
        project_id = self.project_id.text().strip() or None
        try:
            self.repository.update(
                memory_id,
                self.content.toPlainText(),
                enabled=self.status.currentData() != "disabled",
                memory_type=str(self.memory_type.currentData()),
                scope=str(self.scope.currentData()),
                project_id=project_id,
                status=str(self.status.currentData()),
                confidence=self.confidence.value(),
                importance=self.importance.value(),
                pinned=self.pinned.isChecked(),
            )
            self.repository.set_profile_summary(self.summary.toPlainText())
        except ValueError as exc:
            QMessageBox.warning(self, "Hafıza kaydedilemedi", str(exc))
            return
        self.refresh()

    def activate_selected(self) -> None:
        memory_id = self._selected_id()
        if memory_id and self.repository.activate(memory_id):
            self.refresh()

    def delete_selected(self) -> None:
        memory_id = self._selected_id()
        if memory_id and self.repository.delete(memory_id):
            self.refresh()

    def export_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Hafızayı dışa aktar", "nexus-memory.json", "JSON (*.json)"
        )
        if path:
            payload = {
                "summary": self.repository.profile_summary(),
                "memories": self.repository.list(),
            }
            Path(path).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

    def delete_everything(self) -> None:
        answer = QMessageBox.warning(
            self,
            "Tüm hafızayı sil",
            "Hafıza özeti, kayıtlar ve sürüm geçmişi kalıcı olarak silinecek.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.repository.delete_all()
            self.summary.clear()
            self.refresh()
