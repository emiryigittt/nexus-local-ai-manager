"""Publish a pinned prerelease after verifying the entire source and installer set."""

import argparse
import json
import os
import re
import subprocess
import tomllib
from pathlib import Path

from scripts.finalize_windows_release import ASSETS, REQUIRED_CHECKS, TAG, digest
from scripts.publish_source_beta import REPOSITORY, request_api

ROOT = Path(__file__).resolve().parents[1]


def trusted_context():
    if (os.environ.get("GITHUB_REPOSITORY") != REPOSITORY
            or os.environ.get("GITHUB_EVENT_NAME") != "push"
            or os.environ.get("GITHUB_REF") != "refs/heads/main"):
        raise RuntimeError("Publication requires this repository's trusted main push")
    sha = os.environ.get("GITHUB_SHA", "")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise RuntimeError("Missing verified source commit")
    return sha


def find_release(token):
    release = request_api(f"releases/tags/{TAG}", token)
    if release:
        return release
    # GitHub's tag endpoint excludes unpublished drafts. Resolve their IDs from
    # the authenticated release list instead of treating them as missing.
    drafts = [item for item in request_api("releases?per_page=100", token)
              if item["tag_name"] == TAG]
    if len(drafts) > 1:
        raise RuntimeError("Multiple matching release drafts; refusing publication")
    return drafts[0] if drafts else None


def verify_assets(folder, sha):
    expected = ASSETS | {"release-manifest.json", "SHA256SUMS.txt"}
    if {path.name for path in folder.iterdir()} != expected or any((folder / name).is_symlink() for name in expected):
        raise RuntimeError("Release asset set is incomplete or contains unexpected files")
    manifest = json.loads((folder / "release-manifest.json").read_text(encoding="utf-8"))
    if (manifest.get("release") != TAG or manifest.get("source_commit") != sha
            or manifest.get("distribution_license") != "GPL-3.0-only"
            or manifest.get("clean_installer_checks_passed") is not True
            or set(manifest.get("files", {})) != ASSETS):
        raise RuntimeError("Release manifest does not match the verified source")
    for name, entry in manifest["files"].items():
        if digest(folder / name) != entry["sha256"] or (folder / name).stat().st_size != entry["bytes"]:
            raise RuntimeError("Release asset integrity failure: " + name)
    expected_sums = "".join(f"{digest(folder / name)}  {name}\n" for name in sorted(ASSETS | {"release-manifest.json"}))
    if (folder / "SHA256SUMS.txt").read_text(encoding="utf-8") != expected_sums:
        raise RuntimeError("Release checksum list mismatch")
    report = json.loads((folder / "windows-package-check.json").read_text(encoding="utf-8"))
    checks = report.get("checks", {})
    if (report.get("error") or not REQUIRED_CHECKS.issubset(checks)
            or not all(value is True for value in checks.values())
            or report.get("installer_sha256") != digest(folder / "NexusSetup.exe")):
        raise RuntimeError("Installer checks do not match the release")
    catalog = json.loads((folder / "dependency-sources.json").read_text(encoding="utf-8"))
    if catalog.get("release") != TAG or catalog.get("review_status") != "ready":
        raise RuntimeError("Corresponding source review is incomplete")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    sha = trusted_context()
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if project["project"]["version"] != "0.3.0b2":
        print("Windows beta publisher skipped: project version has advanced")
        return
    token = os.environ["GITHUB_TOKEN"]
    existing = find_release(token)
    if existing and not existing["draft"]:
        print("Existing public release preserved")
        if args.check_only:
            output = os.environ.get("GITHUB_OUTPUT")
            if output:
                with open(output, "a", encoding="utf-8") as stream:
                    stream.write("build=false\n")
        return
    tag = request_api(f"git/ref/tags/{TAG}", token)
    if tag and (tag["object"]["type"] != "commit" or tag["object"]["sha"] != sha):
        raise RuntimeError("Existing tag does not match verified commit; refusing publication")
    if args.check_only:
        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as stream:
                stream.write("build=true\n")
        return
    folder = ROOT / "dist/release"
    verify_assets(folder, sha)
    notes = ROOT / "docs/releases/v0.3.0-beta.2.md"
    environment = dict(os.environ, GH_TOKEN=token)
    if not existing:
        existing = request_api("releases", token, "POST", {
            "tag_name": TAG, "target_commitish": sha, "draft": True,
            "prerelease": True, "name": "Nexus 0.3.0 Beta 2 — Windows installer",
            "body": notes.read_text(encoding="utf-8"),
        })
    elif existing.get("target_commitish") != sha:
        # Only an unpublished draft may be refreshed, and only after the new
        # source and installer have passed verification. Published tags are fixed.
        request_api(f"releases/{existing['id']}", token, "PATCH", {
            "target_commitish": sha, "body": notes.read_text(encoding="utf-8"),
        })
    subprocess.run(["gh", "release", "upload", TAG, "--repo", REPOSITORY, "--clobber", *[str(path) for path in sorted(folder.iterdir())]], env=environment, check=True)
    # A draft is made public only after every asset is present at the expected size.
    uploaded = request_api(f"releases/{existing['id']}", token)
    if not uploaded or not uploaded["draft"] or uploaded.get("target_commitish") != sha:
        raise RuntimeError("Release draft source changed; refusing publication")
    expected = {path.name: path.stat().st_size for path in folder.iterdir()}
    actual = {entry["name"]: entry["size"] for entry in uploaded["assets"]}
    if actual != expected:
        raise RuntimeError("Uploaded asset set mismatch; draft remains unpublished")
    for entry in uploaded["assets"]:
        if entry.get("digest") and entry["digest"] != "sha256:" + digest(folder / entry["name"]):
            raise RuntimeError("Remote asset digest mismatch; draft remains unpublished")
    request_api(f"releases/{uploaded['id']}", token, "PATCH", {"draft": False, "prerelease": True, "make_latest": "false"})
    print(f"Published complete Windows beta: https://github.com/{REPOSITORY}/releases/tag/{TAG}")


if __name__ == "__main__":
    main()
