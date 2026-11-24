# youtube-seo-skill

Agent skill (SKILL.md) para SEO e descoberta no YouTube, long-form e Shorts, com cada afirmação rotulada por nível de evidência e ligada a uma fonte pública.

An agent skill (SKILL.md) for YouTube SEO and discovery, covering long-form and Shorts, where every claim is labeled by evidence level and linked to a public source.

## PT-BR

**O que é.** Um guia operacional para títulos, thumbnails, ganchos, descrição, tags, capítulos, pesquisa de palavra-chave, Shorts, multi-idioma, telas finais, cards, posts, lives, testes A/B, diagnóstico de queda de views e checklists de publicação. Pesquisa revisada em novembro de 2026 (133 fontes; lacunas verificadas em fonte primária na v2.1).

**Arquivos**
- `SKILL.md`: a skill (frontmatter + corpo).
- `FONTES.md`: todas as fontes com URL, data, nível e o que afirmam.
- `HISTORICO.md`: linha do tempo do sistema de 2008 a 2026.
- `DIVERGENCIAS.md`: onde praticantes e o YouTube discordam.
- `GITHUB_SKILLS.md`: levantamento de skills parecidas.
- `VERIFICACAO_LACUNAS.md`: vereditos das lacunas (confirmado, parcial, desmentido, sem fonte primária).
- `estudo-10k/`: estudo próprio com 17.882 vídeos longos de 203 canais de 200 mil inscritos ou mais (PT e EN, 11 nichos): `RESULTADOS.md` em linguagem simples, gráficos, tabelas, dataset (`dados/dataset.parquet`), lista de canais e scripts reproduzíveis (exigem sua própria chave da YouTube Data API em `YOUTUBE_API_KEY`).
- `docs/research/`: laboratório que amplia esse recorte para **26.194 vídeos longos de 310 canais** (mais 107 canais de 5 mil a 200 mil inscritos, 8.312 vídeos). Relatório consolidado (`RELATORIO_FINAL_CONSOLIDADO.md`), 9 relatórios de apoio, 20 gráficos, catálogo visual, 4 pareceres de exemplo e o ranking de alavancas (`data/ranking_alavancas.csv`).
- `youtube_seo/`: sistema **YouTube SEO Intelligence** (CLI `youtube-seo`). Cinco módulos, cota gratuita e cache local, mais o Idea Advisor offline (`youtube_seo/advisor/`). Ver a seção abaixo. Os scripts de `estudo-10k/` não foram alterados.

**Instalar**
- Claude Code: copie a pasta para `~/.claude/skills/youtube-seo/` (pessoal) ou `.claude/skills/youtube-seo/` (projeto).
- Claude.ai / Claude Desktop: compacte a pasta em .zip e envie em Settings > Capabilities > Skills.
- Cursor: copie para `.cursor/skills/youtube-seo/` no projeto, ou cole o conteúdo de `SKILL.md` numa regra em `.cursor/rules/`.
- Outros agentes: qualquer agente que leia SKILL.md (frontmatter `name` + `description`). Se não houver suporte a skills, use `SKILL.md` como prompt de sistema e deixe os demais arquivos acessíveis.

**Níveis de evidência**
- `[OFICIAL]`: Ajuda do YouTube, YouTube Blog, How YouTube Works, Creator Insider.
- `[OFICIAL-LIAISON]`: Creator Liaison do YouTube (fala pública, não documentação).
- `[PAPER]`: papers de engenheiros do Google/YouTube (contexto histórico).
- `[PRATICANTE]`: ferramentas, consultores, creators, imprensa, estudos (sempre com nome).
- `[ESTUDO-PRÓPRIO]`: resultado do estudo em `estudo-10k/` (correlação, não causa).
- `[INFERÊNCIA]`: dedução explícita.

### YouTube SEO Intelligence

Pacote Python de biblioteca padrão (visão computacional é opcional). O caminho padrão custa R$ 0: autocomplete público, Data API v3 só se você definir `YOUTUBE_API_KEY` (cota gratuita) e OCR/OpenCV local se instalar o extra `vision`. Gemini fica **desligado**. Ele só roda com `--gemini` e `GEMINI_API_KEY`, na conta de quem forneceu a chave.

Não há `.env` no repositório. Exporte a chave no shell. Ela não é impressa nem gravada no cache.

**Instalar e testar**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Visão e OCR locais, no mesmo desenho de `estudo-10k/scripts/04b_miniaturas.py` e `04c_ocr_miniaturas.py`:

```bash
pip install -e ".[vision]"
```

**CLI.** `keywords`, `serp`, `competitors`, `titles`, `gaps` e `pipeline` gravam `<modulo>.json` e `<modulo>.md` em `-o` (padrão `saida-youtube-seo/`). Cache e acumulado de cota ficam em `~/.cache/youtube-seo/` (`--cache-dir` e `--quota-file` mudam o lugar). `advise` imprime o parecer no terminal e não abre cache nem cota.

```bash
export YOUTUBE_API_KEY=...          # opcional; sem ela, keywords e gaps ficam no autocomplete
youtube-seo keywords "pão caseiro" --hl pt --gl BR -o saida/pao
youtube-seo serp "pão caseiro" "pão integral" --hl pt --gl BR -o saida/pao
youtube-seo competitors UCxxxxxxxxxxxxxxxxxxxxxx -o saida/canais
youtube-seo titles --termo "pão caseiro" --hl pt --gl BR -o saida/titulos
youtube-seo titles --imagens ./minhas-thumbs -o saida/thumbs
youtube-seo gaps "pão caseiro" --hl pt --gl BR --max-serp 3 -o saida/gaps
youtube-seo pipeline "pão caseiro" --hl pt --gl BR --canais UCxxxxxxxxxxxxxxxxxxxxxx -o saida/pipeline
```

### Laboratório (26.194 vídeos, 310 canais)

O estudo em `docs/research/` amplia o `estudo-10k/`. São 26.194 vídeos longos de 310 canais: 203 canais com 200 mil inscritos ou mais (17.882 vídeos) e 107 canais de 5 mil a 200 mil (8.312 vídeos), 11 nichos, português e inglês, snapshot de 23/11/2026. O relatório consolidado está em `docs/research/RELATORIO_FINAL_CONSOLIDADO.md`.

Desempenho, neste laboratório, é a quantidade de views do vídeo contra a mediana do próprio canal. A base não inclui CTR, impressões, retenção, tempo de exibição, origem de tráfego, inscritos ganhos por vídeo nem transcrições. Os efeitos são associação dentro do canal (efeito fixo, intervalo de 95% e correção de Benjamini-Hochberg), não causa.

Achados com sinal forte, dentro do canal:

- **Duração.** Dobrar a duração soma +30,2% nos canais de 5 mil a 200 mil e +14,9% nos de 200 mil ou mais. A faixa de 20 a 45 min rende +25,1% contra 8 a 20 min do mesmo canal; menos de 5 min rende −33,5%. O ótimo médio fica em 34 min (IC 28 a 43). Tech cai depois de cerca de 30 min.
- **Consistência.** Fugir do tema habitual custa cerca de −14,8% por desvio padrão nos canais de 5 mil a 200 mil e −10,5% nos de 200 mil ou mais. Fugir do visual habitual da capa custa −10,9% e −7,4%.
- **Cadência.** Nos canais de 200 mil ou mais, publicar com menos de 2 dias do vídeo anterior se associa a −8,8%; lançar menos de 3 dias depois de um fracasso, a −17,8%. Nos canais de 5 mil a 200 mil, o intervalo curto fica inconclusivo (q = 0,59).
- **Legenda enviada pelo canal.** +28,6% nos canais de 200 mil ou mais, com risco real de causalidade reversa.
- **Título.** Vocabulário abstrato −15,4%; marca ou produto famoso em tech e games +25,5%; 1ª pessoa em inglês −11,0%.

Rosto grande na capa, expressão de surpresa, seta ou círculo, saturação alta, contraste alto e horário de publicação não se sustentam dentro do canal (rosto grande chega a +30,0% na comparação ingênua entre canais e a −2,5% dentro do canal). O texto do título explica no máximo R² 0,018 fora da amostra. A ruptura de porte aparece por volta de 2 milhões de inscritos, não em 200 mil: pequeno, emergente e médio se parecem; grande e gigante concentram menos views no top 10% e geram menos anomalias de 10x.

### Avaliar uma ideia de vídeo (offline)

`youtube-seo advise` (alias `idea`) compara uma ideia de vídeo longo com essa base. Não chama API, não usa rede e não gasta cota. O parecer sai no terminal (markdown ou `--format json`), com diagnóstico, grau de confiança, faixa de duração, leitura do título, diretrizes de capa, cadência, exemplos reais parecidos e checklist. Ele não prevê views.

```bash
youtube-seo advise --title "5 celulares baratos que valem a pena em 2026" --niche tech --lang pt \
  --tier pequeno --duration-min 18 --thumb-notes "fundo escuro, produto em destaque, sem rosto" --days-since-last 5
youtube-seo idea --title "50 Geography Facts You Won't Believe" --niche educacao --lang en \
  --subscribers 19500 --duration-min 21 --format json
```

`--tier` aceita `pequeno`, `emergente`, `medio`, `grande` ou `gigante`. Sem `--tier`, `--subscribers` define o porte (abaixo de 50 mil, pequeno; até 200 mil, emergente; até 2 milhões, médio; até 10 milhões, grande; acima, gigante). Sem os dois, o padrão é pequeno. Nichos: `culinaria`, `documentario`, `educacao`, `entretenimento`, `esportes`, `financas`, `games`, `historias`, `infantil`, `lifestyle`, `tech`.

A base fica em `youtube_seo/advisor/knowledge_base.json`. `scripts/research/build_knowledge_base.py` regenera esse JSON a partir das bases do laboratório (pandas e pyarrow). As bases brutas, embeddings e miniaturas não estão neste repositório. Quatro pareceres de exemplo estão em `docs/research/advisor_examples/`.

`--letras aeiou` expande o autocomplete (use `--letras abcdefghijklmnopqrstuvwxyz` para o alfabeto). `--sem-prefixos` desliga como/melhor/vs. `--sem-cache` ignora o cache. `--paginas 2` pede outra página de busca e custa mais 100 unidades por termo.

**Cota gratuita (YouTube Data API v3).** Teto diário padrão: **10.000** unidades, por projeto Google, não por este repositório.

| Chamada | Unidades | Onde entra |
|---|---|---|
| `search.list` | 100 por página | keywords, serp, gaps, pipeline |
| `videos.list` | 1 por lote de até 50 ids | enriquecimento e concorrentes |
| `channels.list` | 1 por lote de até 50 canais | porte e playlist de uploads |
| `playlistItems.list` | 1 por página | concorrentes (lista UULF, senão UU) |
| autocomplete | 0 | suggestqueries público, fora da Data API |

Uma SERP de um termo, com cache frio, fica em cerca de **102** unidades (100 + vídeos + canais). Dez termos sem cache são 1.000 unidades só de `search.list`. O relatório avisa a estimativa, o que o cache evitou, o acumulado do dia UTC e bloqueia a busca quando restam menos de 100. Concorrentes não usam `search.list`: 1 + 1 + 1 por canal no caso simples (até 50 vídeos).

O porte segue `estudo-10k/scripts/02_selecao.py`: pequeno &lt; 200 mil, médio 200 mil–2 milhões, grande 2–20 milhões, gigante ≥ 20 milhões.

**Formato da saída.** Os trechos abaixo ilustram a forma dos Markdown. Não são uma coleta ao vivo.

Keyword Research — sugestão, tags e canais. O volume não é número oficial:

```markdown
| Termo | Fonte | Posição | Intenção (inferência) |
| --- | --- | --- | --- |
| pao caseiro facil | autocomplete | 1 | indefinida |
```

SERP Analyzer — título, duração, idade, legenda, porte e concentração, com a força do sinal no estudo (forte, provável, fraco, sem efeito):

```markdown
| Mediana (s) | Idade mediana (dias) | % legendas | % capítulos | Mediana de inscritos | HHI |
| --- | --- | --- | --- | --- | --- |
| 480 | 100 | 66.7 | 33.3 | 50000 | 0.556 |
```

Competitor Intelligence — frequência, temas e views contra a mediana do próprio canal (acima = 1,5× ou mais):

```markdown
| Por semana | Intervalo mediano (dias) | % legendas | Título | Versus mediana | Faixa |
| --- | --- | --- | --- | --- | --- |
| 1.0 | 7 | 60 | receita de pao caseiro | 4.0 | acima |
```

Title & Thumbnail Intelligence — o traço na amostra ao lado do que o estudo mediu. Miniatura sem imagem fica de fora; com `--imagens` ou `--baixar-miniaturas` entra a medição local. Gemini desligado não gera chamada:

```markdown
| Traço | Força no estudo | Nesta amostra |
| --- | --- | --- |
| Tamanho do título | sem efeito confirmado | 15 caracteres (mediana) |
| Uma palavra em CAIXA ALTA | provável, não passou na correção conservadora | 33% dos títulos |
| Rosto grande na miniatura | correlação fraca | depende da imagem |
```

Content Gap Analysis — a primeira linha do relatório é o aviso de demanda estimada. `oportunidade` é demanda aparente com concorrência relativamente baixa. Termo sem SERP fica `incompleta` para não gastar 100 unidades:

```markdown
> A demanda é estimada. O YouTube não publica volume oficial de buscas.

| Termo | Demanda aparente | Concorrência | Classe | Pontos |
| --- | --- | --- | --- | --- |
| pao caseiro | semente | baixa | oportunidade | 85 |
| pao caseiro facil | aparente_alta | nao_medida | incompleta | — |
```

Pontos, quando a oferta foi medida: demanda aparente (alta 60, média 40, semente 45, baixa 20) + concorrência (baixa 40, média 20, alta 0). Não é volume e não é score do YouTube.

## English

**What it is.** An operational guide for titles, thumbnails, hooks, descriptions, tags, chapters, keyword research, Shorts, multi-language audio, end screens, cards, posts, live streams, A/B tests, view-drop diagnosis and publishing checklists. The skill is written in Brazilian Portuguese. Research reviewed November 2026 (133 sources; gaps checked against primary sources in v2.1). v2.2 adds an original observational study of 17,882 long-form videos from 203 channels with 200k or more subscribers in `estudo-10k/` (each video compared with its own channel's baseline; mixed-effects and within-channel models, Benjamini-Hochberg correction, out-of-sample validation), with thumbnails also read by a vision model (expression, gaze, arrows, style, background). Headline of that slice: all 35 metadata and thumbnail traits together explain about 1.5% of within-channel variation; channel-uploaded captions (+28%) and longer duration (+14% per doubling) are the only robust correlates. v2.4 extends the same snapshot to **26,194 long-form videos from 310 channels** (adding 107 channels between 5k and 200k subscribers, 8,312 videos) in `docs/research/`. Within-channel associations that hold up there: duration (about +30% per doubling below 200k, +15% at 200k+), staying on the channel's usual topic and thumbnail look, a slower cadence on channels of 200k+, and channel-uploaded captions (+29%, with a real reverse-causality risk). Big-face thumbnails, surprise expressions, arrows, saturation and publish hour do not hold up inside the channel. The public dataset has no CTR, impressions, retention, watch time, traffic source, subscribers gained per video, or transcripts.

**Install**
- Claude Code: copy the folder to `~/.claude/skills/youtube-seo/` (personal) or `.claude/skills/youtube-seo/` (project).
- Claude.ai / Claude Desktop: zip the folder and upload it under Settings > Capabilities > Skills.
- Cursor: copy to `.cursor/skills/youtube-seo/` in your project, or paste `SKILL.md` into a rule under `.cursor/rules/`.
- Other agents: any agent that reads SKILL.md (`name` + `description` frontmatter). Without skill support, use `SKILL.md` as a system prompt and keep the other files available.

**Evidence levels.** OFICIAL (YouTube official docs and channels), OFICIAL-LIAISON (YouTube Creator Liaison statements), PAPER (Google/YouTube research papers, historical context), PRATICANTE (named practitioners, tools, press, studies), ESTUDO-PRÓPRIO (this repo's own study; correlation, not causation), INFERÊNCIA (explicit inference). Official sources win when they conflict with practitioners.

### YouTube SEO Intelligence

Local CLI (`youtube-seo`) with five modules plus an offline idea advisor. The default path costs nothing: public autocomplete, the YouTube Data API v3 only when `YOUTUBE_API_KEY` is set (free quota), and local OpenCV/OCR if you install the `vision` extra. Gemini is off unless you pass `--gemini` and set `GEMINI_API_KEY`. `advise` (alias `idea`) never calls the network. No `.env` is committed. Reports are written in Portuguese; this section is the English map. The `estudo-10k/` scripts are unchanged.

**Install and test**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
pip install -e ".[vision]"   # optional local thumbnails
```

**Commands.** `keywords`, `serp`, `competitors`, `titles`, `gaps` and `pipeline` each write `<module>.json` and `<module>.md`. Cache and the daily quota ledger live in `~/.cache/youtube-seo/`. `advise` prints to the terminal and does not open the cache or the quota ledger.

```bash
export YOUTUBE_API_KEY=...
youtube-seo keywords "sourdough" --hl en --gl US -o out/bread
youtube-seo serp "sourdough" "sourdough starter" --hl en --gl US -o out/bread
youtube-seo competitors UCxxxxxxxxxxxxxxxxxxxxxx -o out/channels
youtube-seo titles --termo "sourdough" --hl en --gl US -o out/titles
youtube-seo titles --imagens ./thumbs -o out/thumbs
youtube-seo gaps "sourdough" --hl en --gl US --max-serp 3 -o out/gaps
youtube-seo pipeline "sourdough" --hl en --gl US --canais UCxxxxxxxxxxxxxxxxxxxxxx -o out/all
youtube-seo advise --title "5 cheap phones that are actually worth it in 2026" --niche tech --lang en \
  --tier pequeno --duration-min 18 --thumb-notes "dark background, product in frame, no face" --days-since-last 5
youtube-seo idea --title "50 Geography Facts You Won't Believe" --niche educacao --lang en \
  --subscribers 19500 --duration-min 21 --format json
```

`advise` / `idea` prints a markdown opinion to the terminal (`--format json` for the raw object). It does not write the `-o` folder and it does not spend quota. Pass `--tier` (`pequeno`, `emergente`, `medio`, `grande`, `gigante`) or `--subscribers`. Niches: `culinaria`, `documentario`, `educacao`, `entretenimento`, `esportes`, `financas`, `games`, `historias`, `infantil`, `lifestyle`, `tech`. The bundled base is `youtube_seo/advisor/knowledge_base.json` (packaged via `[tool.setuptools.package-data]`). `scripts/research/build_knowledge_base.py` rebuilds it from the lab parquets, which are not in this repository. The opinion states its confidence and the hard limits: no CTR, impressions, retention, traffic source, or transcripts, and no view prediction. Full write-up: `docs/research/RELATORIO_FINAL_CONSOLIDADO.md`.

`--letras aeiou` expands autocomplete; `--letras abcdefghijklmnopqrstuvwxyz` walks the alphabet. `--sem-prefixos` skips how-to/best/vs prefixes. `--paginas 2` requests another search page (another 100 units per term). `--sem-cache` bypasses the cache.

**Free quota.** Default daily cap: **10,000** units per Google project.

| Call | Units | Used by |
|---|---|---|
| `search.list` | 100 per page | keywords, serp, gaps, pipeline |
| `videos.list` | 1 per batch of up to 50 ids | video details and competitors |
| `channels.list` | 1 per batch of up to 50 channels | size and the uploads playlist |
| `playlistItems.list` | 1 per page | competitors (`UULF`, then `UU`) |
| autocomplete | 0 | public suggest endpoint, not the Data API |

One cold SERP is about **102** units. Ten uncached terms are 1,000 units of `search.list` alone. Every report shows the estimate, units saved by cache, the UTC-day total, and a hard stop when fewer than 100 units remain. Competitors do not call `search.list` (1 + 1 + 1 units per channel for up to 50 videos). Channel size uses the study cuts: small &lt; 200k subscribers, medium 200k–2M, large 2–20M, giant ≥ 20M.

**Output shape** (illustrative, not a live pull). Demand is estimated because YouTube does not publish search volume.

- Keyword Research: suggestion, source (`autocomplete`, `prefixo`, `letra`), inferred intent, related tags and channels.
- SERP Analyzer: title patterns, duration, age, captions, chapters, subscriber median, channel HHI, and the study label (strong, probable, weak, no confirmed effect).
- Competitor Intelligence: posts per week, recurring title terms, caption rate, and each video versus that channel's own median (above = 1.5× or more).
- Title & Thumbnail Intelligence: each title trait next to the `estudo-10k/` finding. Local vision runs only with an image. Gemini stays off and is never a "strong signal" — thumbnail traits in the study did not survive multiple-testing correction.
- Content Gap Analysis: the report opens with the estimate warning. Class `oportunidade` means apparent demand and relatively weak ranking channels. A term without its own SERP is `incompleta`, so the tool does not spend 100 units on it. Points (only when supply was measured) = apparent demand (high 60, medium 40, seed 45, low 20) + competition (low 40, medium 20, high 0).

```markdown
> A demanda é estimada. O YouTube não publica volume oficial de buscas.

| Termo | Demanda aparente | Concorrência | Classe | Pontos |
| --- | --- | --- | --- | --- |
| pao caseiro | semente | baixa | oportunidade | 85 |
| pao caseiro facil | aparente_alta | nao_medida | incompleta | — |
```

## License

MIT, see `LICENSE`. Third-party inspirations in `ATTRIBUTIONS.md`. Not affiliated with Google or YouTube.

## Auditoria e errata (v2.5)

O laboratório de `docs/research/` passou por auditoria sênior. A errata formal está em `docs/research/ERRATA_E_LIMITES.md` (17 itens, com o que foi corrigido no motor e o que segue pendente de reprocessamento dos dados brutos). O ranking vigente é `docs/research/data/ranking_alavancas_revisado.csv`. O `youtube-seo advise` só trata como recomendação o que tem q < 0,05 com IC válido, e mostra o restante como hipótese para teste A/B.
