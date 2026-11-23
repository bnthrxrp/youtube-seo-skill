"""Keyword Research: autocomplete público e, se houver chave, vídeos, tags e canais."""

from __future__ import annotations

import statistics
from typing import Any, Callable

from youtube_seo.cache import FileCache
from youtube_seo.cliente import YouTubeClient, YouTubeError
from youtube_seo.coleta import agregar_canais, agregar_tags, enriquecer
from youtube_seo.http import Transport
from youtube_seo.quota import QuotaExceeded, QuotaLedger
from youtube_seo.suggest import coletar
from youtube_seo.texto import intencao


def _mediana_int(valores: list[int]) -> float | None:
    if not valores:
        return None
    return statistics.median(valores)


def pesquisar_palavras(
    termo: str,
    *,
    hl: str | None,
    gl: str | None,
    client: YouTubeClient,
    transport: Transport,
    cache: FileCache,
    quota: QuotaLedger,
    now: Callable[[], float],
    letras: str = "aeiou",
    usar_prefixos: bool = True,
    max_results: int = 25,
    pages: int = 1,
) -> dict[str, Any]:
    instante = now()
    coletado = coletar(
        termo,
        hl=hl,
        gl=gl,
        transport=transport,
        cache=cache,
        letras=letras,
        usar_prefixos=usar_prefixos,
    )
    sugestoes = []
    for item in coletado["sugestoes"]:
        sugestoes.append({**item, "intencao": intencao(item["termo"]), "intencao_nota": "inferência, não volume"})
    payload: dict[str, Any] = {
        "modulo": "keywords",
        "ok": True,
        "consulta": {"termo": termo, "hl": hl, "gl": gl},
        "sugestoes": sugestoes,
        "expansoes": coletado["expansoes"],
        "videos": [],
        "canais": [],
        "tags": [],
        "metricas": {},
        "api": {"usada": False, "bloqueada_por_cota": False, "motivo": None},
        "avisos": list(coletado["erros"]),
        "nota_volume": (
            "Volume de busca não medido. O YouTube não publica esse número. "
            "A evidência aqui é aparição no autocomplete ou numa expansão."
        ),
    }
    if not client.enabled:
        payload["api"]["motivo"] = (
            "YOUTUBE_API_KEY ausente. Sugestões públicas coletadas. "
            "Vídeos, tags, canais e métricas exigem a Data API, na cota gratuita."
        )
        payload["avisos"].append(payload["api"]["motivo"])
        payload["cota"] = quota.resumo()
        payload["cota_estimada_sem_cache"] = {"search.list": pages * 100, "nota": "não gasto, chave ausente"}
        return payload

    payload["cota_estimada_sem_cache"] = {
        "search.list": pages * 100,
        "nota": "Estimativa se o cache não tiver esta consulta. videos.list e channels.list somam 1 unidade por lote de até 50.",
    }
    try:
        bruto = client.search_videos(termo, region=gl, language=hl, max_results=max_results, pages=pages)
    except QuotaExceeded as exc:
        payload["api"].update({"bloqueada_por_cota": True, "motivo": str(exc)})
        payload["avisos"].append(str(exc))
        payload["cota"] = quota.resumo()
        return payload
    except YouTubeError as exc:
        payload["ok"] = False
        payload["api"]["motivo"] = str(exc)
        payload["avisos"].append(str(exc))
        payload["cota"] = quota.resumo()
        return payload

    videos, avisos = enriquecer(bruto, client, instante)
    payload["avisos"].extend(avisos)
    payload["avisos"].extend(client.avisos)
    views = [v["views"] for v in videos if isinstance(v.get("views"), int)]
    duracoes = [v["duracao_segundos"] for v in videos if isinstance(v.get("duracao_segundos"), int)]
    payload.update(
        {
            "videos": videos,
            "canais": agregar_canais(videos),
            "tags": agregar_tags(videos),
            "metricas": {
                "n_videos": len(videos),
                "n_canais": len({v["canal_id"] for v in videos if v.get("canal_id")}),
                "mediana_views": _mediana_int(views),
                "mediana_duracao_segundos": _mediana_int(duracoes),
                "pct_legendas": round(100 * sum(1 for v in videos if v.get("legendas") is True) / len(videos), 1) if videos else None,
            },
            "api": {"usada": True, "bloqueada_por_cota": False, "motivo": None},
        }
    )
    payload["cota"] = quota.resumo()
    return payload
