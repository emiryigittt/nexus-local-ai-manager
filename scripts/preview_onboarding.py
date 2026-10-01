"""Render first-run pages using fictional provider/model data, without a server."""

import argparse
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtGui import QFontDatabase  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from backend.user_settings import SettingsStore  # noqa: E402
from frontend.onboarding import OnboardingDialog  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("build/onboarding-preview"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for name in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf"):
        path = fonts / name
        if path.exists():
            QFontDatabase.addApplicationFont(str(path))
    with tempfile.TemporaryDirectory(prefix="nexus-onboarding-preview-") as temporary:
        dialog = OnboardingDialog(store=SettingsStore(Path(temporary) / "settings.json"))
        dialog.resize(640, 600)
        dialog.results = [{"id": "ollama", "name": "Ollama", "healthy": True, "models": ["sample-model (preview)"]}]
        dialog.provider.addItem("Ollama", "ollama")
        dialog.fill_models()
        dialog.show()
        for language in ("tr", "en"):
            dialog.language.setCurrentIndex(dialog.language.findData(language))
            for page in range(3):
                dialog.pages.setCurrentIndex(page)
                dialog.status.clear()
                dialog.sync()
                app.processEvents()
                dialog.grab().save(str(args.output / f"{language}-step-{page + 1}.png"))
        dialog.reject()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
