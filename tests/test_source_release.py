import urllib.error
from unittest.mock import Mock

import pytest

from scripts import publish_source_beta as publisher


@pytest.fixture
def trusted_run(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_REPOSITORY", publisher.REPOSITORY)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-test-only")
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.3.0b1"\n', encoding="utf-8")
    notes = tmp_path / "docs/releases"
    notes.mkdir(parents=True)
    (notes / "v0.3.0-beta.1.md").write_text("source code; no Windows installer", encoding="utf-8")
    monkeypatch.setattr(publisher, "ROOT", tmp_path)


@pytest.mark.parametrize("field,value", [
    ("GITHUB_REPOSITORY", "another/project"),
    ("GITHUB_EVENT_NAME", "pull_request"),
    ("GITHUB_REF", "refs/heads/other"),
])
def test_untrusted_context_never_requests_publication(trusted_run, monkeypatch, field, value):
    monkeypatch.setenv(field, value)
    api = Mock()
    monkeypatch.setattr(publisher, "request_api", api)
    with pytest.raises(RuntimeError, match="trusted main"):
        publisher.main()
    api.assert_not_called()


def test_existing_release_is_preserved(trusted_run, monkeypatch):
    api = Mock(return_value={"html_url": "https://example.invalid/existing"})
    monkeypatch.setattr(publisher, "request_api", api)
    publisher.main()
    assert api.call_count == 1
    assert api.call_args.args[0] == f"releases/tags/{publisher.TAG}"


def test_future_version_never_publishes_old_beta(trusted_run, monkeypatch):
    (publisher.ROOT / "pyproject.toml").write_text('[project]\nversion = "0.4.0"\n', encoding="utf-8")
    api = Mock()
    monkeypatch.setattr(publisher, "request_api", api)
    publisher.main()
    api.assert_not_called()


def test_existing_different_tag_is_never_moved(trusted_run, monkeypatch):
    api = Mock(side_effect=[None, {"object": {"type": "commit", "sha": "b" * 40}}])
    monkeypatch.setattr(publisher, "request_api", api)
    with pytest.raises(RuntimeError, match="refusing publication"):
        publisher.main()
    assert api.call_count == 2


def test_new_release_pins_commit_and_contains_no_installer(trusted_run, monkeypatch):
    api = Mock(side_effect=[None, None, {"html_url": "https://example.invalid/new"}])
    monkeypatch.setattr(publisher, "request_api", api)
    publisher.main()
    payload = api.call_args.args[3]
    assert payload["target_commitish"] == "a" * 40
    assert payload["prerelease"] is True
    assert payload["make_latest"] == "false"
    assert "source code" in payload["body"]
    assert "Windows installer" in payload["body"]
    assert api.call_args.args[:3] == ("releases", "synthetic-test-only", "POST")


@pytest.mark.parametrize("status", [403, 429, 500])
def test_api_errors_do_not_look_like_missing_release(monkeypatch, status):
    def fail(request, timeout):
        raise urllib.error.HTTPError(request.full_url, status, "synthetic", {}, None)

    monkeypatch.setattr(publisher.urllib.request, "urlopen", fail)
    with pytest.raises(RuntimeError, match=f"HTTP {status}"):
        publisher.request_api("releases/tags/test", "synthetic-test-only")
