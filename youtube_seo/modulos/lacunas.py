"""Content Gap Analysis.

Cruza sugestões de busca (demanda aparente) com a oferta recente e o porte dos
canais ranqueados. A demanda é estimada: o YouTube não publica volume oficial.
"""

from __future__ import annotations

from typing import Any, Callable

from youtube_seo.cache import FileCache
from youtube_seo.cliente import YouTubeClient
from youtube_seo.http import Transport
from youtube_seo.modulos.palavras import pesquisar_palavras
from youtube_seo.modulos.serp import analisar_serp
from youtube_seo.padroes import classificar_concorrencia
from youtube_seo.quota import QuotaLedger

DISCLAIMER = (
    "A demanda é estimada. O YouTube não publica volume oficial de buscas. "
    "Aparição no autocomplete e nas expansões indica que o termo é sugerido, "
    "não quantas pessoas pesquisam."
)

_DEMANDA_PONTOS = {"aparente_alta": 60, "aparente_media": 40, "semente": 45, "aparente_baixa": 20}
_CONCORRENCIA_PONTOS = {"baixa": 40, "media": 20, "alta": 0, "incerta": 10}
FORMULA = (
    "Pontos só quando a oferta foi medida: demanda aparente "
    "(alta 60, média 40, semente 45, baixa 20) + concorrência "
    "(baixa 40, média 20, alta 0, incerta 10). "
    "Não é volume de busca e não é um score do YouTube."
)


def _demanda(termo: str, semente: str, fonte: str | None, posicao: int | None) -> tuple[str, str]:
    if termo.casefold() == semente.casefold():
        return "semente", "Termo pedido. Não há volume oficial; a semente entra para comparar com a oferta."
    if fonte == "autocomplete" and (posicao or 99) <= 5:
        return "aparente_alta", "Entre as primeiras sugestões do autocomplete."
    if fonte == "autocomplete":
        return "aparente_media", "Aparece no autocomplete, fora das primeiras posições."
    if fonte == "prefixo":
        return "aparente_media", "Surgiu numa expansão de prefixo (como, melhor, vs, review). Sinal aparente, sem volume oficial."
    return "aparente_baixa", "Surgiu só na expansão por letra, não no autocomplete da semente."


def _oportunidade(demanda: str, concorrencia: str) -> tuple[str, str]:
    if concorrencia == "nao_medida":
        return (
            "incompleta",
            "Há um sinal de demanda aparente, mas a oferta deste termo não foi medida.",
        )
    if demanda in {"aparente_alta", "aparente_media", "semente"} and concorrencia == "baixa":
        return "oportunidade", "Demanda aparente com concorrência relativamente baixa."
    if demanda in {"aparente_alta", "aparente_media", "semente"} and concorrencia == "media":
        return "observar", "Há sinal de demanda aparente, e a oferta não é fraca."
    if concorrencia == "alta":
        return "concorrida", "A oferta medida é de canais fortes e relativamente recente."
    return "fraca", "Sinal de demanda aparente fraco diante da oferta medida."


def _indice_serp(serp: dict | None) -> dict[str, dict]:
    indice: dict[str, dict] = {}
    for bloco in (serp or {}).get("termos") or []:
        if bloco.get("termo"):
            indice[bloco["termo"].casefold()] = bloco
    return indice


def analisar_lacunas(
    termo: str,
    *,
    hl: str | None,
    gl: str | None,
    client: YouTubeClient,
    transport: Transport,
    cache: FileCache,
    quota: QuotaLedger,
    now: Callable[[], float],
    max_serp: int = 3,
    max_results: int = 25,
    pages: int = 1,
    letras: str = "aeiou",
    usar_prefixos: bool = True,
    resultado_palavras: dict | None = None,
    resultado_serp: dict | None = None,
) -> dict[str, Any]:
    palavras = resultado_palavras
    if palavras is None:
        palavras = pesquisar_palavras(
            termo,
            hl=hl,
            gl=gl,
            client=client,
            transport=transport,
            cache=cache,
            quota=quota,
            now=now,
            letras=letras,
            usar_prefixos=usar_prefixos,
            max_results=max_results,
            pages=pages,
        )
    candidatos = [termo]
    for fonte in ("autocomplete", "prefixo", "letra"):
        for item in palavras.get("sugestoes") or []:
            texto = item.get("termo")
            if item.get("fonte") == fonte and texto and texto not in candidatos:
                candidatos.append(texto)
    escolhidos = candidatos[: max(1, max_serp)]
    indice = _indice_serp(resultado_serp)
    faltam = [t for t in escolhidos if t.casefold() not in indice]
    avisos = list(palavras.get("avisos") or [])
    if faltam:
        extra = analisar_serp(
            faltam, hl=hl, gl=gl, client=client, now=now, max_results=max_results, pages=pages
        )
        avisos.extend(extra.get("avisos") or [])
        for bloco in extra.get("termos") or []:
            indice[bloco["termo"].casefold()] = bloco
        for pulado in extra.get("pulados") or []:
            avisos.append(f"SERP pulada ({pulado['termo']}): {pulado['motivo']}")
    por_termo = {termo.casefold(): {"fonte": "semente", "posicao": None}}
    for item in palavras.get("sugestoes") or []:
        por_termo.setdefault(item["termo"].casefold(), item)

    linhas = []
    for consulta in candidatos:
        meta = por_termo.get(consulta.casefold(), {})
        fonte = "semente" if consulta.casefold() == termo.casefold() else meta.get("fonte")
        demanda, demanda_nota = _demanda(consulta, termo, fonte, meta.get("posicao"))
        bloco = indice.get(consulta.casefold()) if consulta in escolhidos or consulta.casefold() in indice else None
        padrao = (bloco or {}).get("padroes")
        concorrencia, concorrencia_nota = classificar_concorrencia(padrao)
        classe, classe_nota = _oportunidade(demanda, concorrencia)
        pontos = None
        if concorrencia in _CONCORRENCIA_PONTOS and demanda in _DEMANDA_PONTOS:
            pontos = _DEMANDA_PONTOS[demanda] + _CONCORRENCIA_PONTOS[concorrencia]
        linhas.append(
            {
                "termo": consulta,
                "demanda": demanda,
                "demanda_nota": demanda_nota,
                "concorrencia": concorrencia,
                "concorrencia_nota": concorrencia_nota,
                "classe": classe,
                "classe_nota": classe_nota,
                "pontos": pontos,
                "oferta": None
                if not padrao
                else {
                    "n": padrao.get("n"),
                    "mediana_inscritos": padrao.get("mediana_inscritos"),
                    "idade_mediana_dias": (padrao.get("idade") or {}).get("mediana_dias"),
                    "pct_canais_pequenos": padrao.get("pct_canais_pequenos"),
                    "concentracao": padrao.get("concentracao"),
                },
            }
        )
    medidas = sum(1 for linha in linhas if linha["concorrencia"] != "nao_medida")
    return {
        "modulo": "gaps",
        "ok": bool(linhas),
        "completo": medidas == len(linhas) and medidas > 0,
        "cobertura_serp": {"medidas": medidas, "termos": len(linhas)},
        "disclaimer": DISCLAIMER,
        "formula": FORMULA,
        "consulta": {"termo": termo, "hl": hl, "gl": gl, "max_serp": max_serp},
        "oportunidades": linhas,
        "sugestoes_nao_medidas": [t for t in candidatos if t not in escolhidos],
        "avisos": avisos,
        "cota": quota.resumo(),
        "cota_estimada_sem_cache": {
            "search.list": max_serp * max(1, pages) * 100,
            "nota": "Teto se nenhuma destas consultas estiver em cache. O padrão é a semente mais as primeiras sugestões, até max_serp.",
        },
    }
