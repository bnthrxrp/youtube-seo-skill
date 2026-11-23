"""Controle da cota diária gratuita da YouTube Data API v3.

``search.list`` custa 100 unidades. ``channels.list``, ``playlistItems.list`` e
``videos.list`` custam 1 unidade por chamada. A cota diária gratuita padrão é
10.000 unidades. Chamada atendida pelo cache local não debita.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

DAILY_LIMIT = 10_000

COSTS = {
    "search.list": 100,
    "videos.list": 1,
    "channels.list": 1,
    "playlistItems.list": 1,
}

REGRA = (
    "search.list custa 100 unidades na cota diária gratuita de 10.000. "
    "channels.list, playlistItems.list e videos.list custam 1 unidade por chamada. "
    "Resposta vinda do cache local não debita cota."
)


class QuotaExceeded(Exception):
    def __init__(self, method: str, cost: int, remaining: int, limit: int = DAILY_LIMIT):
        self.method = method
        self.cost = cost
        self.remaining = remaining
        self.limit = limit
        super().__init__(
            f"Cota insuficiente para {method}: custa {cost} unidades e restam {remaining} "
            f"de {limit} na cota diária gratuita."
        )


class QuotaLedger:
    def __init__(
        self,
        path: str | Path,
        now: Callable[[], float] | None = None,
        limit: int = DAILY_LIMIT,
    ):
        self.path = Path(path)
        self.now = now or time.time
        self.limit = limit
        self.session_used = 0
        self.session_avoided = 0
        self.session_events: list[dict[str, Any]] = []
        self.used = 0
        self.events: list[dict[str, Any]] = []
        self.date = self._today()
        self._load()

    def _today(self) -> str:
        return datetime.fromtimestamp(self.now(), timezone.utc).date().isoformat()

    def _load(self) -> None:
        self.date = self._today()
        self.used = 0
        self.events = []
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if data.get("date") == self.date:
            self.used = int(data.get("used", 0))
            self.events = list(data.get("events", []))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "date": self.date,
                    "used": self.used,
                    "limit": self.limit,
                    "events": self.events[-200:],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def remaining(self) -> int:
        return max(0, self.limit - self.used)

    def cost(self, method: str) -> int:
        if method not in COSTS:
            raise KeyError(method)
        return COSTS[method]

    def can(self, method: str, calls: int = 1) -> bool:
        return self.remaining() >= self.cost(method) * calls

    def charge(self, method: str) -> int:
        cost = self.cost(method)
        if self.used + cost > self.limit:
            raise QuotaExceeded(method, cost, self.remaining(), self.limit)
        self.used += cost
        self.session_used += cost
        event = {"method": method, "units": cost, "cached": False, "ts": int(self.now())}
        self.events.append(event)
        self.session_events.append(event)
        self.save()
        return cost

    def cache_hit(self, method: str) -> int:
        avoided = self.cost(method)
        self.session_avoided += avoided
        self.session_events.append(
            {
                "method": method,
                "units": 0,
                "evitadas": avoided,
                "cached": True,
                "ts": int(self.now()),
            }
        )
        return avoided

    def resumo(self) -> dict[str, Any]:
        avisos: list[str] = []
        if self.used >= int(self.limit * 0.8):
            avisos.append(
                f"Cota diária gratuita em {self.used} de {self.limit} unidades (80% ou mais)."
            )
        if self.remaining() < COSTS["search.list"]:
            avisos.append(
                "Restam menos de 100 unidades: não há cota para outro search.list hoje."
            )
        return {
            "data_utc": self.date,
            "limite_diario": self.limit,
            "usadas_no_dia": self.used,
            "restante": self.remaining(),
            "gastas_nesta_execucao": self.session_used,
            "evitadas_por_cache": self.session_avoided,
            "custos": dict(COSTS),
            "regra": REGRA,
            "avisos": avisos,
            "eventos_nesta_execucao": list(self.session_events),
        }
