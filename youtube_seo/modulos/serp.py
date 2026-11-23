"""SERP Analyzer: padrões dos vídeos devolvidos por search.list, com cache e cota explícitos."""

from __future__ import annotations

from typing import Any, Callable

from youtube_seo.cliente import YouTubeClient, YouTubeError
from youtube_seo.coleta import enriquecer
from youtube_seo.findings import NOTA_GERAL, achar
from youtube_seo.padroes import padroes_serp
from youtube_seo.quota import QuotaExceeded


def _notas(padrao: dict) -> list[dict[str, str]]:
    duracao = achar("duracao")
    legenda = achar("legenda_canal")
    tamanho = achar("tamanho_titulo")
    caps = achar("palavra_caps")
    return [
        {
            "traco": duracao["traco"],
            "forca": duracao["forca"],
            "rotulo": duracao["rotulo"],
            "observado": f"mediana {padrao['duracao']['mediana_segundos']} s; faixas {padrao['duracao']['faixas']}",
            "estudo": f"{duracao['efeito']} ({duracao['margem']}). {duracao['leitura']}",
        },
        {
            "traco": legenda["traco"],
            "forca": legenda["forca"],
            "rotulo": legenda["rotulo"],
            "observado": f"{padrao['pct_legendas']}% dos vídeos com contentDetails.caption=true",
            "estudo": f"{legenda['efeito']} ({legenda['margem']}). {legenda['leitura']}",
        },
        {
            "traco": tamanho["traco"],
            "forca": tamanho["forca"],
            "rotulo": tamanho["rotulo"],
            "observado": f"mediana de {padrao['titulos']['mediana_caracteres']} caracteres",
            "estudo": f"{tamanho['efeito']} ({tamanho['margem']}). {tamanho['leitura']}",
        },
        {
            "traco": caps["traco"],
            "forca": caps["forca"],
            "rotulo": caps["rotulo"],
            "observado": f"{padrao['titulos']['pct_palavra_caps']}% dos títulos têm uma palavra em caixa alta",
            "estudo": f"{caps['efeito']} ({caps['margem']}). {caps['leitura']}",
        },
    ]


def analisar_serp(
    termos: list[str],
    *,
    hl: str | None,
    gl: str | None,
    client: YouTubeClient,
    now: Callable[[], float],
    max_results: int = 25,
    pages: int = 1,
) -> dict[str, Any]:
    estimativa = len(termos) * max(1, pages) * 100
    payload: dict[str, Any] = {
        "modulo": "serp",
        "ok": True,
        "consulta": {"termos": termos, "hl": hl, "gl": gl, "max_resultados": max_results, "paginas": pages},
        "cota_estimada_sem_cache": {
            "search.list": estimativa,
            "nota": (
                "Cada termo, em cada página, custa 100 unidades se não estiver no cache. "
                "videos.list e channels.list custam 1 por lote de até 50 ids."
            ),
        },
        "termos": [],
        "pulados": [],
        "avisos": [],
        "nota_ranking": (
            "A ordem é a que search.list devolve para a chave, a região e o idioma pedidos. "
            "Não é um ranking auditável de aba anônima: a busca do YouTube é personalizada."
        ),
        "estudo": NOTA_GERAL,
    }
    if not client.enabled:
        payload["ok"] = False
        payload["avisos"].append(str(client._sem_chave()))
        payload["cota"] = client.quota.resumo()
        return payload

    for termo in termos:
        try:
            bruto = client.search_videos(
                termo, region=gl, language=hl, max_results=max_results, pages=pages
            )
        except QuotaExceeded as exc:
            payload["pulados"].append({"termo": termo, "motivo": str(exc)})
            payload["avisos"].append(str(exc))
            continue
        except YouTubeError as exc:
            payload["ok"] = False
            payload["termos"].append({"termo": termo, "ok": False, "motivo": str(exc), "videos": [], "padroes": None})
            payload["avisos"].append(str(exc))
            continue
        videos, avisos = enriquecer(bruto, client, now())
        padrao = padroes_serp(videos, termo)
        payload["termos"].append(
            {
                "termo": termo,
                "ok": True,
                "videos": videos,
                "padroes": padrao,
                "leitura_estudo": _notas(padrao),
                "avisos": avisos,
            }
        )
        payload["avisos"].extend(avisos)
    payload["avisos"].extend(client.avisos)
    if not payload["termos"] and payload["pulados"]:
        payload["ok"] = False
    payload["cota"] = client.quota.resumo()
    return payload
