"""Normalização dos objetos da Data API e cortes de porte do estudo."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

_ISO = re.compile(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
_SHORT = re.compile(r"#shorts?\b", re.IGNORECASE)


def iso_duracao(valor: str | None) -> int | None:
    if not valor or not str(valor).startswith("P"):
        return None
    match = _ISO.match(valor)
    if not match:
        return None
    return sum(int(x or 0) * k for x, k in zip(match.groups(), (86400, 3600, 60, 1)))


def parse_publicado(valor: str | None) -> float | None:
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None


def porte_de(inscritos: int | None, oculto: bool = False) -> str:
    """Cortes de estudo-10k/scripts/02_selecao.py. Abaixo de 200 mil é 'pequeno' (fora da amostra)."""
    if oculto:
        return "oculto"
    if inscritos is None:
        return "desconhecido"
    if inscritos >= 20_000_000:
        return "gigante"
    if inscritos >= 2_000_000:
        return "grande"
    if inscritos >= 200_000:
        return "medio"
    return "pequeno"


def _int_stat(stats: dict, campo: str) -> int | None:
    if campo not in stats or stats[campo] in (None, ""):
        return None
    try:
        return int(stats[campo])
    except (TypeError, ValueError):
        return None


def video_de_busca(item: dict, posicao: int, now: float) -> dict[str, Any]:
    snippet = item.get("snippet") or {}
    bruto_id = item.get("id")
    if isinstance(bruto_id, dict):
        video_id = bruto_id.get("videoId")
    else:
        video_id = bruto_id
    publicado = parse_publicado(snippet.get("publishedAt"))
    thumbs = snippet.get("thumbnails") or {}
    thumb = (thumbs.get("medium") or thumbs.get("high") or thumbs.get("default") or {}).get("url")
    ao_vivo = snippet.get("liveBroadcastContent", "none") not in (None, "none")
    return {
        "posicao": posicao,
        "video_id": video_id,
        "titulo": snippet.get("title") or "",
        "descricao": snippet.get("description") or "",
        "tags": [],
        "canal_id": snippet.get("channelId"),
        "canal_nome": snippet.get("channelTitle"),
        "publicado_em": snippet.get("publishedAt"),
        "publicado_ts": publicado,
        "idade_dias": round((now - publicado) / 86400, 1) if publicado else None,
        "duracao_segundos": None,
        "legendas": None,
        "capitulos": False,
        "views": None,
        "likes": None,
        "comentarios": None,
        "thumbnail_url": thumb,
        "ao_vivo": ao_vivo,
        "inscritos": None,
        "porte": "desconhecido",
    }


def aplicar_detalhe(video: dict, detalhe: dict, now: float) -> dict:
    snippet = detalhe.get("snippet") or {}
    content = detalhe.get("contentDetails") or {}
    stats = detalhe.get("statistics") or {}
    publicado = parse_publicado(snippet.get("publishedAt")) or video.get("publicado_ts")
    ao_vivo = snippet.get("liveBroadcastContent", "none") not in (None, "none") or (
        "actualStartTime" in (detalhe.get("liveStreamingDetails") or {})
        and not (detalhe.get("liveStreamingDetails") or {}).get("actualEndTime")
    )
    video.update(
        {
            "titulo": snippet.get("title") or video.get("titulo") or "",
            "descricao": snippet.get("description") if snippet.get("description") is not None else video.get("descricao") or "",
            "tags": list(snippet.get("tags") or []),
            "canal_id": snippet.get("channelId") or video.get("canal_id"),
            "canal_nome": snippet.get("channelTitle") or video.get("canal_nome"),
            "publicado_em": snippet.get("publishedAt") or video.get("publicado_em"),
            "publicado_ts": publicado,
            "idade_dias": round((now - publicado) / 86400, 1) if publicado else video.get("idade_dias"),
            "duracao_segundos": iso_duracao(content.get("duration")),
            "legendas": content.get("caption") == "true",
            "capitulos": False,
            "views": _int_stat(stats, "viewCount"),
            "likes": _int_stat(stats, "likeCount"),
            "comentarios": _int_stat(stats, "commentCount"),
            "ao_vivo": bool(video.get("ao_vivo") or ao_vivo),
        }
    )
    from youtube_seo.texto import tem_capitulos

    video["capitulos"] = tem_capitulos(video.get("descricao") or "")
    thumbs = snippet.get("thumbnails") or {}
    thumb = (thumbs.get("medium") or thumbs.get("high") or thumbs.get("default") or {}).get("url")
    if thumb:
        video["thumbnail_url"] = thumb
    return video


def aplicar_canal(video: dict, canal: dict | None) -> dict:
    if not canal:
        return video
    stats = canal.get("statistics") or {}
    oculto = bool(stats.get("hiddenSubscriberCount"))
    inscritos = None if oculto else _int_stat(stats, "subscriberCount")
    video["inscritos"] = inscritos
    video["porte"] = porte_de(inscritos, oculto)
    nome = (canal.get("snippet") or {}).get("title")
    if nome:
        video["canal_nome"] = nome
    return video


def eh_short_ou_live(video: dict) -> bool:
    if video.get("ao_vivo"):
        return True
    titulo = video.get("titulo") or ""
    descricao = (video.get("descricao") or "")[:500]
    return bool(_SHORT.search(titulo) or _SHORT.search(descricao))


def aceita_longo(video: dict, origem_uulf: bool) -> bool:
    if eh_short_ou_live(video):
        return False
    duracao = video.get("duracao_segundos")
    if duracao is None:
        return origem_uulf
    if origem_uulf:
        return duracao > 60
    return duracao > 180
