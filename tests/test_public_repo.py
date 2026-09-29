import json
from pathlib import Path

import pytest

from scripts.check_public_repo import check_language_pairs, inspect_text, path_problem


@pytest.mark.parametrize("name", [".env", ".env.local", "private.sqlite3", "private.db-wal",
                                  "models/voice.bin", "venv/settings.py", "speech.wav",
                                  "settings.json", "memory-export-1.json", "pano_ozelligi.png"])
def test_runtime_files_are_not_publishable(name):
    assert path_problem(Path(name))


@pytest.mark.parametrize("name", [".env.example", "backend/main.py", "docs/assets/preview.png"])
def test_source_and_reviewable_preview_paths_are_allowed(name):
    assert path_problem(Path(name)) is None


def test_local_links_are_checked_but_remote_links_are_not_fetched(tmp_path):
    (tmp_path / "README.md").touch()
    text = "[good](../README.md) [bad](missing.md) [site](https://example.invalid) [anchor](#test)"
    assert inspect_text(Path("docs/test.md"), text, tmp_path) == ["missing local link: missing.md"]


def test_link_escape_is_rejected_and_code_examples_ignored(tmp_path):
    text = "[escape](../../outside.md)\n```python\n[x](ignored.md)\n```"
    assert inspect_text(Path("docs/test.md"), text, tmp_path) == ["local link escapes repository"]


def test_credential_findings_do_not_repeat_the_value(tmp_path):
    synthetic = "ghp_" + "A" * 36
    findings = inspect_text(Path("test.py"), synthetic, tmp_path)
    assert findings and synthetic not in str(findings)


def test_markdown_url_encoded_file_names(tmp_path):
    (tmp_path / "example file.md").touch()
    assert not inspect_text(Path("README.md"), "[file](example%20file.md)", tmp_path)


def test_language_manifest_requires_both_files_and_reciprocal_links(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/languages.json").write_text(json.dumps({
        "pairs": [["README.md", "README.tr.md"]],
    }), encoding="utf-8")
    (tmp_path / "README.md").write_text("[Türkçe](README.tr.md)", encoding="utf-8")
    assert check_language_pairs(tmp_path)
    (tmp_path / "README.tr.md").write_text("Türkçe", encoding="utf-8")
    assert check_language_pairs(tmp_path) == [
        ("README.tr.md", "missing link to paired language document"),
    ]
    (tmp_path / "README.tr.md").write_text("[English](README.md)", encoding="utf-8")
    assert check_language_pairs(tmp_path) == []


@pytest.mark.parametrize("manifest", [{}, {"pairs": []}, {"pairs": [["../outside.md", "missing.md"]]},
                                       {"pairs": [["single.md"]]}, {"pairs": [[1, 2]]}])
def test_bad_language_manifests_fail_closed(tmp_path, manifest):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/languages.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert check_language_pairs(tmp_path)


def test_maintained_documentation_has_language_navigation():
    root = Path(__file__).resolve().parents[1]
    assert check_language_pairs(root) == []


@pytest.mark.parametrize("name", ["output/pdf/example.pdf", "tmp/pdfs/photo.jpg",
                                  "tmp/pdfs/generate.py"])
def test_personal_document_outputs_stay_out_even_if_force_added(name):
    assert path_problem(Path(name)) == "personal document-generation output"


def test_link_to_existing_but_unpublished_file_is_rejected(tmp_path):
    (tmp_path / "private.pdf").touch()
    issues = inspect_text(Path("README.md"), "[file](private.pdf)", tmp_path, {"README.md"})
    assert issues == ["local link points to a file excluded from publication: private.pdf"]


def test_link_to_published_file_is_accepted(tmp_path):
    (tmp_path / "guide.md").touch()
    assert not inspect_text(Path("README.md"), "[guide](guide.md)", tmp_path,
                            {"README.md", "guide.md"})
