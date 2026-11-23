# Histórico do sistema de descoberta do YouTube (2005-2026)

Arquivo de referência da skill youtube-seo. IDs (Fxx) apontam para FONTES.md. Datas em dia/mês/ano. Itens marcados [PRATICANTE] vêm de imprensa e ainda pedem confirmação em fonte oficial. Revisado na v2.1 (23/11/2026): itens que vinham só da PPC Land foram checados em fonte primária; ver VERIFICACAO_LACUNAS.md.

## Por que a história importa

Muita "regra" que circula (views a qualquer custo, tags, postar todo dia no mesmo horário, primeiras 2 horas decidem tudo) é resíduo de fases antigas do sistema. Saber quando cada mudança aconteceu ajuda a descartar conselho vencido. [INFERÊNCIA]

## Linha do tempo

| Quando | O que mudou | Nível | Fonte |
|---|---|---|---|
| 2008 | Recomendações ranqueadas sobretudo por popularidade (página "Trending"). | [OFICIAL] | F35 |
| 2010 | Paper descreve recomendações por co-visitação (vídeos assistidos na mesma sessão). | [PAPER] | F71 |
| 2011 | YouTube percebe que clique não significa satisfação; era de thumbnails enganosas ("Reply Girls"). Classificadores para conteúdo apelativo. | [OFICIAL] + [PRATICANTE] (Mark Bergen) | F35, F94 |
| 03/2012 | Sugeridos passam a otimizar tempo assistido em vez de cliques. Views caem 20% de imediato; watch time sobe. | [OFICIAL] | F35, F36 |
| 10/2012 | Busca também passa a premiar vídeos que mantêm a pessoa assistindo ("less clicking, more watching"). | [OFICIAL] | F36, F95, F104 |
| 2015 | Rebaixamento de conteúdo sensacionalista/tabloide na home. Resultado relatado: watch time subiu 0,5% em 2,5 meses. | [OFICIAL] | F35 |
| 2016 | Paper de deep learning: geração de candidatos + ranqueamento; objetivo = watch time esperado, não clique. | [PAPER] | F68 |
| 2016-2017 | 2016: previsão de menores em situação de risco (removidos das recomendações). 2017: avaliação de fairness do ML. Em algum momento (o post não data): pesquisas de satisfação 1 a 5 estrelas viram sinal ("valued watchtime"). | [OFICIAL] | F35 |
| 2018-2019 | Aprendizado por reforço (REINFORCE) com correção off-policy em produção; ranqueador multitarefa (engajamento + satisfação). | [PAPER] | F69, F70 |
| 25/01/2019 | Redução de recomendação de conteúdo limítrofe (borderline) e desinformação nociva. Em 2021 o YouTube disse que o consumo de borderline vindo de recomendações estava "significativamente abaixo de 1%". | [OFICIAL] | F37, F35 |
| 15/09/2021 | Post de Cristos Goodrow: sistema usa mais de 80 bilhões de sinais; não existe fórmula fixa; peso varia por pessoa. | [OFICIAL] | F35 |
| 2020-2022 | Lançamento e escala dos Shorts; Think with Google: quem publica long-form e Shorts tem mais watch time e inscritos. | [OFICIAL] | F47 |
| 06/2023 | Teste de thumbnails ("Test & Compare") anunciado. | [PRATICANTE] (imprensa) | F96 |
| 30/07/2024 | Caso oficial de multi-idioma: faixas dubladas do canal Jamie Oliver com "three times more views". | [OFICIAL] | F125 |
| 18/09/2024 | Hype lançado para canais menores (< 500 mil inscritos). | [OFICIAL] | F41, F14 |
| 15/10/2024 | Shorts podem ter até 3 minutos (vertical/quadrado). Short > 1 min com qualquer reivindicação de copyright é bloqueado (sem penalidade ao canal). | [OFICIAL] | F39, F26, F124 |
| 31/03/2025 | Views de Shorts passam a contar todo início/replay; YPP continua com engaged views. | [OFICIAL] | F25 |
| 07/2025 | Teste de títulos chega a uma parcela de creators. Segmentos novos/casuais/regulares em Analytics. | [PRATICANTE] (imprensa) / [OFICIAL] para os segmentos (F15, F22) | F96, F73 |
| 26/08/2025 | Hype global. | [OFICIAL] | F42 |
| 10/09/2025 | Multi-language audio expandido; mais de 25% do watch time de idiomas não principais para quem usa. | [OFICIAL] | F40, F12 |
| 06/10/2025 | Liaison: A/B de títulos disponível; sem impressões suficientes, trabalhar o básico. | [OFICIAL-LIAISON] | F58, F59 |
| 29/10/2025 | Thumbnail até 50 MB; upscaling para TV. | [OFICIAL-LIAISON] | F62 |
| 04/12/2025 | Title A/B global para quem tem recursos avançados. | [OFICIAL] | F54 |
| 12/2025 | Home com prateleiras de Shorts mais presentes (queixas de creators de long-form). SEM FONTE PRIMÁRIA após busca (v2.1). | [PRATICANTE] (PPC Land) | F73 |
| 08/01/2026 | Filtros de busca: "Sort By" vira "Prioritize" (Relevância, Popularidade); "View count" vira "Popularity" (views + watch time); removidos "Última hora" e "Classificação"; novo filtro de Shorts. Ordenar por data deixou de aparecer como ordenação; recentes só via filtro de data (Hoje/Semana/Mês/Ano). | [OFICIAL] (parcial: a remoção da ordenação por data não é dita literalmente) | F118, F133 |
| 04/02/2026 | Auto-dubbing: 27 idiomas; expressivo em 8 (inclui português); AVD do dub ≈ 75% do original. | [OFICIAL] | F53 |
| 21/04/2026 | Fim do push para inscritos "Todas" inativos (~1 mês sem assistir + ignoraram notificações); seguem na caixa de entrada. Teste começou em 26/03/2025. Limite de 3 notificações de vídeo por 24h. | [OFICIAL] | F119 |
| 15/05/2026 | Unique Reach (alcance único). | [OFICIAL-LIAISON] | F64 |
| 25/06/2026 | Shorts: coração substitui o like; dislike aposentado; feedback negativo via "Não tenho interesse" e "Não recomendar o canal". | [OFICIAL] | F120 |
| 07/2026 | Nova experiência da aba Tendências; stickers de Shorts; guia "Shorts para long-form". | [OFICIAL] | F11, F51, F56 |
| 29/07/2026 | Estudo de collabs (+30% quando o parceiro é ~30x maior; +25% entre pares). | [OFICIAL] | F52 |
| 10/08/2026 | Novos requisitos do YPP a partir de 01/02/2027: 1.000 inscritos + 8.000 horas qualificadas (365 dias) ou 20 mi de views qualificadas de Shorts (90 dias); receita de Shorts exige 10 mi em 90 dias. Quem já está no YPP não sai. | [OFICIAL] | F121, F122 |
| 24/08/2026 | Views contadas a partir do primeiro frame em todos os formatos (inclui autoplay). Engaged views seguem para CTR, AVD, retenção, recomendação e YPP. | [OFICIAL] | F38, F63, F24 |
| 01/09/2026 | Todd Beaupré: sistema "puxa" por espectador; sem teste só com inscritos; nenhuma métrica sozinha; evergreen cresce depois. | [OFICIAL] | F48 |
| 23/09/2026 | Made On YouTube 2026: Video A/B, dynamic thumbnails, feedback em rascunho, thumbnails geradas, feeds por prompt, auto-dub em live. | [OFICIAL] | F43, F50 |
| 01/10/2026 | Shorts priorizam conteúdo original; re-uploads/agregadores perdem alcance. | [OFICIAL] | F34, F55 |
| 16/10/2026 | Ask YouTube conta como busca; pilotos de bônus de Shorts (inclui BR). | [OFICIAL] | F55 |
| 27/10/2026 | Chucky (MrBeast): pacote = título + thumbnail + ideia + intro. | [OFICIAL] | F49 |
| 13/11/2026 | Analytics vira Insights; aba Research substitui Tendências no desktop (outliers). | [OFICIAL] | F57, F65 |
| 16/11/2026 | Co-views (pessoas extras na TV) entram na contagem pública; mais de 1 bilhão de horas/dia na TV. | [OFICIAL-LIAISON] | F66, F22, F24 |
| 13-14/11/2026 | Relatos de Shorts com zero impressões no feed. Busca na v2.1: nenhum Known Issue; TeamYouTube responde com texto padrão ("fluctuating Shorts views", personalização, originalidade). SEM FONTE PRIMÁRIA de incidente. | [PRATICANTE] (relatos) / [OFICIAL] para as respostas | F102, F130, F131 |

## Leituras que mudaram com o tempo

- **Views não são mais comparáveis entre períodos.** Paddy Galloway mediu em uma dúzia de canais aumento médio de 30-50% nas views públicas (até 100%+) após 24/08/2026 [PRATICANTE] F128. Mar/2025 (Shorts), 24/08/2026 (todos os formatos) e 16/11/2026 (co-views na TV) inflaram a contagem pública. Para comparar antes e depois, use engaged views e watch time. [OFICIAL] F24, F25, F38, F66
- **"Primeiras horas decidem" ficou fraco.** Todd diz que o sistema aprende por público e que evergreen pode crescer um mês ou mais depois. [OFICIAL] F48
- **Teste com inscritos primeiro** não é o modelo descrito pelo YouTube. [OFICIAL] F48 (ver DIVERGENCIAS.md)
- **CTR deixou de ser alvo de teste.** Os testes oficiais escolhem por watch time. [OFICIAL] F27, F54
