"""User-accessible distribution notices and source access."""

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QPushButton, QTextBrowser, QVBoxLayout

from backend.runtime import resource_root

RELEASE_URL = "https://github.com/emiryigittt/nexus-local-ai-manager/releases/tag/v0.3.0-beta.2"


class AboutDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        english = parent.ui_text.language == "en"
        self.setWindowTitle("About Nexus" if english else "Nexus hakkında")
        self.resize(540, 380)
        layout = QVBoxLayout(self)
        body = QTextBrowser()
        body.setOpenExternalLinks(True)
        body.setHtml(
            '<h2>Nexus · 0.3.0 Beta 2</h2>'
            + ("<p>Your personal AI companion for Windows.</p><p>The combined Windows distribution is licensed under GNU GPL version 3. Nexus-authored source retains its MIT license; dependencies retain their copyright and license notices.</p><p>You may study, modify and redistribute the application under the applicable licenses. The application is provided without warranty.</p>" if english else
               "<p>Windows için kişisel yapay zekâ yardımcın.</p><p>Birleşik Windows dağıtımı GNU GPL sürüm 3 kapsamındadır. Nexus tarafından yazılan kaynak kod MIT lisansını korur; bağımlılıkların telif ve lisans bildirimleri geçerlidir.</p><p>Uygulamayı ilgili lisansların koşullarıyla inceleyebilir, değiştirebilir ve yeniden dağıtabilirsin. Uygulama garanti verilmeden sunulur.</p>")
            + f'<p><a href="{RELEASE_URL}">' + ("Source archives and release files" if english else "Kaynak arşivleri ve sürüm dosyaları") + "</a></p>"
        )
        layout.addWidget(body)
        notices = QPushButton("Open licenses and included source" if english else "Lisansları ve ekli kaynak kodu aç")
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
