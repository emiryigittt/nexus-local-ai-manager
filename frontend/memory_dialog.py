"""User-facing control center for Nexus Memory 2.0."""

from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
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
    QScrollArea,
    QSplitter,
    QStyle,
    QStyledItemDelegate,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from backend.memory import MEMORY_TYPES, MemoryRepository, memory_repository
from backend.memory_jobs import MemoryJobStatus
from backend.user_settings import settings_store
from frontend.appearance import readable_accent, themed_style
from frontend.i18n import UiText

TYPES = {"preference": "Tercih", "fact": "Bilgi", "goal": "Hedef", "instruction": "Talimat", "project_decision": "Proje kararı"}
STATUSES = {"candidate": "Onay bekliyor", "active": "Etkin", "superseded": "Eski sürüm", "disabled": "Devre dışı"}


class MemoryCardDelegate(QStyledItemDelegate):
    def __init__(self, color, parent):
        super().__init__(parent)
        self.accent = readable_accent(color)

    def sizeHint(self, option, index):
        return QSize(1, 82)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        bounds = QRectF(option.rect).adjusted(2, 3, -2, -3)
        painter.setBrush(QColor("#293b3a" if selected else "#22292d"))
        painter.setPen(QPen(self.accent if selected else QColor("#374246"), 1))
        painter.drawRoundedRect(bounds, 11, 11)
        text, metadata = str(index.data()).split("\n", 1)
        painter.setPen(QColor("#edf1f0"))
        font = QFont(option.font)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        title = painter.fontMetrics().elidedText(text, Qt.TextElideMode.ElideRight, int(bounds.width()) - 24)
        painter.drawText(bounds.adjusted(12, 11, -12, -35), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)
        font.setWeight(QFont.Weight.Normal)
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(self.accent if selected else QColor("#acbabb"))
        subtitle = painter.fontMetrics().elidedText(metadata, Qt.TextElideMode.ElideRight, int(bounds.width()) - 24)
        painter.drawText(bounds.adjusted(12, 41, -12, -10), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, subtitle)
        painter.restore()


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
        preferences = settings_store.load()
        self.ui = UiText(preferences.language)
        ui = self.ui
        self.setWindowTitle(ui("Nexus · Kişisel Hafıza"))
        self.setStyleSheet(themed_style(preferences.accent_color))
        self.setMinimumSize(620, 480)
        self.resize(920, 680)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 18)
        root.setSpacing(12)
        title = QLabel(ui("Seni tanıyan bir hafıza"))
        title.setObjectName("dialogTitle")
        root.addWidget(title)
        explanation = QLabel(ui("Kayıtlar bu bilgisayarda saklanır. Önerileri incele; neyi hatırlayacağına sen karar ver."))
        explanation.setObjectName("settingsNote")
        explanation.setWordWrap(True)
        root.addWidget(explanation)
        self.learning_status = QLabel()
        self.learning_status.setObjectName("settingsNote")
        self.learning_status.setWordWrap(True)
        root.addWidget(self.learning_status)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        records = QWidget()
        record_layout = QVBoxLayout(records)
        record_layout.setContentsMargins(0, 14, 0, 0)
        self.tabs.addTab(records, ui("Kayıtlar"))
        profile = QWidget()
        profile_layout = QVBoxLayout(profile)
        profile_layout.setContentsMargins(0, 18, 0, 0)
        profile_layout.addWidget(QLabel(ui("Nexus seni nasıl tanısın?")))
        self.summary = QTextEdit()
        self.summary.setPlaceholderText(ui("Tercihlerin ve çalışma biçimin hakkında kısa bir özet…"))
        self.summary.setPlainText(repository.profile_summary())
        profile_layout.addWidget(self.summary, 1)
        summary_save = QPushButton(ui("Özeti kaydet"))
        summary_save.setProperty("primary", True)
        summary_save.clicked.connect(self.save_summary)
        profile_layout.addWidget(summary_save, alignment=Qt.AlignmentFlag.AlignLeft)
        self.summary_feedback = QLabel()
        self.summary_feedback.setObjectName("settingsNote")
        profile_layout.addWidget(self.summary_feedback)
        self.tabs.addTab(profile, ui("Profil özeti"))

        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(ui("Hafızada ara…"))
        self.search.setAccessibleName(ui("Hafızada ara…"))
        self.search.textChanged.connect(self.refresh)
        filters.addWidget(self.search, 1)
        self.type_filter = QComboBox()
        self.type_filter.addItem(ui("Tüm türler"), "")
        for value in sorted(MEMORY_TYPES):
            self.type_filter.addItem(ui(TYPES[value]), value)
        self.type_filter.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.type_filter)
        self.status_filter = QComboBox()
        self.status_filter.addItem(ui("Tüm durumlar"), "")
        for value in ("candidate", "active", "superseded", "disabled"):
            self.status_filter.addItem(ui(STATUSES[value]), value)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.status_filter)
        record_layout.addLayout(filters)

        splitter = QSplitter()
        self.list = QListWidget()
        self.list.setItemDelegate(MemoryCardDelegate(preferences.accent_color, self.list))
        self.list.setMinimumWidth(190)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setAccessibleName(ui("Hafıza kayıtları"))
        self.list.currentItemChanged.connect(self.load_selected)
        splitter.addWidget(self.list)

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(12, 0, 0, 0)
        self.editor = QWidget()
        editor_layout = QVBoxLayout(self.editor)
        editor_layout.setContentsMargins(0, 0, 8, 0)
        self.selection_title = QLabel(ui("Kaydı incele"))
        self.selection_title.setObjectName("sectionTitle")
        editor_layout.addWidget(self.selection_title)
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setSpacing(12)
        self.content = QTextEdit()
        self.content.setMinimumHeight(100)
        self.content.setMaximumHeight(140)
        self.content.setAccessibleName(ui("Hatırlanacak bilgi"))
        editor_layout.addWidget(self.content)
        self.memory_type = QComboBox()
        for value in sorted(MEMORY_TYPES):
            self.memory_type.addItem(ui(TYPES[value]), value)
        form.addRow(ui("Tür"), self.memory_type)
        self.status = QComboBox()
        for value in ("candidate", "active", "superseded", "disabled"):
            self.status.addItem(ui(STATUSES[value]), value)
        form.addRow(ui("Durum"), self.status)
        self.pinned = QCheckBox(ui("Bu bilgiyi önceliklendir"))
        form.addRow(self.pinned)
        editor_layout.addLayout(form)
        advanced_toggle = QPushButton(ui("Ayrıntılar"))
        advanced_toggle.setCheckable(True)
        editor_layout.addWidget(advanced_toggle, alignment=Qt.AlignmentFlag.AlignLeft)
        advanced = QWidget()
        advanced_form = QFormLayout(advanced)
        advanced_form.setContentsMargins(0, 0, 0, 0)
        advanced_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.scope = QComboBox()
        self.scope.addItem(ui("Genel"), "global")
        self.scope.addItem(ui("Proje"), "project")
        advanced_form.addRow(ui("Kapsam"), self.scope)
        self.project_id = QLineEdit()
        advanced_form.addRow(ui("Proje kimliği"), self.project_id)
        self.confidence = QDoubleSpinBox()
        self.confidence.setRange(0, 1)
        self.confidence.setSingleStep(0.05)
        advanced_form.addRow(ui("Güven"), self.confidence)
        self.importance = QDoubleSpinBox()
        self.importance.setRange(0, 1)
        self.importance.setSingleStep(0.05)
        advanced_form.addRow(ui("Önem"), self.importance)
        self.source = QLabel("—")
        self.source.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.source.setWordWrap(True)
        advanced_form.addRow(ui("Kaynak"), self.source)
        editor_layout.addWidget(advanced)
        advanced.hide()
        advanced_toggle.toggled.connect(advanced.setVisible)
        editor_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self.editor)
        detail_layout.addWidget(scroll, 1)

        actions = QHBoxLayout()
        self.save_button = QPushButton(ui("Kaydet"))
        self.save_button.setProperty("primary", True)
        self.save_button.clicked.connect(self.save_selected)
        actions.addWidget(self.save_button)
        self.activate_button = QPushButton(ui("Onayla"))
        self.activate_button.clicked.connect(self.activate_selected)
        actions.addWidget(self.activate_button)
        self.delete_button = QPushButton(ui("Unut"))
        self.delete_button.clicked.connect(self.delete_selected)
        actions.addWidget(self.delete_button)
        detail_layout.addLayout(actions)
        splitter.addWidget(detail)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([330, 500])
        record_layout.addWidget(splitter, 1)
        self.empty_state = QLabel(ui("Henüz kayıt yok. Sohbette /remember ile bir bilgi ekleyebilirsin."))
        self.empty_state.setObjectName("settingsNote")
        self.empty_state.setWordWrap(True)
        record_layout.addWidget(self.empty_state)

        footer = QHBoxLayout()
        self.counts = QLabel()
        self.counts.setObjectName("settingsNote")
        footer.addWidget(self.counts)
        footer.addStretch()
        refresh = QPushButton(ui("Yenile"))
        refresh.setToolTip("Arka plandaki hafıza işleminin durumunu ve yeni adayları getirir.")
        refresh.clicked.connect(self.refresh)
        footer.addWidget(refresh)
        export = QPushButton(ui("Dışa aktar"))
        export.clicked.connect(self.export_json)
        footer.addWidget(export)
        delete_all = QPushButton(ui("Tümünü sil"))
        delete_all.clicked.connect(self.delete_everything)
        footer.addWidget(delete_all)
        close = QPushButton(ui("Kapat"))
        close.clicked.connect(self.accept)
        footer.addWidget(close)
        root.addLayout(footer)
        self.refresh()
        if focus_memory_id:
            self.focus_memory(focus_memory_id)

    def save_summary(self):
        self.repository.set_profile_summary(self.summary.toPlainText())
        self.summary_feedback.setText(self.ui("Özet kaydedildi."))

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
        detail = self.ui("Henüz bir otomatik hafıza işlemi yok.")
        if job:
            detail = {
                "running": "Son işlem başladı; sonuç henüz kaydedilmedi. Uygulama kapandıysa işlem yarım kalmış olabilir.",
                "completed": self.ui("Son işlem: {count} yeni aday. Adayları seçip etkinleştirin.", count=job["count"]),
                "failed": "Son işlem başarısız: model bağlantısını ve JSON desteğini kontrol edin.",
                "model_unavailable": "Hafıza kaydedilemedi: yerel model sunucusuna ulaşılamıyor.",
                "timeout": "Hafıza çıkarma zaman aşımına uğradı; model yükünü kontrol edin.",
                "invalid_output": "Hafıza kaydedilemedi: model beklenen JSON biçimini döndürmedi.",
                "cancelled": "Son işlem iptal edildi.",
            }.get(job["state"], "")
        self.learning_status.setText(self.ui(
            "Hafıza: {enabled} · Otomatik öneriler: {learning}",
            enabled=self.ui("açık" if preferences.memory_enabled else "kapalı"),
            learning=self.ui("açık" if preferences.memory_auto_learn else "kapalı")) + "\n" + self.ui(detail))
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
            title = " ".join(str(memory["content"]).split())
            item_text = f"{prefix}{title}\n{self.ui(TYPES[memory['memory_type']])} · {self.ui(STATUSES[memory['status']])}"
            self.list.addItem(item_text)
            item = self.list.item(self.list.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, memory["id"])
            item.setToolTip(str(memory["content"]))
            if memory["id"] == selected_id:
                self.list.setCurrentItem(item)
        active = sum(item["status"] == "active" for item in self._memories)
        candidates = sum(item["status"] == "candidate" for item in self._memories)
        self.counts.setText(self.ui("{count} kayıt · {active} etkin · {candidates} aday",
                                   count=len(self._memories), active=active, candidates=candidates))
        if not self.list.currentItem() and self.list.count():
            self.list.setCurrentRow(0)
        self.empty_state.setVisible(not self.list.count())
        self.empty_state.setText(self.ui("Aramana uygun kayıt bulunamadı.") if self._memories else
                                 self.ui("Henüz kayıt yok. Sohbette /remember ile bir bilgi ekleyebilirsin."))
        self.load_selected()

    def load_selected(self) -> None:
        memory_id = self._selected_id()
        memory = next((item for item in self._memories if item["id"] == memory_id), None)
        self.editor.setEnabled(memory is not None)
        self.save_button.setEnabled(memory is not None)
        self.delete_button.setEnabled(memory is not None)
        self.activate_button.setEnabled(memory is not None and memory["status"] == "candidate")
        if not memory:
            self.content.clear()
            self.source.setText("—")
            self.selection_title.setText(self.ui("Kaydı incele"))
            return
        self.selection_title.setText(self.ui(STATUSES[memory["status"]]))
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
