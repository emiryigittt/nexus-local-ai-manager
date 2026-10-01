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
for package in ("sherpa_onnx", "faster_whisper", "ctranslate2"):
    package_datas, package_binaries, package_imports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_imports
hiddenimports += collect_submodules("ddgs")
a = Analysis(
    [str(root / "run_nexus.py")], pathex=[str(root)], binaries=binaries,
    datas=datas, hiddenimports=hiddenimports,
    excludes=["pytest", "ruff", "matplotlib", "tkinter", "torch", "soundfile", "_soundfile", "_soundfile_data", "PyQt6.QtPdf", "PyQt6.QtPdfWidgets", "PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineWidgets"],
    noarchive=False,
)
# The assistant uses text PDF extraction and raster widgets, not Qt's PDF
# image plugin or software OpenGL. Ship only the standard x64 PortAudio backend.
def needed_binary(entry):
    name = Path(entry[0]).name.lower()
    if name in {"qpdf.dll", "qt6pdf.dll", "opengl32sw.dll"}:
        return False
    if name.startswith("libportaudio") and name != "libportaudio64bit.dll":
        return False
    return True

a.binaries = [entry for entry in a.binaries if needed_binary(entry)]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Nexus", debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=False,
          icon=str(root / "build/nexus.ico"))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Nexus")

# Record the files actually shipped, separately from installed build tools.
import hashlib
import json
frozen_root = Path(DISTPATH) / "Nexus" / "_internal"
frozen_files = []
for file in sorted(frozen_root.rglob("*")):
    if file.is_file() and "distribution-notices" not in file.relative_to(frozen_root).parts:
        with file.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        frozen_files.append({"path": file.relative_to(frozen_root).as_posix(), "bytes": file.stat().st_size, "sha256": digest})
(frozen_root / "distribution-notices/frozen-files.json").write_text(json.dumps(frozen_files, indent=2), encoding="utf-8")
