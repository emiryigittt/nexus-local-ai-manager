"""Synthetic extraction -> candidate -> approval -> reopen check using the selected local LLM.

Never reads existing conversations or changes live memory/settings. Uses temporary SQLite.
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    from backend.config import settings
    from backend.user_settings import settings_store

    profile = settings_store.selected_provider()
    if not profile or not profile.enabled or not profile.is_local:
        raise RuntimeError("Select an enabled local model first")
    model = profile.selected_model or settings.model
    url = profile.base_url.rstrip("/") + "/chat/completions"
    with tempfile.TemporaryDirectory(prefix="nexus-memory-check-") as directory:
        os.environ["NEXUS_DATA_DIR"] = directory
        from backend.memory import MemoryRepository
        from backend.memory_learning import learn_from_turn

        repository = MemoryRepository(Path(directory) / "check.db")
        try:
            count = asyncio.run(learn_from_turn(
                "Kalıcı tercihim: teknik yanıtları kısa ve Türkçe istiyorum.",
                "Anladım, teknik yanıtları kısa ve Türkçe tutacağım.",
                chat_url=url, model=model,
                headers={"Authorization": f"Bearer {settings.api_key}"} if settings.api_key else {},
                conversation_id="synthetic-test", project_id=None, repository=repository,
            ))
            candidates = repository.list()
            inactive_before_approval = not repository.for_context()
            for item in candidates:
                repository.activate(item["id"])
            reopened = MemoryRepository(repository.path)
            result = {"saved_candidates": count, "inactive_before_approval": inactive_before_approval,
                      "active_after_reopen": len(reopened.for_context()), "live_data_changed": False}
        except Exception as exc:
            result = {"failed": type(exc).__name__, "live_data_changed": False}
        print(json.dumps(result))
        return 0 if result.get("saved_candidates", 0) > 0 and result.get("active_after_reopen", 0) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
