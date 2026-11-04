"""User-accessible distribution notices and source access."""

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QPushButton, QTextBrowser, QVBoxLayout

from backend.runtime import resource_root
from frontend.i18n import UiText

RELEASE_URL = "https://github.com/emiryigittt/nexus-local-ai-manager/releases/tag/v0.3.0-beta.3"
RELEASE_LABEL = "Nexus · 0.3.0 Beta 3"


class AboutDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        inherited = getattr(parent, "ui_text", None)
        self.ui_text = inherited if isinstance(inherited, UiText) else UiText()
        ui = self.ui_text
        self.setWindowTitle(ui("Nexus hakkında"))
        self.resize(540, 380)
        layout = QVBoxLayout(self)
        body = QTextBrowser()
        body.setOpenExternalLinks(True)
        body.setHtml(
            f"<h2>{RELEASE_LABEL}</h2>"
            + ui(
                "<p>Windows için kişisel yapay zekâ yardımcın.</p>"
                "<p>Birleşik Windows dağıtımı GNU GPL sürüm 3 kapsamındadır. Nexus tarafından yazılan "
                "kaynak kod MIT lisansını korur; bağımlılıkların telif ve lisans bildirimleri geçerlidir.</p>"
                "<p>Uygulamayı ilgili lisansların koşullarıyla inceleyebilir, değiştirebilir ve yeniden "
                "dağıtabilirsin. Uygulama garanti verilmeden sunulur.</p>"
            )
            + f'<p><a href="{RELEASE_URL}">'
            + ui("Kaynak arşivleri ve sürüm dosyaları")
            + "</a></p>"
        )
        layout.addWidget(body)
        notices = QPushButton(ui("Lisansları ve ekli kaynak kodu aç"))
        notices.clicked.connect(self.open_notices)
        layout.addWidget(notices)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        layout.addWidget(close)

    def open_notices(self):
        path = resource_root() / "distribution-notices"
        if not path.is_dir():
            path = resource_root()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
