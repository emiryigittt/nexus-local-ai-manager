"""An optional, offline introduction with explicit, reviewable memory saving."""

from __future__ import annotations

import sqlite3

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from backend.identity import PROFILE_FIELDS, profile_memories
from backend.memory import MemoryRepository, memory_repository
from backend.user_settings import SettingsStore, settings_store
from frontend.appearance import themed_style
from frontend.companion import CompanionAvatar

COPY = {
    "title": ("Nexus · Tanışalım", "Nexus · Meet Nexus"),
    "heading": ("Ben Nexus. Birlikte ilerleyelim.", "I'm Nexus. Let's move forward together."),
    "purpose": (
        "Fikirlerini netleştirmek, öğrenmene yardımcı olmak ve işlerini ilerletmek için buradayım.",
        "I'm here to help you think clearly, learn and move your work forward.",
    ),
    "name": ("Sana nasıl hitap edeyim?", "What should I call you?"),
    "name_hint": ("Gerçek adın olmak zorunda değil. Bir takma ad da olur.", "A nickname is fine. It doesn't have to be your real name."),
    "work": ("Nelerle uğraşıyorsun?", "What do you spend your time on?"),
    "work_hint": ("İşin, öğrenmek istediğin bir alan veya sevdiğin bir uğraş…", "Your work, something you're learning, or an interest…"),
    "goal": ("Şu sıralar neyi başarmak istiyorsun?", "What are you working toward right now?"),
    "goal_hint": ("Bir hedef veya üzerinde çalıştığın bir proje yeterli.", "A goal or a project you're working on is enough."),
    "style": ("Sana nasıl yardımcı olayım?", "How would you like me to help?"),
    "style_hint": ("Yanıtlarımı çalışma tarzına göre uyarlayabilirim.", "I can adapt my answers to the way you work."),
    "unset": ("Henüz bir tercihim yok", "No preference yet"),
    "short": ("Kısa ve doğrudan", "Short and direct"),
    "balanced": ("Dengeli, gerektiğinde örneklerle", "Balanced, with examples when useful"),
    "detailed": ("Ayrıntılı, adım adım", "Detailed, step by step"),
    "questions": ("Uygun anlarda beni tanımak için kısa sorular sor", "Ask brief questions to get to know me when it fits"),
    "review": ("Seni böyle tanıyacağım.", "Here's how I'll get to know you."),
    "review_hint": ("Kaydetmeden önce gözden geçir. Geri dönüp değiştirebilirsin.", "Review before saving. You can go back and change anything."),
    "empty": ("Henüz bir yanıt vermedin. Tanışmayı daha sonra da yapabiliriz.", "You haven't answered yet. We can get acquainted later."),
    "learn": ("Sohbetlerimden yeni hafıza önerileri oluştur", "Suggest new memories from my conversations"),
    "learn_note": (
        "Öneriler, Hafıza ekranında onaylayana kadar yanıtlarda kullanılmaz. Özel oturumlarda öğrenme kapalıdır.",
        "Suggestions aren't used in answers until you approve them in Memory. Learning is off in private sessions.",
    ),
    "local": (
        "Kaydet dediğinde yanıtların bu bilgisayardaki hafızaya eklenir ve hafıza kullanımı açılır. "
        "Sohbet ederken seçtiğin modele bağlam olarak iletilir. Hafıza ekranından değiştirebilir veya silebilirsin.",
        "Saving adds your answers to memory on this computer and enables memory context. "
        "They are sent as context to your selected model when chatting. Edit or forget them in Memory.",
    ),
    "optional": ("Her soru isteğe bağlı. Boş bırakıp devam edebilirsin.", "Every question is optional. Leave it blank to continue."),
    "later": ("Şimdi değil", "Not now"),
    "back": ("Geri", "Back"),
    "next": ("Devam", "Continue"),
    "save": ("Kaydet ve başlayalım", "Save and let's begin"),
    "done": ("Kaydetmeden başla", "Start without saving"),
    "error": ("Kaydedemedim. Yanıtların burada duruyor; tekrar deneyebilirsin.", "I couldn't save. Your answers are still here; you can try again."),
    "settings_error": (
        "Yanıtların hafızaya eklendi, fakat ayarları kaydedemedim. Yeniden Kaydet'e basabilirsin; kayıtlar çoğalmaz.",
        "Your answers were added to memory, but I couldn't save preferences. Save again to retry; records won't be duplicated.",
    ),
    "progress": ("Tanışma · {step} / 5", "Introduction · {step} / 5"),
    "label_name": ("Hitap adı", "Name"),
    "label_work": ("Uğraşların", "Work and interests"),
    "label_goal": ("Hedefin", "Goal"),
    "label_style": ("Yanıt tercihin", "Response preference"),
}


class IntroductionDialog(QDialog):
    def __init__(self, parent=None, *, store: SettingsStore = settings_store,
                 repository: MemoryRepository = memory_repository):
        super().__init__(parent)
        self.store, self.repository = store, repository
        preferences = store.load()
        self.english = preferences.language == "en"
        self.setWindowTitle(self.t("title"))
        self.setStyleSheet(themed_style(preferences.accent_color))
        self.resize(600, 620)
        self.setMinimumSize(560, 590)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        header = QHBoxLayout()
        self.avatar = CompanionAvatar(80)
        self.avatar.set_appearance(preferences.companion_style, preferences.accent_color)
        self.avatar.set_reduced_motion(preferences.reduced_motion)
        header.addWidget(self.avatar)
        greeting = QVBoxLayout()
        heading = self.label("heading", "dialogTitle")
        # Keep the companion header readable in both languages at this width.
        heading.setStyleSheet("font-size: 21px; font-weight: 600;")
        greeting.addWidget(heading)
        greeting.addWidget(self.label("purpose", "settingsNote"))
        header.addLayout(greeting, 1)
        layout.addLayout(header)
        self.progress = QLabel()
        self.progress.setObjectName("sectionTitle")
        layout.addWidget(self.progress)
        self.pages = QStackedWidget()
        layout.addWidget(self.pages, 1)
        self.fields = {}
        for key, limit in (("name", 60), ("work", 240), ("goal", 300)):
            page = self.page(key, key + "_hint")
            edit = QLineEdit()
            edit.setMaxLength(limit)
            edit.setMinimumHeight(46)
            edit.setPlaceholderText(self.t(key + "_hint"))
            edit.setAccessibleName(self.t(key))
            self.fields["user." + key] = edit
            page.addWidget(edit)
            page.addWidget(self.label("optional", "settingsNote"))
            page.addStretch()
        style_page = self.page("style", "style_hint")
        self.style = QComboBox()
        self.style.setAccessibleName(self.t("style"))
        for key in ("unset", "short", "balanced", "detailed"):
            self.style.addItem(self.t(key), "" if key == "unset" else key)
        style_page.addWidget(self.style)
        self.questions = QCheckBox(self.t("questions"))
        self.questions.setChecked(preferences.personal_questions_enabled)
        style_page.addWidget(self.questions)
        style_page.addStretch()
        review_page = self.page("review", "review_hint")
        self.review = QLabel()
        self.review.setWordWrap(True)
        self.review.setTextFormat(Qt.TextFormat.PlainText)
        self.review.setObjectName("settingsCard")
        self.review.setStyleSheet("padding: 14px;")
        self.review.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.review_scroll = QScrollArea()
        self.review_scroll.setWidgetResizable(True)
        self.review_scroll.setMinimumHeight(140)
        self.review_scroll.setWidget(self.review)
        review_page.addWidget(self.review_scroll, 1)
        self.learn = QCheckBox(self.t("learn"))
        # Explicit choice on the review page; never enabled by merely opening it.
        self.learn.setChecked(preferences.memory_auto_learn)
        review_page.addWidget(self.learn)
        review_page.addWidget(self.label("learn_note", "settingsNote"))
        review_page.addWidget(self.label("local", "settingsNote"))
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        row = QHBoxLayout()
        self.later = QPushButton(self.t("later"))
        self.later.clicked.connect(self.skip)
        row.addWidget(self.later)
        row.addStretch()
        self.back = QPushButton(self.t("back"))
        self.back.clicked.connect(self.previous)
        row.addWidget(self.back)
        self.next = QPushButton()
        self.next.setProperty("primary", True)
        self.next.setDefault(True)
        self.next.clicked.connect(self.advance)
        row.addWidget(self.next)
        layout.addLayout(row)
        # Prefill only current approved records, including edits made in Memory.
        records = profile_memories(repository, preferences)
        for record in records:
            key = record.get("memory_key")
            if key in self.fields:
                self.fields[key].setText(record["content"])
            elif key == "user.response_style":
                for choice in ("short", "balanced", "detailed"):
                    if record["content"] in COPY[choice]:
                        self.style.setCurrentIndex(self.style.findData(choice))
        self.sync()

    def t(self, key):
        return COPY[key][self.english]

    def label(self, key, object_name=""):
        label = QLabel(self.t(key))
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setObjectName(object_name)
        return label

    def page(self, title, hint):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self.label(title, "dialogTitle"))
        layout.addWidget(self.label(hint, "settingsNote"))
        self.pages.addWidget(page)
        return layout

    def answers(self):
        answers = {key: " ".join(edit.text().split()) for key, edit in self.fields.items() if edit.text().strip()}
        if self.style.currentData():
            answers["user.response_style"] = self.style.currentText()
        return answers

    def sync(self):
        index = self.pages.currentIndex()
        self.progress.setText(self.t("progress").format(step=index + 1))
        self.back.setEnabled(index > 0)
        self.next.setText(self.t("next") if index < 4 else self.t("save" if self.answers() else "done"))
        labels = dict(zip(PROFILE_FIELDS, ("label_name", "label_work", "label_goal", "label_style"), strict=True))
        self.review.setText("\n\n".join(f"{self.t(labels[key])}: {value}" for key, value in self.answers().items()) or self.t("empty"))
        if index < 3:
            list(self.fields.values())[index].setFocus()

    def previous(self):
        self.pages.setCurrentIndex(max(0, self.pages.currentIndex() - 1))
        self.sync()

    def advance(self):
        if self.pages.currentIndex() < 4:
            self.pages.setCurrentIndex(self.pages.currentIndex() + 1)
            self.sync()
            return
        self.save()

    def skip(self):
        try:
            self.store.update(introduction_complete=True, personal_questions_enabled=False)
        except OSError:
            self.status.setText(self.t("error"))
            return
        self.reject()

    def save(self):
        answers = self.answers()
        try:
            self.repository.save_introduction({key: (value, PROFILE_FIELDS[key][1]) for key, value in answers.items()})
        except (OSError, sqlite3.Error, ValueError):
            self.status.setText(self.t("error"))
            return
        try:
            changes = {"introduction_complete": True, "personal_questions_enabled": self.questions.isChecked()}
            if answers:
                changes["memory_enabled"] = True
                changes["memory_auto_learn"] = self.learn.isChecked()
            self.store.update(**changes)
        except OSError:
            self.status.setText(self.t("settings_error"))
            return
        self.accept()
