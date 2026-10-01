"""Build a local Windows preview; use a clean Python 3.11–3.13 environment for releases."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def prepare_notices():
    output = ROOT / "build/distribution-notices"
    if output.exists():
        if not output.resolve().is_relative_to((ROOT / "build").resolve()):
            raise RuntimeError("Notice output escapes build directory")
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    inventory = []
    for distribution in sorted(importlib.metadata.distributions(), key=lambda value: value.metadata.get("Name", "").lower()):
        name = distribution.metadata.get("Name", "unknown")
        inventory.append({"name": name, "version": distribution.version})
        for file in distribution.files or []:
            if any(word in file.name.lower() for word in ("license", "licence", "copying", "notice")) and file.suffix.lower() in {"", ".txt", ".md", ".rst", ".html"}:
                source = Path(distribution.locate_file(file))
                if source.is_file():
                    target = output / "licenses" / name / str(file).replace("..", "parent")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
    (output / "build-environment.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md", "THIRD_PARTY_NOTICES.tr.md"):
        shutil.copyfile(ROOT / name, output / name)
    (output / "PREVIEW.txt").write_text(
        "LOCAL DEVELOPMENT PREVIEW — NOT A PUBLIC RELEASE\n"
        "Nexus-authored source: MIT. Dependencies retain their separate licenses.\n"
        "PyQt6: GPLv3 or commercial. Qt/native dependencies: separate terms.\n"
        "The included inventory describes the build environment, not a final audited SBOM.\n"
        "No LLM, Whisper or Supertonic model weights are bundled.\n"
        "Complete distribution/license review and clean-machine tests before public release.\n"
        "This package is unsigned. Verify the installer hash against the local build manifest.\n",
        encoding="utf-8",
    )
    # Git-visible source includes current reviewed changes, never ignored runtime files.
    files = subprocess.run(["git", "-c", f"safe.directory={ROOT.as_posix()}", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT, check=True, capture_output=True).stdout.decode("utf-8").split("\0")
    from scripts.check_public_repo import path_problem

    with zipfile.ZipFile(output / "nexus-source.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(set(files)):
            if name and (ROOT / name).is_file():
                if path_problem(Path(name)):
                    raise RuntimeError("Source bundle contains a non-public file")
                archive.write(ROOT / name, name)
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication

    from frontend.brand import brand_pixmap

    app = QApplication.instance() or QApplication([])
    if not brand_pixmap(256).save(str(ROOT / "build/nexus.ico"), "ICO"):
        raise RuntimeError("Could not create installer icon")
    app.processEvents()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, help="Path to Inno Setup ISCC.exe")
    parser.add_argument("--installer-only", action="store_true")
    parser.add_argument("--refresh-notices", action="store_true", help="Refresh source/notices in an existing desktop build")
    args = parser.parse_args()
    if sys.platform != "win32":
        raise SystemExit("Build on Windows")
    if args.installer_only and args.refresh_notices:
        prepare_notices()
        destination = ROOT / "dist/Nexus/_internal/distribution-notices"
        if not destination.is_dir() or not destination.resolve().is_relative_to((ROOT / "dist/Nexus").resolve()):
            raise RuntimeError("Existing desktop notice directory not found")
        shutil.rmtree(destination)
        shutil.copytree(ROOT / "build/distribution-notices", destination)
    if not args.installer_only:
        prepare_notices()
        environment = os.environ.copy()
        windows = Path(environment.get("SystemRoot", "C:/Windows"))
        # External tools on PATH can silently substitute incompatible native DLLs
        # (for example Poppler's ICU for Windows ICU). Analyze a clean runtime.
        environment["PATH"] = os.pathsep.join([str(Path(sys.executable).parent), str(Path(sys.base_prefix)), str(windows / "System32"), str(windows)])
        environment["HF_HUB_OFFLINE"] = "1"
        environment["HF_HUB_DISABLE_TELEMETRY"] = "1"
        subprocess.run([sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", str(ROOT / "packaging/nexus.spec")], cwd=ROOT, env=environment, check=True)
    if args.compiler:
        subprocess.run([str(args.compiler), str(ROOT / "packaging/Nexus.iss")], cwd=ROOT, check=True)
        installer = ROOT / "dist/installer/NexusSetup.exe"
        manifest = {"file": installer.name, "sha256": hashlib.file_digest(installer.open("rb"), "sha256").hexdigest(), "bytes": installer.stat().st_size,
                    "python": sys.version.split()[0], "status": "local-preview", "signed": False, "models_bundled": False}
        installer.with_name("build-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
