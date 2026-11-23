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
- `estudo-10k/`: estudo próprio com 17.882 vídeos longos de 203 canais (PT e EN, 11 nichos): `RESULTADOS.md` em linguagem simples, gráficos, tabelas, dataset (`dados/dataset.parquet`), lista de canais e scripts reproduzíveis (exigem sua própria chave da YouTube Data API em `YOUTUBE_API_KEY`).
- `youtube_seo/`: sistema **YouTube SEO Intelligence** (CLI `youtube-seo`). Cinco módulos, cota gratuita e cache local. Ver a seção abaixo. Os scripts de `estudo-10k/` não foram alterados.

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

**CLI.** Cada comando grava `<modulo>.json` e `<modulo>.md` em `-o` (padrão `saida-youtube-seo/`). Cache e acumulado de cota ficam em `~/.cache/youtube-seo/` (`--cache-dir` e `--quota-file` mudam o lugar).

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

**What it is.** An operational guide for titles, thumbnails, hooks, descriptions, tags, chapters, keyword research, Shorts, multi-language audio, end screens, cards, posts, live streams, A/B tests, view-drop diagnosis and publishing checklists. The skill is written in Brazilian Portuguese. Research reviewed November 2026 (133 sources; gaps checked against primary sources in v2.1). v2.2 adds an original observational study of 17,882 long-form videos from 203 channels in `estudo-10k/` (each video compared with its own channel's baseline; mixed-effects and within-channel models, Benjamini-Hochberg correction, out-of-sample validation), with thumbnails also read by a vision model (expression, gaze, arrows, style, background). Headline: all 35 metadata and thumbnail traits together explain about 1.5% of within-channel variation; channel-uploaded captions (+28%) and longer duration (+14% per doubling) are the only robust correlates.

**Install**
- Claude Code: copy the folder to `~/.claude/skills/youtube-seo/` (personal) or `.claude/skills/youtube-seo/` (project).
- Claude.ai / Claude Desktop: zip the folder and upload it under Settings > Capabilities > Skills.
- Cursor: copy to `.cursor/skills/youtube-seo/` in your project, or paste `SKILL.md` into a rule under `.cursor/rules/`.
- Other agents: any agent that reads SKILL.md (`name` + `description` frontmatter). Without skill support, use `SKILL.md` as a system prompt and keep the other files available.

**Evidence levels.** OFICIAL (YouTube official docs and channels), OFICIAL-LIAISON (YouTube Creator Liaison statements), PAPER (Google/YouTube research papers, historical context), PRATICANTE (named practitioners, tools, press, studies), ESTUDO-PRÓPRIO (this repo's own study; correlation, not causation), INFERÊNCIA (explicit inference). Official sources win when they conflict with practitioners.

### YouTube SEO Intelligence

Local CLI (`youtube-seo`) with five modules. The default path costs nothing: public autocomplete, the YouTube Data API v3 only when `YOUTUBE_API_KEY` is set (free quota), and local OpenCV/OCR if you install the `vision` extra. Gemini is off unless you pass `--gemini` and set `GEMINI_API_KEY`. No `.env` is committed. Reports are written in Portuguese; this section is the English map. The `estudo-10k/` scripts are unchanged.

**Install and test**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
pip install -e ".[vision]"   # optional local thumbnails
```

**Commands.** Each one writes `<module>.json` and `<module>.md`. Cache and the daily quota ledger live in `~/.cache/youtube-seo/`.

```bash
export YOUTUBE_API_KEY=...
youtube-seo keywords "sourdough" --hl en --gl US -o out/bread
youtube-seo serp "sourdough" "sourdough starter" --hl en --gl US -o out/bread
youtube-seo competitors UCxxxxxxxxxxxxxxxxxxxxxx -o out/channels
youtube-seo titles --termo "sourdough" --hl en --gl US -o out/titles
youtube-seo titles --imagens ./thumbs -o out/thumbs
youtube-seo gaps "sourdough" --hl en --gl US --max-serp 3 -o out/gaps
youtube-seo pipeline "sourdough" --hl en --gl US --canais UCxxxxxxxxxxxxxxxxxxxxxx -o out/all
```

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
