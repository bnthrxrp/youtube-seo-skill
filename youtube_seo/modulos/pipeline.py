"""Pipeline na ordem dos módulos: palavras, SERP, concorrentes, títulos, lacunas.

Lacunas reutilizam a pesquisa e a SERP já feitas. O cache evita um segundo
search.list da mesma consulta.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from youtube_seo.cache import FileCache
from youtube_seo.cliente import YouTubeClient
from youtube_seo.gemini import MODELO_PADRAO
from youtube_seo.http import Transport
from youtube_seo.modulos.concorrentes import monitorar_concorrentes
from youtube_seo.modulos.lacunas import analisar_lacunas
from youtube_seo.modulos.palavras import pesquisar_palavras
from youtube_seo.modulos.serp import analisar_serp
from youtube_seo.modulos.titulos import analisar_titulos
from youtube_seo.quota import QuotaLedger


def executar_pipeline(
    termo: str,
    *,
    hl: str | None,
    gl: str | None,
    client: YouTubeClient,
    transport: Transport,
    cache: FileCache,
    quota: QuotaLedger,
    now: Callable[[], float],
    canais: list[str] | None = None,
    max_results: int = 25,
    max_serp: int = 3,
    max_videos: int = 50,
    letras: str = "aeiou",
    usar_prefixos: bool = True,
    pages: int = 1,
    imagens: list[Path] | None = None,
    baixar_miniaturas: bool = False,
    vision=None,
    gemini_enabled: bool = False,
    gemini_key: str | None = None,
    gemini_model: str = MODELO_PADRAO,
) -> dict[str, Any]:
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
    serp = analisar_serp(
        [termo],
        hl=hl,
        gl=gl,
        client=client,
        now=now,
        max_results=max_results,
        pages=pages,
    )
    concorrentes = None
    if canais:
        concorrentes = monitorar_concorrentes(canais, client=client, now=now, max_videos=max_videos)
    videos = []
    if serp.get("termos"):
        videos = serp["termos"][0].get("videos") or []
    titulos = analisar_titulos(
        videos=videos,
        transport=transport,
        client=client,
        now=now,
        imagens=imagens,
        baixar_miniaturas=baixar_miniaturas,
        vision=vision,
        gemini_enabled=gemini_enabled,
        gemini_key=gemini_key,
        gemini_model=gemini_model,
    )
    lacunas = analisar_lacunas(
        termo,
        hl=hl,
        gl=gl,
        client=client,
        transport=transport,
        cache=cache,
        quota=quota,
        now=now,
        max_serp=max_serp,
        max_results=max_results,
        letras=letras,
        usar_prefixos=usar_prefixos,
        resultado_palavras=palavras,
        resultado_serp=serp,
    )
    partes = [palavras, serp, titulos, lacunas]
    if concorrentes:
        partes.append(concorrentes)
    return {
        "modulo": "pipeline",
        "ok": all(parte.get("ok") for parte in partes),
        "ordem": ["keywords", "serp", "competitors", "titles", "gaps"],
        "consulta": {"termo": termo, "hl": hl, "gl": gl, "canais": canais or []},
        "keywords": palavras,
        "serp": serp,
        "competitors": concorrentes,
        "titles": titulos,
        "gaps": lacunas,
        "cota": quota.resumo(),
        "avisos": [a for parte in partes for a in (parte.get("avisos") or [])],
    }
