"""Stable locations for Nexus user data and caches."""

from __future__ import annotations

import os
from pathlib import Path


def data_dir() -> Path:
    override = os.getenv("NEXUS_DATA_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    local_app_data = os.getenv("LOCALAPPDATA", "").strip()
    root = Path(local_app_data) if local_app_data else Path.home() / ".local" / "share"
    return root / "Nexus"


def ensure_data_dirs() -> Path:
    root = data_dir()
    for child in (root, root / "cache", root / "logs", root / "models"):
        child.mkdir(parents=True, exist_ok=True)
    return root


def settings_path() -> Path:
    return data_dir() / "settings.json"


def database_path() -> Path:
    return data_dir() / "nexus.db"


def mcp_settings_path() -> Path:
    return data_dir() / "mcp_servers.json"
