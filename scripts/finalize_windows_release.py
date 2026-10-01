"""Assemble release assets only after clean Windows installer checks pass."""

import hashlib
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = "v0.3.0-beta.2"
ASSETS = {"NexusSetup.exe", "Nexus-source.zip", "Nexus-dependency-sources.zip", "windows-package-check.json", "dependency-sources.json"}
REQUIRED_CHECKS = {"installer_completed", "installed_app_opens_without_python", "installer_upgrade_completed", "uninstaller_completed", "uninstall_preserves_user_data", "uninstall_removes_test_registration", "packaged_distribution_notices", "unneeded_native_libraries_excluded"}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    sha = os.environ.get("GITHUB_SHA", "")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise RuntimeError("Release assembly requires a CI source commit")
    report_path = ROOT / "build/windows-package-check.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    checks = report.get("checks", {})
    if (report.get("error") or not REQUIRED_CHECKS.issubset(checks)
            or not checks or not all(value is True for value in checks.values())):
        raise RuntimeError("Clean Windows installer verification has not passed")
    installer = ROOT / "dist/installer/NexusSetup.exe"
    if report.get("installer_sha256") != digest(installer):
        raise RuntimeError("The checked installer is not the release installer")
    release = ROOT / "dist/release"
    release.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(installer, release / installer.name)
    shutil.copyfile(ROOT / "build/distribution-notices/nexus-source.zip", release / "Nexus-source.zip")
    shutil.copyfile(report_path, release / "windows-package-check.json")
    shutil.copyfile(ROOT / "packaging/dependency-sources.json", release / "dependency-sources.json")
    files = {name: {"sha256": digest(release / name), "bytes": (release / name).stat().st_size} for name in sorted(ASSETS)}
    manifest = {"release": TAG, "source_commit": sha, "distribution_license": "GPL-3.0-only", "signed": False, "clean_installer_checks_passed": True, "files": files}
    (release / "release-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    sums = "".join(f"{digest(release / name)}  {name}\n" for name in sorted(ASSETS | {"release-manifest.json"}))
    (release / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
    print(f"Prepared {len(files)} checked assets plus manifest and checksums")


if __name__ == "__main__":
    main()
