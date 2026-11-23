"""Transporte HTTP injetável. A implementação padrão usa só a biblioteca padrão."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Protocol

_SECRET_PARAMS = {"key", "api_key"}


class HttpError(Exception):
    def __init__(self, status: int | None, message: str):
        super().__init__(message)
        self.status = status


class Transport(Protocol):
    def get_json(self, url: str, params: dict[str, Any] | None = None) -> Any: ...

    def post_json(
        self, url: str, payload: dict[str, Any], params: dict[str, Any] | None = None
    ) -> Any: ...

    def get_bytes(self, url: str) -> bytes: ...


def redact_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    clean = [(k, "***" if k.lower() in _SECRET_PARAMS else v) for k, v in query]
    return urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode(clean), parts.fragment)
    )


def redact_text(text: str, secrets: list[str]) -> str:
    out = text
    for secret in secrets:
        if secret:
            out = out.replace(secret, "***")
    return out


def _loads(raw: bytes) -> Any:
    last: Exception | None = None
    for encoding in ("utf-8", "latin-1"):
        try:
            return json.loads(raw.decode(encoding))
        except UnicodeDecodeError as exc:
            last = exc
        except json.JSONDecodeError as exc:
            last = exc
            break
    raise HttpError(None, f"resposta não é JSON ({last})")


class UrllibTransport:
    """GET/POST JSON com timeout. A chave na querystring nunca volta na mensagem de erro."""

    def __init__(self, timeout: float = 20.0, retries: int = 2):
        self.timeout = timeout
        self.retries = retries

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        return _loads(self._request("GET", url, params=params))

    def post_json(
        self, url: str, payload: dict[str, Any], params: dict[str, Any] | None = None
    ) -> Any:
        data = json.dumps(payload).encode("utf-8")
        raw = self._request(
            "POST",
            url,
            params=params,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        return _loads(raw)

    def get_bytes(self, url: str) -> bytes:
        return self._request("GET", url)

    def _request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        if params:
            encoded = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = url + ("&" if "?" in url else "?") + encoded
        safe = redact_url(url)
        last: HttpError | None = None
        for attempt in range(self.retries + 1):
            request = urllib.request.Request(url, data=data, method=method, headers=headers or {})
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return response.read()
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")[:300]
                last = HttpError(exc.code, f"HTTP {exc.code} em {safe}: {body}")
                if exc.code in {429, 500, 502, 503} and attempt < self.retries:
                    continue
                raise last from None
            except urllib.error.URLError as exc:
                last = HttpError(None, f"falha de rede em {safe}: {exc.reason}")
                if attempt < self.retries:
                    continue
                raise last from None
        raise last or HttpError(None, f"falha de rede em {safe}")
