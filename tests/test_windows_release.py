import hashlib
import json

import pytest

from scripts.finalize_windows_release import ASSETS, REQUIRED_CHECKS, TAG
from scripts.publish_windows_release import trusted_context, verify_assets


@pytest.fixture
def release(tmp_path):
    def write(name, data):
        (tmp_path / name).write_text(json.dumps(data), encoding="utf-8")

    (tmp_path / "NexusSetup.exe").write_bytes(b"synthetic-installer")
    (tmp_path / "Nexus-source.zip").write_bytes(b"synthetic-source")
    (tmp_path / "Nexus-dependency-sources.zip").write_bytes(b"synthetic-dependency-source")
    write("dependency-sources.json", {"release": TAG, "review_status": "ready"})
    write("windows-package-check.json", {
        "checks": dict.fromkeys(REQUIRED_CHECKS, True),
        "installer_sha256": hashlib.sha256(b"synthetic-installer").hexdigest(),
    })

    def refresh():
        files = {name: {"sha256": hashlib.sha256((tmp_path / name).read_bytes()).hexdigest(), "bytes": (tmp_path / name).stat().st_size} for name in ASSETS}
        write("release-manifest.json", {"release": TAG, "source_commit": "a" * 40, "distribution_license": "GPL-3.0-only", "clean_installer_checks_passed": True, "files": files})
        sums = "".join(f"{hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()}  {name}\n" for name in sorted(ASSETS | {"release-manifest.json"}))
        (tmp_path / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")

    refresh()
    return tmp_path, refresh, write


def test_complete_matching_release_is_accepted(release):
    folder, _, _ = release
    verify_assets(folder, "a" * 40)


@pytest.mark.parametrize("change", ["missing-source", "modified-installer", "extra-file", "wrong-commit", "missing-install-check", "wrong-tested-installer", "incomplete-source-review"])
def test_incomplete_or_mismatched_release_is_rejected(release, change):
    folder, refresh, write = release
    sha = "a" * 40
    if change == "missing-source":
        (folder / "Nexus-dependency-sources.zip").unlink()
    elif change == "modified-installer":
        (folder / "NexusSetup.exe").write_bytes(b"modified")
    elif change == "extra-file":
        (folder / "personal.txt").write_text("synthetic")
    elif change == "wrong-commit":
        sha = "b" * 40
    elif change in {"missing-install-check", "wrong-tested-installer"}:
        report = json.loads((folder / "windows-package-check.json").read_text())
        if change == "missing-install-check":
            report["checks"].pop("installer_completed")
        else:
            report["installer_sha256"] = "b" * 64
        write("windows-package-check.json", report)
        refresh()
    else:
        write("dependency-sources.json", {"release": TAG, "review_status": "incomplete"})
        refresh()
    with pytest.raises(RuntimeError):
        verify_assets(folder, sha)


def test_untrusted_workflow_cannot_publish(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "another/project")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    with pytest.raises(RuntimeError, match="trusted main"):
        trusted_context()
