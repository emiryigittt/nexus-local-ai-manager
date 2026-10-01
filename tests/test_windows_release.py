import hashlib
import json
import shutil
from unittest.mock import Mock

import pytest

from scripts import publish_windows_release as publisher
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


def test_unpublished_draft_is_found_when_tag_endpoint_returns_404(monkeypatch):
    draft = {"id": 42, "tag_name": TAG, "draft": True}
    api = Mock(side_effect=[None, [draft]])
    monkeypatch.setattr(publisher, "request_api", api)
    assert publisher.find_release("synthetic") == draft
    assert api.call_args.args[0] == "releases?per_page=100"


def test_duplicate_drafts_are_not_published(monkeypatch):
    api = Mock(side_effect=[None, [{"tag_name": TAG}, {"tag_name": TAG}]])
    monkeypatch.setattr(publisher, "request_api", api)
    with pytest.raises(RuntimeError, match="Multiple"):
        publisher.find_release("synthetic")


@pytest.mark.parametrize("corrupt", [False, True])
def test_draft_refresh_requires_verified_assets_and_uses_release_id(monkeypatch, release, tmp_path, corrupt):
    source, _, _ = release
    repository = tmp_path / "repository"
    folder = repository / "dist/release"
    folder.mkdir(parents=True)
    for file in source.iterdir():
        if file.is_file():
            shutil.copyfile(file, folder / file.name)
    (repository / "pyproject.toml").write_text('[project]\nversion="0.3.0b2"\n')
    notes = repository / "docs/releases"
    notes.mkdir(parents=True)
    (notes / "v0.3.0-beta.2.md").write_text("Synthetic release notes")
    monkeypatch.setattr(publisher, "ROOT", repository)
    monkeypatch.setattr("sys.argv", ["publisher"])
    for key, value in {"GITHUB_REPOSITORY": publisher.REPOSITORY, "GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main", "GITHUB_SHA": "a" * 40, "GITHUB_TOKEN": "synthetic"}.items():
        monkeypatch.setenv(key, value)
    assets = [{"id": index + 100, "name": path.name, "size": path.stat().st_size, "digest": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()} for index, path in enumerate(folder.iterdir())]
    draft = {"id": 42, "tag_name": TAG, "draft": True, "target_commitish": "b" * 40, "assets": assets}
    calls = []

    def api(path, token, method="GET", payload=None):
        calls.append((path, method, payload))
        if path.startswith(("releases/tags/", "git/ref/")):
            return None
        if path == "releases?per_page=100":
            return [draft]
        if path == "releases/42":
            if method == "PATCH":
                draft.update(payload)
            return draft
        if path.startswith("releases/assets/") and method == "DELETE":
            return None
        raise AssertionError(path)

    monkeypatch.setattr(publisher, "request_api", api)
    command = Mock()
    monkeypatch.setattr(publisher, "upload_asset", command)
    if corrupt:
        (folder / "NexusSetup.exe").write_bytes(b"modified")
        with pytest.raises(RuntimeError, match="integrity"):
            publisher.main()
        assert not any(method != "GET" for _, method, _ in calls)
        command.assert_not_called()
    else:
        publisher.main()
        assert ("releases/42", "GET", None) in calls
        assert ("releases/42", "PATCH", {"tag_name": TAG, "target_commitish": "a" * 40, "body": "Synthetic release notes"}) in calls
        assert calls[-1] == ("releases/42", "PATCH", {"draft": False, "prerelease": True, "make_latest": "false"})


@pytest.mark.parametrize("status", [201, 503])
def test_release_id_upload_streams_exact_bytes_and_checks_status(monkeypatch, tmp_path, status):
    path = tmp_path / "asset.zip"
    content = b"synthetic" * 200000
    path.write_bytes(content)
    connection = Mock()
    connection.getresponse.return_value = type("Response", (), {"status": status, "read": lambda self: b'{"id":42}'})()
    constructor = Mock(return_value=connection)
    monkeypatch.setattr(publisher.http.client, "HTTPSConnection", constructor)
    if status == 201:
        assert publisher.upload_asset(123, path, "synthetic") == {"id": 42}
    else:
        with pytest.raises(RuntimeError, match="HTTP 503"):
            publisher.upload_asset(123, path, "synthetic")
    constructor.assert_called_once_with("uploads.github.com", timeout=180)
    assert connection.putrequest.call_args.args == ("POST", f"/repos/{publisher.REPOSITORY}/releases/123/assets?name=asset.zip")
    assert b"".join(call.args[0] for call in connection.send.call_args_list) == content
    assert ("Content-Length", str(len(content))) in [call.args for call in connection.putheader.call_args_list]
    connection.close.assert_called_once()
