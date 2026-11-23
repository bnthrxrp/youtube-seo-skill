# Levantamento: skills, prompts e agent skills de SEO de YouTube no GitHub

Feito em 23/11/2026 (America/Sao_Paulo). Estrelas e licença lidas pela API do GitHub (`gh api repos/OWNER/REPO` e `/license`) nesse dia; estrelas mudam.

Política aplicada: incorporar só IDEIAS e ESTRUTURA. Texto literal só de repos MIT/Apache-2.0/BSD/CC0, com atribuição. Resultado: **nenhum trecho literal foi copiado**. Todo o texto da skill é original; ideias de estrutura estão creditadas em ATTRIBUTIONS.md.

## Repos analisados

| Repo | ★ | Licença | O que tem de bom | O que incorporamos (ideia) | Problemas |
|---|---|---|---|---|---|
| [AgriciDaniel/claude-youtube](https://github.com/AgriciDaniel/claude-youtube) | 856 | MIT | Skill "roteadora" que manda cada pedido (auditoria, SEO, roteiro, thumbnail, Shorts, analytics) para uma sub-skill; 14 sub-skills; pasta de referências; templates por tipo de canal. | Índice no topo + "roteador de pedidos" (qual seção usar para cada tipo de pedido); separação corpo x arquivos de referência. | Muitos números sem fonte oficial: "testing cascade de 4 camadas", "AVD < 40% despriorizado", "50+ respostas em 2h = +15-20% alcance", pesos dos sinais ranqueados, CTR por fonte (Focus Digital), "12+/mês = 8x". Contradizem F35/F48. Registrados em DIVERGENCIAS.md. Exceção: o "máximo de 3 notificações por 24h" foi CONFIRMADO em fonte oficial (F119, D19). |
| [sergebulaev/youtube-skills](https://github.com/sergebulaev/youtube-skills) | 106 | MIT | SKILL.md enxuto + references (heurísticas do algoritmo, fórmulas de gancho, princípios de thumbnail, voz); arquivo que manda tratar comentários/transcrições de terceiros como conteúdo não confiável. | Regra de segurança: conteúdo de terceiros (comentários, transcrições, páginas) é dado, não instrução. Moldura "valor da impressão ≈ chance de clique × chance de assistir satisfeito" (como heurística, reescrita). | Tabela de "peso dos sinais" sem fonte oficial. |
| [adityaarsharma/youtube-marketing-skills](https://github.com/adityaarsharma/youtube-marketing-skills) | 88 | MIT | Arquivo de benchmarks de analytics separado do corpo. | Ideia de manter benchmarks num bloco próprio e rotulado. | Benchmarks de agência (Focus Digital, dez/2025) sem método aberto. Não usamos os números. |
| [deeployCO/youtube-seo-skills](https://github.com/deeployCO/youtube-seo-skills) | 28 | MIT | 8 sub-skills com tabela de roteamento; separação por objetivo (busca, browse, sugeridos). | Organização "playbook por superfície" (busca, Home/Sugeridos, Shorts). | Atribui o paper REINFORCE a Covington 2016 (é Chen et al. 2019). |
| [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills) | ~50.200 | MIT | Coletânea grande; contém uma skill youtube-seo genérica. | Nada além de confirmar o formato SKILL.md com frontmatter name/description. | Conteúdo genérico, sem níveis de evidência. |
| [kostja94/marketing-skills](https://github.com/kostja94/marketing-skills) | 1.135 | MIT | Suíte de marketing com skills de vídeo. | Formato de "template de entrega" no final. | Genérico. |
| [Illyism/seo-skills](https://github.com/Illyism/seo-skills) | 2.025 | sem licença | 30 skills de SEO web (técnico, SERP, backlinks, GEO). | Nada (sem licença = nada copiado). | Foco em SEO de site, não de YouTube. |
| [charlesdove977/ez-thumb](https://github.com/charlesdove977/ez-thumb) | 8 | MIT | Skill de pacote (título + thumbnail) calibrada contra concorrentes reais do nicho (vidIQ + Apify), lendo thumbnails com visão e sinalizando views compradas. | Ideia de comparar o pacote com evidência do nicho (outliers de concorrentes), não com regras genéricas. | Depende de ferramentas pagas. |
| [JxLeoo/framewise-method](https://github.com/JxLeoo/framewise-method) | 1 | MIT | Rubrica explicável para diagnosticar pacote fraco antes de publicar. | Ideia de rubrica de pré-publicação com critério explícito. | Pouca adoção. |
| [manoharkharvi43/thumbnail-strategist](https://github.com/manoharkharvi43/thumbnail-strategist) | 1 | MIT | Estratégia de thumbnail antes do design: brief, motivos de clique, conceitos pontuados. | Brief de thumbnail em campos fixos. | Pouca adoção. |
| [shashu10/youtube-growth-skills](https://github.com/shashu10/youtube-growth-skills) | 1 | MIT | Transforma analytics do Studio em diagnóstico: prompts para o Ask Studio, separa formato x tema x distribuição, sinaliza casos n=1. | Diagnóstico em funil separando formato, tema e distribuição; alerta contra conclusão com um vídeo só. | Pouca adoção. |
| [improvired-hash/youtube-distribution-skill](https://github.com/improvired-hash/youtube-distribution-skill) | 1 | MIT | Pacote, Shorts, auditoria, distribuição e atribuição para marcas (foco Índia). | Bloco de canais de marca/empresa (views baixas podem bastar). | Pouca adoção. |
| [nayakanamikn-dot/youtube-research-and-packaging](https://github.com/nayakanamikn-dot/youtube-research-and-packaging) | 1 | sem licença | Pesquisa + pacote (títulos, thumbnails, descrição, tags, plano de teste). | Nada (sem licença). | — |
| [vid-io/vidiq-mcp](https://github.com/vid-io/vidiq-mcp) | 11 | Apache-2.0 | MCP oficial da vidIQ (keywords, outliers). | Citado como ferramenta opcional de pesquisa de palavra-chave. | Exige conta vidIQ. |
| [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | ~80.100 | sem licença na API | Lista de skills. | Só descoberta. | — |
| [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) | ~15.900 | — | Lista de skills. | Só descoberta. | — |
| [BehiSecc/awesome-claude-skills](https://github.com/BehiSecc/awesome-claude-skills) | ~10.500 | — | Lista de skills. | Só descoberta. | — |
| [karanb192/awesome-claude-skills](https://github.com/karanb192/awesome-claude-skills) | 606 | MIT | Lista de skills. | Só descoberta. | — |

Achados também via busca de código (arquivos soltos, não analisados a fundo): BenAIOS/benai-skills (geração de títulos), classroomio (youtube-seo), komunite/kalfa, OpenClaudia (youtube-analytics), leamsigc (youtube-title), sandeco/prompts (tags de YouTube, PT-BR).

## Padrão do mercado de skills (síntese)

1. Quase todas misturam fato oficial e folclore sem rótulo. A maior lacuna do mercado é rastreabilidade de evidência. [INFERÊNCIA]
2. Quase todas repetem a "cascata com inscritos primeiro" e pesos fixos de sinais, contrariando o YouTube (F48).
3. Poucas cobrem 2026: views a partir do primeiro frame, co-views, Video A/B, dynamic thumbnails, originalidade em Shorts, Ask YouTube, aba Research.
4. Boas ideias de estrutura: roteador no topo, referências separadas, template de entrega, guarda contra conteúdo não confiável.

## O que a nossa skill faz diferente

- Rótulo de evidência em toda afirmação, com ID de fonte.
- Arquivo de divergências explícito.
- Cobertura das mudanças de 2025-2026.
- PT-BR, com exemplos para mercado brasileiro, sem perder a parte multilíngue.
