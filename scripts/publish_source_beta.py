"""Publish the first source beta from a successful trusted-main CI run.

No installers, models, local outputs or user data are uploaded. Existing releases
are left alone, and an existing tag is never moved.
"""

import json
import os
import re
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "emiryigittt/nexus-local-ai-manager"
TAG = "v0.3.0-beta.1"
TITLE = "Nexus 0.3.0 Beta 1 — Your local AI companion"


def request_api(path, token, method="GET", payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPOSITORY}/{path}",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Nexus-source-beta-publisher",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if method == "GET" and error.code == 404:
            return None
        raise RuntimeError(f"GitHub request failed: HTTP {error.code}") from None
    except urllib.error.URLError:
        raise RuntimeError("GitHub request failed: network unavailable") from None


def main():
    if (os.environ.get("GITHUB_REPOSITORY") != REPOSITORY
            or os.environ.get("GITHUB_EVENT_NAME") != "push"
            or os.environ.get("GITHUB_REF") != "refs/heads/main"):
        raise RuntimeError("Publication requires this repository's trusted main push")
    sha = os.environ.get("GITHUB_SHA", "")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise RuntimeError("Missing verified source commit")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if project["project"]["version"] != "0.3.0b1":
        print("First-beta publisher skipped: project version has advanced")
        return
    token = os.environ["GITHUB_TOKEN"]
    existing = request_api(f"releases/tags/{TAG}", token)
    if existing:
        print(f"Existing release preserved: {existing['html_url']}")
        return
    tag = request_api(f"git/ref/tags/{TAG}", token)
    if tag and (tag["object"]["type"] != "commit" or tag["object"]["sha"] != sha):
        raise RuntimeError("Existing tag does not match this verified commit; refusing publication")
    notes = (ROOT / "docs/releases/v0.3.0-beta.1.md").read_text(encoding="utf-8")
    release = request_api("releases", token, "POST", {
        "tag_name": TAG,
        "target_commitish": sha,
        "name": TITLE,
        "body": notes,
        "draft": False,
        "prerelease": True,
        "make_latest": "false",
    })
    print(f"Published source beta: {release['html_url']}")


if __name__ == "__main__":
    main()
