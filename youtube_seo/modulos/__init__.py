"""Cinco módulos do YouTube SEO Intelligence."""

from youtube_seo.modulos.concorrentes import monitorar_concorrentes
from youtube_seo.modulos.lacunas import analisar_lacunas
from youtube_seo.modulos.palavras import pesquisar_palavras
from youtube_seo.modulos.pipeline import executar_pipeline
from youtube_seo.modulos.serp import analisar_serp
from youtube_seo.modulos.titulos import analisar_titulos

__all__ = [
    "pesquisar_palavras",
    "analisar_serp",
    "monitorar_concorrentes",
    "analisar_titulos",
    "analisar_lacunas",
    "executar_pipeline",
]
