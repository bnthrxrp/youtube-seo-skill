"""Junta search.list, videos.list e channels.list num vídeo normalizado."""

from __future__ import annotations

from typing import Any

from youtube_seo.cliente import YouTubeClient, YouTubeError
from youtube_seo.modelos import aplicar_canal, aplicar_detalhe, video_de_busca
from youtube_seo.quota import QuotaExceeded


def enriquecer(
    itens_busca: list[dict],
    client: YouTubeClient,
    now: float,
) -> tuple[list[dict], list[str]]:
    videos = [video_de_busca(item, i, now) for i, item in enumerate(itens_busca, start=1)]
    avisos: list[str] = []
    ids = [v["video_id"] for v in videos if v.get("video_id")]
    detalhes: list[dict] = []
    if ids:
        try:
            detalhes = client.videos(ids)
        except (QuotaExceeded, YouTubeError) as exc:
            avisos.append(f"videos.list não rodou: {exc}")
    por_id = {d.get("id"): d for d in detalhes}
    for video in videos:
        detalhe = por_id.get(video.get("video_id"))
        if detalhe:
            aplicar_detalhe(video, detalhe, now)
    canais_ids = list(dict.fromkeys(v["canal_id"] for v in videos if v.get("canal_id")))
    canais: list[dict] = []
    if canais_ids:
        try:
            canais = client.channels(canais_ids)
        except (QuotaExceeded, YouTubeError) as exc:
            avisos.append(f"channels.list não rodou: {exc}")
    por_canal = {c.get("id"): c for c in canais}
    for video in videos:
        aplicar_canal(video, por_canal.get(video.get("canal_id")))
    return videos, avisos


def agregar_canais(videos: list[dict]) -> list[dict[str, Any]]:
    grupos: dict[str, dict[str, Any]] = {}
    for video in videos:
        cid = video.get("canal_id")
        if not cid:
            continue
        grupo = grupos.setdefault(
            cid,
            {
                "canal_id": cid,
                "canal_nome": video.get("canal_nome"),
                "inscritos": video.get("inscritos"),
                "porte": video.get("porte"),
                "videos": 0,
                "melhor_posicao": video.get("posicao"),
            },
        )
        grupo["videos"] += 1
        posicao = video.get("posicao")
        if posicao is not None and (grupo["melhor_posicao"] is None or posicao < grupo["melhor_posicao"]):
            grupo["melhor_posicao"] = posicao
        if video.get("canal_nome"):
            grupo["canal_nome"] = video["canal_nome"]
        if video.get("inscritos") is not None:
            grupo["inscritos"] = video["inscritos"]
            grupo["porte"] = video.get("porte")
    return sorted(grupos.values(), key=lambda g: (g["melhor_posicao"] if g["melhor_posicao"] is not None else 999, -g["videos"]))


def agregar_tags(videos: list[dict], top: int = 20) -> list[dict[str, Any]]:
    from collections import Counter

    contagem: Counter[str] = Counter()
    for video in videos:
        vistos = set()
        for tag in video.get("tags") or []:
            chave = str(tag).strip().lower()
            if chave and chave not in vistos:
                vistos.add(chave)
                contagem[chave] += 1
    return [{"tag": tag, "videos": n} for tag, n in contagem.most_common(top)]
