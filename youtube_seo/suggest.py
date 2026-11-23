"""Autocomplete público do YouTube. Não usa a Data API e não gasta cota."""

from __future__ import annotations

from typing import Any

from youtube_seo.cache import FileCache
from youtube_seo.http import HttpError, Transport
from youtube_seo.texto import prefixos_de_idioma

SUGGEST_URL = "https://suggestqueries.google.com/complete/search"
TTL_SUGGEST = 12 * 3600


def parse_suggest(payload: Any) -> list[str]:
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        return []
    saida: list[str] = []
    for item in payload[1]:
        if isinstance(item, str) and item.strip():
            saida.append(item.strip())
        elif isinstance(item, list) and item and isinstance(item[0], str) and item[0].strip():
            saida.append(item[0].strip())
    return saida


def buscar_sugestoes(
    termo: str,
    *,
    hl: str | None,
    gl: str | None,
    transport: Transport,
    cache: FileCache,
) -> tuple[list[str], str | None]:
    params = {
        "client": "firefox",
        "ds": "yt",
        "q": termo,
        "hl": hl or "",
        "gl": (gl or "").upper(),
    }
    key = cache.make_key("suggest", params)
    payload = cache.get(key)
    if payload is None:
        try:
            payload = transport.get_json(SUGGEST_URL, params)
        except HttpError as exc:
            return [], str(exc)
        cache.put(key, payload, TTL_SUGGEST, meta={"endpoint": "suggest"})
    return parse_suggest(payload), None


def _fonte(consulta: str, semente: str) -> str:
    if consulta == semente:
        return "autocomplete"
    resto = consulta[len(semente) :].strip() if consulta.startswith(semente + " ") else ""
    if len(resto) == 1 and resto.isalpha():
        return "letra"
    return "prefixo"


def coletar(
    termo: str,
    *,
    hl: str | None,
    gl: str | None,
    transport: Transport,
    cache: FileCache,
    letras: str = "aeiou",
    usar_prefixos: bool = True,
) -> dict[str, Any]:
    consultas = [termo]
    if usar_prefixos:
        for prefixo in prefixos_de_idioma(hl):
            if not termo.casefold().startswith(prefixo.casefold()):
                consultas.append(f"{prefixo} {termo}".strip())
    for letra in letras:
        if letra.isalpha():
            consultas.append(f"{termo} {letra.casefold()}")

    vistos: dict[str, dict[str, Any]] = {}
    expansoes: list[dict[str, Any]] = []
    erros: list[str] = []
    for consulta in consultas:
        sugestoes, erro = buscar_sugestoes(consulta, hl=hl, gl=gl, transport=transport, cache=cache)
        if erro:
            erros.append(f"{consulta}: {erro}")
        expansoes.append({"consulta": consulta, "sugestoes": sugestoes, "erro": erro})
        fonte = _fonte(consulta, termo)
        for posicao, sugestao in enumerate(sugestoes, start=1):
            chave = sugestao.casefold()
            if chave in vistos:
                continue
            vistos[chave] = {
                "termo": sugestao,
                "fonte": fonte,
                "consulta_origem": consulta,
                "posicao": posicao,
            }
    return {"sugestoes": list(vistos.values()), "expansoes": expansoes, "erros": erros}
