"""First-run and provider settings dialog."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from backend.user_settings import SettingsStore, settings_store
from frontend.api_client import request_json
from frontend.appearance import themed_style
from frontend.appearance_settings import AppearanceSettings
from frontend.design import settings_card
from frontend.i18n import UiText
from frontend.memory_dialog import MemoryDialog
from frontend.voice_settings import VoiceSettings


class SetupDialog(QDialog):
    def __init__(self, store: SettingsStore = settings_store, parent=None):
        super().__init__(parent)
        self.store = store
        self.results: dict[str, dict] = {}
        preferences = store.load()
        self.ui_text = UiText(preferences.language)
        tr = self.ui_text

        self.setWindowTitle(tr("Nexus · Ayarlar"))
        self.setStyleSheet(themed_style(preferences.accent_color))
        self.setMinimumWidth(480)
        self.setModal(True)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 20, 22, 16)
        outer.setSpacing(16)
        title = QLabel(tr("Nexus'u kendine göre ayarla"))
        title.setObjectName("dialogTitle")
        outer.addWidget(title)
        subtitle = QLabel(tr("Tercihlerin. Senin kontrolünde."))
        subtitle.setObjectName("settingsNote")
        outer.addWidget(subtitle)
        self.tabs = QTabWidget()
        outer.addWidget(self.tabs, 1)

        def page(name):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            content = QWidget()
            page_layout = QVBoxLayout(content)
            page_layout.setContentsMargins(8, 20, 12, 12)
            page_layout.setSpacing(14)
            scroll.setWidget(content)
            self.tabs.addTab(scroll, tr(name))
            return page_layout

        layout = page("Genel")
        privacy = page("Gizlilik")
        voice_layout = page("Ses")
        appearance_layout = page("Görünüm")
        screen = QApplication.primaryScreen()
        self.resize(640, min(720, screen.availableGeometry().height() - 80) if screen else 700)
        description = QLabel(tr(
            "Nexus çalışan LM Studio, Ollama ve llama.cpp sunucularını bulur. "
            "Dil modeli isteği seçtiğin yerel sağlayıcıda kalır."
        ))
        description.setWordWrap(True)
        description.setObjectName("settingsNote")
        layout.addWidget(description)

        model_card = settings_card(layout, tr("Çalışma alanın"))
        form = QFormLayout()
        form.setSpacing(14)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.language = QComboBox()
        self.language.addItem("Türkçe", "tr")
        self.language.addItem("English", "en")
        self.language.setCurrentIndex(max(0, self.language.findData(preferences.language)))
        form.addRow(tr("Dil"), self.language)

        self.provider = QComboBox()
        for item in preferences.providers:
            self.provider.addItem(f"{item.name} · {item.base_url}", item.id)
        self.provider.setCurrentIndex(
            max(0, self.provider.findData(preferences.selected_provider_id))
        )
        self.provider.currentIndexChanged.connect(self._fill_models)
        form.addRow(tr("Sağlayıcı"), self.provider)

        self.model = QComboBox()
        self.model.setEditable(True)
        self._fill_models()
        form.addRow(tr("Model"), self.model)
        self.embedding_model = QComboBox()
        self.embedding_model.setEditable(True)
        self.embedding_model.addItem(preferences.embedding_model)
        self.embedding_model.setToolTip(tr(
            "Örnek: nomic-embed-text. Boş bırakılırsa yalnızca anahtar kelime araması kullanılır."
        ))
        form.addRow(tr("Embedding modeli"), self.embedding_model)
        model_card.addLayout(form)
        self.reduced_motion = QCheckBox(tr("Hareketi azalt"))
        self.reduced_motion.setChecked(preferences.reduced_motion)
        self.reduced_motion.setToolTip(tr("Logo ve pencere animasyonlarını kapatır; durum bilgileri görünür kalır."))
        model_card.addWidget(self.reduced_motion)
        language_note = QLabel(tr(
            "Dil değişikliği Kaydet ile uygulanır. Ses, geçmiş ve hafıza pencerelerinin bazı metinleri henüz çevrilmedi."))
        language_note.setWordWrap(True)
        language_note.setObjectName("settingsNote")
        layout.addWidget(language_note)

        access_card = settings_card(privacy, tr("Erişim izinleri"))
        memory_card = settings_card(privacy, tr("Kişisel hafızan"))
        self.web_consent = QCheckBox(tr("Web araştırmasına gerektiğinde izin ver"))
        self.web_consent.setChecked(preferences.web_consent)
        access_card.addWidget(self.web_consent)
        self.cloud_speech = QCheckBox(tr("Bulut sesini gerektiğinde onayla ve kullan"))
        self.cloud_speech.setChecked(preferences.cloud_speech_consent)
        access_card.addWidget(self.cloud_speech)
        self.memory_enabled = QCheckBox(tr("Açıkça kaydettiğim kişisel hafızayı kullan"))
        self.memory_enabled.setChecked(preferences.memory_enabled)
        memory_card.addWidget(self.memory_enabled)
        self.memory_auto_learn = QCheckBox(tr(
            "Konuşmalardan yerel modelle hafıza adayları çıkar"
        ))
        self.memory_auto_learn.setChecked(preferences.memory_auto_learn)
        memory_card.addWidget(self.memory_auto_learn)
        self.memory_reference_history = QCheckBox(tr(
            "Konuşma ve proje özetlerini gelecekteki yanıtlarda kullan"
        ))
        self.memory_reference_history.setChecked(preferences.memory_reference_history)
        memory_card.addWidget(self.memory_reference_history)
        self.personal_questions = QCheckBox(tr("Uygun anlarda beni tanımak için kısa sorular sor"))
        self.personal_questions.setChecked(preferences.personal_questions_enabled)
        memory_card.addWidget(self.personal_questions)
        manage_memory = QPushButton(tr("Kişisel hafızayı yönet…"))
        manage_memory.clicked.connect(self.open_memory_manager)
        memory_card.addWidget(manage_memory, alignment=Qt.AlignmentFlag.AlignLeft)

        self.clipboard_policy = QComboBox()
        self.clipboard_policy.addItem(tr("Her kullanımda sor"), "ask")
        self.clipboard_policy.addItem(tr("Her zaman izin ver"), "always")
        self.clipboard_policy.addItem(tr("Pano erişimini engelle"), "never")
        self.clipboard_policy.setCurrentIndex(
            max(0, self.clipboard_policy.findData(preferences.clipboard_policy))
        )
        privacy_form = QFormLayout()
        privacy_form.addRow(tr("Pano erişimi"), self.clipboard_policy)
        access_card.addLayout(privacy_form)
        privacy.addStretch()

        self.voice = VoiceSettings(preferences)
        voice_layout.addWidget(self.voice)
        voice_layout.addStretch()
        self.appearance = AppearanceSettings(preferences, tr)
        appearance_layout.addWidget(self.appearance)
        self.reduced_motion.toggled.connect(self.appearance.set_reduced_motion)

        self.status = QLabel(tr("Çalışan yerel sağlayıcıları bulmak için tara."))
        self.status.setWordWrap(True)
        self.status.setObjectName("settingsNote")
        layout.addWidget(self.status)
        scan = QPushButton(tr("Yerel sağlayıcıları tara"))
        scan.clicked.connect(self.discover)
        layout.addWidget(scan, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()
        for combo in self.findChildren(QComboBox):
            combo.setMinimumContentsLength(18)
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(tr("Kaydet"))
        buttons.button(QDialogButtonBox.StandardButton.Save).setProperty("primary", True)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("Vazgeç"))
        outer.addWidget(buttons)

    def discover(self) -> None:
        self.status.setText(self.ui_text("Yerel sağlayıcılar aranıyor…"))
        try:
            discovered = request_json("POST", "/api/v1/providers/discover")
        except RuntimeError as exc:
            self.status.setText(str(exc))
            return
        self.results = {item["id"]: item for item in discovered}
        healthy = [item for item in discovered if item.get("healthy")]
        if not healthy:
            self.status.setText(self.ui_text(
                "Çalışan sağlayıcı bulunamadı. LM Studio, Ollama veya llama.cpp'yi başlatıp yeniden tara."
            ))
            return
        first_id = next(
            (item["id"] for item in healthy if item["id"] == self.provider.currentData()),
            healthy[0]["id"],
        )
        self.provider.setCurrentIndex(self.provider.findData(first_id))
        self._fill_models()
        self.status.setText(self.ui_text("{count} çalışan yerel sağlayıcı bulundu.", count=len(healthy)))

    def done(self, result):
        wake_stopped = self.voice.wake_setup.stop_and_wait()
        voice_stopped = self.voice.local_setup.stop_and_wait()
        speech_stopped = self.voice.speech_setup.stop()
        if wake_stopped and voice_stopped and speech_stopped:
            super().done(result)

    def open_memory_manager(self) -> None:
        MemoryDialog(parent=self).exec()

    def _fill_models(self) -> None:
        provider_id = self.provider.currentData()
        result = self.results.get(provider_id, {})
        self.model.clear()
        self.model.addItems(result.get("models", []))
        profile = next(
            (item for item in self.store.load().providers if item.id == provider_id), None
        )
        if profile and profile.selected_model:
            self.model.setCurrentText(profile.selected_model)

    def save(self) -> None:
        provider_id = str(self.provider.currentData())
        model_id = self.model.currentText().strip()
        preferences = self.store.load()
        preferences.language = str(self.language.currentData())
        preferences.reduced_motion = self.reduced_motion.isChecked()
        preferences.web_consent = self.web_consent.isChecked()
        preferences.cloud_speech_consent = self.cloud_speech.isChecked()
        preferences.memory_enabled = self.memory_enabled.isChecked()
        preferences.memory_auto_learn = self.memory_auto_learn.isChecked()
        preferences.memory_reference_history = self.memory_reference_history.isChecked()
        preferences.personal_questions_enabled = self.personal_questions.isChecked()
        preferences.clipboard_policy = str(self.clipboard_policy.currentData())
        preferences.selected_provider_id = provider_id
        preferences.embedding_model = self.embedding_model.currentText().strip()
        self.voice.apply(preferences)
        self.appearance.apply(preferences)
        preferences.setup_complete = True
        for item in preferences.providers:
            if item.id == provider_id:
                item.selected_model = model_id
                break
        self.store.save(preferences)
        self.accept()
