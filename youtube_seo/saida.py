"""Grava JSON e Markdown lado a lado."""

from __future__ import annotations

import json
from pathlib import Path

from youtube_seo.relatorio import render

_FILHOS = ("keywords", "serp", "competitors", "titles", "gaps")


def salvar(diretorio: str | Path, payload: dict) -> list[Path]:
    destino = Path(diretorio)
    destino.mkdir(parents=True, exist_ok=True)
    caminhos: list[Path] = []
    if payload.get("modulo") == "pipeline":
        for nome in _FILHOS:
            filho = payload.get(nome)
            if isinstance(filho, dict) and filho.get("modulo"):
                caminhos.extend(salvar(destino, filho))
    stem = payload.get("modulo") or "relatorio"
    json_path = destino / f"{stem}.json"
    md_path = destino / f"{stem}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render(payload), encoding="utf-8")
    return [*caminhos, json_path, md_path]
