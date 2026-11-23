"""Cliente da YouTube Data API v3 com cache e cota. A chave não é gravada nem impressa."""

from __future__ import annotations

import json
from typing import Any

from youtube_seo.cache import FileCache
from youtube_seo.http import HttpError, Transport, redact_text
from youtube_seo.quota import QuotaExceeded, QuotaLedger

API = "https://www.googleapis.com/youtube/v3/"

TTL = {
    "search": 24 * 3600,
    "videos": 6 * 3600,
    "channels": 6 * 3600,
    "playlistItems": 6 * 3600,
}


class YouTubeError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def _lotes(itens: list[str], tamanho: int) -> list[list[str]]:
    return [itens[i : i + tamanho] for i in range(0, len(itens), tamanho)]


class YouTubeClient:
    def __init__(self, api_key: str, transport: Transport, cache: FileCache, quota: QuotaLedger):
        self.api_key = api_key or ""
        self.transport = transport
        self.cache = cache
        self.quota = quota
        self.avisos: list[str] = []

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _sem_chave(self) -> YouTubeError:
        return YouTubeError(
            "YOUTUBE_API_KEY não definida. Sem a chave, a Data API não é consultada. "
            "O autocomplete público continua disponível e não gasta cota."
        )

    def _call(self, endpoint: str, method: str, params: dict[str, Any]) -> dict:
        if not self.api_key:
            raise self._sem_chave()
        clean = {k: v for k, v in params.items() if v is not None}
        key = self.cache.make_key(endpoint, clean)
        hit = self.cache.get(key)
        if hit is not None:
            self.quota.cache_hit(method)
            return hit
        if not self.quota.can(method):
            raise QuotaExceeded(method, self.quota.cost(method), self.quota.remaining(), self.quota.limit)
        try:
            data = self.transport.get_json(API + endpoint, {**clean, "key": self.api_key})
        except HttpError as exc:
            raise YouTubeError(redact_text(str(exc), [self.api_key]), status=exc.status) from None
        if isinstance(data, dict) and data.get("error"):
            message = json.dumps(data["error"], ensure_ascii=False)[:300]
            status = (data["error"] or {}).get("code")
            raise YouTubeError(redact_text(message, [self.api_key]), status=status)
        self.quota.charge(method)
        self.cache.put(key, data, TTL[endpoint], meta={"endpoint": endpoint})
        return data

    def search_videos(
        self,
        q: str,
        *,
        region: str | None = None,
        language: str | None = None,
        max_results: int = 25,
        pages: int = 1,
    ) -> list[dict]:
        items: list[dict] = []
        token = None
        page_size = min(50, max(1, max_results))
        for index in range(max(1, pages)):
            params: dict[str, Any] = {
                "part": "snippet",
                "type": "video",
                "q": q,
                "maxResults": page_size,
                "regionCode": (region or None),
                "relevanceLanguage": (language or None),
                "pageToken": token,
            }
            try:
                data = self._call("search", "search.list", params)
            except QuotaExceeded as exc:
                if items:
                    self.avisos.append(str(exc) + " A página extra não foi pedida.")
                    break
                raise
            items.extend(data.get("items") or [])
            token = data.get("nextPageToken")
            if not token or len(items) >= max_results or index + 1 >= pages:
                break
        return items[:max_results]

    def videos(self, ids: list[str]) -> list[dict]:
        saida: list[dict] = []
        unicos = list(dict.fromkeys(i for i in ids if i))
        for lote in _lotes(unicos, 50):
            data = self._call(
                "videos",
                "videos.list",
                {
                    "part": "snippet,contentDetails,statistics,liveStreamingDetails",
                    "id": ",".join(lote),
                    "maxResults": 50,
                },
            )
            saida.extend(data.get("items") or [])
        return saida

    def channels(self, ids: list[str]) -> list[dict]:
        saida: list[dict] = []
        unicos = list(dict.fromkeys(i for i in ids if i))
        for lote in _lotes(unicos, 50):
            data = self._call(
                "channels",
                "channels.list",
                {
                    "part": "snippet,statistics,contentDetails",
                    "id": ",".join(lote),
                    "maxResults": 50,
                },
            )
            saida.extend(data.get("items") or [])
        return saida

    def playlist_items(self, playlist_id: str, max_items: int = 50) -> list[dict] | None:
        saida: list[dict] = []
        token = None
        while len(saida) < max_items:
            params: dict[str, Any] = {
                "part": "contentDetails",
                "playlistId": playlist_id,
                "maxResults": min(50, max_items - len(saida)),
                "pageToken": token,
            }
            try:
                data = self._call("playlistItems", "playlistItems.list", params)
            except YouTubeError as exc:
                if exc.status == 404 and not saida:
                    return None
                raise
            saida.extend(data.get("items") or [])
            token = data.get("nextPageToken")
            if not token:
                break
        return saida
