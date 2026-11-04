import hashlib
import urllib.error

import pytest

from scripts import prepare_distribution

PAYLOAD = b"synthetic corresponding source body"


def archive_entry(body: bytes = PAYLOAD):
    return {
        "name": "synthetic",
        "filename": "synthetic.tar.gz",
        "url": "https://example.invalid/synthetic.tar.gz",
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
    }


class Response:
    """Minimal stand-in for the streamed HTTP response the mirror copies."""

    def __init__(self, body: bytes):
        self.body = body
        self.delivered = False

    def read(self, size=-1):
        if self.delivered:
            return b""
        self.delivered = True
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Open:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = 0

    def __call__(self, request, context=None, timeout=None):
        self.calls += 1
        result = self.results.pop(0) if len(self.results) > 1 else self.results[0]
        if isinstance(result, BaseException):
            raise result
        return result


@pytest.fixture
def mirror(tmp_path, monkeypatch):
    monkeypatch.setattr(prepare_distribution, "CACHE", tmp_path)
    monkeypatch.setattr(prepare_distribution.time, "sleep", lambda seconds: None)
    return tmp_path


def http_error(status: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://example.invalid/synthetic.tar.gz", status, "synthetic", {}, None)


@pytest.mark.parametrize("status", [429, 503])
def test_a_busy_or_reset_host_is_retried(mirror, monkeypatch, status):
    open_source = Open(http_error(status), urllib.error.URLError("synthetic reset"), Response(PAYLOAD))
    monkeypatch.setattr(prepare_distribution.urllib.request, "urlopen", open_source)
    entry = archive_entry()

    assert prepare_distribution.checked_source(entry) == mirror / entry["filename"]
    assert (mirror / entry["filename"]).read_bytes() == PAYLOAD
    assert open_source.calls == 3
    assert not list(mirror.glob("*.partial"))


def test_a_removed_archive_fails_once_with_its_status(mirror, monkeypatch):
    open_source = Open(http_error(404))
    monkeypatch.setattr(prepare_distribution.urllib.request, "urlopen", open_source)

    with pytest.raises(RuntimeError, match="HTTP 404"):
        prepare_distribution.checked_source(archive_entry())
    assert open_source.calls == 1
    assert not list(mirror.glob("*"))


def test_exhausted_retries_keep_the_original_reason(mirror, monkeypatch):
    open_source = Open(urllib.error.URLError("synthetic dns failure"))
    monkeypatch.setattr(prepare_distribution.urllib.request, "urlopen", open_source)

    with pytest.raises(RuntimeError, match="synthetic dns failure"):
        prepare_distribution.checked_source(archive_entry())
    assert open_source.calls == prepare_distribution.DOWNLOAD_ATTEMPTS
    assert not list(mirror.glob("*"))


def test_a_stale_cached_copy_is_refetched_once(mirror, monkeypatch):
    entry = archive_entry()
    (mirror / entry["filename"]).write_bytes(b"truncated by an earlier run")
    open_source = Open(Response(PAYLOAD))
    monkeypatch.setattr(prepare_distribution.urllib.request, "urlopen", open_source)

    assert prepare_distribution.checked_source(entry) == mirror / entry["filename"]
    assert (mirror / entry["filename"]).read_bytes() == PAYLOAD
    assert open_source.calls == 1


def test_a_host_that_keeps_serving_the_wrong_bytes_is_rejected(mirror, monkeypatch):
    open_source = Open(Response(b"substituted content"))
    monkeypatch.setattr(prepare_distribution.urllib.request, "urlopen", open_source)

    with pytest.raises(RuntimeError, match="integrity failure"):
        prepare_distribution.checked_source(archive_entry())
    assert open_source.calls == 2
    assert not list(mirror.glob("*"))
