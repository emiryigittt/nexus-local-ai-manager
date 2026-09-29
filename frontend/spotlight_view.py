"""Presentation-only construction; application behavior stays in SpotlightApp."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from backend.user_settings import settings_store
from frontend.brand import brand_pixmap
from frontend.design import STYLE, ActionCard, ComposerFrame, StatusLabel, button
from frontend.history_input import HistoryLineEdit
from frontend.motion import MotionLogo


def build_interface(window):
    ui = window.ui_text

    def label(source=""):
        widget = QLabel()
        ui.bind(widget, "setText", source)
        return widget

    def control(name, tip, callback, text="", primary=False):
        widget = button(name, ui(tip), callback, ui(text), primary=primary)
        ui.bind(widget, "setToolTip", tip)
        ui.bind(widget, "setAccessibleName", tip)
        if text:
            ui.bind(widget, "setText", text)
        return widget

    def action(menu, source, callback):
        item = menu.addAction(ui(source), callback)
        ui.bind(item, "setText", source)
        return item
    outer = QWidget()
    outer.setObjectName("outer")
    outer_layout = QVBoxLayout(outer)
    outer_layout.setContentsMargins(16, 16, 16, 16)
    window.setCentralWidget(outer)
    window.container = QFrame()
    window.container.setObjectName("container")
    shadow = QGraphicsDropShadowEffect(window)
    shadow.setBlurRadius(30)
    shadow.setOffset(0, 8)
    shadow.setColor(QColor(0, 0, 0, 110))
    window.container.setGraphicsEffect(shadow)
    outer_layout.addWidget(window.container)
    root = QVBoxLayout(window.container)
    root.setContentsMargins(26, 16, 26, 16)
    root.setSpacing(16)

    header = QWidget()
    header.setObjectName("header")
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(0, 0, 0, 0)
    mark = QLabel()
    mark.setObjectName("brandMark")
    mark.setPixmap(brand_pixmap(30, tile=False))
    header_layout.addWidget(mark)
    brand = QLabel("nexus")
    brand.setObjectName("brand")
    header_layout.addWidget(brand)
    note = label("Kişisel alanın.")
    note.setObjectName("brandNote")
    header_layout.addWidget(note)
    header_layout.addStretch()
    for name, tip, callback in (
        ("plus", "Yeni sohbet · Ctrl+N", window.new_conversation),
        ("history", "Geçmiş · Ctrl+H", window.open_history),
        ("settings", "Ayarlar · Ctrl+,", window.open_settings),
        ("hide", "Pencereyi gizle · Esc", window.hide),
    ):
        header_layout.addWidget(control(name, tip, callback))
    # Dragging the empty header moves the native window without stealing editor events.
    def drag(event):
        if event.button() == Qt.MouseButton.LeftButton and window.windowHandle():
            window.windowHandle().startSystemMove()
    header.mousePressEvent = drag
    root.addWidget(header)

    content = QWidget()
    content.setObjectName("content")
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(8, 0, 8, 0)
    content_layout.setSpacing(12)
    window.welcome = QWidget()
    window.welcome.setObjectName("welcome")
    welcome = QVBoxLayout(window.welcome)
    welcome.setContentsMargins(0, 8, 0, 2)
    welcome.setSpacing(12)
    welcome.addStretch(2)
    hero = MotionLogo()
    window.hero_logo = hero
    hero.setObjectName("heroMark")
    window.welcome_identity = QWidget()
    identity = QHBoxLayout(window.welcome_identity)
    identity.setContentsMargins(0, 0, 0, 0)
    identity.addWidget(hero)
    eyebrow = label("DÜŞÜNMEK İÇİN BİR ALAN")
    eyebrow.setObjectName("eyebrow")
    identity.addWidget(eyebrow)
    identity.addStretch()
    welcome.addWidget(window.welcome_identity)
    window.welcome_identity.setVisible(window.height() >= 600)
    title = label("Aklında ne var?")
    title.setObjectName("welcomeTitle")
    title.setAlignment(Qt.AlignmentFlag.AlignLeft)
    welcome.addWidget(title)
    subtitle = label("Bir fikir, bir soru, yarım kalan bir iş.\nBirlikte devam edelim.")
    subtitle.setObjectName("subtitle")
    subtitle.setAlignment(Qt.AlignmentFlag.AlignLeft)
    welcome.addWidget(subtitle)
    welcome.addStretch(2)
    suggestions = QHBoxLayout()
    suggestions.setSpacing(10)
    for name, caption, description, shortcut, callback in (
        ("copy", "Panoyu incele", "Kopyaladığın içerikle çalış", "Ctrl+Shift+V", window.analyze_clipboard),
        ("web", "Bir konuyu araştır", "Kaynaklarla daha derine in", "/web", window.start_research),
        ("mic", "Sesli konuş", "Aklındakini anlat", "F2", window.toggle_voice_recording),
    ):
        item = ActionCard(name, caption, description, shortcut, callback, ui)
        suggestions.addWidget(item, 1)
    welcome.addLayout(suggestions)
    content_layout.addWidget(window.welcome, 1)

    window.response_bar = QWidget()
    response_layout = QHBoxLayout(window.response_bar)
    response_layout.setContentsMargins(0, 0, 0, 0)
    window.activity_logo = MotionLogo(30, tile=False)
    response_layout.addWidget(window.activity_logo)
    heading = QLabel("Nexus")
    heading.setObjectName("responseHeading")
    response_layout.addWidget(heading)
    window.question_label = StatusLabel()
    window.question_label.setObjectName("modelStatus")
    response_layout.addWidget(window.question_label, 1)
    window.copy_button = control("copy", "Yanıtı kopyala", window.copy_response)
    response_layout.addWidget(window.copy_button)
    window.response_bar.hide()
    content_layout.addWidget(window.response_bar)
    window.output_browser = QTextBrowser()
    window.output_browser.setObjectName("output")
    window.output_browser.setOpenExternalLinks(True)
    window.output_browser.setFont(QFont("Segoe UI", 11))
    window.output_browser.document().setDefaultStyleSheet(
        "p { margin-top: 4px; margin-bottom: 14px; line-height: 145%; }"
        "h1,h2,h3 { color: #f0eeea; margin-top: 20px; }"
        "a { color: #acd8bf; } pre { background-color: #252a2e; }"
        "code { font-family: Consolas; }"
    )
    window.output_browser.hide()
    content_layout.addWidget(window.output_browser, 1)
    root.addWidget(content, 1)
    window.speech_caption = QLabel()
    window.speech_caption.setObjectName("subtitle")
    window.speech_caption.setTextFormat(Qt.TextFormat.PlainText)
    window.speech_caption.setWordWrap(True)
    window.speech_caption.setMaximumHeight(60)
    window.speech_caption.hide()
    root.addWidget(window.speech_caption)

    composer = ComposerFrame()
    composer.setObjectName("composer")
    composer_layout = QVBoxLayout(composer)
    composer_layout.setContentsMargins(16, 12, 12, 9)
    composer_layout.setSpacing(5)
    window.input_line = HistoryLineEdit()
    ui.bind(window.input_line, "setPlaceholderText", "Nexus'a bir şey sor…")
    ui.bind(window.input_line, "setAccessibleName", "Nexus komut alanı")
    ui.bind(window.input_line, "setAccessibleDescription", "Mesajınızı yazıp Enter'a veya gönder düğmesine basın.")
    window.input_line.setMinimumHeight(36)
    window.input_line.installEventFilter(composer)
    window.input_line.returnPressed.connect(window.send_message)
    entry = QHBoxLayout()
    entry.addWidget(window.input_line, 1)
    window.send_button = control("send", "Mesajı gönder · Enter", window.send_message, primary=True)
    window.send_button.setFixedSize(40, 40)
    entry.addWidget(window.send_button)
    composer_layout.addLayout(entry)
    window.context_button = QPushButton()
    window.context_button.setObjectName("contextButton")
    window.context_button.setCursor(Qt.CursorShape.PointingHandCursor)
    window.context_button.clicked.connect(window.analyze_clipboard)
    window.context_button.hide()
    composer_layout.addWidget(window.context_button)
    tools = QHBoxLayout()
    tools.setSpacing(5)
    tools.addWidget(control("plus", "Belge ekle", window.import_document, "Ekle"))
    tools.addWidget(control("web", "Web araştırması", window.start_research, "Araştır"))
    menu_button = control("more", "Sohbet araçları", lambda: None, "Araçlar")
    menu = QMenu(menu_button)
    window.private_btn = action(menu, "Özel oturum", window.toggle_private_session)
    window.private_btn.setCheckable(True)
    window.knowledge_btn = action(menu, "Belgelerimden yanıtla", window.toggle_knowledge)
    window.knowledge_btn.setCheckable(True)
    window.speaker_btn = action(menu, "Yanıtları seslendir", window.toggle_tts)
    window.speaker_btn.setCheckable(True)
    window.speaker_btn.setChecked(window.tts_enabled)
    menu.addSeparator()
    action(menu, "Hafızamı göster", window.show_remembered_context)
    action(menu, "Hafızayı yönet · adayları incele", lambda: window.open_memory_manager())
    menu_button.setMenu(menu)
    tools.addWidget(menu_button)
    tools.addStretch()
    window.stop_btn = QPushButton()
    ui.bind(window.stop_btn, "setText", "Durdur")
    ui.bind(window.stop_btn, "setAccessibleName", "Durdur")
    window.stop_btn.setObjectName("stopButton")
    window.stop_btn.clicked.connect(window.cancel_active_response)
    window.stop_btn.hide()
    tools.addWidget(window.stop_btn)
    window.mic_btn = control("mic", "Sesli konuş · F2", window.toggle_voice_recording)
    window.mic_btn.setCheckable(True)
    tools.addWidget(window.mic_btn)
    composer_layout.addLayout(tools)
    root.addWidget(composer)

    footer = QHBoxLayout()
    footer.setSpacing(10)
    window.local_badge = QLabel(ui("YEREL MODEL"))
    window.local_badge.setObjectName("localBadge")
    footer.addWidget(window.local_badge)
    preferences = settings_store.load()
    selected = next((p for p in preferences.providers if p.id == preferences.selected_provider_id), None)
    name = selected.selected_model if selected else ""
    window.model_status = StatusLabel(name.rsplit("/", 1)[-1] if name else ui("Ayarlar'dan bir model seç"))
    window.model_status.setObjectName("modelStatus")
    footer.addWidget(window.model_status, 1)
    window.wake_button = QPushButton("Hey Nexus")
    window.wake_button.setObjectName("wakeButton")
    ui.bind(window.wake_button, "setAccessibleName", "Hey Nexus dinlemesini duraklat veya devam ettir")
    footer.addWidget(window.wake_button)
    hint = label("Enter  gönder")
    hint.setObjectName("footerHint")
    footer.addWidget(hint)
    root.addLayout(footer)
    window.setStyleSheet(STYLE)
    window.input_line.textChanged.connect(window._sync_send_button)
    window.send_button.setEnabled(False)
    window.setTabOrder(window.input_line, window.send_button)
    window.setTabOrder(window.send_button, window.mic_btn)
