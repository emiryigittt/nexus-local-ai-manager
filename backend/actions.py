"""Validated built-in and user-defined prompt actions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from backend.app_paths import data_dir


@dataclass(frozen=True, slots=True)
class PromptAction:
    id: str
    name: str
    description: str
    prompt: str
    risk: str = "local"
    source: str = "built-in"

    def render(self, value: str) -> str:
        return self.prompt.replace("{input}", value.strip())

    def public(self) -> dict[str, str]:
        return asdict(self)


BUILT_IN_ACTIONS = (
    PromptAction("summarize", "Özetle", "Ana noktaları kısa ve açık çıkar.", "Şunu özetle:\n\n{input}"),
    PromptAction(
        "rewrite", "Yeniden yaz", "Metni daha açık ve profesyonel yap.", "Şunu anlamını koruyarak daha açık ve profesyonel yaz:\n\n{input}"
    ),
    PromptAction("translate", "Çevir", "Metni kullanıcının diline çevir.", "Şunu kullanıcının diline doğal biçimde çevir:\n\n{input}"),
    PromptAction("fix-writing", "Yazımı düzelt", "Yazım ve dil bilgisini düzelt.", "Yalnızca gerekli yazım ve dil bilgisi düzeltmelerini yap:\n\n{input}"),
    PromptAction("explain-code", "Kodu açıkla", "Kodun davranışını ve risklerini açıkla.", "Bu kodun ne yaptığını, önemli kararlarını ve olası risklerini açıkla:\n\n{input}"),
)


class ActionRegistry:
    def __init__(self, directory: Path | None = None):
        self.directory = directory or data_dir() / "actions"

    @staticmethod
    def _validate(raw: dict[str, Any], source: str) -> PromptAction:
        identifier = str(raw.get("id", "")).strip()
        name = str(raw.get("name", "")).strip()
        prompt = str(raw.get("prompt", "")).strip()
        if not identifier or not identifier.replace("-", "").isalnum():
            raise ValueError("Action id must contain only letters, numbers, and hyphens.")
        if not name or "{input}" not in prompt:
            raise ValueError("Action name and a prompt containing {input} are required.")
        risk = str(raw.get("risk", "local")).strip().casefold()
        if risk not in {"local", "network", "sensitive"}:
            raise ValueError("Action risk must be local, network, or sensitive.")
        return PromptAction(
            id=identifier,
            name=name,
            description=str(raw.get("description", "")).strip(),
            prompt=prompt,
            risk=risk,
            source=source,
        )

    def all(self) -> list[PromptAction]:
        actions = {item.id: item for item in BUILT_IN_ACTIONS}
        if not self.directory.exists():
            return list(actions.values())
        for path in sorted((*self.directory.glob("*.yaml"), *self.directory.glob("*.yml"))):
            try:
                document = yaml.safe_load(path.read_text(encoding="utf-8"))
                values = document if isinstance(document, list) else [document]
                for value in values:
                    if isinstance(value, dict):
                        action = self._validate(value, path.name)
                        actions[action.id] = action
            except (OSError, ValueError, yaml.YAMLError):
                continue
        return sorted(actions.values(), key=lambda item: item.name.casefold())

    def get(self, action_id: str) -> PromptAction | None:
        return next((item for item in self.all() if item.id == action_id), None)


action_registry = ActionRegistry()
