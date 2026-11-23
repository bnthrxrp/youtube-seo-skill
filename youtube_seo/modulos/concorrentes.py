"""Competitor Intelligence.

Padrão econômico de estudo-10k/scripts/03_api.py: channels.list + playlistItems.list
+ videos.list, 1 unidade por chamada. Playlist de longos UULF; se não existir,
a playlist de uploads UU com filtro de duração. Sem search.list.
"""

from __future__ import annotations

import statistics
from typing import Any, Callable

from youtube_seo.cliente import YouTubeClient, YouTubeError
from youtube_seo.modelos import aceita_longo, aplicar_detalhe, porte_de
from youtube_seo.quota import QuotaExceeded
from youtube_seo.texto import temas


def _canal_resumo(canal: dict) -> dict[str, Any]:
    stats = canal.get("statistics") or {}
    oculto = bool(stats.get("hiddenSubscriberCount"))
    inscritos = None if oculto or "subscriberCount" not in stats else int(stats["subscriberCount"])
    return {
        "canal_id": canal.get("id"),
        "canal_nome": (canal.get("snippet") or {}).get("title"),
        "inscritos": inscritos,
        "porte": porte_de(inscritos, oculto),
        "videos_no_canal": int(stats["videoCount"]) if str(stats.get("videoCount") or "").isdigit() else None,
    }


def _frequencia(videos: list[dict]) -> dict[str, Any]:
    marcas = sorted(v["publicado_ts"] for v in videos if v.get("publicado_ts"))
    if len(marcas) < 2:
        return {
            "videos_coletados": len(marcas),
            "janela_dias": None,
            "por_semana": None,
            "intervalo_mediano_dias": None,
        }
    intervalos = [(b - a) / 86400 for a, b in zip(marcas, marcas[1:])]
    janela = (marcas[-1] - marcas[0]) / 86400
    por_semana = (len(marcas) - 1) / (janela / 7) if janela > 0 else None
    return {
        "videos_coletados": len(marcas),
        "janela_dias": round(janela, 1),
        "por_semana": round(por_semana, 2) if por_semana is not None else None,
        "intervalo_mediano_dias": round(statistics.median(intervalos), 1),
    }


def _desempenho(videos: list[dict]) -> dict[str, Any]:
    nota = (
        "Cada vídeo é comparado à mediana de views dos vídeos longos coletados deste canal "
        "com 30 dias ou mais. O estudo-10k usou os 10 vizinhos temporais; aqui a janela é "
        "a lista coletada. Acima = 1,5× a mediana ou mais; abaixo = 2/3 ou menos."
    )
    maduros = [v for v in videos if (v.get("idade_dias") or 0) >= 30 and (v.get("views") or 0) > 0]
    fragil = len(maduros) < 5
    base = maduros if not fragil else [v for v in videos if (v.get("views") or 0) > 0]
    if fragil:
        nota += " Menos de 5 vídeos com 30+ dias: a comparação usa o que houver e fica marcada como frágil."
    if not base:
        return {"mediana_views": None, "fragil": True, "nota": nota, "videos": []}
    mediana_views = statistics.median([v["views"] for v in base])
    ids_base = {v.get("video_id") for v in base}
    linhas = []
    for video in videos:
        linha = {
            "video_id": video.get("video_id"),
            "titulo": video.get("titulo"),
            "views": video.get("views"),
            "idade_dias": video.get("idade_dias"),
            "duracao_segundos": video.get("duracao_segundos"),
            "legendas": video.get("legendas"),
            "vs_mediana": None,
            "faixa": None,
        }
        if video.get("video_id") in ids_base and mediana_views:
            razao = video["views"] / mediana_views
            linha["vs_mediana"] = round(razao, 2)
            if razao >= 1.5:
                linha["faixa"] = "acima"
            elif razao <= 2 / 3:
                linha["faixa"] = "abaixo"
            else:
                linha["faixa"] = "perto_da_mediana"
        elif (video.get("idade_dias") or 0) < 30 and not fragil:
            linha["faixa"] = "recente_fora_da_comparacao"
        linhas.append(linha)
    return {
        "mediana_views": mediana_views,
        "fragil": fragil,
        "n_base": len(base),
        "nota": nota,
        "videos": linhas,
    }


def _um_canal(canal: dict | None, cid: str, client: YouTubeClient, now: float, max_videos: int) -> dict[str, Any]:
    if not canal:
        return {"canal_id": cid, "ok": False, "motivo": "Canal não encontrado."}
    resumo = _canal_resumo(canal)
    fonte = "UULF"
    playlist_id = "UULF" + cid[2:] if cid.startswith("UC") and len(cid) > 2 else None
    itens = client.playlist_items(playlist_id, max_items=max_videos) if playlist_id else None
    if not itens:
        fonte = "UU"
        uploads = ((canal.get("contentDetails") or {}).get("relatedPlaylists") or {}).get("uploads")
        itens = client.playlist_items(uploads, max_items=max_videos) if uploads else []
    ids = []
    for item in itens or []:
        video_id = (item.get("contentDetails") or {}).get("videoId")
        if video_id:
            ids.append(video_id)
    detalhes = client.videos(ids) if ids else []
    videos = []
    for detalhe in detalhes:
        video = aplicar_detalhe(
            {
                "video_id": detalhe.get("id"),
                "titulo": "",
                "descricao": "",
                "canal_id": cid,
                "canal_nome": resumo["canal_nome"],
            },
            detalhe,
            now,
        )
        if aceita_longo(video, origem_uulf=fonte == "UULF"):
            videos.append(video)
    videos.sort(key=lambda v: v.get("publicado_ts") or 0)
    duracoes = [v["duracao_segundos"] for v in videos if isinstance(v.get("duracao_segundos"), int)]
    return {
        **resumo,
        "ok": True,
        "fonte_lista": fonte,
        "n_videos": len(videos),
        "frequencia": _frequencia(videos),
        "temas": temas([v.get("titulo") or "" for v in videos]),
        "duracao_mediana_segundos": statistics.median(duracoes) if duracoes else None,
        "pct_legendas": round(100 * sum(1 for v in videos if v.get("legendas") is True) / len(videos), 1) if videos else None,
        "pct_capitulos": round(100 * sum(1 for v in videos if v.get("capitulos")) / len(videos), 1) if videos else None,
        "desempenho": _desempenho(videos),
        "nota_cota": "channels.list + playlistItems.list + videos.list custam 1 unidade por chamada. search.list não entra aqui.",
    }


def monitorar_concorrentes(
    canais: list[str],
    *,
    client: YouTubeClient,
    now: Callable[[], float],
    max_videos: int = 50,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "modulo": "competitors",
        "ok": True,
        "max_videos": max_videos,
        "canais": [],
        "avisos": [],
        "cota_estimada_sem_cache": {
            "search.list": 0,
            "nota": (
                "Sem search.list. Por canal, no cache frio: 1 playlistItems.list por página "
                "e 1 videos.list por lote de 50, mais 1 channels.list por lote de 50 canais."
            ),
        },
    }
    if not client.enabled:
        payload["ok"] = False
        payload["avisos"].append(str(client._sem_chave()))
        payload["cota"] = client.quota.resumo()
        return payload
    ids = list(dict.fromkeys(c.strip() for c in canais if c and c.strip()))
    try:
        brutos = client.channels(ids) if ids else []
    except QuotaExceeded as exc:
        payload["ok"] = False
        payload["avisos"].append(str(exc))
        payload["cota"] = client.quota.resumo()
        return payload
    except YouTubeError as exc:
        payload["ok"] = False
        payload["avisos"].append(str(exc))
        payload["cota"] = client.quota.resumo()
        return payload
    por_id = {c.get("id"): c for c in brutos}
    for cid in ids:
        try:
            payload["canais"].append(_um_canal(por_id.get(cid), cid, client, now(), max_videos))
        except QuotaExceeded as exc:
            payload["avisos"].append(str(exc))
            payload["canais"].append({"canal_id": cid, "ok": False, "motivo": str(exc)})
        except YouTubeError as exc:
            payload["ok"] = False
            payload["avisos"].append(str(exc))
            payload["canais"].append({"canal_id": cid, "ok": False, "motivo": str(exc)})
    if payload["canais"] and not any(c.get("ok") for c in payload["canais"]):
        payload["ok"] = False
    payload["cota"] = client.quota.resumo()
    return payload
