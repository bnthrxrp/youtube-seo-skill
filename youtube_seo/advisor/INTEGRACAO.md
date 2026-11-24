# Integração do Idea Advisor ao CLI `youtube-seo`

O módulo é só biblioteca padrão (Python 3.11+), lê `knowledge_base.json` ao lado do código e não usa rede nem API paga.

O subcomando já está ligado em `youtube_seo/cli.py` (`advise`, alias `idea`) e o JSON entra no pacote por `[tool.setuptools.package-data]` em `pyproject.toml`. O contrato abaixo é o que essa ligação implementa. O parecer sai no terminal e não grava a pasta `-o`, mesmo que as opções comuns de cache e saída apareçam na ajuda.

## 1. Arquivos

```
youtube_seo/advisor/__init__.py
youtube_seo/advisor/idea_advisor.py
youtube_seo/advisor/knowledge_base.json
tests/test_idea_advisor.py
scripts/research/build_knowledge_base.py      # regenera o JSON a partir das bases do laboratório (pandas, pyarrow)
docs/research/...                             # relatórios, gráficos e exemplos de saída
```

## 2. `pyproject.toml`

Garanta que o JSON vá junto no pacote instalado:

```toml
[tool.setuptools.package-data]
"youtube_seo.advisor" = ["knowledge_base.json"]
```

## 3. `youtube_seo/cli.py`

Import no topo:

```python
from youtube_seo.advisor.idea_advisor import Ideia, aconselhar, para_markdown, porte_por_inscritos
```

Dentro de `_construir()`, junto dos outros subcomandos:

```python
    advise = sub.add_parser("advise", aliases=["idea"], parents=[comum],
                            help="Idea Advisor: parecer offline de uma ideia de vídeo longo (sem API)")
    advise.add_argument("--title", required=True)
    advise.add_argument("--niche", required=True)
    advise.add_argument("--lang", default="pt")
    advise.add_argument("--tier", default=None, help="pequeno, emergente, medio, grande ou gigante")
    advise.add_argument("--subscribers", type=int, default=None)
    advise.add_argument("--duration-min", type=float, default=None)
    advise.add_argument("--thumb-notes", default="")
    advise.add_argument("--thumb-text", default=None)
    advise.add_argument("--days-since-last", type=float, default=None)
    advise.add_argument("--last-result", choices=["hit", "flop", "normal"], default=None)
    advise.add_argument("--recent-titles", default=None, help="Títulos recentes separados por ||")
    advise.add_argument("--format", choices=["markdown", "json"], default="markdown")
```

No despacho por `comando` (antes de criar cliente, cache ou cota, porque o advisor é offline):

```python
    if comando in ("advise", "idea"):
        porte = args.tier or (porte_por_inscritos(args.subscribers) if args.subscribers else "pequeno")
        parecer = aconselhar(Ideia(
            titulo=args.title, nicho=args.niche, idioma=args.lang, porte=porte,
            duracao_min=args.duration_min, thumb_notes=args.thumb_notes, texto_capa=args.thumb_text,
            dias_desde_ultimo=args.days_since_last, ultimo_resultado=args.last_result,
            titulos_recentes=[t.strip() for t in (args.recent_titles or "").split("||") if t.strip()],
        ))
        if args.format == "json":
            import json
            print(json.dumps(parecer, ensure_ascii=False, indent=2))
        else:
            print(para_markdown(parecer))
        return 0
```

Ajuste o `return` ao padrão de `main()` do arquivo (código de saída inteiro).

## 4. `SKILL.md` (nova seção sugerida)

```markdown
## Idea Advisor (offline, sem cota)

Use `youtube-seo advise` (alias `idea`) quando a pessoa pedir para avaliar uma ideia, título, duração ou capa antes de gravar.
O parecer compara a ideia com 26.194 vídeos longos de 310 canais (5 mil a mais de 10 milhões de inscritos, 11 nichos, PT e EN)
e devolve: diagnóstico com grau de confiança, faixa de duração do nicho e porte, leitura do título, diretrizes de capa,
cadência, exemplos reais parecidos e checklist. Não prevê views: a base não tem CTR, impressões, retenção nem origem de tráfego.
Sempre repasse o grau de confiança e os avisos de limite ao usuário.
```

## 5. `README.md` (trecho sugerido)

```markdown
### Avaliar uma ideia de vídeo (offline)

    youtube-seo advise --title "5 celulares baratos que valem a pena em 2026" --niche tech --lang pt \
      --tier pequeno --duration-min 18 --thumb-notes "fundo escuro, produto em destaque, sem rosto" --days-since-last 5

Base de conhecimento: `youtube_seo/advisor/knowledge_base.json`, gerada a partir do estudo em `docs/research/`
(ver `docs/research/RELATORIO_FINAL_CONSOLIDADO.md`).
```

## 6. Testes

```
python -m pytest tests/test_idea_advisor.py
```
