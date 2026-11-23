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
- `[INFERÊNCIA]`: dedução explícita.

## English

**What it is.** An operational guide for titles, thumbnails, hooks, descriptions, tags, chapters, keyword research, Shorts, multi-language audio, end screens, cards, posts, live streams, A/B tests, view-drop diagnosis and publishing checklists. The skill is written in Brazilian Portuguese. Research reviewed November 2026 (133 sources; gaps checked against primary sources in v2.1).

**Install**
- Claude Code: copy the folder to `~/.claude/skills/youtube-seo/` (personal) or `.claude/skills/youtube-seo/` (project).
- Claude.ai / Claude Desktop: zip the folder and upload it under Settings > Capabilities > Skills.
- Cursor: copy to `.cursor/skills/youtube-seo/` in your project, or paste `SKILL.md` into a rule under `.cursor/rules/`.
- Other agents: any agent that reads SKILL.md (`name` + `description` frontmatter). Without skill support, use `SKILL.md` as a system prompt and keep the other files available.

**Evidence levels.** OFICIAL (YouTube official docs and channels), OFICIAL-LIAISON (YouTube Creator Liaison statements), PAPER (Google/YouTube research papers, historical context), PRATICANTE (named practitioners, tools, press, studies), INFERÊNCIA (explicit inference). Official sources win when they conflict with practitioners.

## License

MIT, see `LICENSE`. Third-party inspirations in `ATTRIBUTIONS.md`. Not affiliated with Google or YouTube.
