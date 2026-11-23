"""Relatórios Markdown. O JSON é o mesmo dicionário do módulo, gravado à parte."""

from __future__ import annotations

from typing import Any


def _nao(valor: Any) -> str:
    if valor is None or valor == "":
        return "—"
    return str(valor).replace("|", "\\|").replace("\n", " ")


def _tabela(cabecalhos: list[str], linhas: list[list[Any]]) -> str:
    if not linhas:
        return "_Sem linhas._\n"
    head = "| " + " | ".join(cabecalhos) + " |"
    sep = "| " + " | ".join("---" for _ in cabecalhos) + " |"
    body = ["| " + " | ".join(_nao(col) for col in linha) + " |" for linha in linhas]
    return "\n".join([head, sep, *body]) + "\n"


def _cota(cota: dict | None) -> str:
    if not cota:
        return "## Cota\n\n_Sem ledger de cota nesta execução._\n"
    linhas = [
        "## Cota da YouTube Data API v3",
        "",
        f"- Unidades gastas nesta execução: **{cota.get('gastas_nesta_execucao')}**",
        f"- Unidades evitadas pelo cache: **{cota.get('evitadas_por_cache')}**",
        f"- Acumulado do dia UTC {cota.get('data_utc')}: **{cota.get('usadas_no_dia')} / {cota.get('limite_diario')}**",
        f"- Restante estimado: **{cota.get('restante')}**",
        "",
        f"> {cota.get('regra')}",
    ]
    for aviso in cota.get("avisos") or []:
        linhas.append(f"- **Aviso de cota:** {aviso}")
    return "\n".join(linhas) + "\n"


def _avisos(avisos: list[str] | None) -> str:
    if not avisos:
        return ""
    linhas = ["## Avisos", ""]
    linhas.extend(f"- {aviso}" for aviso in avisos)
    return "\n".join(linhas) + "\n"


def render_keywords(payload: dict) -> str:
    consulta = payload.get("consulta") or {}
    partes = [
        "# Pesquisa de palavras-chave / Keyword research",
        "",
        "Relatório em português. Volume de busca **não** é número oficial.",
        "",
        f"**Termo:** {consulta.get('termo')}  ",
        f"**Idioma / país:** {_nao(consulta.get('hl'))} / {_nao(consulta.get('gl'))}",
        "",
        f"> {payload.get('nota_volume')}",
        "",
        "## Sugestões",
        "",
        _tabela(
            ["Termo", "Fonte", "Posição", "Intenção (inferência)"],
            [
                [s.get("termo"), s.get("fonte"), s.get("posicao"), s.get("intencao")]
                for s in payload.get("sugestoes") or []
            ],
        ),
        "## Métricas dos vídeos relacionados",
        "",
        _tabela(
            ["Vídeos", "Canais", "Mediana de views", "Mediana de duração (s)", "% com legenda"],
            [[
                (payload.get("metricas") or {}).get("n_videos"),
                (payload.get("metricas") or {}).get("n_canais"),
                (payload.get("metricas") or {}).get("mediana_views"),
                (payload.get("metricas") or {}).get("mediana_duracao_segundos"),
                (payload.get("metricas") or {}).get("pct_legendas"),
            ]]
            if payload.get("metricas")
            else [],
        ),
        "## Canais que aparecem",
        "",
        _tabela(
            ["Canal", "Porte", "Inscritos", "Vídeos na lista", "Melhor posição"],
            [
                [c.get("canal_nome"), c.get("porte"), c.get("inscritos"), c.get("videos"), c.get("melhor_posicao")]
                for c in payload.get("canais") or []
            ],
        ),
        "## Tags recorrentes",
        "",
        _tabela(
            ["Tag", "Vídeos"],
            [[t.get("tag"), t.get("videos")] for t in payload.get("tags") or []],
        ),
        _cota(payload.get("cota")),
        _avisos(payload.get("avisos")),
    ]
    return "\n".join(partes)


def render_serp(payload: dict) -> str:
    partes = [
        "# Analisador de SERP / SERP analyzer",
        "",
        "Relatório em português.",
        "",
        f"> {payload.get('nota_ranking')}",
        "",
        f"**Cota estimada sem cache (search.list):** {(payload.get('cota_estimada_sem_cache') or {}).get('search.list')} unidades.",
        "",
        payload.get("estudo") or "",
        "",
    ]
    for bloco in payload.get("termos") or []:
        padrao = bloco.get("padroes") or {}
        titulos = padrao.get("titulos") or {}
        duracao = padrao.get("duracao") or {}
        idade = padrao.get("idade") or {}
        concentracao = padrao.get("concentracao") or {}
        partes.extend(
            [
                f"## {bloco.get('termo')}",
                "",
                "### Estrutura de título",
                "",
                _tabela(
                    ["Mediana de caracteres", "% número", "% pergunta", "% emoji", "% palavra em caixa alta", "% termo no início"],
                    [[
                        titulos.get("mediana_caracteres"),
                        titulos.get("pct_numero"),
                        titulos.get("pct_pergunta"),
                        titulos.get("pct_emoji"),
                        titulos.get("pct_palavra_caps"),
                        titulos.get("pct_termo_no_inicio"),
                    ]],
                ),
                "### Duração, idade, legendas e capítulos",
                "",
                _tabela(
                    ["Mediana (s)", "P25", "P75", "Faixas", "Idade mediana (dias)", "% legendas", "% capítulos"],
                    [[
                        duracao.get("mediana_segundos"),
                        duracao.get("p25_segundos"),
                        duracao.get("p75_segundos"),
                        duracao.get("faixas"),
                        idade.get("mediana_dias"),
                        padrao.get("pct_legendas"),
                        padrao.get("pct_capitulos"),
                    ]],
                ),
                "### Porte e concentração de canais",
                "",
                _tabela(
                    ["Mediana de inscritos", "% canais pequenos", "Portes", "Canais distintos", "Top 1", "Top 3", "HHI"],
                    [[
                        padrao.get("mediana_inscritos"),
                        padrao.get("pct_canais_pequenos"),
                        padrao.get("portes"),
                        concentracao.get("n_canais"),
                        concentracao.get("participacao_top1"),
                        concentracao.get("participacao_top3"),
                        concentracao.get("hhi"),
                    ]],
                ),
                "### Leitura à luz do estudo próprio",
                "",
                _tabela(
                    ["Traço", "Força", "Nesta SERP", "Estudo"],
                    [
                        [n.get("traco"), n.get("rotulo"), n.get("observado"), n.get("estudo")]
                        for n in bloco.get("leitura_estudo") or []
                    ],
                ),
            ]
        )
    if payload.get("pulados"):
        partes.extend(["## Termos não consultados", ""])
        partes.append(
            _tabela(
                ["Termo", "Motivo"],
                [[p.get("termo"), p.get("motivo")] for p in payload["pulados"]],
            )
        )
    partes.extend([_cota(payload.get("cota")), _avisos(payload.get("avisos"))])
    return "\n".join(partes)


def render_competitors(payload: dict) -> str:
    partes = [
        "# Inteligência de concorrentes / Competitor intelligence",
        "",
        "Relatório em português. Sem `search.list`: o custo é o de `channels.list`, `playlistItems.list` e `videos.list` (1 unidade por chamada).",
        "",
    ]
    for canal in payload.get("canais") or []:
        if not canal.get("ok"):
            partes.extend([f"## {_nao(canal.get('canal_id'))}", "", canal.get("motivo") or "Falhou.", ""])
            continue
        freq = canal.get("frequencia") or {}
        partes.extend(
            [
                f"## {canal.get('canal_nome')} ({canal.get('porte')})",
                "",
                _tabela(
                    ["Inscritos", "Lista", "Vídeos", "Por semana", "Intervalo mediano (dias)", "Duração mediana (s)", "% legendas", "% capítulos"],
                    [[
                        canal.get("inscritos"),
                        canal.get("fonte_lista"),
                        canal.get("n_videos"),
                        freq.get("por_semana"),
                        freq.get("intervalo_mediano_dias"),
                        canal.get("duracao_mediana_segundos"),
                        canal.get("pct_legendas"),
                        canal.get("pct_capitulos"),
                    ]],
                ),
                "### Temas recorrentes",
                "",
                _tabela(
                    ["Termo", "Vezes"],
                    [[t.get("termo"), t.get("vezes")] for t in (canal.get("temas") or {}).get("termos") or []],
                ),
                "### Desempenho contra a mediana do próprio canal",
                "",
                (canal.get("desempenho") or {}).get("nota") or "",
                "",
                _tabela(
                    ["Título", "Views", "Idade (dias)", "Versus mediana", "Faixa"],
                    [
                        [v.get("titulo"), v.get("views"), v.get("idade_dias"), v.get("vs_mediana"), v.get("faixa")]
                        for v in (canal.get("desempenho") or {}).get("videos") or []
                    ],
                ),
            ]
        )
    partes.extend([_cota(payload.get("cota")), _avisos(payload.get("avisos"))])
    return "\n".join(partes)


def render_titles(payload: dict) -> str:
    gemini = payload.get("gemini") or {}
    partes = [
        "# Títulos e miniaturas / Title and thumbnail intelligence",
        "",
        "Relatório em português. Visão e OCR locais são o caminho gratuito. Gemini é opt-in e vem desligado.",
        "",
        payload.get("estudo") or "",
        "",
        f"**Gemini:** {'ligado' if gemini.get('habilitado') else 'desligado'}. Chamadas ok: {gemini.get('chamadas_ok')}. {gemini.get('nota')}",
        "",
        "## O que esta amostra faz, e o que o estudo disse",
        "",
        _tabela(
            ["Traço", "Força no estudo", "Nesta amostra", "Efeito", "Margem", "Leitura"],
            [
                [c.get("traco"), c.get("rotulo"), f"{_nao(c.get('nesta_amostra'))} {c.get('unidade') or ''}", c.get("efeito"), c.get("margem"), c.get("leitura")]
                for c in payload.get("cruzamento_estudo") or []
            ],
        ),
    ]
    visao = payload.get("visao_agregada")
    if visao:
        partes.extend(
            [
                "## Miniaturas (medição local)",
                "",
                _tabela(
                    ["N", "% com rosto", "% rosto grande", "% com texto", "% repete título", "% com 5+ palavras"],
                    [[
                        visao.get("n"),
                        visao.get("pct_rosto"),
                        visao.get("pct_rosto_grande"),
                        visao.get("pct_texto"),
                        visao.get("pct_repete_titulo"),
                        visao.get("pct_5_palavras_ou_mais"),
                    ]],
                ),
                "Nenhum destes traços é sinal forte no estudo. Rosto grande muda de sinal conforme o detector; 5+ palavras e contraste são correlação fraca.",
                "",
            ]
        )
    else:
        partes.extend(
            [
                "## Miniaturas",
                "",
                "Nenhuma imagem foi lida nesta execução. Passe `--imagens` ou `--baixar-miniaturas`. Sem OpenCV/RapidOCR a visão local avisa e o relatório de título continua.",
                "",
            ]
        )
    partes.extend(
        [
            "## Amostra",
            "",
            _tabela(
                ["Título", "Emoji", "Palavra em caixa alta", "Pergunta", "Gemini"],
                [
                    [
                        item.get("titulo"),
                        (item.get("titulo_tracos") or {}).get("tem_emoji"),
                        (item.get("titulo_tracos") or {}).get("tem_palavra_caps"),
                        (item.get("titulo_tracos") or {}).get("tem_pergunta"),
                        (item.get("gemini") or {}).get("status"),
                    ]
                    for item in (payload.get("itens") or [])[:30]
                ],
            ),
            _cota(payload.get("cota")),
            _avisos(payload.get("avisos")),
        ]
    )
    return "\n".join(partes)


def _cobertura(payload: dict) -> str:
    cob = payload.get("cobertura_serp") or {}
    if payload.get("completo"):
        return "sim, nos termos listados"
    if cob.get("medidas"):
        return f"parcial ({cob.get('medidas')} de {cob.get('termos')} termos; o resto evita search.list)"
    return "não"


def render_gaps(payload: dict) -> str:
    partes = [
        "# Lacunas de conteúdo / Content gap analysis",
        "",
        "Relatório em português.",
        "",
        f"> **{payload.get('disclaimer')}**",
        "",
        payload.get("formula") or "",
        "",
        f"**Oferta medida:** {_cobertura(payload)}.",
        "",
        "## Termos",
        "",
        _tabela(
            ["Termo", "Demanda aparente", "Concorrência", "Classe", "Pontos", "Mediana de inscritos", "Idade mediana (dias)"],
            [
                [
                    linha.get("termo"),
                    linha.get("demanda"),
                    linha.get("concorrencia"),
                    linha.get("classe"),
                    linha.get("pontos"),
                    (linha.get("oferta") or {}).get("mediana_inscritos") if linha.get("oferta") else None,
                    (linha.get("oferta") or {}).get("idade_mediana_dias") if linha.get("oferta") else None,
                ]
                for linha in payload.get("oportunidades") or []
            ],
        ),
        "Classe `oportunidade` significa demanda aparente com concorrência relativamente baixa. Não é volume oficial e não promete views.",
        "",
    ]
    if payload.get("sugestoes_nao_medidas"):
        partes.extend(
            [
                "## Sugestões sem SERP própria",
                "",
                "Ficaram de fora para não gastar 100 unidades por termo. Suba `--max-serp` se a cota do dia permitir.",
                "",
                ", ".join(payload["sugestoes_nao_medidas"]),
                "",
            ]
        )
    partes.extend([_cota(payload.get("cota")), _avisos(payload.get("avisos"))])
    return "\n".join(partes)


def render_pipeline(payload: dict) -> str:
    consulta = payload.get("consulta") or {}
    return "\n".join(
        [
            "# Pipeline YouTube SEO Intelligence",
            "",
            "Relatório em português. Os cinco módulos estão nos arquivos ao lado (`keywords`, `serp`, `competitors`, `titles`, `gaps`).",
            "",
            f"**Termo:** {consulta.get('termo')}  ",
            f"**Canais:** {', '.join(consulta.get('canais') or []) or '—'}",
            "",
            "Ordem: pesquisa de palavra-chave, SERP, concorrentes (se houver canais), títulos e miniaturas, lacunas. A SERP da semente reutiliza o cache da pesquisa.",
            "",
            _tabela(
                ["Módulo", "Ok"],
                [
                    ["keywords", (payload.get("keywords") or {}).get("ok")],
                    ["serp", (payload.get("serp") or {}).get("ok")],
                    ["competitors", None if payload.get("competitors") is None else payload["competitors"].get("ok")],
                    ["titles", (payload.get("titles") or {}).get("ok")],
                    ["gaps", (payload.get("gaps") or {}).get("ok")],
                ],
            ),
            _cota(payload.get("cota")),
            _avisos(payload.get("avisos")),
        ]
    )


_RENDER = {
    "keywords": render_keywords,
    "serp": render_serp,
    "competitors": render_competitors,
    "titles": render_titles,
    "gaps": render_gaps,
    "pipeline": render_pipeline,
}


def render(payload: dict) -> str:
    fn = _RENDER.get(payload.get("modulo"))
    if fn is None:
        return "Relatório sem módulo conhecido.\n"
    texto = fn(payload).rstrip() + "\n"
    return texto
