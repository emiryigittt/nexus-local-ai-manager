"""Small synchronous client used by short-lived desktop dialogs."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from backend.config import settings


def request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        f"{settings.backend_url}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            if response.status == 204:
                return None
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            message = json.loads(exc.read().decode("utf-8")).get("detail", str(exc))
        except (UnicodeDecodeError, ValueError):
            message = str(exc)
        raise RuntimeError(message) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError("Nexus yerel servisine ulaşılamadı.") from exc
    except (UnicodeDecodeError, ValueError) as exc:
        raise RuntimeError("Nexus servisi geçersiz bir yanıt döndürdü.") from exc
