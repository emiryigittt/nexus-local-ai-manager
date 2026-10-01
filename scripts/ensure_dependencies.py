"""Install source dependencies once, then only when the requirements change."""

import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_MODULES = ("PyQt6", "fastapi", "uvicorn", "httpx", "keyboard", "ddgs", "sounddevice", "numpy", "faster_whisper", "pyttsx3", "edge_tts", "dotenv", "yaml", "pypdf", "docx")


def main():
    requirements = ROOT / "requirements.txt"
    fingerprint = hashlib.sha256(requirements.read_bytes() + sys.version.encode()).hexdigest()
    marker = Path(sys.prefix) / ".nexus-dependencies"
    installed = all(importlib.util.find_spec(name) for name in REQUIRED_MODULES)
    if installed and marker.exists() and marker.read_text(encoding="utf-8").strip() == fingerprint:
        return 0
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements)], check=False)
    if result.returncode == 0:
        marker.write_text(fingerprint, encoding="utf-8")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
