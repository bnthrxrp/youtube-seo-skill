"""CLI única dos cinco módulos e do pipeline."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, TextIO

from youtube_seo.cache import FileCache
from youtube_seo.cliente import YouTubeClient
from youtube_seo.gemini import MODELO_PADRAO
from youtube_seo.http import UrllibTransport
from youtube_seo.modulos.concorrentes import monitorar_concorrentes
from youtube_seo.modulos.lacunas import analisar_lacunas
from youtube_seo.modulos.palavras import pesquisar_palavras
from youtube_seo.modulos.pipeline import executar_pipeline
from youtube_seo.modulos.serp import analisar_serp
from youtube_seo.modulos.titulos import analisar_titulos
from youtube_seo.quota import QuotaLedger
from youtube_seo.saida import salvar


def _comum() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-o", "--saida", default="saida-youtube-seo", help="Pasta dos JSON e Markdown")
    parser.add_argument("--cache-dir", default=None, help="Pasta do cache (padrão: ~/.cache/youtube-seo)")
    parser.add_argument("--quota-file", default=None, help="Arquivo do acumulado diário de cota")
    parser.add_argument("--sem-cache", action="store_true", help="Ignora e não grava cache")
    return parser


def _construir() -> argparse.ArgumentParser:
    comum = _comum()
    parser = argparse.ArgumentParser(
        prog="youtube-seo",
        description=(
            "YouTube SEO Intelligence. Caminho padrão gratuito: autocomplete público, "
            "Data API v3 só com YOUTUBE_API_KEY (cota gratuita) e visão local. "
            "Gemini só com --gemini e GEMINI_API_KEY."
        ),
    )
    sub = parser.add_subparsers(dest="comando")

    def regiao(p: argparse.ArgumentParser) -> None:
        p.add_argument("--hl", default="pt", help="Idioma (relevanceLanguage / autocomplete)")
        p.add_argument("--gl", default="BR", help="País (regionCode / autocomplete)")
        p.add_argument("--max-resultados", type=int, default=25, help="Vídeos por busca (teto 50 por página)")
        p.add_argument("--paginas", type=int, default=1, help="Páginas de search.list; cada uma custa 100 unidades")
        p.add_argument("--letras", default="aeiou", help="Letras da expansão. Vazio desliga. a-z varre o alfabeto")
        p.add_argument("--sem-prefixos", action="store_true", help="Não expande como/melhor/vs e equivalentes")

    palavras = sub.add_parser("keywords", parents=[comum], help="Keyword Research")
    palavras.add_argument("termo")
    regiao(palavras)

    serp = sub.add_parser("serp", parents=[comum], help="SERP Analyzer")
    serp.add_argument("termos", nargs="+")
    regiao(serp)

    concorrentes = sub.add_parser("competitors", parents=[comum], help="Competitor Intelligence")
    concorrentes.add_argument("canais", nargs="+", help="IDs de canal (UC...)")
    concorrentes.add_argument("--max-videos", type=int, default=50)

    titulos = sub.add_parser("titles", parents=[comum], help="Title & Thumbnail Intelligence")
    titulos.add_argument("--termo", default=None)
    regiao(titulos)
    titulos.add_argument("--imagens", default=None, help="Pasta com miniaturas locais")
    titulos.add_argument("--baixar-miniaturas", action="store_true")
    titulos.add_argument("--gemini", action="store_true", help="Opt-in. Exige GEMINI_API_KEY. Desligado por padrão")
    titulos.add_argument("--gemini-model", default=MODELO_PADRAO)

    lacunas = sub.add_parser("gaps", parents=[comum], help="Content Gap Analysis")
    lacunas.add_argument("termo")
    regiao(lacunas)
    lacunas.add_argument("--max-serp", type=int, default=3, help="Quantas consultas vão à SERP (100 unidades cada, sem cache)")

    pipeline = sub.add_parser("pipeline", parents=[comum], help="Os cinco módulos, nesta ordem")
    pipeline.add_argument("termo")
    regiao(pipeline)
    pipeline.add_argument("--canais", nargs="*", default=None)
    pipeline.add_argument("--max-serp", type=int, default=3)
    pipeline.add_argument("--max-videos", type=int, default=50)
    pipeline.add_argument("--imagens", default=None)
    pipeline.add_argument("--baixar-miniaturas", action="store_true")
    pipeline.add_argument("--gemini", action="store_true")
    pipeline.add_argument("--gemini-model", default=MODELO_PADRAO)
    return parser


def _servicos(args: argparse.Namespace, env: dict, transport, now: Callable[[], float]):
    cache_dir = Path(args.cache_dir) if args.cache_dir else Path.home() / ".cache" / "youtube-seo"
    quota_path = Path(args.quota_file) if args.quota_file else cache_dir / "quota.json"
    cache = FileCache(cache_dir, now=now, enabled=not args.sem_cache)
    quota = QuotaLedger(quota_path, now=now)
    client = YouTubeClient(env.get("YOUTUBE_API_KEY", "") or "", transport, cache, quota)
    return cache, quota, client


def _imagens(pasta: str | None) -> list[Path] | None:
    if not pasta:
        return None
    caminho = Path(pasta)
    if not caminho.exists():
        return []
    ext = {".jpg", ".jpeg", ".png", ".webp"}
    return sorted(p for p in caminho.iterdir() if p.suffix.lower() in ext)


def _rodar(args: argparse.Namespace, cache, quota, client, transport, env, now) -> dict:
    letras = getattr(args, "letras", "aeiou")
    prefixos = not getattr(args, "sem_prefixos", False)
    hl = getattr(args, "hl", None)
    gl = getattr(args, "gl", None)
    max_results = getattr(args, "max_resultados", 25)
    pages = getattr(args, "paginas", 1)
    comando = args.comando
    if comando == "keywords":
        return pesquisar_palavras(
            args.termo,
            hl=hl,
            gl=gl,
            client=client,
            transport=transport,
            cache=cache,
            quota=quota,
            now=now,
            letras=letras,
            usar_prefixos=prefixos,
            max_results=max_results,
            pages=pages,
        )
    if comando == "serp":
        return analisar_serp(
            args.termos,
            hl=hl,
            gl=gl,
            client=client,
            now=now,
            max_results=max_results,
            pages=pages,
        )
    if comando == "competitors":
        return monitorar_concorrentes(
            args.canais, client=client, now=now, max_videos=args.max_videos
        )
    if comando == "titles":
        return analisar_titulos(
            termo=args.termo,
            hl=hl,
            gl=gl,
            client=client,
            transport=transport,
            now=now,
            max_results=max_results,
            pages=pages,
            imagens=_imagens(args.imagens),
            baixar_miniaturas=args.baixar_miniaturas,
            gemini_enabled=args.gemini,
            gemini_key=env.get("GEMINI_API_KEY") or None,
            gemini_model=args.gemini_model,
        )
    if comando == "gaps":
        return analisar_lacunas(
            args.termo,
            hl=hl,
            gl=gl,
            client=client,
            transport=transport,
            cache=cache,
            quota=quota,
            now=now,
            max_serp=args.max_serp,
            max_results=max_results,
            pages=pages,
            letras=letras,
            usar_prefixos=prefixos,
        )
    return executar_pipeline(
        args.termo,
        hl=hl,
        gl=gl,
        client=client,
        transport=transport,
        cache=cache,
        quota=quota,
        now=now,
        canais=args.canais or None,
        max_results=max_results,
        max_serp=args.max_serp,
        max_videos=args.max_videos,
        letras=letras,
        usar_prefixos=prefixos,
        pages=pages,
        imagens=_imagens(args.imagens),
        baixar_miniaturas=args.baixar_miniaturas,
        gemini_enabled=args.gemini,
        gemini_key=env.get("GEMINI_API_KEY") or None,
        gemini_model=args.gemini_model,
    )


def main(
    argv: list[str] | None = None,
    *,
    env: dict | None = None,
    transport=None,
    now: Callable[[], float] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    saida = stdout or sys.stdout
    erro = stderr or sys.stderr
    parser = _construir()
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        parser.print_help(saida)
        return 0
    args = parser.parse_args(argv)
    if not getattr(args, "comando", None):
        parser.print_help(saida)
        return 0
    ambiente = os.environ if env is None else env
    relogio = now or time.time
    transporte = transport or UrllibTransport()
    cache, quota, client = _servicos(args, ambiente, transporte, relogio)
    try:
        payload = _rodar(args, cache, quota, client, transporte, ambiente, relogio)
    except Exception as exc:  # última rede de segurança: a chave não pode ir para o terminal
        secreto = ambiente.get("YOUTUBE_API_KEY") or ""
        mensagem = str(exc).replace(secreto, "***") if secreto else str(exc)
        print(f"erro: {mensagem}", file=erro)
        return 1
    caminhos = salvar(args.saida, payload)
    for caminho in caminhos:
        print(caminho, file=saida)
    cota = payload.get("cota") or {}
    if cota:
        print(
            f"cota: {cota.get('gastas_nesta_execucao')} gastas nesta execução, "
            f"{cota.get('evitadas_por_cache')} evitadas por cache, "
            f"{cota.get('usadas_no_dia')}/{cota.get('limite_diario')} no dia.",
            file=saida,
        )
    return 0 if payload.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
