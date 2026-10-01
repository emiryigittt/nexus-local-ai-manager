"""Nexus desktop interface: a calm, keyboard-first local AI command center."""

from __future__ import annotations

import asyncio
import html
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path

import httpx
from PyQt6.QtCore import (
    QEasingCurve,
    QEvent,
    QObject,
    QPropertyAnimation,
    Qt,
    QThread,
    QTimer,
    QUrl,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QImage,
    QKeySequence,
    QShortcut,
    QTextBlockFormat,
    QTextCursor,
    QTextDocument,
)
from PyQt6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QWidget,
)

from backend.audio_transcriber import AudioRecorder, WhisperTranscriber
from backend.chat_context import recent_turns
from backend.config import settings
from backend.conversations import conversation_repository
from backend.document_extract import TEXT_SUFFIXES, extract_document
from backend.identity import preferred_name, profile_memories
from backend.memory import memory_repository
from backend.runtime import resource_root
from backend.speech_chunks import take_speech_chunks
from backend.user_settings import settings_store
from frontend.about_dialog import AboutDialog
from frontend.api_client import request_json
from frontend.appearance import AccentEdge, themed_style
from frontend.brand import brand_icon
from frontend.history_dialog import HistoryDialog
from frontend.i18n import UiText
from frontend.image_utils import qimage_to_base64_adaptive as encode_image
from frontend.introduction import IntroductionDialog
from frontend.memory_dialog import MemoryDialog
from frontend.micro_motion import DropTarget, MotionButton, ShellTransition
from frontend.notch import NotchController
from frontend.onboarding import OnboardingDialog
from frontend.setup_dialog import SetupDialog
from frontend.sound_feedback import SoundFeedback
from frontend.speech_follow import SpeechFollow
from frontend.spotlight_view import build_interface
from frontend.voice_worker import StreamingVoiceWorker, VoiceRecordWorker
from frontend.wake_controller import WakeController


class ChatWorker(QThread):
    status_changed = pyqtSignal(str)
    response_chunk = pyqtSignal(str)
    response_completed = pyqtSignal()
    response_cancelled = pyqtSignal()
    memory_sources_received = pyqtSignal(list)
    error_received = pyqtSignal(str)
    warning_received = pyqtSignal(str)

    def __init__(
        self,
        text: str,
        image_b64: str | None = None,
        *,
        conversation_id: str | None = None,
        provider_id: str | None = None,
        model_id: str | None = None,
        private: bool = False,
        use_knowledge: bool = False,
        action_id: str | None = None,
        history: list[dict] | None = None,
        language: str = "tr",
    ):
        super().__init__()
        self.text = text
        self.image_b64 = image_b64
        self.conversation_id = conversation_id
        self.provider_id = provider_id
        self.model_id = model_id
        self.private = private
        self.use_knowledge = use_knowledge
        self.action_id = action_id
        self.history = history or []
        self.ui_text = UiText(language)
        self._loop = None
        self._task = None

    def cancel(self) -> None:
        self.requestInterruption()
        loop, task = self._loop, self._task
        if loop and task:
            try:
                loop.call_soon_threadsafe(task.cancel)
            except RuntimeError:
                pass  # The loop already finished.

    def run(self):
        try:
            asyncio.run(self._stream())
        except asyncio.CancelledError:
            self.response_cancelled.emit()
        except httpx.HTTPStatusError as exc:
            self.error_received.emit(self.ui_text("Nexus servisi hata döndürdü ({status}).", status=exc.response.status_code))
        except httpx.TimeoutException:
            self.error_received.emit(self.ui_text("Model yanıtı zaman aşımına uğradı. Yeniden deneyin."))
        except httpx.HTTPError:
            self.error_received.emit(self.ui_text("Nexus servisine ulaşılamadı. Uygulamayı yeniden başlatmayı deneyin."))
        except Exception as exc:
            self.error_received.emit(str(exc))
        finally:
            self._loop = None
            self._task = None

    async def _stream(self):
        self._loop = asyncio.get_running_loop()
        self._task = asyncio.current_task()
        if self.isInterruptionRequested():
            raise asyncio.CancelledError
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            self.status_changed.emit(self.ui_text("Yerel model düşünüyor…"))
            payload = {"text": self.text}
            if self.image_b64:
                payload["image"] = self.image_b64
            payload.update(
                {
                    "conversation_id": self.conversation_id,
                    "provider_id": self.provider_id,
                    "model_id": self.model_id,
                    "private": self.private,
                    "use_knowledge": self.use_knowledge,
                    "action_id": self.action_id,
                    "history": self.history,
                }
            )
            async with client.stream("POST", f"{settings.backend_url}/chat/stream", json=payload) as response:
                response.raise_for_status()
                async for raw_line in response.aiter_lines():
                    if self.isInterruptionRequested():
                        self.response_cancelled.emit()
                        return
                    if not raw_line.strip():
                        continue
                    event = json.loads(raw_line)
                    if event.get("event") == "chunk":
                        self.response_chunk.emit(event.get("text", ""))
                    elif event.get("event") == "memory_sources":
                        self.memory_sources_received.emit(event.get("sources", []))
                    elif event.get("event") == "error":
                        self.error_received.emit(event.get("message", self.ui_text("Bilinmeyen hata")))
                        return
                    elif event.get("event") == "warning":
                        self.warning_received.emit(event.get("message", ""))
                    elif event.get("event") == "done":
                        self.response_completed.emit()
                        return
            if self.isInterruptionRequested():
                self.response_cancelled.emit()
            else:
                self.error_received.emit(self.ui_text("Nexus bağlantısı yanıt tamamlanmadan kesildi. Yeniden deneyin."))


class HotkeyBridge(QObject):
    activated = pyqtSignal()
    selection_activated = pyqtSignal()


class SpotlightApp(QMainWindow):
    IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
    DOCUMENT_EXTENSIONS = tuple(sorted(TEXT_SUFFIXES | {".pdf", ".docx"}))

    def __init__(self):
        super().__init__()
        self.active_image_b64: str | None = None
        self.active_image_name: str | None = None
        self._last_document_name: str | None = None
        preferences = settings_store.load()
        self.ui_text = UiText(preferences.language)
        self.reduced_motion = preferences.reduced_motion
        self._recording_ready = False
        self._wake_listening = False
        self.tts_enabled = preferences.tts_enabled or os.getenv("NEXUS_TTS_ENABLED", "0").casefold() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.tts_backend = preferences.tts_backend or os.getenv("NEXUS_TTS_BACKEND", "auto").casefold()
        self.voice_input_mode = preferences.voice_input_mode
        self._voice_key_down = False
        self.current_conversation_id = str(uuid.uuid4())
        self.active_memory_sources: list[dict] = []
        self.private_session = False
        self.knowledge_enabled = False
        self._setup_prompted = False
        self.worker: ChatWorker | None = None
        self.voice_record_worker: VoiceRecordWorker | None = None
        self.stream_voice_worker: StreamingVoiceWorker | None = None
        self.streaming_text = ""
        self.speech_buffer = ""
        self.audio_queue: list[str] = []
        self.current_audio_path: str | None = None
        self._audio_details = {}
        self._audio_timings = {}
        self._workers: set[QThread] = set()
        self._quitting = False
        self._shell_mode = None
        self._private_history: list[dict[str, str]] = []
        self._pending_prompt = ""
        self._response_complete = True
        self._transcriber = WhisperTranscriber()
        self._speech_wait_started = 0.0

        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.mediaStatusChanged.connect(self._on_media_status)
        self.media_player.errorOccurred.connect(self._on_audio_error)

        self._configure_window()
        self._build_interface()
        self.speech_follow = SpeechFollow(self)
        self.media_player.positionChanged.connect(self.speech_follow.update)
        self.render_timer = QTimer(self)
        self.render_timer.setSingleShot(True)
        self.render_timer.setInterval(40)
        self.render_timer.timeout.connect(self._flush_response_render)
        self.shell_transition = ShellTransition(self)
        self.drop_target = DropTarget(self.centralWidget(), self.ui_text("Belgeyi veya görseli buraya bırak"))
        self.notch_controller = NotchController(self)
        self.accent_edge = AccentEdge(self.container)
        self.sound_feedback = SoundFeedback(self)
        self.apply_appearance(preferences)
        self.set_shell_mode("notch")
        self.apply_motion_preference(self.reduced_motion)
        self._install_shortcuts()
        self.media_player.playbackStateChanged.connect(self._on_playback_state)
        QApplication.instance().installEventFilter(self)
        self.show_welcome_state(expand=False)
        self.wake = WakeController(self)
        self.wake_button.clicked.connect(self.wake.toggle)
        self.speech_timer = QTimer(self)
        self.speech_timer.setInterval(250)
        self.speech_timer.timeout.connect(self._flush_waiting_speech)
        self.speech_timer.start()

    def _configure_window(self):
        self.setWindowTitle("Nexus")
        self.setWindowIcon(brand_icon())
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        screen = QApplication.primaryScreen().availableGeometry()
        self.setFixedSize(min(800, screen.width() - 32), min(640, screen.height() - 48))
        self.setAcceptDrops(True)
        self._center_window()

    def _build_interface(self):
        build_interface(self)

    def set_shell_mode(self, mode, *, transient=False):
        """Switch presentation only; live conversation, draft and workers stay intact."""
        if mode not in {"notch", "dock", "chat"}:
            raise ValueError("Unknown window view")
        if mode == self._shell_mode:
            return
        self._shell_mode = mode
        self.notch_controller.mode_changed(mode, transient)
        self.notch_button.setVisible(mode == "notch")
        self.header.setVisible(mode == "chat")
        self.dock_overview.setVisible(mode == "dock")
        self.chat_content.setVisible(mode == "chat")
        self.composer.setVisible(mode == "chat")
        self.footer_widget.setVisible(mode == "chat")
        self.container.setProperty("shell", mode)
        self.container.style().unpolish(self.container)
        self.container.style().polish(self.container)
        self.outer_layout.setContentsMargins(*((12, 12, 12, 12) if mode == "chat" else (0, 0, 0, 0)))
        self.root_layout.setContentsMargins(*((18, 12, 18, 14) if mode == "chat" else
                                             (12, 8, 12, 12) if mode == "dock" else (0, 0, 0, 0)))
        self.root_layout.setSpacing(12 if mode == "chat" else 6 if mode == "dock" else 0)
        self.document_hint.setVisible(mode == "chat" and bool(self._last_document_name))
        for tab, selected in ((self.home_tab, mode == "dock"), (self.chat_tab, mode == "chat")):
            tab.setProperty("selected", selected)
            tab.style().unpolish(tab)
            tab.style().polish(tab)
        target = self.notch_controller.target_rect(mode)
        content = self.notch_button if mode == "notch" else self.dock_overview if mode == "dock" else self.chat_content
        self.shell_transition.start(target, content)
        self._sync_presence_layout()
        (self.notch_avatar if mode == "notch" else self.dock_avatar if mode == "dock" else self.hero_logo).reveal()
        if mode == "chat":
            self.input_line.setFocus()

    def open_full_chat(self):
        was_chat = self._shell_mode == "chat" and self.isVisible()
        self.set_shell_mode("chat")
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_line.setFocus()
        if not was_chat:
            self.sound_feedback.play("open")

    def collapse_to_notch(self):
        was_expanded = self._shell_mode != "notch"
        self.set_shell_mode("notch")
        if was_expanded:
            self.sound_feedback.play("collapse")

    def enterEvent(self, event):
        super().enterEvent(event)
        if hasattr(self, "notch_controller"):
            self.notch_controller.enter()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if hasattr(self, "notch_controller"):
            self.notch_controller.leave()

    def copy_response(self):
        text = self.output_browser.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)
            self.copy_button.setToolTip(self.ui_text("Yanıt kopyalandı"))
            self._react_companions("success")

    def _sync_send_button(self):
        self.send_button.setEnabled(self.input_line.isEnabled() and not self._quitting and
                                    bool(self.input_line.text().strip() or self.active_image_b64))

    def _install_shortcuts(self):
        self.shortcuts = []
        for sequence, callback in (
            ("Escape", self.escape_action),
            ("Ctrl+Q", self.request_quit),
            ("Ctrl+L", self.show_welcome_state),
            ("Ctrl+N", self.new_conversation),
            ("Ctrl+H", self.open_history),
            ("Ctrl+,", self.open_settings),
            ("Ctrl+Shift+P", self.toggle_private_session),
            ("Ctrl+K", self.toggle_knowledge),
            ("F2", self.toggle_voice_recording),
            ("Ctrl+Shift+V", self.analyze_clipboard),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.setAutoRepeat(False)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)

    def escape_action(self):
        if self.voice_record_worker and self.voice_record_worker.isRunning():
            self._cancel_voice_input()
        elif self.worker and self.worker.isRunning():
            self.cancel_active_response()
        else:
            self.collapse_to_notch()

    def _center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.x() + (screen.width() - self.width()) // 2,
            screen.y() + max(8, (screen.height() - self.height()) // 3),
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "welcome_identity"):
            self._sync_presence_layout()
        if hasattr(self, "drop_target"):
            self.drop_target.setGeometry(self.centralWidget().rect())

    def _sync_presence_layout(self):
        size = 136 if self.height() >= 600 else 88
        if self.hero_logo.width() != size:
            self.hero_logo.setFixedSize(size, size)
        full = self.width() >= 740 and not self.welcome.isVisibleTo(self.chat_content)
        self.presence_panel.setVisible(full)
        self.inline_avatar.setVisible(not full)

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, "fade_animation"):
            self.fade_animation.stop()
            self.fade_animation.deleteLater()
            del self.fade_animation
        if self.reduced_motion:
            self.setWindowOpacity(1.0)
        else:
            self.setWindowOpacity(0.0)
            self.fade_animation = QPropertyAnimation(self, b"windowOpacity", self)
            self.fade_animation.setDuration(150)
            self.fade_animation.setStartValue(0.0)
            self.fade_animation.setEndValue(1.0)
            self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.fade_animation.start()
        self.hero_logo.reveal()
        self.dock_avatar.reveal()
        if self._shell_mode == "chat":
            self.input_line.setFocus()
        if not self._setup_prompted and not settings_store.load().setup_complete:
            self._setup_prompted = True
            QTimer.singleShot(200, self.open_onboarding)

    def toggle_visibility(self):
        if self.isVisible() and self._shell_mode == "chat":
            self.collapse_to_notch()
            return
        self.open_full_chat()

    def open_about(self):
        AboutDialog(self).exec()

    def show_welcome_state(self, *, expand=True):
        if expand:
            self.set_shell_mode("chat")
        self.response_bar.hide()
        self.output_browser.hide()
        self.welcome.show()
        self.refresh_identity_greeting()
        self._sync_presence_layout()
        self.input_line.setEnabled(True)
        if self._shell_mode == "chat":
            self.input_line.setFocus()
        self._refresh_composer_context()

    def _refresh_composer_context(self):
        self.document_hint.setText(self.ui_text("Yerel kitaplığa eklendi · {name}", name=self._last_document_name or ""))
        self.document_hint.setVisible(self._shell_mode == "chat" and bool(self._last_document_name))
        if self.active_image_b64:
            self.input_line.setPlaceholderText(self.ui_text(
                "{name} hakkında ne öğrenmek istersin?", name=self.active_image_name))
            self.context_button.setText(self.ui_text("Görsel eklendi  ·  {name}", name=self.active_image_name))
            self.context_button.show()
            return
        self.input_line.setPlaceholderText(self.ui_text("Nexus'a bir şey sor…"))
        policy = settings_store.load().clipboard_policy
        if policy == "never":
            self.context_button.hide()
            return
        if policy == "ask":
            self.context_button.setText(self.ui_text("Panodan ekle  ·  Önce iznin istenir"))
            self.context_button.show()
            return
        clipboard = QApplication.clipboard()
        if clipboard and not clipboard.image().isNull():
            self.context_button.setText(self.ui_text("Panoda bir görsel var  ·  İncelemek için tıkla"))
            self.context_button.show()
        elif clipboard and len(clipboard.text().strip()) > 3:
            snippet = clipboard.text().strip().replace("\n", " ")[:72]
            self.context_button.setText(self.ui_text("Panodan ekle  ·  {snippet}", snippet=snippet))
            self.context_button.show()
        else:
            self.context_button.hide()

    def new_conversation(self):
        self.question_label.setText("")
        self.wake.cancel_pending()
        self._response_complete = True
        self._detach_response()
        if self.voice_record_worker:
            self.voice_record_worker.cancel()
            self.voice_record_worker = None
        self._recording_ready = False
        self._refresh_visual_activity()
        self._private_history.clear()
        self.active_memory_sources = []
        self.active_image_b64 = None
        self.active_image_name = None
        self._last_document_name = None
        self.input_line.clear()
        self.mic_btn.setChecked(False)
        self.current_conversation_id = str(uuid.uuid4())
        self.streaming_text = ""
        self.show_welcome_state()

    def open_settings(self):
        self._cancel_voice_input()
        self.wake.stop_worker()
        dialog = SetupDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            preferences = settings_store.load()
            self.voice_input_mode = preferences.voice_input_mode
            self._stop_speech()
            self.tts_enabled = preferences.tts_enabled
            self.tts_backend = preferences.tts_backend
            self.speaker_btn.setChecked(self.tts_enabled)
            self.apply_ui_language(preferences.language)
            self.apply_motion_preference(preferences.reduced_motion)
            self.apply_appearance(preferences)
            self.wake.reconfigure()

    def open_onboarding(self):
        self._cancel_voice_input()
        self.wake.stop_worker()
        if OnboardingDialog(parent=self).exec() == QDialog.DialogCode.Accepted:
            self.apply_ui_language(settings_store.load().language)
            self.refresh_provider_badge()
            if not settings_store.load().introduction_complete:
                self.open_introduction()
        self.wake.reconfigure()

    def open_introduction(self):
        if self.private_session:
            QMessageBox.information(self, self.ui_text("Özel oturum"), self.ui_text(
                "Tanışma, kişisel hafızanı düzenler. Kullanmak için özel oturumdan çık."))
            return
        self._cancel_voice_input()
        self.wake.stop_worker()
        IntroductionDialog(self, store=settings_store, repository=memory_repository).exec()
        self.refresh_identity_greeting()
        self.wake.reconfigure()

    def refresh_identity_greeting(self):
        preferences = settings_store.load()
        records = profile_memories(memory_repository, preferences, private=self.private_session)
        name = preferred_name(records)
        self.welcome_title.setText(self.ui_text("Merhaba, {name}.", name=name) if name else self.ui_text("Aklında ne var?"))
        invitation = not preferences.introduction_complete and not self.private_session
        self.welcome_subtitle.setText(self.ui_text(
            "Ben Nexus. Nasıl çalıştığını ve hedeflerini tanımak isterim.\nTanışalım mı?"
            if invitation else "Bir fikir, bir soru, yarım kalan bir iş.\nBirlikte devam edelim."))
        self.introduction_button.setText(self.ui_text("Tanışalım" if invitation else "Tanışma"))
        self.introduction_button.setEnabled(not self.private_session)

    def try_sample_document(self):
        """Import only the bundled fictional brief; leave sending to the user."""
        path = resource_root() / "docs" / "demo" / "project-brief.md"
        try:
            content, source_type = extract_document(path)
            request_json("POST", "/api/v1/documents", {
                "name": path.name, "content": content, "source_type": source_type,
            })
        except (OSError, ValueError, ImportError, RuntimeError):
            QMessageBox.warning(self, self.ui_text("Belge eklenemedi"), self.ui_text("Örnek belge yüklenemedi. Nexus'u yeniden açıp dene."))
            return
        self.new_conversation()
        self.knowledge_enabled = True
        self.knowledge_btn.setChecked(True)
        self._refresh_mode_tooltips()
        self.input_line.setText(self.ui_text("Örnek proje belgesini özetle ve sıradaki üç adımı çıkar."))
        self.input_line.setFocus()

    def apply_ui_language(self, language):
        self.ui_text.set_language(language)
        self.refresh_identity_greeting()
        self.drop_target.text = self.ui_text("Belgeyi veya görseli buraya bırak")
        self.drop_target.update()
        self._refresh_composer_context()
        self.refresh_provider_badge()
        self._refresh_mode_tooltips()
        self.wake._set_state(self.wake.state)
        self._refresh_visual_activity()
        self.notch_controller._sync_pin()

    def apply_motion_preference(self, reduced):
        self.reduced_motion = bool(reduced)
        for logo in (self.hero_logo, self.activity_logo, self.dock_avatar, self.inline_avatar,
                     self.notch_avatar, self.activity_indicator):
            logo.set_reduced_motion(self.reduced_motion)
        for control in self.findChildren(MotionButton):
            control.set_reduced_motion(self.reduced_motion)
        self.shell_transition.set_reduced_motion(self.reduced_motion)
        self.drop_target.set_reduced_motion(self.reduced_motion)
        if hasattr(self, "accent_edge"):
            self.accent_edge.configure(self.accent_edge.color, self.accent_edge.rgb, self.reduced_motion)
        if self.reduced_motion and hasattr(self, "fade_animation"):
            self.fade_animation.stop()
            self.setWindowOpacity(1.0)
        self._refresh_visual_activity()

    def apply_appearance(self, preferences):
        self.setStyleSheet(themed_style(preferences.accent_color))
        for avatar in (self.hero_logo, self.activity_logo, self.dock_avatar, self.inline_avatar, self.notch_avatar):
            avatar.set_appearance(preferences.companion_style, preferences.accent_color)
        self.accent_edge.configure(preferences.accent_color, preferences.rgb_enabled, self.reduced_motion)
        self.accent_edge.raise_()
        self.sound_feedback.configure(preferences.ui_sounds_enabled, preferences.ui_sound_volume)

    def set_wake_visual(self, listening):
        self._wake_listening = listening
        self._refresh_visual_activity()

    def _on_playback_state(self, state):
        self._refresh_visual_activity()

    def _react_companions(self, kind):
        if kind in {"success", "attachment", "error"}:
            self.sound_feedback.play(kind)
        for avatar in (self.hero_logo, self.activity_logo, self.dock_avatar, self.inline_avatar, self.notch_avatar):
            avatar.react(kind)

    def _refresh_visual_activity(self):
        if self._recording_ready:
            mode = "listening"
        elif not self._response_complete:
            mode = "thinking"
        elif self._wake_listening:
            mode = "listening"
        else:
            mode = "idle"
        if mode != "listening" and self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            mode = "speaking"
        description = self.ui_text({"idle": "Nexus hazır", "listening": "Nexus dinliyor",
                                    "thinking": "Nexus düşünüyor", "speaking": "Nexus konuşuyor"}[mode])
        self.dock_title.setText(description)
        self.notch_button.setToolTip(description + " · " + self.ui_text("Üzerine gel: mini panel · Tıkla: sohbet"))
        self.notch_button.setAccessibleName(self.ui_text("Nexus sohbetini aç") + " · " + description)
        if self.notch_indicator.property("activity") != mode:
            self.notch_indicator.setProperty("activity", mode)
            color = {"idle": "#528768", "listening": "#55ef9d", "thinking": "#91b6ff", "speaking": "#baa6ff"}[mode]
            self.notch_indicator.setStyleSheet(f"background: {color}; border-radius: 3px;")
        self.presence_title.setText(description)
        if self.presence_panel.property("activity") != mode:
            self.presence_panel.setProperty("activity", mode)
            self.presence_panel.style().unpolish(self.presence_panel)
            self.presence_panel.style().polish(self.presence_panel)
        self.dock_avatar.setProperty("activity", mode)
        if mode == "idle":
            self.dock_status.setText(self.ui_text("Bir soru sor veya araç seç."))
        elif mode == "listening":
            self.dock_status.setText(self.ui_text("Ses yerel olarak işleniyor."))
        elif mode == "speaking":
            self.dock_status.setText(self.ui_text("Yanıt seslendiriliyor."))
        self.presence_status.setText(self.dock_status.full_text)
        self.activity_indicator.set_mode(mode)
        for logo in (self.hero_logo, self.activity_logo, self.dock_avatar, self.inline_avatar, self.notch_avatar):
            # A status refresh must not interrupt the one-shot opening animation.
            if not (mode == "idle" and logo.mode == "entrance"):
                logo.set_mode(mode)
            logo.setAccessibleName(description)
            logo.setToolTip(description)

    def refresh_provider_badge(self):
        preferences = settings_store.load()
        selected = next(
            (item for item in preferences.providers if item.id == preferences.selected_provider_id),
            None,
        )
        if selected:
            model_name = selected.selected_model or self.ui_text("model seçilmedi")
            self.model_status.setText(f"●  {model_name.rsplit('/', 1)[-1]}")
        self.refresh_privacy_badge()

    def _set_badge(self, text: str, mode: str = "local"):
        for badge in (self.local_badge, self.mini_badge):
            badge.setText(self.ui_text(text))
            badge.setProperty("mode", mode)
            badge.style().unpolish(badge)
            badge.style().polish(badge)

    def refresh_privacy_badge(self):
        if self.private_session:
            self._set_badge("ÖZEL OTURUM", "private")
            return
        preferences = settings_store.load()
        selected = next(
            (item for item in preferences.providers if item.id == preferences.selected_provider_id),
            None,
        )
        if selected and not selected.is_local:
            self._set_badge("AĞ SAĞLAYICISI", "cloud")
        elif self.tts_enabled and self.tts_backend == "edge" and preferences.cloud_speech_consent:
            self._set_badge("YEREL MODEL · BULUT SESİ", "cloud")
        else:
            self._set_badge("YEREL MODEL")

    def open_history(self):
        if self.private_session:
            QMessageBox.information(self, "Özel oturum", "Geçmişi açmak için özel oturumdan çıkın.")
            return
        dialog = HistoryDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.selected_conversation_id:
            return
        self.new_conversation()
        self.current_conversation_id = dialog.selected_conversation_id
        messages = conversation_repository.messages(self.current_conversation_id)
        rendered: list[str] = []
        for message in messages:
            label = "Sen" if message["role"] == "user" else "Nexus"
            rendered.append(f"### {label}\n\n{message['content']}")
        self.streaming_text = "\n\n---\n\n".join(rendered)
        self._show_output()
        self._render_markdown(self.streaming_text)
        self.input_line.setFocus()

    def open_memory_manager(self, memory_id: str | None = None):
        MemoryDialog(parent=self, focus_memory_id=memory_id).exec()
        self.refresh_identity_greeting()

    def show_remembered_context(self):
        if self.private_session:
            QMessageBox.information(
                self, "Özel oturum", "Özel oturum mevcut hafızayı okumaz."
            )
            return
        memories = memory_repository.for_context()
        summary = memory_repository.profile_summary()
        lines = [f"- {item['content']}" for item in memories]
        content = "## Nexus'un hatırladıkları\n\n"
        if summary:
            content += f"{summary}\n\n"
        content += "\n".join(lines) if lines else "Henüz etkin bir hafıza yok."
        candidates = sum(item["status"] == "candidate" for item in memory_repository.list())
        if candidates:
            content += (
                f"\n\n**{candidates} aday kayıt onayınızı bekliyor.** "
                "Araçlar → Hafızayı yönet → Adayı etkinleştir ile inceleyebilirsiniz. "
                "Onaylanmayan adaylar yanıtlarda kullanılmaz."
            )
        self.streaming_text = content
        self._show_output()
        self._render_markdown(content)
        self.input_line.clear()

    def forget_last_memory_source(self):
        if not self.active_memory_sources:
            QMessageBox.information(
                self, "Unutulacak hafıza yok", "Son yanıtta kullanılan bir hafıza kaynağı bulunmuyor."
            )
            return
        source = self.active_memory_sources[0]
        answer = QMessageBox.question(
            self,
            "Bu hafızayı unut",
            f"Şu kayıt kalıcı olarak silinsin mi?\n\n{source.get('content', '')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Yes:
            memory_repository.delete(str(source["id"]))
            self.active_memory_sources = self.active_memory_sources[1:]

    def open_memory_correction(self, reference: str):
        memory_id = reference.strip()
        if memory_id.isdigit():
            index = int(memory_id) - 1
            if 0 <= index < len(self.active_memory_sources):
                memory_id = str(self.active_memory_sources[index]["id"])
        if not any(item["id"] == memory_id for item in memory_repository.list()):
            QMessageBox.information(
                self, "Hafıza bulunamadı", "Kaynak numarasını veya hafıza kimliğini kontrol edin."
            )
            return
        self.open_memory_manager(memory_id)

    def toggle_private_session(self):
        self.new_conversation()
        self.input_line.history.history.clear()
        self.input_line.history.index = -1
        self.private_session = not self.private_session
        self.refresh_identity_greeting()
        self.private_btn.setChecked(self.private_session)
        self._refresh_mode_tooltips()
        self.refresh_privacy_badge()

    def _refresh_mode_tooltips(self):
        self.private_btn.setToolTip(
            self.ui_text("Özel oturum açık · hiçbir konuşma kaydedilmez"
            if self.private_session
            else "Özel oturum · geçmişe kaydetme")
        )
        self.knowledge_btn.setToolTip(self.ui_text(
            "Yerel bilgi tabanı açık" if self.knowledge_enabled else "Yerel bilgi tabanını kullan"))
        self.private_pill.setChecked(self.private_session)
        self.private_pill.setToolTip(self.private_btn.toolTip())

    def toggle_knowledge(self):
        self.knowledge_enabled = not self.knowledge_enabled
        self.knowledge_btn.setChecked(self.knowledge_enabled)
        self._refresh_mode_tooltips()

    def import_document(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.ui_text("Nexus'a yerel belge ekle"),
            "",
            "Belgeler (*.pdf *.docx *.txt *.md *.rst *.py *.js *.ts *.json *.yaml *.yml *.toml);;Tüm dosyalar (*)",
        )
        if not path:
            return
        if self.add_local_document(Path(path)):
            QMessageBox.information(self, self.ui_text("Belge eklendi"),
                                    self.ui_text("Belge yalnızca yerel bilgi tabanına eklendi."))

    def add_local_document(self, path: Path) -> bool:
        try:
            content, source_type = extract_document(path)
            request_json(
                "POST",
                "/api/v1/documents",
                {"name": path.name, "content": content, "source_type": source_type},
            )
        except Exception:
            # Third-party file parsers may raise their own errors at this UI boundary.
            self._react_companions("error")
            QMessageBox.warning(self, self.ui_text("Belge eklenemedi"), self.ui_text(
                "Dosya okunamadı veya yerel Nexus bağlantısı kurulamadı. Dosyayı ve bağlantı ayarlarını kontrol et."))
            return False
        self.knowledge_enabled = True
        self.knowledge_btn.setChecked(True)
        self._last_document_name = path.name
        self.set_shell_mode("chat")
        self._refresh_mode_tooltips()
        self._refresh_composer_context()
        self.input_line.setFocus()
        self._react_companions("attachment")
        return True

    def _show_output(self):
        self.set_shell_mode("chat")
        self.response_bar.show()
        self.welcome.hide()
        self._sync_presence_layout()
        self.context_button.hide()
        self.output_browser.show()

    def start_research(self):
        preferences = settings_store.load()
        if not preferences.web_consent:
            answer = QMessageBox.question(
                self,
                "Web erişimi",
                "Bu özellik arama sorgusunu internete gönderir. Web araştırmasına izin verilsin mi?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            settings_store.update(web_consent=True)
        self.set_shell_mode("chat")
        self.input_line.setText("/web ")
        self.input_line.setFocus()
        self.input_line.setCursorPosition(len(self.input_line.text()))

    def dragEnterEvent(self, event):
        if any(
            url.isLocalFile() and url.toLocalFile().lower().endswith(self.IMAGE_EXTENSIONS + self.DOCUMENT_EXTENSIONS)
            for url in event.mimeData().urls()
        ):
            event.acceptProposedAction()
            self.drop_target.show()
        else:
            self.drop_target.hide()

    def dragLeaveEvent(self, event):
        self.drop_target.hide()
        event.accept()

    def dropEvent(self, event):
        self.drop_target.hide()
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            file_path = url.toLocalFile()
            if file_path.lower().endswith(self.DOCUMENT_EXTENSIONS):
                if self.add_local_document(Path(file_path)):
                    if not self.input_line.text().strip():
                        self.input_line.setText(self.ui_text("Eklediğim belgedeki önemli noktaları özetle."))
                    event.acceptProposedAction()
                return
            if not file_path.lower().endswith(self.IMAGE_EXTENSIONS):
                continue
            image = QImage(file_path)
            if image.isNull():
                continue
            self.active_image_b64 = encode_image(image)
            self.active_image_name = Path(file_path).name
            self.set_shell_mode("chat")
            self._refresh_composer_context()
            self._sync_send_button()
            self.input_line.setFocus()
            self._react_companions("attachment")
            event.acceptProposedAction()
            return

    def trigger_analysis(
        self,
        prompt: str,
        preview: str,
        image_b64: str | None = None,
        action_id: str | None = None,
    ):
        if self.worker and self.worker.isRunning():
            return
        self.question_label.setText(prompt[:240])
        self._show_output()
        self.input_line.clear()
        self.input_line.setEnabled(False)
        self.stop_btn.show()
        if re.match(r"^/(?:web|ara|search)\s+", prompt):
            self._set_badge("WEB ERİŞİMİ", "cloud")
        else:
            self.refresh_privacy_badge()
        image_note = self.ui_text("  ·  Görsel dahil") if image_b64 else ""
        self.output_browser.setHtml(
            f"<p style='color:#b6dec5;font-size:16px'>{self.ui_text('Yanıtını hazırlıyorum…')}</p>"
            f"<p style='color:#a0a4ab;font-size:13px'>{html.escape(preview)}{image_note}</p>"
        )
        preferences = settings_store.load()
        provider = next(
            (item for item in preferences.providers if item.id == preferences.selected_provider_id),
            None,
        )
        self.worker = ChatWorker(
            prompt,
            image_b64,
            conversation_id=self.current_conversation_id,
            provider_id=provider.id if provider else None,
            model_id=provider.selected_model if provider else None,
            private=self.private_session,
            use_knowledge=self.knowledge_enabled,
            action_id=action_id,
            history=self._private_history if self.private_session else None,
            language=self.ui_text.language,
        )
        self._connect_current(self.worker, "worker", self.worker.status_changed, self.update_status)
        self._connect_current(self.worker, "worker", self.worker.response_chunk, self.append_response)
        self._connect_current(self.worker, "worker", self.worker.response_completed, self.complete_response)
        self._connect_current(self.worker, "worker", self.worker.response_cancelled, self.response_was_cancelled)
        self._connect_current(self.worker, "worker", self.worker.memory_sources_received, self.set_memory_sources)
        self._connect_current(self.worker, "worker", self.worker.error_received, self.display_error)
        self._connect_current(self.worker, "worker", self.worker.warning_received, self.show_response_warning)
        self._track_worker(self.worker)
        self._pending_prompt = prompt
        self._response_complete = False
        self._refresh_visual_activity()
        self._stop_speech()
        self.streaming_text = ""
        self.active_memory_sources = []
        self.speech_buffer = ""
        if self.tts_enabled:
            self._start_speech()
        self.worker.start()
        self.active_image_b64 = None
        self.active_image_name = None

    def send_message(self):
        if self._quitting or not self.input_line.isEnabled() or (self.worker and self.worker.isRunning()):
            return
        self.wake.cancel_pending()
        text = self.input_line.text().strip()
        if text and not self.private_session:
            self.input_line.add_to_history(text)
        if self.active_image_b64:
            prompt = text or "Bu görseli incele ve önemli detayları açıkla."
            self.trigger_analysis(
                prompt,
                f"Görsel analizi · {self.active_image_name}",
                self.active_image_b64,
            )
            return
        if not text:
            return
        if text.startswith("/clip"):
            self.analyze_clipboard(text[5:].strip())
            return
        if text.startswith("/remember ") or text.startswith("/hatırla "):
            if self.private_session:
                self.display_error("Özel oturumda kalıcı hafızaya kayıt yapılmaz.")
                return
            value = text.split(" ", 1)[1].strip()
            if value:
                memory_repository.add(
                    value,
                    "fact",
                    "global",
                    source_conversation_id=self.current_conversation_id,
                )
                settings_store.update(memory_enabled=True)
                self.input_line.clear()
                QMessageBox.information(
                    self, "Hafızaya kaydedildi", "Bu bilgi yerel ve düzenlenebilir hafızaya eklendi."
                )
            return
        normalized = text.casefold().strip(" ?.!")
        if normalized in {
            "benim hakkımda ne hatırlıyorsun",
            "benimle ilgili ne hatırlıyorsun",
            "what do you remember about me",
        } or normalized in {"/memory", "/memories", "/hafıza"}:
            self.show_remembered_context()
            return
        if normalized in {"bunu unut", "forget this"}:
            self.forget_last_memory_source()
            self.input_line.clear()
            return
        if text.startswith("/correct ") or text.startswith("/düzelt "):
            if self.private_session:
                self.display_error("Özel oturumda kalıcı hafıza düzenlenmez.")
                return
            self.open_memory_correction(text.split(" ", 1)[1])
            self.input_line.clear()
            return
        action_commands = {
            "/summarize ": "summarize",
            "/rewrite ": "rewrite",
            "/translate ": "translate",
            "/fix ": "fix-writing",
            "/explain ": "explain-code",
        }
        for prefix, action_id in action_commands.items():
            if text.startswith(prefix):
                value = text[len(prefix) :].strip()
                if value:
                    self.trigger_analysis(value, text, action_id=action_id)
                return
        self.trigger_analysis(text, text)

    def _confirm_clipboard_access(self, explicit: bool = False) -> bool:
        if explicit:
            return True
        policy = settings_store.load().clipboard_policy
        if policy == "always":
            return True
        if policy == "never":
            QMessageBox.information(
                self, "Pano erişimi kapalı", "Pano erişimini Ayarlar bölümünden açabilirsiniz."
            )
            return False
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Pano izni")
        dialog.setText("Nexus panodaki içeriği okuyup seçili yerel modele gönderebilir mi?")
        once = dialog.addButton("Bir kez izin ver", QMessageBox.ButtonRole.AcceptRole)
        always = dialog.addButton("Her zaman izin ver", QMessageBox.ButtonRole.YesRole)
        dialog.addButton("İptal", QMessageBox.ButtonRole.RejectRole)
        dialog.exec()
        if dialog.clickedButton() is always:
            settings_store.update(clipboard_policy="always")
            return True
        return dialog.clickedButton() is once

    def analyze_clipboard(self, instruction: str | bool = "", *, explicit: bool = False):
        if isinstance(instruction, bool):
            instruction = ""
        if not self._confirm_clipboard_access(explicit):
            return
        clipboard = QApplication.clipboard()
        if not clipboard:
            return
        image = clipboard.image()
        if not image.isNull() and image.width() > 10 and image.height() > 10:
            prompt = instruction or "Bu görseli incele ve önemli detayları açıkla."
            self.trigger_analysis(prompt, "Panodaki görsel", encode_image(image))
            return
        text = clipboard.text().strip()
        if text:
            prompt = f"Aşağıdaki içeriği incele ve yardımcı ol:\n\n{text}"
            if instruction:
                prompt += f"\n\nEk talimat: {instruction}"
            self.trigger_analysis(prompt, "Panodaki içeriği incele")

    def analyze_selected_text(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.analyze_clipboard("Seçili metin üzerinde yardımcı ol", explicit=True)

    def update_status(self, status: str):
        self.dock_status.setText(status)
        self.presence_status.setText(status)
        self.output_browser.setHtml(
            f"<p style='color:#b6dec5;font-size:15px'>{html.escape(status)}</p>"
        )

    def append_response(self, chunk: str):
        if not chunk:
            return
        self.streaming_text += chunk
        if len(self.streaming_text) == len(chunk):
            self._flush_response_render()
        elif not self.render_timer.isActive():
            self.render_timer.start()

        if self.stream_voice_worker:
            if not self.speech_buffer:
                self._speech_wait_started = time.monotonic()
            self.speech_buffer += chunk
            pieces, self.speech_buffer = take_speech_chunks(self.speech_buffer, limit=110)
            for piece in pieces:
                self.stream_voice_worker.enqueue(piece)
            if pieces:
                self._speech_wait_started = time.monotonic()

    def _flush_waiting_speech(self):
        if (self.stream_voice_worker and len(self.speech_buffer) >= 25
                and time.monotonic() - self._speech_wait_started >= 0.45):
            # Leave the unfinished final word for the next chunk.
            end = self.speech_buffer.rfind(" ")
            if end >= 20:
                self.stream_voice_worker.enqueue(self.speech_buffer[:end])
                self.speech_buffer = self.speech_buffer[end:].lstrip()
                self._speech_wait_started = time.monotonic()

    def _flush_response_render(self):
        self.render_timer.stop()
        self._render_markdown(self.streaming_text)
        scrollbar = self.output_browser.verticalScrollBar()
        if not self.speech_follow.text:
            scrollbar.setValue(scrollbar.maximum())

    def set_memory_sources(self, sources: list):
        self.active_memory_sources = [item for item in sources if isinstance(item, dict)]

    def complete_response(self):
        self._response_complete = True
        self._flush_response_render()
        self._refresh_visual_activity()
        if self.private_session and self.streaming_text.strip():
            self._private_history = recent_turns([
                *self._private_history,
                {"role": "user", "content": self._pending_prompt},
                {"role": "assistant", "content": self.streaming_text},
            ])
        self.stop_btn.hide()
        self.input_line.setEnabled(True)
        if self._shell_mode == "chat":
            self.input_line.setFocus()
        if not self.streaming_text:
            self.display_error("Yerel model boş bir yanıt döndürdü.")
        elif self.active_memory_sources:
            source_lines = []
            for index, source in enumerate(self.active_memory_sources, 1):
                label = str(source.get("content", "Hafıza kaynağı"))[:90]
                conversation_id = source.get("source_conversation_id")
                if conversation_id:
                    url = f"{settings.backend_url}/api/v1/conversations/{conversation_id}"
                    source_lines.append(f"{index}. [{label}]({url})")
                else:
                    source_lines.append(f"{index}. {label}")
            self.streaming_text += "\n\n---\n\n**Kullanılan hafıza kaynakları**\n\n" + "\n".join(
                source_lines
            )
            self._render_markdown(self.streaming_text)
        if self.stream_voice_worker:
            if self.speech_buffer.strip():
                self.stream_voice_worker.enqueue(self.speech_buffer)
            self.stream_voice_worker.finish()
            self.speech_buffer = ""
        self.refresh_privacy_badge()
        if self.streaming_text.strip():
            self._react_companions("success")

    def cancel_active_response(self):
        if not self.worker or not self.worker.isRunning():
            return
        self._detach_response()
        self.response_was_cancelled()

    def response_was_cancelled(self):
        self._response_complete = True
        self._refresh_visual_activity()
        if self.streaming_text:
            self.streaming_text += "\n\n*Yanıt kullanıcı tarafından durduruldu.*"
            self._render_markdown(self.streaming_text)
        self.stop_btn.hide()
        self.input_line.setEnabled(True)
        if self._shell_mode == "chat":
            self.input_line.setFocus()
        self.refresh_privacy_badge()

    def display_error(self, message: str):
        self._response_complete = True
        self._refresh_visual_activity()
        self._show_output()
        self.stop_btn.hide()
        self.input_line.setEnabled(True)
        self.input_line.setFocus()
        self.output_browser.setHtml(
            "<div style='color:#fb7185;font-size:11px;font-weight:600'>BAĞLANTI HATASI</div>"
            f"<div style='color:#ddd8e6;margin-top:12px'>{html.escape(message)}</div>"
        )
        self._stop_speech()
        self.refresh_privacy_badge()
        self._react_companions("error")

    def toggle_tts(self):
        self.tts_enabled = not self.tts_enabled
        try:
            settings_store.update(tts_enabled=self.tts_enabled)
        except OSError:
            self.voice_error("Ses tercihi kaydedilemedi; yalnızca bu oturumda uygulanacak.")
        self.speaker_btn.setChecked(self.tts_enabled)
        state = "açık" if self.tts_enabled else "kapalı"
        self.speaker_btn.setToolTip(f"Seslendirme {state} · {self.tts_backend}")
        if not self.tts_enabled:
            self._stop_speech()
        elif self.streaming_text.strip() or not self._response_complete:
            self._stop_speech()
            self._start_speech()
            # Enabling after an answer reads that answer; during streaming, keep
            # accumulating it so the remaining tokens are spoken exactly once.
            self.speech_buffer = self.streaming_text.split("\n\n---\n\n**Kullanılan hafıza kaynakları**", 1)[0]
            if self._response_complete:
                self.stream_voice_worker.enqueue(self.speech_buffer)
                self.stream_voice_worker.finish()
                self.speech_buffer = ""
        self.refresh_privacy_badge()

    def _start_speech(self):
        preferences = settings_store.load()
        backend = self.tts_backend
        if backend == "edge" and not preferences.cloud_speech_consent:
            backend = "auto"
        self.stream_voice_worker = StreamingVoiceWorker(backend=backend)
        self.stream_voice_worker.audio_ready.connect(self.play_audio)
        if hasattr(self.stream_voice_worker, "chunk_ready"):
            self._connect_current(self.stream_voice_worker, "stream_voice_worker",
                                  self.stream_voice_worker.chunk_ready, self._speech_chunk_ready)
        if hasattr(self.stream_voice_worker, "timing_ready"):
            self._connect_current(self.stream_voice_worker, "stream_voice_worker",
                                  self.stream_voice_worker.timing_ready, self._speech_timing_ready)
        self._connect_current(
            self.stream_voice_worker, "stream_voice_worker",
            self.stream_voice_worker.error_received, self.voice_error,
        )
        self._track_worker(self.stream_voice_worker)
        self.speaker_btn.setToolTip(f"Seslendirme açık · {self.stream_voice_worker.speaker.backend}")
        self.stream_voice_worker.start()

    def _speech_chunk_ready(self, path, text, seconds, backend):
        self._audio_details[path] = (text, backend)
        self.speaker_btn.setToolTip(f"{backend} · son ses parçası {seconds:.2f} sn içinde üretildi")

    def _speech_timing_ready(self, path, timings):
        self._audio_timings[path] = timings

    def play_audio(self, path: str):
        if self._quitting or not self.tts_enabled or self.sender() is not self.stream_voice_worker:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass
            return
        self.audio_queue.append(path)
        if self.current_audio_path is None:
            self._play_next_audio()

    def _play_next_audio(self):
        if not self.audio_queue:
            self.current_audio_path = None
            self.speech_caption.hide()
            return
        wanted = settings_store.load().voice_output_device
        output = QMediaDevices.defaultAudioOutput()
        if wanted:
            output = next((device for device in QMediaDevices.audioOutputs()
                           if bytes(device.id()).hex() == wanted), None)
        if output is None or output.isNull():
            self._stop_speech()
            self.voice_error("Seçili hoparlör bulunamadı. Ayarlardan bağlı bir çıkış seçin.")
            return
        self.audio_output.setDevice(output)
        self.current_audio_path = self.audio_queue.pop(0)
        text, backend = self._audio_details.pop(self.current_audio_path, ("", ""))
        self.speech_follow.start(text, self._audio_timings.pop(self.current_audio_path, []))
        self.media_player.setSource(QUrl.fromLocalFile(self.current_audio_path))
        self.media_player.play()

    def _on_media_status(self, status):
        if status != QMediaPlayer.MediaStatus.EndOfMedia:
            return
        completed_path = self.current_audio_path
        self.speech_follow.finish()
        self.current_audio_path = None
        self.media_player.setSource(QUrl())
        if completed_path:
            try:
                Path(completed_path).unlink(missing_ok=True)
            except OSError:
                pass
        self._play_next_audio()

    def _on_audio_error(self, error, message):
        if error == QMediaPlayer.Error.NoError:
            return
        self._stop_speech()
        self.voice_error(f"Ses oynatılamadı: {message}")

    def toggle_voice_recording(self, checked=False, *, wake_triggered=False):
        if self._quitting:
            return
        if self.wake.defer_microphone(lambda: self.toggle_voice_recording(wake_triggered=wake_triggered)):
            self.update_status("Hey Nexus mikrofonu bırakıyor…")
            return
        if self.voice_record_worker and self.voice_record_worker.isRunning():
            self.mic_btn.setChecked(False)
            self._recording_ready = False
            self._refresh_visual_activity()
            self.update_status("Ses yerel Whisper ile çözümleniyor…")
            self.voice_record_worker.stop_recording()
            return

        if any(isinstance(worker, VoiceRecordWorker) and worker.isRunning() for worker in self._workers):
            self.voice_error("Önceki ses işlemi durduruluyor. Biraz sonra yeniden deneyin.")
            return

        # An explicit new recording interrupts both generation and speech playback.
        self._detach_response()
        self._response_complete = True
        self._recording_ready = False
        self._refresh_visual_activity()
        preferences = settings_store.load()
        self._show_output()
        self.mic_btn.setChecked(True)
        self.input_line.setEnabled(False)
        self.update_status(self.ui_text("Mikrofon hazırlanıyor… Konuşmak için hazır işaretini bekle."))
        self._stop_speech()
        recorder = AudioRecorder(
            device=preferences.voice_input_device,
            auto_stop=(wake_triggered or self.voice_input_mode == "vad"
                       or (self.voice_input_mode == "toggle" and preferences.voice_auto_finish)),
            threshold=preferences.voice_threshold,
            silence_seconds=preferences.voice_silence_seconds,
        )
        # Wake has already loaded the same local base model. Reuse it only after
        # its capture worker released the microphone; do not load a second copy.
        self._transcriber.configure(preferences.voice_transcription_model)
        if getattr(self.wake.detector, "model", None) is not None:
            self._transcriber.use_wake_model(self.wake.detector.model)
        self.voice_record_worker = VoiceRecordWorker(
            recorder=recorder, transcriber=self._transcriber, language=preferences.language
        )
        self._track_worker(self.voice_record_worker)
        mode = "vad" if recorder.auto_stop else self.voice_input_mode
        self._connect_current(self.voice_record_worker, "voice_record_worker", self.voice_record_worker.recording_started,
                              lambda: self._show_recording_ready(mode))
        self._connect_current(self.voice_record_worker, "voice_record_worker", self.voice_record_worker.status_changed,
                              self._voice_status)
        self._connect_current(self.voice_record_worker, "voice_record_worker", self.voice_record_worker.text_ready, self.on_voice_text_ready)
        self._connect_current(self.voice_record_worker, "voice_record_worker", self.voice_record_worker.error_received, self._voice_input_error)
        self._connect_current(self.voice_record_worker, "voice_record_worker", self.voice_record_worker.level_changed, self._voice_level)
        self.voice_record_worker.start()

    def _show_recording_ready(self, mode):
        worker = self.voice_record_worker
        if worker is None or worker.isInterruptionRequested() or worker._stopped.is_set():
            return
        self._recording_ready = True
        self._refresh_visual_activity()
        self.sound_feedback.play("listen")
        tr = self.ui_text
        instruction = {"push_to_talk": "F2'yi bırakınca kayıt biter.",
                       "vad": "Konuşma bitince kayıt otomatik durur. F2 ile de bitirebilirsin."}.get(
                           mode, "Bitirmek için F2'ye yeniden bas.")
        self.output_browser.setHtml(
            f"<div style='color:#b6dec5;font-size:11px;font-weight:600'>{tr('DİNLİYORUM')}</div>"
            f"<div style='color:#ddd8e6;font-size:17px;margin-top:12px'>{tr('Konuşmaya başlayabilirsin.')}</div>"
            f"<div style='color:#a0a4ab;margin-top:9px'>{tr(instruction)}</div>"
        )

    def _voice_status(self, status):
        if status != "Dinleniyor…":
            self._recording_ready = False
            self._refresh_visual_activity()
        self.update_status(self.ui_text(status))

    def _voice_level(self, level):
        self.mic_btn.setToolTip(f"Dinleniyor · ses düzeyi %{min(100, int(level * 100))} · Esc iptal")

    def _voice_input_error(self, message):
        self._recording_ready = False
        self._refresh_visual_activity()
        self.input_line.setEnabled(True)
        self.voice_error(message)
        self.update_status(self.ui_text(message))

    def _cancel_voice_input(self):
        self._recording_ready = False
        self._refresh_visual_activity()
        if hasattr(self, "wake"):
            self.wake.cancel_pending()
        self._voice_key_down = False
        if self.voice_record_worker:
            self.voice_record_worker.cancel()
            self.voice_record_worker = None
            self.mic_btn.setChecked(False)
            self.mic_btn.setToolTip(self.ui_text("Sesli konuş · F2"))
            self.input_line.setEnabled(True)
            self.update_status("Ses kaydı iptal edildi.")

    def hideEvent(self, event):
        self.notch_controller.stop()
        self.shell_transition.finish()
        self.drop_target.hide()
        self._cancel_voice_input()
        if hasattr(self, "fade_animation"):
            self.fade_animation.stop()
        super().hideEvent(event)

    def eventFilter(self, watched, event):
        # Qt may dispatch events while Python clears a collected window's attributes.
        if not hasattr(self, "input_line"):
            return False
        if watched is self.input_line and event.type() == QEvent.Type.EnabledChange:
            self._sync_send_button()
        if event.type() == QEvent.Type.WindowDeactivate and watched is self and self._voice_key_down:
            self._cancel_voice_input()
        if (self.voice_input_mode == "push_to_talk" and isinstance(watched, QWidget)
                and watched.window() is self and QApplication.activeModalWidget() is None
                and event.type() in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress, QEvent.Type.KeyRelease)
                and event.key() == Qt.Key.Key_F2):
            event.accept()
            if event.type() == QEvent.Type.ShortcutOverride or event.isAutoRepeat():
                return True
            if event.type() == QEvent.Type.KeyPress and not self._voice_key_down:
                self._voice_key_down = True
                if not self.voice_record_worker:
                    self.toggle_voice_recording()
            elif event.type() == QEvent.Type.KeyRelease and self._voice_key_down:
                self._voice_key_down = False
                self.wake.cancel_pending()
                if self.voice_record_worker:
                    self.voice_record_worker.stop_recording()
            return True
        return super().eventFilter(watched, event)

    def on_voice_text_ready(self, text: str):
        self._recording_ready = False
        self._refresh_visual_activity()
        self.input_line.setEnabled(True)
        self.mic_btn.setChecked(False)
        self.mic_btn.setToolTip(self.ui_text("Sesli konuş · F2"))
        if text.strip():
            self.input_line.setText(text.strip())
            if settings_store.load().voice_review_before_send:
                self.input_line.setFocus()
                self.update_status(self.ui_text("Metin hazır. Düzenleyip Enter ile gönderebilirsin."))
            else:
                self.send_message()
        else:
            self.display_error("Ses algılanamadı. Lütfen yeniden dene.")

    def _render_markdown(self, text):
        # QTextDocument accepts features; QTextBrowser's convenience method does not.
        self.render_timer.stop()
        document = self.output_browser.document()
        document.setMarkdown(text, QTextDocument.MarkdownFeature.MarkdownNoHTML)
        cursor = QTextCursor(document)
        cursor.beginEditBlock()
        block = document.begin()
        while block.isValid():
            cursor.setPosition(block.position())
            fmt = block.blockFormat()
            fmt.setLineHeight(140, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
            fmt.setBottomMargin(10 if not block.textList() else 5)
            cursor.setBlockFormat(fmt)
            block = block.next()
        cursor.endEditBlock()
        if self.speech_follow.text:
            self.speech_follow.remap()
            self.speech_follow.update(self.media_player.position())

    def _connect_current(self, worker, attribute, signal, callback):
        def deliver(*args):
            if not self._quitting and getattr(self, attribute) is worker:
                callback(*args)
        signal.connect(deliver)

    def _track_worker(self, worker):
        self._workers.add(worker)
        worker.finished.connect(lambda: self._release_worker(worker))

    def _release_worker(self, worker):
        self._workers.discard(worker)
        for attribute in ("worker", "voice_record_worker", "stream_voice_worker"):
            if getattr(self, attribute) is worker:
                setattr(self, attribute, None)
        worker.deleteLater()

    def _stop_speech(self):
        self._audio_details.clear()
        self._audio_timings.clear()
        self.speech_follow.reset()
        self.speech_caption.hide()
        if self.stream_voice_worker:
            self.stream_voice_worker.stop()
            self.stream_voice_worker = None
        self.speech_buffer = ""
        self.media_player.stop()
        self.media_player.setSource(QUrl())
        for path in [self.current_audio_path, *self.audio_queue]:
            if path:
                try:
                    Path(path).unlink(missing_ok=True)
                except OSError:
                    pass
        self.current_audio_path = None
        self.audio_queue.clear()

    def _detach_response(self):
        self.render_timer.stop()
        self._response_complete = True
        self._refresh_visual_activity()
        if self.worker:
            self.worker.cancel()
            self.worker = None
        self._stop_speech()
        self.stop_btn.hide()

    def voice_error(self, message):
        self.mic_btn.setChecked(False)
        self.model_status.setText(f"Ses hatası: {message[:100]}")
        self.model_status.setToolTip(message)
        self.speaker_btn.setToolTip(message)

    def show_response_warning(self, message):
        self.model_status.setText(self.ui_text("Yanıt uzunluk sınırına ulaştı"))
        self.model_status.setToolTip(message)

    def request_quit(self):
        self._quitting = True
        self.wake.close()
        self._private_history.clear()
        self._detach_response()
        for worker in tuple(self._workers):
            if isinstance(worker, StreamingVoiceWorker):
                worker.stop()
            else:
                worker.cancel()
        self.input_line.setEnabled(False)
        self.model_status.setText(self.ui_text("İşlemler durduruluyor…"))
        self._finish_quit()

    def _finish_quit(self):
        if any(worker.isRunning() for worker in self._workers):
            QTimer.singleShot(50, self._finish_quit)
            return
        self.close()
        QApplication.quit()

    def closeEvent(self, event):
        self.notch_controller.stop()
        self.accent_edge.timer.stop()
        self.sound_feedback.stop()
        self.wake.close()
        if any(worker.isRunning() for worker in self._workers):
            event.ignore()
            self.request_quit()
            return
        self._stop_speech()
        self.speech_timer.stop()
        QApplication.instance().removeEventFilter(self)
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Nexus")
    app.setQuitOnLastWindowClosed(False)
    window = SpotlightApp()
    window.show()
    hotkey_bridge = HotkeyBridge()
    hotkey_bridge.activated.connect(window.toggle_visibility)
    hotkey_bridge.selection_activated.connect(window.analyze_selected_text)
    try:
        import keyboard

        keyboard.add_hotkey("alt+space", hotkey_bridge.activated.emit)

        def capture_selection():
            keyboard.send("ctrl+c")
            time.sleep(0.15)
            hotkey_bridge.selection_activated.emit()

        keyboard.add_hotkey("ctrl+shift+space", capture_selection)
        app.aboutToQuit.connect(keyboard.unhook_all_hotkeys)
    except Exception as exc:
        print(f"Global hotkey could not be registered: {exc}", file=sys.stderr)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
