"""Render deterministic desktop UI previews without network, microphone, or user data."""

import argparse
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--language", choices=("tr", "en"), default="tr")
    parser.add_argument("--compact", action="store_true", help="Render 640x560 main and 560x600 settings")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nexus-ui-preview-") as directory:
        os.environ["NEXUS_DATA_DIR"] = directory
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        os.environ["NEXUS_TTS_ENABLED"] = "0"
        from PyQt6.QtGui import QFontDatabase
        from PyQt6.QtWidgets import QApplication

        from backend.user_settings import settings_store
        from frontend.app import SpotlightApp
        from frontend.setup_dialog import SetupDialog

        app = QApplication([])
        # Qt's Windows offscreen platform does not always discover system fonts.
        fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for name in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf", "consola.ttf"):
            path = fonts / name
            if path.exists():
                QFontDatabase.addApplicationFont(str(path))
        preferences = settings_store.load()
        preferences.setup_complete = True
        preferences.language = args.language
        preferences.providers[0].selected_model = "Local model" if args.language == "en" else "Yerel model"
        settings_store.save(preferences)
        window = SpotlightApp()
        if args.compact:
            window.setFixedSize(640, 560)
        window.wake.timer.stop()
        window.show()
        app.processEvents()
        window.setWindowOpacity(1)
        window.grab().save(str(args.output / "welcome.png"))
        window._show_output()
        window.question_label.setText("Bu hafta daha odaklı çalışmak için bir plan yapalım.")
        window.streaming_text = (
            "## Daha az dağınıklık, daha çok odak.\n\n"
            "Haftayı doldurmak yerine, gerçekten ilerlemek istediğin **üç sonuca** odaklanalım.\n\n"
            "1. **Önceliğini seç.** Her sabah, bugün bitse fark yaratacak tek işi belirle.\n"
            "2. **Kendine alan aç.** Bildirimleri kapat ve 45 dakikalık bir çalışma aralığı ayır.\n"
            "3. **Küçük bir kapanış yap.** Gün sonunda ilerlemeni not et; yarının ilk adımını yaz.\n\n"
            "İstersen şimdi üzerinde çalıştığın projeye göre bu planı birlikte düzenleyebiliriz."
        )
        if args.language == "en":
            window.question_label.setText("Let's make a plan for a more focused week.")
            window.streaming_text = (
                "## Less distraction, more focus.\n\n"
                "Instead of filling your week, choose **three outcomes** that matter.\n\n"
                "1. **Pick a priority.** Identify one task that would make today worthwhile.\n"
                "2. **Make room.** Silence notifications for a focused 45-minute session.\n"
                "3. **Close the loop.** Note your progress and write down tomorrow's first step.\n\n"
                "We can adapt this plan to the project you're working on."
            )
        window._render_markdown(window.streaming_text)
        app.processEvents()
        window.grab().save(str(args.output / "response.png"))
        window.speech_caption.setText("supertonic · Pick a priority. Focus on one task each morning."
                                      if args.language == "en" else
                                      "supertonic · Önceliğini seç. Her sabah tek bir işe odaklan.")
        window.speech_caption.show()
        app.processEvents()
        window.grab().save(str(args.output / "speech-caption.png"))
        window.speech_caption.hide()
        dialog = SetupDialog(parent=window)
        if args.compact:
            dialog.resize(560, 600)
        dialog.show()
        app.processEvents()
        dialog.grab().save(str(args.output / "settings.png"))
        dialog.tabs.setCurrentIndex(1)
        app.processEvents()
        dialog.grab().save(str(args.output / "privacy.png"))
        dialog.tabs.setCurrentIndex(2)
        app.processEvents()
        dialog.grab().save(str(args.output / "voice.png"))
        dialog.voice.sections.setCurrentIndex(1)
        app.processEvents()
        dialog.grab().save(str(args.output / "voice-wake.png"))
        dialog.voice.sections.setCurrentIndex(2)
        scrollbar = dialog.tabs.currentWidget().verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        app.processEvents()
        dialog.grab().save(str(args.output / "voice-output.png"))
        dialog.close()
        window.close()
        app.processEvents()
    print(str(args.output.resolve()))


if __name__ == "__main__":
    main()
