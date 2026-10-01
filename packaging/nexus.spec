# PyInstaller Windows preview. Model weights and user data are never bundled.
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

root = Path(SPECPATH).parent
datas = [
    (str(root / "frontend/assets"), "frontend/assets"),
    (str(root / "docs/demo/project-brief.md"), "docs/demo"),
    (str(root / "build/distribution-notices"), "distribution-notices"),
]
binaries = []
# Qt's modern MSVC runtime uses additional companion DLLs that dependency
# analysis can miss when they are loaded dynamically. Ship the complete set.
import PyQt6
for runtime_dll in (Path(PyQt6.__file__).parent / "Qt6/bin").glob("*140*.dll"):
    binaries.append((str(runtime_dll), "."))
    binaries.append((str(runtime_dll), "PyQt6/Qt6/bin"))
hiddenimports = [
    "uvicorn.logging", "uvicorn.loops.auto", "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl", "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on", "pyttsx3.drivers.sapi5",
]
for package in ("sherpa_onnx", "soundfile", "faster_whisper", "ctranslate2"):
    package_datas, package_binaries, package_imports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_imports
hiddenimports += collect_submodules("ddgs")
a = Analysis(
    [str(root / "run_nexus.py")], pathex=[str(root)], binaries=binaries,
    datas=datas, hiddenimports=hiddenimports,
    excludes=["pytest", "ruff", "matplotlib", "tkinter", "torch", "PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineWidgets"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Nexus", debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=False,
          icon=str(root / "build/nexus.ico"))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Nexus")
