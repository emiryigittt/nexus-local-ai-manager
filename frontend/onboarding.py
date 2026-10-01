"""Three-step first run. Preferences are committed only after inference succeeds."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from backend.user_settings import settings_store
from frontend.brand import brand_icon
from frontend.design import STYLE
from frontend.setup_task import SetupTask

TEXT = {
    "title": ("Nexus'a hoş geldin", "Welcome to Nexus"),
    "steps": ("1 · Dil   →   2 · Yerel model   →   3 · Başla", "1 · Language   →   2 · Local model   →   3 · Start"),
    "language": ("Hangi dilde devam edelim?", "Choose your language"),
    "local": ("Bilgisayarındaki modeli bulalım", "Find a model on your computer"),
    "note": ("Nexus model çalıştırmak için LM Studio, Ollama veya llama.cpp'ye bağlanır. İlk tarama yalnızca bu bilgisayarı kontrol eder.", "Nexus connects to LM Studio, Ollama or llama.cpp. The first scan checks this computer only."),
    "help": ("LM Studio: bir model indirip yükle, Developer ekranında Start Server'a bas.\nOllama: uygulamayı aç ve bir model indir. Sonra Yeniden tara'ya bas.", "LM Studio: download and load a model, then click Start Server in Developer.\nOllama: open the app and download a model. Then click Scan again."),
    "links": ('<a href="https://lmstudio.ai/">LM Studio</a> · <a href="https://ollama.com/">Ollama</a>', '<a href="https://lmstudio.ai/">LM Studio</a> · <a href="https://ollama.com/">Ollama</a>'),
    "scan": ("Yeniden tara", "Scan again"),
    "ready": ("Kısa bir bağlantı testi", "A quick connection test"),
    "test_note": ("Seçtiğin modele kısa bir deneme mesajı gönderilecek. Yanıt geldiğinde başlayabilirsin. Bu işlem mikrofonu açmaz veya gizlilik izinlerini değiştirmez.", "A short test message will be sent to your selected model. Once it replies, you can start. This does not open the microphone or change privacy permissions."),
    "test": ("Bağlantıyı test et", "Test connection"),
    "next": ("Devam", "Continue"),
    "start": ("Nexus'u aç", "Open Nexus"),
    "back": ("Geri", "Back"),
    "later": ("Daha sonra", "Later"),
    "scanning": ("Yerel sunucular aranıyor…", "Looking for local servers…"),
    "missing": ("Çalışan yerel model bulunamadı. Aşağıdaki adımları tamamlayıp yeniden tara.", "No running local model found. Follow the steps below and scan again."),
    "found": ("Model bulundu. Birini seçip devam et.", "Models found. Select one to continue."),
    "testing": ("Modelin yanıtı bekleniyor… İlk yükleme biraz sürebilir.", "Waiting for a model reply… The first load can take a moment."),
    "passed": ("Bağlantı başarılı. İlk sohbetine hazırsın.", "Connection successful. You are ready for your first chat."),
    "failed": ("Yanıt alınamadı. Modeli yüklediğinden ve sunucunun açık olduğundan emin ol. İlk yükleme uzun sürdüyse yeniden dene.", "No reply received. Check that your model is loaded and the server is running. Retry if the first load took too long."),
    "unsaved": ("Ayarlar kaydedilemedi. Disk alanını ve klasör erişimini kontrol et.", "Could not save settings. Check disk space and folder access."),
}


class OnboardingDialog(QDialog):
    def __init__(self, parent=None, store=settings_store):
        super().__init__(parent)
        self.store = store
        self.language_code = store.load().language
        self.setWindowIcon(brand_icon())
        self.setStyleSheet(STYLE)
        self.setMinimumSize(570, 520)
        self.setMaximumWidth(740)
        self.bindings = []
        self.results = []
        self.job = ""
        self.tested = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)
        layout.addWidget(self.label("steps"))
        self.pages = QStackedWidget()
        layout.addWidget(self.pages, 1)
        language = self.page("language")
        self.language = QComboBox()
        self.language.addItem("Türkçe", "tr")
        self.language.addItem("English", "en")
        self.language.setCurrentIndex(max(0, self.language.findData(self.language_code)))
        self.language.setAccessibleName("Language / Dil")
        language.addWidget(self.language)
        language.addStretch()
        local = self.page("local")
        local.addWidget(self.label("note"))
        self.provider = QComboBox()
        self.model = QComboBox()
        self.provider.setAccessibleName("Local provider / Yerel sağlayıcı")
        self.model.setAccessibleName("Model")
        local.addWidget(self.provider)
        local.addWidget(self.model)
        self.scan = self.button("scan", self.discover)
        local.addWidget(self.scan)
        local.addWidget(self.label("help"))
        links = self.label("links")
        links.setOpenExternalLinks(True)
        local.addWidget(links)
        local.addStretch()
        ready = self.page("ready")
        ready.addWidget(self.label("test_note"))
        self.test_button = self.button("test", self.test_connection)
        ready.addWidget(self.test_button)
        ready.addStretch()
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        row = QHBoxLayout()
        self.later = self.button("later", self.reject)
        self.back = self.button("back", self.previous)
        self.next = self.button("next", self.advance)
        self.next.setProperty("primary", True)
        row.addWidget(self.later)
        row.addStretch()
        row.addWidget(self.back)
        row.addWidget(self.next)
        layout.addLayout(row)
        self.task = SetupTask(self)
        self.task.event_received.connect(self.receive)
        self.task.completed.connect(self.completed)
        self.language.currentIndexChanged.connect(self.change_language)
        self.provider.currentIndexChanged.connect(self.fill_models)
        self.model.currentIndexChanged.connect(self.invalidate)
        self.retranslate()
        self.sync()

    def t(self, key):
        return TEXT[key][self.language_code == "en"]

    def label(self, key):
        item = QLabel()
        item.setWordWrap(True)
        self.bindings.append((item.setText, key))
        return item

    def button(self, key, callback):
        item = QPushButton()
        self.bindings.append((item.setText, key))
        item.clicked.connect(callback)
        return item

    def page(self, title):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 12, 0, 0)
        heading = self.label(title)
        heading.setObjectName("welcomeTitle")
        layout.addWidget(heading)
        self.pages.addWidget(widget)
        return layout

    def change_language(self):
        self.language_code = self.language.currentData()
        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(self.t("title"))
        for setter, key in self.bindings:
            setter(self.t(key))
        self.sync()

    def selection(self):
        return self.provider.currentData(), self.model.currentText()

    def invalidate(self):
        self.tested = None
        self.status.clear()
        self.sync()

    def fill_models(self):
        self.model.clear()
        current = next((item for item in self.results if item["id"] == self.provider.currentData()), {})
        self.model.addItems(current.get("models", []))
        self.invalidate()

    def sync(self):
        busy = hasattr(self, "task") and self.task.busy
        page = self.pages.currentIndex()
        self.back.setVisible(page > 0)
        for control in (self.back, self.scan, self.provider, self.model, self.test_button):
            control.setEnabled(not busy)
        self.next.setText(self.t("start" if page == 2 else "next"))
        self.next.setEnabled(not busy and (page == 0 or (page == 1 and bool(self.model.currentText())) or (page == 2 and self.tested == self.selection())))

    def advance(self):
        page = self.pages.currentIndex()
        if page == 2:
            self.finish_setup()
            return
        self.pages.setCurrentIndex(page + 1)
        self.status.clear()
        self.sync()
        if page == 0:
            self.discover()

    def previous(self):
        self.pages.setCurrentIndex(max(0, self.pages.currentIndex() - 1))
        self.status.clear()
        self.sync()

    def discover(self):
        self.job = "discover"
        self.tested = None
        self.results = []
        self.provider.clear()
        self.task.start("onboarding-task", "onboarding_task.py", ["discover"])
        self.status.setText(self.t("scanning"))
        self.sync()

    def test_connection(self):
        if not all(self.selection()):
            return
        self.job = "test"
        self.tested = None
        provider, model = self.selection()
        self.task.start("onboarding-task", "onboarding_task.py", ["test", "--provider", provider, "--model", model])
        self.status.setText(self.t("testing"))
        self.sync()

    def receive(self, value):
        if self.job == "discover" and value.get("stage") == "ready":
            self.results = [item for item in value.get("providers", []) if item.get("healthy") and item.get("models")]

    def completed(self, success):
        if self.job == "discover":
            for item in self.results:
                self.provider.addItem(item["name"], item["id"])
            preferred = self.provider.findData(self.store.load().selected_provider_id)
            if preferred >= 0:
                self.provider.setCurrentIndex(preferred)
            self.fill_models()
            self.status.setText(self.t("found" if success and self.results else "missing"))
        else:
            self.tested = self.selection() if success else None
            self.status.setText(self.t("passed" if success else "failed"))
        self.sync()

    def finish_setup(self):
        if self.task.busy or self.tested != self.selection() or not all(self.selection()):
            return
        preferences = self.store.load()
        profile = next((item for item in preferences.providers if item.id == self.selection()[0]), None)
        if profile is None:
            return
        profile.selected_model = self.selection()[1]
        preferences.selected_provider_id = profile.id
        preferences.language = self.language_code
        preferences.setup_complete = True
        try:
            self.store.save(preferences)
        except OSError:
            self.status.setText(self.t("unsaved"))
            return
        self.accept()

    def done(self, result):
        if self.task.stop():
            super().done(result)
