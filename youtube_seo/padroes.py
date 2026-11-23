"""Padrões agregados da SERP e a régua de concorrência usada nas lacunas."""

from __future__ import annotations

import statistics
from collections import Counter
from typing import Any

from youtube_seo.texto import extrair_titulo, termo_no_inicio, termo_no_titulo


def pct(parte: int, total: int) -> float | None:
    if not total:
        return None
    return round(100 * parte / total, 1)


def mediana(valores: list[float]) -> float | None:
    if not valores:
        return None
    return statistics.median(valores)


def quantil(valores: list[float], q: float) -> float | None:
    if not valores:
        return None
    ordenados = sorted(valores)
    if len(ordenados) == 1:
        return ordenados[0]
    pos = q * (len(ordenados) - 1)
    baixo = int(pos)
    alto = min(len(ordenados) - 1, int(pos) if pos == int(pos) else int(pos) + 1)
    if baixo == alto:
        return ordenados[baixo]
    frac = pos - baixo
    return ordenados[baixo] * (1 - frac) + ordenados[alto] * frac


def _arredondar(valor: float | None, casas: int) -> float | None:
    if valor is None:
        return None
    return round(float(valor), casas)


def _faixa_duracao(segundos: int | None) -> str | None:
    if segundos is None:
        return None
    if segundos < 300:
        return "ate_5min"
    if segundos < 900:
        return "de_5_a_15"
    if segundos <= 3600:
        return "de_15_a_60"
    return "acima_60"


def concentracao(videos: list[dict]) -> dict[str, Any]:
    ids = [v["canal_id"] for v in videos if v.get("canal_id")]
    if not ids:
        return {"n_canais": 0, "participacao_top1": None, "participacao_top3": None, "hhi": None, "canal_top": None}
    contagem = Counter(ids)
    total = len(ids)
    ordenado = contagem.most_common()
    return {
        "n_canais": len(contagem),
        "participacao_top1": round(ordenado[0][1] / total, 3),
        "participacao_top3": round(sum(n for _, n in ordenado[:3]) / total, 3),
        "hhi": round(sum((n / total) ** 2 for n in contagem.values()), 3),
        "canal_top": ordenado[0][0],
    }


def padroes_serp(videos: list[dict], termo: str) -> dict[str, Any]:
    n = len(videos)
    titulos = [extrair_titulo(v.get("titulo") or "") for v in videos]
    duracoes = [v["duracao_segundos"] for v in videos if isinstance(v.get("duracao_segundos"), (int, float))]
    idades = [v["idade_dias"] for v in videos if isinstance(v.get("idade_dias"), (int, float))]
    inscritos = [v["inscritos"] for v in videos if isinstance(v.get("inscritos"), int)]
    faixas = Counter(_faixa_duracao(v.get("duracao_segundos")) for v in videos)
    faixas.pop(None, None)
    portes = Counter((v.get("porte") or "desconhecido") for v in videos)
    pequenos = sum(1 for v in videos if v.get("porte") == "pequeno")

    def taxa(pred) -> float | None:
        return pct(sum(1 for item in titulos if pred(item)), n)

    return {
        "n": n,
        "titulos": {
            "mediana_caracteres": _arredondar(mediana([t["chars"] for t in titulos]), 1) if titulos else None,
            "pct_numero": taxa(lambda t: t["tem_numero"]),
            "pct_pergunta": taxa(lambda t: t["tem_pergunta"]),
            "pct_emoji": taxa(lambda t: t["tem_emoji"]),
            "pct_palavra_caps": taxa(lambda t: t["tem_palavra_caps"]),
            "pct_titulo_todo_caps": taxa(lambda t: t["titulo_todo_caps"]),
            "pct_separador": taxa(lambda t: t["tem_separador"]),
            "pct_parenteses": taxa(lambda t: t["tem_parenteses"]),
            "pct_eu": taxa(lambda t: t["tem_eu"]),
            "pct_voce": taxa(lambda t: t["tem_voce"]),
            "pct_termo_no_inicio": pct(sum(1 for v in videos if termo_no_inicio(v.get("titulo") or "", termo)), n),
            "pct_termo_no_titulo": pct(sum(1 for v in videos if termo_no_titulo(v.get("titulo") or "", termo)), n),
        },
        "duracao": {
            "mediana_segundos": _arredondar(mediana(duracoes), 1),
            "p25_segundos": _arredondar(quantil(duracoes, 0.25), 1),
            "p75_segundos": _arredondar(quantil(duracoes, 0.75), 1),
            "faixas": {k: faixas[k] for k in ("ate_5min", "de_5_a_15", "de_15_a_60", "acima_60") if faixas.get(k)},
        },
        "idade": {
            "mediana_dias": _arredondar(mediana(idades), 1),
            "pct_ate_30_dias": pct(sum(1 for x in idades if x <= 30), len(idades)),
            "pct_ate_90_dias": pct(sum(1 for x in idades if x <= 90), len(idades)),
            "pct_ate_365_dias": pct(sum(1 for x in idades if x <= 365), len(idades)),
            "pct_mais_de_365_dias": pct(sum(1 for x in idades if x > 365), len(idades)),
        },
        "pct_legendas": pct(sum(1 for v in videos if v.get("legendas") is True), n),
        "pct_capitulos": pct(sum(1 for v in videos if v.get("capitulos")), n),
        "portes": dict(portes),
        "pct_canais_pequenos": pct(pequenos, n),
        "mediana_inscritos": _arredondar(mediana(inscritos), 1),
        "concentracao": concentracao(videos),
    }


def classificar_concorrencia(padrao: dict | None) -> tuple[str, str]:
    if not padrao or not padrao.get("n"):
        return (
            "nao_medida",
            "SERP não consultada. Cada search.list custa 100 unidades; este termo ficou sem oferta medida.",
        )
    mediana_inscritos = padrao.get("mediana_inscritos")
    idade = (padrao.get("idade") or {}).get("mediana_dias")
    pct_pequenos = padrao.get("pct_canais_pequenos") or 0
    if mediana_inscritos is None:
        return "incerta", "Inscritos ausentes ou ocultos nos vídeos ranqueados."
    oferta_antiga = idade is not None and idade > 365 and mediana_inscritos < 2_000_000
    if mediana_inscritos < 200_000 or oferta_antiga or pct_pequenos >= 30:
        return (
            "baixa",
            "Canais ranqueados relativamente pequenos, ou a oferta do topo está velha.",
        )
    if mediana_inscritos >= 2_000_000 and (idade is None or idade < 180):
        return "alta", "Canais grandes ou gigantes, com vídeos relativamente recentes no topo."
    return "media", "Mistura de portes, ou oferta nem pequena nem dominada por gigantes recentes."
