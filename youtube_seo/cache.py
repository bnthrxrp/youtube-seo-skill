"""Cache em disco. A chave da API nunca entra na chave nem no arquivo."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable

_SECRET_PARAMS = {"key", "api_key"}


class FileCache:
    def __init__(
        self,
        directory: str | Path,
        now: Callable[[], float] | None = None,
        enabled: bool = True,
    ):
        self.directory = Path(directory)
        self.now = now or time.time
        self.enabled = enabled

    def make_key(self, namespace: str, params: dict[str, Any]) -> str:
        clean = {
            k: v
            for k, v in params.items()
            if v is not None and k.lower() not in _SECRET_PARAMS
        }
        raw = namespace + "\n" + json.dumps(clean, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Any | None:
        if not self.enabled:
            return None
        path = self.directory / f"{key}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if float(data.get("expires_at", 0)) <= self.now():
            return None
        return data.get("payload")

    def put(self, key: str, payload: Any, ttl: float, meta: dict[str, Any] | None = None) -> None:
        if not self.enabled:
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        body = {
            "expires_at": self.now() + ttl,
            "meta": meta or {},
            "payload": payload,
        }
        (self.directory / f"{key}.json").write_text(
            json.dumps(body, ensure_ascii=False),
            encoding="utf-8",
        )
