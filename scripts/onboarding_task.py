"""Local-only provider discovery and a small real inference test."""

import argparse
import asyncio
import ipaddress
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402

from backend.providers import probe_provider  # noqa: E402
from backend.setup_events import report  # noqa: E402
from backend.user_settings import settings_store  # noqa: E402


def is_loopback(profile):
    url = urlsplit(profile.base_url)
    if not profile.enabled or not profile.is_local or url.scheme not in {"http", "https"}:
        return False
    if url.hostname == "localhost":
        return True
    try:
        return ipaddress.ip_address(url.hostname or "").is_loopback
    except ValueError:
        return False


async def run(action, provider_id="", model=""):
    profiles = [profile for profile in settings_store.load().providers if is_loopback(profile)]
    if action == "discover":
        results = await asyncio.gather(*(probe_provider(profile) for profile in profiles))
        # Do not expose exception bodies, keys or paths in the setup protocol.
        report("ready", providers=[{"id": item["id"], "name": item["name"], "healthy": item["healthy"], "models": item["models"]} for item in results])
        return 0
    profile = next((item for item in profiles if item.id == provider_id), None)
    if profile is None or not model.strip():
        report("failed")
        return 1
    try:
        async with httpx.AsyncClient(timeout=35, trust_env=False) as client:
            response = await client.post(f"{profile.base_url.rstrip('/')}/chat/completions", json={
                "model": model, "messages": [{"role": "user", "content": "Reply with OK."}],
                "stream": False, "max_tokens": 32,
            })
            response.raise_for_status()
            message = response.json()["choices"][0]["message"]
            if not (message.get("content") or message.get("reasoning_content")):
                raise ValueError("Empty response")
    except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError):
        report("failed")
        return 1
    report("ready")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["discover", "test"])
    parser.add_argument("--provider", default="")
    parser.add_argument("--model", default="")
    args = parser.parse_args(argv)
    return asyncio.run(run(args.action, args.provider, args.model))


if __name__ == "__main__":
    raise SystemExit(main())
