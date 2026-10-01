"""Prepare checked, locally mirrored source archives and distribution notices."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import ssl
import subprocess
import tarfile
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath

import certifi

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "build/source-cache"
CATALOG = ROOT / "packaging/dependency-sources.json"
TAG = "v0.3.0-beta.2"


def source_catalog():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    if data.get("release") != TAG or data.get("review_status") != "ready":
        raise RuntimeError("Corresponding source review is incomplete")
    names = {entry["name"].casefold() for entry in data["archives"]}
    required = {"pyqt6", "qtbase", "qtmultimedia", "qtsvg", "qtimageformats", "qttranslations", "ffmpeg", "ffmpeg-qt", "edge-tts", "pyttsx3", "certifi", "tqdm", "x264", "x265", "lamer", "opus", "pyav-ffmpeg-build"}
    if not required.issubset(names):
        raise RuntimeError("Missing mandatory corresponding source")
    for entry in data["archives"]:
        if (Path(entry["filename"]).name != entry["filename"]
                or len(entry["sha256"]) != 64 or not entry["url"].startswith("https://")):
            raise RuntimeError("Invalid source catalog entry")
    return data


def checked_source(entry):
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / entry["filename"]
    if not target.exists():
        partial = target.with_name(target.name + ".partial")
        request = urllib.request.Request(entry["url"], headers={"User-Agent": "Nexus-source-distribution"})
        with urllib.request.urlopen(request, context=ssl.create_default_context(cafile=certifi.where()), timeout=120) as response, partial.open("wb") as stream:
            shutil.copyfileobj(response, stream)
        partial.replace(target)
    with target.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != entry["sha256"] or target.stat().st_size != entry["bytes"]:
        raise RuntimeError("Source archive integrity failure: " + entry["name"])
    return target


def is_notice(name):
    path = PurePosixPath(name)
    return (not path.is_absolute() and ".." not in path.parts and ":" not in name and "\\" not in name
            and (any(word in path.name.casefold() for word in ("license", "licence", "copying", "notice", "copyright"))
                 or any(part.casefold() in {"licenses", "licences", "copyrights"} for part in path.parts))
            and path.suffix.casefold() not in {".dll", ".pyd", ".so", ".png", ".jpg", ".pdf", ".zip", ".gz", ".xz", ".bz2", ".zst"})


def archive_notices(source, destination):
    """Read regular text only; never extract arbitrary upstream archive paths."""
    count = 0

    def save(name, content):
        nonlocal count
        if not is_notice(name) or len(content) > 2_000_000 or b"\0" in content:
            return
        # Full upstream paths can exceed Win32 installation limits. Preserve the
        # original text in a short unique filename and retain its source path index.
        basename = re.sub(r"[^A-Za-z0-9._-]", "_", PurePosixPath(name).name)[:32]
        short_name = hashlib.sha256(name.encode()).hexdigest()[:12] + "-" + basename + ".txt"
        target = destination / short_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        index = destination / "source-paths.json"
        records = json.loads(index.read_text(encoding="utf-8")) if index.exists() else {}
        records[short_name] = name
        index.write_text(json.dumps(records, indent=2), encoding="utf-8")
        count += 1

    if source.name.endswith(".tar.zst"):
        # Windows tar supports zstd source packages. Files are read to stdout only.
        members = subprocess.check_output(["tar", "-tf", str(source)], timeout=60).decode().splitlines()
        for name in members:
            if is_notice(name):
                save(name, subprocess.check_output(["tar", "-xOf", str(source), "--", name], timeout=60))
            elif name.endswith((".tar.xz", ".tar.gz", ".tar.bz2")) and not PurePosixPath(name).is_absolute() and ".." not in PurePosixPath(name).parts and ":" not in name and "\\" not in name:
                # MSYS2 source packages carry original sources plus packaging patches.
                nested = CACHE / ("nested-" + Path(name).name)
                nested.write_bytes(subprocess.check_output(["tar", "-xOf", str(source), "--", name], timeout=120))
                try:
                    count += archive_notices(nested, destination / "upstream")
                finally:
                    nested.unlink()
    elif zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as archive:
            for entry in archive.infolist():
                if not entry.is_dir() and entry.file_size <= 2_000_000 and is_notice(entry.filename):
                    save(entry.filename, archive.read(entry))
    else:
        with tarfile.open(source) as archive:
            for entry in archive:
                if entry.isfile() and entry.size <= 2_000_000 and is_notice(entry.name):
                    stream = archive.extractfile(entry)
                    if stream:
                        save(entry.name, stream.read())
    return count


def decorate_notices(output):
    catalog = source_catalog()
    with ThreadPoolExecutor(max_workers=6) as pool:
        paths = list(pool.map(checked_source, catalog["archives"]))
    counts = {}
    for entry, path in zip(catalog["archives"], paths, strict=True):
        counts[entry["filename"]] = archive_notices(path, output / "licenses" / entry["name"] / "source-notices")
    for name in ("COPYING", "DISTRIBUTION_LICENSE.md", "DISTRIBUTION_LICENSE.tr.md"):
        shutil.copyfile(ROOT / name, output / name)
    shutil.copyfile(CATALOG, output / "dependency-sources.json")
    shutil.copyfile(ROOT / "packaging/windows-build.lock.txt", output / "windows-build.lock.txt")
    shutil.copytree(ROOT / "packaging/licenses", output / "licenses/supplemental", dirs_exist_ok=True)
    (output / "source-notice-counts.json").write_text(json.dumps(counts, indent=2), encoding="utf-8")
    (output / "SOURCE_ACCESS.txt").write_text(
        f"Nexus {TAG}: combined Windows application under GNU GPL version 3.\n"
        "Nexus-authored source: MIT; third-party notices remain applicable.\n"
        "Complete Nexus source is included in nexus-source.zip.\n"
        "Corresponding dependency sources and build recipes are served alongside the installer:\n"
        f"https://github.com/emiryigittt/nexus-local-ai-manager/releases/tag/{TAG}\n"
        "Download Nexus-dependency-sources.zip; verify SHA256SUMS.txt.\n"
        "No activation or signing key is required to install a modified build.\n"
        "Compatible dynamically linked libraries can be replaced in the application directory.\n"
        "Unsigned build; no warranty. LLM, Whisper and Supertonic weights are separate downloads.\n",
        encoding="utf-8",
    )
    (output / "PREVIEW.txt").unlink(missing_ok=True)


def prepare_sources():
    catalog = source_catalog()
    release = ROOT / "dist/release"
    release.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        paths = list(pool.map(checked_source, catalog["archives"]))
    with zipfile.ZipFile(release / "Nexus-dependency-sources.zip", "w", zipfile.ZIP_STORED, allowZip64=True) as archive:
        for path in paths:
            archive.write(path, "archives/" + path.name)
        for name in ("packaging/dependency-sources.json", "packaging/windows-build.lock.txt", "COPYING", "LICENSE", "DISTRIBUTION_LICENSE.md", "DISTRIBUTION_LICENSE.tr.md", "THIRD_PARTY_NOTICES.md", "THIRD_PARTY_NOTICES.tr.md", "docs/WINDOWS_PREVIEW.md", "docs/WINDOWS_PREVIEW.tr.md"):
            archive.write(ROOT / name, name)
        for path in sorted((ROOT / "packaging/licenses").rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(ROOT).as_posix())
    print(f"Mirrored {len(paths)} verified source archives")


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    prepare_sources()
