"""Keep an older main build from publishing after its source has been corrected."""

import os

from scripts.publish_source_beta import REPOSITORY, request_api


def main():
    if (os.environ.get("GITHUB_REPOSITORY") != REPOSITORY
            or os.environ.get("GITHUB_EVENT_NAME") != "push"
            or os.environ.get("GITHUB_REF") != "refs/heads/main"):
        print("No superseded main runs to cancel in this context")
        return
    current = int(os.environ["GITHUB_RUN_ID"])
    sha = os.environ["GITHUB_SHA"]
    token = os.environ["GITHUB_TOKEN"]
    runs = request_api("actions/workflows/ci.yml/runs?branch=main&event=push&per_page=30", token)
    for run in runs["workflow_runs"]:
        if run["id"] < current and run["head_sha"] != sha and run["status"] != "completed":
            try:
                request_api(f"actions/runs/{run['id']}/cancel", token, "POST", {})
            except RuntimeError as error:
                if "HTTP 409" in str(error):
                    continue
                raise
            print(f"Cancelled superseded main run {run['id']}")


if __name__ == "__main__":
    main()
