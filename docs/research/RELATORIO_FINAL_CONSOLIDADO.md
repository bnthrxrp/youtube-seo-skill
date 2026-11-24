> **AVISO DE AUDITORIA E GOVERNANÇA ESTATÍSTICA (ERRATA ATIVA):**
> Este relatório contém estimativas geradas antes do fechamento da auditoria metodológica sênior. Ao consultar este material, aplique obrigatoriamente as seguintes travas:
> 1. **Teto preditivo:** Metadados estáticos (título, capa e horário) explicam menos de 2,5% da variância intra-canal ($R^2 \le 0,025$). Nenhum coeficiente deve ser lido como garantia causal de alcance.
> 2. **Recomendações firmes vs. Hipóteses A/B:** Como **recomendação prescritiva firme** (`faixa = validada` em `docs/research/data/ranking_alavancas_revisado.csv`), valem exclusivamente itens com $q < 0,05$, IC 95% limpo sem cruzar zero e penalização de endogeneidade. Itens na zona $0,05 \le q < 0,15$ (ou rebaixados por limites da base bruta) pertencem à faixa `hipotese_ab`: **hipótese A/B não é recomendação**, servindo apenas para experimentação controlada no *Testar e Comparar* do YouTube Studio. Ignore integralmente clusters visuais (`HDB-*`, `KM12-*`), ângulos de vídeo e qualquer item com $q \ge 0,15$ (`faixa = removida`).
> 3. **Reconciliações e pendências:** Em caso de conflito sobre alinhamento Capa × Título ou Momentum pós-hit, ou para verificar variáveis marcadas como `PENDENTE DE REPROCESSAMENTO` (vazamento temporal residual, filtro de canais pequenos e denominador de idade), prevalece o disposto em `docs/research/ERRATA_E_LIMITES.md`.

---

# Relatório Final Consolidado: o que move views em vídeos longos do YouTube

Laboratório de Data Science de YouTube. **26.194 vídeos longos de 310 canais**: 203 canais de 200 mil inscritos ou mais (17.882 vídeos) e 107 canais de 5 mil a 200 mil inscritos (8.312 vídeos), 11 nichos, português e inglês. Snapshot de 23/11/2026 (horário de Brasília).

> **A base não possui CTR, impressões, retenção, tempo de exibição, origem de tráfego, inscritos ganhos por vídeo nem transcrições.** Todo "desempenho" aqui é views do vídeo relativas ao normal do próprio canal (múltiplo sobre a mediana do canal, com e sem ajuste de idade). Tudo é associação observacional controlada, não causa.

## 1. Sumário executivo

**A pergunta certa não é "o que faz um vídeo viralizar", é "o que faz um vídeo render mais que o normal do próprio canal".** Quando se compara cada vídeo com os outros vídeos do mesmo canal, a maior parte das "regras de YouTube" encolhe para perto de zero. O canal (nicho, público, tamanho, volatilidade) é o grande confundidor de quase todas as análises amadoras.

**O que realmente move views dentro do canal (efeitos controlados, em ordem de prioridade):**

1. **Duração.** Dobrar a duração soma +30,2% nos canais de 5k a 200k e +14,9% nos 200k+. Contra 8 a 20 min, a faixa de 20 a 45 min rende +25,1% e vídeos de menos de 5 min rendem −33,5%. O ótimo médio fica em 34 min (IC 28 a 43), com retorno decrescente a partir de cerca de 24 min. Tech é a exceção: cai depois de cerca de 30 min. Nos pequenos, duração é o único traço que separa breakouts de 10x dentro do canal.
2. **Consistência temática e visual.** Fugir do assunto habitual custa cerca de −14,8% por desvio padrão de novidade nos pequenos e −10,5% nos 200k+; fugir do visual habitual da capa custa −10,9% e −7,4%. Novidade não aumenta a chance de breakout.
3. **Cadência.** Nos 200k+, publicar com menos de 2 dias do vídeo anterior se associa a −8,8% (q = 0,003); lançar menos de 3 dias depois de um fracasso, a −17,8%. Dobrar o volume semanal, −9,6%.
4. **Legenda enviada pelo canal** (+28,6% nos 200k+, resiste ao controle de duração), com risco real de causalidade reversa.
5. **Filtros finos de título:** vocabulário abstrato (−15,4%), marca ou produto famoso em tech e games (+25,5%), 1ª pessoa em inglês (−11,0%), afirmação contraintuitiva em inglês (+14,2%) e texto da capa alinhado ao título (+4,1% por desvio padrão de similaridade).

**O que é mito ou ruído dentro do canal:** rosto grande na capa (+30,0% entre canais, −2,5% dentro do canal), cara de surpresa, setas e círculos, saturação e contraste altos, olhar para a câmera, números na capa, comprimento ideal de título, perguntas, listas, tutoriais e mistério como ganchos, "arquétipo vencedor", horário e dia de publicação, capítulos por si só, "momentum" depois de um hit nos canais 200k+ e imitar a cara de capa de canal grande.

**O teto do que dá para prever é baixo, e isso é um achado, não uma falha.** O título explica no máximo R² 0,018 fora da amostra; os embeddings da capa, 0,025 dentro do canal; o melhor modelo com 68 traços pré-publicação, 0,016 em canais nunca vistos, e acerta o top 5% do próprio canal com AUC 0,58 (0,5 é moeda). Um único número do canal (volatilidade histórica) prevê o top 5% global melhor que todos os traços do vídeo (AUC 0,744). "Viral" é sobretudo traço do canal.

**O porte muda as regras, mas a ruptura não está em 200 mil inscritos.** Pequenos (5k a 50k), emergentes (50k a 200k) e médios (200k a 2M) formam um bloco parecido em concentração, volatilidade e anomalias (diferenças com q ≥ 0,35). A ruptura estrutural fica **entre médio e grande** (por volta de 2 milhões): grandes e gigantes concentram menos views no top 10% (−8,9 e −9,3 p.p. contra médios, q ≤ 0,006) e produzem menos da metade das anomalias de 10x.

**Como usar:** o motor de consulta (`youtube_seo/advisor/idea_advisor.py`) aplica tudo isso a uma ideia concreta (título, nicho, idioma, porte, duração, notas da capa, intervalo) e devolve diagnóstico, faixa de duração, leitura do título e da capa, cadência, exemplos reais parecidos e checklist, sem API e sem rede.

## 2. Ranking Geral de Alavancas

Todas as linhas abaixo vêm de modelos com **efeito fixo de canal** (só compara vídeos do mesmo canal), erro padrão agrupado por canal, IC 95% (analítico ou bootstrap por canal) e correção de Benjamini-Hochberg (q) dentro de cada bateria. Notas de 0 a 10: **Impacto** (tamanho do efeito e alcance), **Confiança** (rigor, replicação e risco de causalidade reversa), **Aplicabilidade** (quanto vira regra prática) e **Facilidade** (custo de implementar). Prioridade = 0,35 × Impacto + 0,35 × Confiança + 0,15 × Aplicabilidade + 0,15 × Facilidade. Arquivo: `docs/research/data/ranking_alavancas.csv`.

| # | Alavanca | Porte | Efeito dentro do canal | IC 95% | q (BH) | Impacto | Confiança | Aplicabilidade | Facilidade | Prioridade | Fonte | Observação |
|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---|---|
| 1 | Dobrar a duração | 5k a 200k | +30,2% | +19,7% a +41,6% | < 0,001 | 9 | 7 | 8 | 4 | 7,40 | 2D peq_06 | único traço ligado a breakout de 10x nos pequenos |
| 2 | Trocar vocabulário abstrato por termos concretos | 200k+ | −15,4% com abstrato | −22,9% a −7,9% | 0,005 | 6 | 7 | 9 | 10 | 7,40 | 2C b1_tracos_titulo_efeitos.csv |  |
| 3 | Ficar no tema habitual do canal (cada +1 DP de novidade) | 5k a 200k | −14,8% | −18,4% a −11,1% | p < 0,001 | 7 | 7 | 8 | 8 | 7,30 | 2D peq_05_novidade_tematica.csv | 200k+ −10,5% (p < 0,001); novidade não aumenta breakout |
| 4 | Não publicar com menos de 2 dias do vídeo anterior | 200k+ | −8,8% | −13,5% a −3,9% | 0,003 | 6 | 7 | 9 | 9 | 7,25 | 2D peq_04e (replica 2A F) | nos pequenos −4,4% (q = 0,59), inconclusivo |
| 5 | Duração de 20 a 45 min (contra 8 a 20 min do mesmo canal) | 200k+ | +25,1% | +17,6% a +33,0% | < 0,001 | 8 | 7 | 8 | 4 | 7,05 | 2A E_faixas_duracao_vs_8a20min.csv | ótimo médio 34 min; tech cai depois de cerca de 30 min |
| 6 | Evitar menos de 5 min como formato principal | 200k+ | −33,5% | −45,7% a −18,6% | 0,001 | 7 | 7 | 8 | 6 | 7,00 | 2A E_faixas_duracao_vs_8a20min.csv |  |
| 7 | Manter o padrão visual próprio da capa (cada +1 DP de desvio) | 5k a 200k | −10,9% | −15,3% a −6,4% | < 0,001 | 6 | 7 | 8 | 8 | 6,95 | 2D peq_05b_visual_embeddings.csv | 200k+ −7,4% (q < 0,001) |
| 8 | Depois de um fracasso, esperar 3 dias ou mais | 200k+ | −17,8% se < 3 dias | −25,7% a −9,0% | p = 0,0002 | 6 | 6 | 9 | 9 | 6,90 | 2A F_pos_viral_x_intervalo.csv | interação 3 a 10 dias +24,2% (p = 0,002); teste conjunto p = 0,008 |
| 9 | Marca ou produto famoso no título (tech e games) | 200k+ | +25,5% | +11,6% a +40,1% | 0,014 | 6 | 6 | 8 | 10 | 6,90 | 2C b1_tracos_titulo_efeitos.csv | 35 canais |
| 10 | Tirar a 1ª pessoa do título (EN) | 200k+ | −11,0% com 1ª pessoa | −16,9% a −5,5% | 0,031 | 5 | 6 | 8 | 10 | 6,55 | 2C b1_tracos_titulo_efeitos.csv | em PT nulo |
| 11 | Legenda enviada pelo canal | 200k+ | +28,6% | +15,3% a +43,4% | < 0,001 | 7 | 5 | 7 | 8 | 6,45 | 2D peq_06 (replica 2A E) | resiste ao controle de duração (+27,9%, q = 0,024); risco de causalidade reversa; nos pequenos só 3,8% dos vídeos têm |
| 12 | Não dobrar o volume semanal | 200k+ | −9,6% por dobro | −14,1% a −4,9% | 0,003 | 5 | 6 | 8 | 8 | 6,25 | 2A F_volume_recente.csv | em y_passado −4,8% (q = 0,013) |
| 13 | Afirmação contraintuitiva como gancho (EN) | 200k+ | +14,2% | +3,8% a +23,7% | 0,015 | 5 | 6 | 7 | 9 | 6,25 | 2C b1_gancho_principal_vs_descritivo.csv | em PT não confirmado |
| 14 | Alinhar texto da capa ao título (+1 DP de similaridade) | 200k+ | +4,1% | +0,9% a +7,4% | 0,034 | 4 | 6 | 8 | 9 | 6,05 | 2C b2_redundancia_vs_complementaridade.csv | repetir o título não é punido |
| 15 | Palavra-chave no início do título (chance de top 5% do canal) | 200k+ | +1,3 p.p. | +0,6 p.p. a +2,1 p.p. | 0,023 | 3 | 6 | 9 | 10 | 6,00 | 2C b1_tracos_titulo_efeitos.csv |  |
| 16 | Capa: gadget em primeiro plano (KM12-07) | 200k+ | +28,8% | +7,9% a +53,7% | 0,088 | 6 | 4 | 6 | 8 | 5,60 | 2B padroes_stats.csv | 58 canais; confiança média no relatório 2B |
| 17 | Número no título | 5k a 200k | +15,4% | +4,5% a +27,3% | 0,023 | 5 | 3 | 8 | 10 | 5,50 | 2D peq_06 | diferença contra 200k+ não confirmada; testar A/B |
| 18 | Uma palavra em CAIXA ALTA no título | 5k a 200k | +15,3% | +5,6% a +25,9% | 0,020 | 5 | 3 | 8 | 10 | 5,50 | 2D peq_06 | diferença contra 200k+ não confirmada; testar A/B |
| 19 | Evitar colab/versus como aposta de alcance | 5k a 200k | −21,6% com colab | −33,2% a −7,8% | 0,020 | 5 | 3 | 7 | 9 | 5,20 | 2D peq_06 | confiança baixa |
| 20 | Depois de um hit, publicar o próximo no mesmo veio | 5k a 200k | +12,3% | +0,9% a +25,7% | bootstrap | 4 | 4 | 8 | 7 | 5,05 | 2D peq_04f_momentum.csv | nos 200k+ o pós-hit some com tendência quadrática (+2,4%, IC cruza zero) |
| 21 | Capítulos na descrição (controlando duração) | 200k+ | +9,6% | −2,8% a +23,7% | 0,399 | 2 | 6 | 6 | 9 | 5,05 | 2A E_estrutura_controlada_duracao.csv | nos pequenos +27,1% (q = 0,020), confiança baixa |
| 22 | Capa: cor dominante verde | 200k+ | +14,6% | +3,2% a +27,3% | 0,136 | 4 | 4 | 6 | 8 | 4,90 | 2B padroes_stats.csv | 131 canais; confiança média no relatório 2B |
| 23 | Emoji no título (PT) | 200k+ | +23,5% | +6,7% a +41,7% | 0,090 | 4 | 3 | 6 | 10 | 4,85 | 2C b1_tracos_titulo_efeitos.csv | concentrado em 45 canais |
| 24 | Capa: peso visual à esquerda | 200k+ | +6,4% | +2,2% a +10,9% | 0,056 | 3 | 4 | 6 | 8 | 4,55 | 2B padroes_stats.csv | 201 canais; confiança média no relatório 2B |
| 25 | Ângulo Choque, Terror e Listas para reduzir flops (canais médios) | 200k a 2M | −5,7 p.p. de flop | −9,8 p.p. a −2,1 p.p. | 0,088 | 4 | 4 | 5 | 6 | 4,45 | 2C g5_canais_medios_efeito_fixo.csv | 62 canais médios |
| 26 | Capa rara: azul dominante + visual carregado | 200k+ | +32,3% | +15,2% a +51,9% | 0,010 | 4 | 3 | 5 | 7 | 4,25 | 2B padroes_raros.csv | hipótese entre 1.802 candidatos; 66 canais |

Leitura rápida: as 8 primeiras linhas são as alavancas com sinal forte e replicado (duração, tema, visual, cadência e o filtro de vocabulário). Da linha 16 em diante, os sinais são fracos ou concentrados em poucos canais e devem entrar só como **testes A/B** no próprio canal.

## 3. Mapa Universal x Pequenos (5k a 200k) x Grandes (200k+)

### 3.1 Os 5 portes lado a lado

| Porte | Canais | Vídeos | Views medianas por vídeo | Top 10% das views (IC 95%) | Gini | DP de y | 10x por mil (IC 95%) | 10x robustas por mil |
|---|---:|---:|---:|---|---:|---:|---|---:|
| Pequeno (5k a 50k) | 50 | 3.730 | 6.700 | 45,6% (37,2 a 53,2) | 0,54 | 1,04 | 31,1 (21,5 a 42,0) | 26,3 |
| Emergente (50k a 200k) | 57 | 4.582 | 19.158 | 41,5% (33,6 a 50,5) | 0,51 | 1,00 | 31,6 (20,9 a 43,4) | 24,0 |
| Médio (200k a 2M) | 83 | 7.141 | 65.935 | 37,1% (33,9 a 44,7) | 0,50 | 0,93 | 26,5 (19,4 a 34,8) | 21,7 |
| Grande (2M a 10M) | 82 | 7.244 | 545.184 | 31,0% (28,8 a 34,8) | 0,42 | 0,78 | 12,0 (6,7 a 18,8) | 10,2 |
| Gigante (10M+) | 38 | 3.497 | 3.010.168 | 30,4% (25,2 a 36,6) | 0,42 | 0,70 | 12,9 (6,0 a 22,3) | 10,9 |

Fonte: Frente 2D, `peq_01_concentracao_volatilidade_anomalias_5portes.csv` (bootstrap clusterizado por canal). Robusta = 10x confirmada também pelo baseline só do passado e pelo leave-one-out.

Comentários por mil views caem com o porte: 3,3 (pequeno), 2,7 (emergente), 1,8 (médio), 1,6 (grande) e 1,0 (gigante). Curtidas por mil ficam entre 31 e 33 até o grande (21 no gigante).

### 3.2 Como as regras mudam por porte

| Regra | Pequenos (5k a 200k) | Médios (200k a 2M) | Grandes e gigantes (2M+) | Classe |
|---|---|---|---|---|
| Vídeo mais longo rende mais dentro do canal | +30,2% por dobro; curva ainda sobe depois de 30 min (acima de 60 min puxada por formatos específicos) | ótimo em 28 min (IC 24 a 41) | grande: ótimo em 31 min; gigante: curva plana e crescente até 109 min | **Universal** (alta) |
| Fugir do tema habitual reduz views | −14,8% por DP | −10,5% por DP (200k+) | −10,5% por DP (200k+) | **Universal** (alta) |
| Fugir do visual habitual da capa reduz views | −10,9% por DP (−14,4% no pequeno 5k a 50k) | −7,4% por DP (200k+) | −7,4% por DP (200k+) | **Universal** (alta) |
| Queda depois de fracasso | −13,3% no vídeo seguinte | −9,2% (200k+) | −9,2% (200k+) | **Universal** (média) |
| Brilho, saturação, contraste, rosto e quantidade de texto na capa | nulos | nulos | nulos | **Universal: não importa** |
| Horário e dia de publicação | nada sobrevive a BH | fim de semana +2,75 p.p. de top 5% só em médios (q = 0,040) | nada sobrevive | **Universal: não importa** |
| Publicar com menos de 2 dias do anterior | −4,4% (q = 0,59), inconclusivo | −8,8% nos 200k+ (q = 0,003) | idem | **Só aparece nos 200k+** |
| Legenda enviada pelo canal | inconclusivo (só 3,8% dos vídeos e 14 canais têm) | +28,6% nos 200k+ | idem | **Só mensurável nos 200k+** |
| Número e CAIXA ALTA no título | +15,4% e +15,3% (q ≈ 0,02) | +2,3% e +8,2% (200k+) | idem | **Sinal só nos pequenos, diferença não confirmada** (baixa) |
| Colab/versus no título | −21,6% (q = 0,020) | +4,4% (200k+) | idem | **Sinal só nos pequenos** (baixa) |
| Capítulos na descrição | +27,1% (q = 0,020) | +9,6% controlando duração (q = 0,40) | idem | **Sinal só nos pequenos** (baixa) |
| Rosto nos breakouts | breakouts têm menos rosto (72,9% contra 81,5%, q < 0,001) | rosto nulo | rosto nulo | **Específico dos pequenos** (média) |
| Concentração e volatilidade | top 10% com 41,5% a 45,6% das views; DP de y 1,00 a 1,04 | 37,1%; DP 0,93 | 30,4% a 31,0%; DP 0,70 a 0,78 | **Ruptura entre médio e grande** |
| Anomalias de 10x por mil vídeos | 31,1 a 31,6 | 26,5 | 12,0 a 12,9 | **Ruptura entre médio e grande** |
| Quem rompe a bolha | volátil e ativo | médios menores rompem mais (mediana de 565 mil contra 1,2 milhão de inscritos) | raro | romper é volatilidade persistente do canal (correlação 0,94) |

**Ruptura estrutural.** No nível do canal, ajustando nicho, idioma e número de vídeos: pequeno e emergente contra médio, diferenças pequenas e não significativas (q de 0,35 a 0,98); grande e gigante contra médio, top 10% −8,9 e −9,3 p.p. (q ≤ 0,006). Anomalias de 10x: pequeno +6,2 e emergente +6,6 por mil contra médio (q = 0,52); grande −13,7 por mil (q = 0,014). Dentro dos pequenos o DP de y quase não varia com o log de inscritos (−0,02). A lógica de distribuição muda por volta de 2 milhões, não em 200 mil.

## 4. Catálogo Consolidado de Hipóteses Descartadas

Nada foi escondido: abaixo estão todas as hipóteses que os dados derrubaram, transformaram em artefato ou deixaram inconclusivas, juntando a Fase 1 e as 4 frentes.

| ID | Hipótese | Teste | Resultado | Status |
|---|---|---|---|---|
| H-2 | Vídeos acima do normal em views são mais engajados por view | correlação dentro do canal | −0,35, negativa nos 11 nichos | descartada (é o contrário) |
| H-3 | Engajamento e alcance formam regimes divergentes | taxa bruta × resíduo de escala | correlação ≈ 0 no resíduo | artefato de razão |
| H-8 | Algum traço aumenta curtidas por view de forma robusta | 3 especificações | nenhum passa nas 3 | descartada |
| A-1 | Existem traços que só aparecem no top 1% ou 5% do canal | efeito fixo no topo | nada além do que aparece na média | descartada |
| A-2 | Rosto grande e 1ª pessoa reduzem a chance de topo | global × dentro do canal | global OR 0,63 e 0,60; dentro do canal nulo | artefato de composição |
| A-6 | Concentração extrema (poucos vídeos com quase todas as views) | fração do top 10% | 33,9% das views no canal mediano | descartada (moderada) |
| D-2 | Anomalias de 10x têm traço próprio de título, capa, duração ou legenda (200k+) | 40 traços + BH | 0 de 40 | descartada |
| D-3 | Anomalias têm formato próprio (tutorial, review, desafio) | classificação por LLM + bootstrap | nenhum passa BH | descartada |
| D-4 | Anomalias falam com público de fora do nicho | idem | +9,5 p.p., q = 0,06 | inconclusiva |
| D-5 | Anomalias dependem de gancho temporal | idem | +2,3 p.p., q = 0,97 | descartada |
| F-2 | Pausa longa (mais de 45 dias) melhora o desempenho | 3 alvos | +16,9% em y, nulo em y_passado | inconclusiva (provável relançamento) |
| F-4 | Ressaca depois de um hit | vizinhos de y | −8,1% | artefato da métrica |
| F-6 | Vídeos continuam crescendo muito depois de 35 dias | elasticidade de idade | 0,077 no geral | descartada no geral |
| F-7 | Padrões explosivo, evergreen e crescimento tardio | exige séries | um snapshot só | não mensurável |
| ANT-2 | Expressões tensas na capa puxam views | bateria com BH | nenhuma expressão passa | descartada para views |
| 2A-1 | Existe um "DNA do viral" previsível nos metadados | top 5% do canal, 2 regimes | AUC 0,58 e 0,54 | descartada |
| 2A-2 | Árvores captam interações que o linear não vê | top 5% do canal | 0,583 contra 0,581 | descartada |
| 2A-3 | Traços de miniatura melhoram a previsão | ablação de 26 variáveis | Spearman 0,162 contra 0,163 | descartada |
| 2A-4 | Rosto, texto, contraste ou saturação funcionam diferente por porte ou nicho | 12 interações | todas q ≥ 0,26 | descartada |
| 2A-5 | Efeito da duração muda com porte ou idioma | Wald | q = 0,75 e 0,54 | descartada (muda com nicho) |
| 2A-6 | Legenda funciona diferente em PT e EN | Wald | q = 0,87 | descartada |
| 2A-7 | Capítulos ou timestamps aumentam views por si | efeito fixo com spline de duração | +9,6% (q = 0,40) e +12,5% (q = 0,36) | descartada |
| 2A-8 | Momentum depois de um hit (200k+) | tendência quadrática | +2,4%, IC −2,4% a +7,6% | descartada (fase do canal) |
| 2A-9 | Esperar alguns dias depois de um hit rende mais | extremo × intervalo | p = 0,58 | descartada |
| 2A-10 | Existe um dia ou horário melhor | Wald e hora circular | q = 0,31 e 0,86 | descartada |
| 2A-11 | Volume de 30 dias derruba o desempenho | y_passado | −1,2% (q = 0,63) | descartada (só 7 dias importam) |
| 2A-12 | Médios rompedores têm capas ou estrutura diferentes | 24 características | q ≥ 0,25 | descartada |
| 2A-13 | Romper a bolha é habilidade além da variância | observado × esperado | excesso nulo (q = 0,45) | descartada (volatilidade persistente) |
| 2A-14 | Há um intervalo ótimo de cerca de 2 meses | spline | ótimo na borda | descartada como regra |
| 2B-1 | Rosto grande em close aumenta views | efeito fixo, 201 canais | −2,5% (IC −6,8% a +1,9%) | refutada |
| 2B-2 | Expressão de surpresa atrai mais público | 189 canais | −2,7% (q = 0,64) | refutada |
| 2B-3 | Setas ou círculos impulsionam o vídeo | 2.969 vídeos | +0,4% (q = 0,95) | refutada |
| 2B-4 | Capa sem rosto prejudica o alcance | 107 canais | +4,6% dentro do canal (−40,7% só na leitura ingênua) | refutada |
| 2B-5 | Saturação alta e vermelho dominante geram mais views | efeito fixo | −4,3% e −5,9% | não confirmada |
| 2B-6 | Olhar para a câmera eleva views | 199 canais | −0,7% (q = 0,94) | refutada |
| 2B-7 | Números ou dinheiro na capa alavancam o resultado | 4.548 vídeos | −4,9% (q = 0,48) | não confirmada |
| 2B-8 | Mistério visual (silhueta, borrão, interrogação) aumenta o sucesso | amostra semântica | OR 0,49, q canal 0,37 | não confirmada |
| 2B-9 | A capa sozinha explica o desempenho relativo | GroupKFold por canal | R² 0,025 no melhor caso | descartada |
| 2B-10 | Clusters visuais são receitas copiáveis | concentração por canal | 41 de 91 clusters são identidade de 1 canal | descartada |
| 2C-1 | O texto do título prevê bem o desempenho relativo | 6 conjuntos | R² ≤ 0,018 | descartada |
| 2C-2 | Capa que repete o título é punida | 3 especificações | +1,1% (IC −9,5% a +13,4%) | descartada |
| 2C-3 | Capa deve ser semanticamente diferente do título | cosseno título × OCR | +4,1% por DP de proximidade | descartada (é o contrário) |
| 2C-4 | Existe comprimento ideal de título | faixas por idioma | todas q > 0,93 | descartada |
| 2C-5 | Pergunta, número, lista, tutorial, desafio, mistério ou urgência elevam a média | gancho × descritivo | IC cruzando zero | descartada |
| 2C-6 | Lacuna de curiosidade alta distingue o topo | LLM, top 5% × flop | diferença nula | descartada |
| 2C-7 | Combinações título × capa "mágicas" | 649 interações | 0 positivas com q < 0,10 | descartada |
| 2C-8 | Algum arquétipo de vídeo vence o padrão do canal | 18 ângulos | q ≥ 0,89 | descartada |
| 2C-9 | Formatos de canal têm médias relativas diferentes | nível 1 | diferem só em risco | reformulada |
| 2C-10 | Há nichos com arquétipo forte e pouco saturado | 176 células | 0 sobrevivem | descartada |
| 2C-11 | Há arbitragem de formato EN para PT | 18 ângulos + 33 traços | 0 ângulos | descartada (fica como teste) |
| 2C-12 | Desafio em 1ª pessoa é o ângulo mais viral | nível 2 | menor taxa de top 5% (2,9%) | descartada |
| 2C-14 | 1ª pessoa no título ajuda em qualquer idioma | por idioma | EN −11%; PT nulo | descartada |
| 2D-1 | Canais pequenos são um mundo à parte abaixo de 200 mil | nível do canal | pequeno e emergente = médio (q ≥ 0,35) | descartada |
| 2D-2 | Pequenos dependem mais de capa chamativa | efeito fixo | nenhum traço visual move views | descartada |
| 2D-3 | Ter cara de canal grande na capa ajuda o pequeno | embeddings | −2,6% por DP (q = 0,30) | descartada |
| 2D-4 | Mudar de assunto é o caminho para o breakout | novidade × 10x | reduz views e não aumenta 10x | descartada |
| 2D-5 | Postar quase todo dia prejudica o pequeno | intervalo | −4,4% (q = 0,59) | inconclusiva |
| 2D-6 | Vídeo antigo de canal pequeno perde views | elasticidade | artefato do crescimento do canal | artefato |
| 2D-7 | Horário ou dia certo destrava canal pequeno | BH | nada sobrevive | descartada |
| 2D-8 | Engajamento e alcance brigam mais em pequenos | elasticidade | 0,77 contra 0,80 (p = 0,32) | descartada |
| 2D-9 | Texto da capa que complementa o título rende mais | OCR | −4,6% (q = 0,49) | descartada |

## 5. Limitações honestas e a fronteira do que esta base responde

**Limitações transversais.**

- **Sem dados privados do YouTube Studio:** CTR, impressões, retenção, tempo de exibição, origem de tráfego e inscritos por vídeo não existem na base. Também não há transcrições nem histórico de views ao longo do tempo (um único snapshot).
- **Causalidade reversa:** título, capa, legenda e capítulos foram lidos no dia da coleta. Criadores editam vídeos depois que estouram ou flopam.
- **Seleção e sobrevivência:** canais 200k+ chegaram lá; canais pequenos vieram da busca de vídeos recentes (ativos e visíveis), não do pequeno típico. Lifestyle e documentário perderam 41% a 45% dos canais no funil da base 200k+.
- **Poucos clusters em recortes finos:** nichos com 9 a 24 canais e células de 3 a 10 canais geram hipóteses, não decisões.
- **Muitos testes:** BH é aplicado dentro de cada bateria, não entre baterias. Achados com q entre 0,05 e 0,15 são candidatos a teste.
- **Duração carrega escopo:** vídeo longo costuma ser projeto maior; a curva mede duração mais esforço.
- **Breakout relativo:** 10x a mediana do canal num canal pequeno pode ser poucos milhares de views.

**Fronteira: o que a base pública responde e o que só o analytics privado responde.**

| Pergunta | Esta base responde? | O que falta |
|---|---|---|
| Quanto um vídeo rendeu contra o normal do canal | sim (múltiplo relativo) | nada |
| Qual faixa de duração se associa a mais views dentro do canal | sim, por nicho e porte | retenção para separar tempo assistido de alcance |
| Se um traço de título ou capa se associa a views | sim, com efeito fixo | CTR e impressões por vídeo para isolar o clique |
| Se a capa aumentou o clique | **não** | CTR por variação (Testar e comparar do YouTube) |
| Se o público ficou até o fim | **não** | curva de retenção |
| De onde veio o tráfego (busca, sugeridos, navegação) | **não** | origem de tráfego |
| Se o vídeo é evergreen, explosivo ou de crescimento tardio | **não** | série diária de views |
| Se um vídeo trouxe inscritos | **não** | inscritos por vídeo |
| Qual tema tem demanda de busca e pouca oferta | só oferta dos canais da base | volume de busca e concorrência |

## 6. Motor de consulta acionável

Módulo Python sem dependências externas: `build_knowledge_base.py` gera `knowledge_base.json` (0,87 MB, 4.639 vídeos de referência) a partir dos arquivos reais das 5 frentes; `idea_advisor.py` oferece função e CLI.

```
python idea_advisor.py --title "Título proposto" --niche tech --lang pt --tier pequeno \
  --duration-min 18 --thumb-notes "fundo escuro, produto em destaque, sem rosto" \
  --days-since-last 5 --format markdown
```

O parecer traz 7 blocos: diagnóstico com grau de confiança e teto preditivo explícito; faixa ótima de duração do nicho e porte contra a curva real; análise do título (comprimento, vocabulário abstrato, 1ª pessoa em EN, marca famosa em tech e games, afirmação contraintuitiva, número e CAIXA ALTA em pequenos com aviso de confiança baixa, e o que não importa); diretrizes de capa e alinhamento título ↔ capa; cadência e consistência; exemplos reais parecidos de alto desempenho (busca TF-IDF nos 26.194 vídeos, sem API); e checklist pré-publicação. Testes: 10 testes pytest aprovados (função, CLI, alertas, aliases, sem travessão). Exemplos de saída em `docs/research/advisor_examples/` (4 cenários: pequeno PT histórias, emergente EN tech, grande PT finanças e pequeno EN ciência).

## 7. Custos

Gasto total registrado em todos os `uso_gemini*.csv`: **R$ 65,29** (US$ 11,01) de R$ 100,00 autorizados; saldo de **R$ 34,71**. A consolidação final gastou R$ 0,00. YouTube Data API: 1.280 unidades. Detalhe por frente e por modelo em `CUSTOS_LAB.md`.

## 8. Índice completo

**Relatórios (`docs/research/`)**

| Documento | Arquivo |
|---|---|
| Este relatório | `RELATORIO_FINAL_CONSOLIDADO.md` |
| Auditoria da base 200k+ | `01_AUDITORIA.md` |
| Primeiras descobertas (Fase 1) | `02_PRIMEIRAS_DESCOBERTAS.md` |
| Registro de hipóteses | `HIPOTESES_LOG.md` |
| Custos consolidados | `CUSTOS_LAB.md` |
| Frente 2A: ML, duração, cadência e breakout | `RELATORIO_ML_AEFG.md` |
| Frente 2B: thumbnails visuais | `RELATORIO_THUMBS_VISUAL.md` e `GUIA_PRATICO_THUMBNAILS.md` |
| Frente 2C: títulos, arquétipos e oportunidades | `RELATORIO_TITULOS_ARQUETIPOS_BCG.md` |
| Frente 2D: canais pequenos | `RELATORIO_CANAIS_PEQUENOS.md` |

Os relatórios das frentes citam caminhos internos do laboratório (`resultados/`, `dados/`, `scripts/`). As bases brutas (parquet), embeddings e miniaturas não fazem parte deste repositório por tamanho; os números citados vêm desses arquivos e estão condensados em `youtube_seo/advisor/knowledge_base.json`.

**Gráficos (`docs/research/assets/`)**

- Fase 1: `01_funil_e_cobertura.png`, `02_engajamento.png`, `03_anatomia_do_topo.png`, `04_cadencia_e_sequencia.png`.
- 2A: `ml_01_shap_global_e_interacoes.png`, `ml_02_curvas_duracao_gam_nichos.png`, `ml_03_cadencia_pos_viral_horario.png`, `ml_04_mapa_oportunidades_breakout.png`.
- 2B: `thumb_01_mapa_umap_clusters.png`, `thumb_02_ranking_padroes_performance.png`, `thumb_03_elementos_cores_composicao.png`, `thumb_04_padroes_por_nicho_e_raros.png`, `catalogo_geral_ranking.png`.
- 2C: `arq_01_sinergia_titulo_thumb.png`, `arq_02_mapa_umap_arquetipos.png`, `arq_03_ranking_arquetipos_risco_retorno.png`, `arq_04_matriz_oportunidades_nicho_idioma.png`.
- 2D: `peq_01_cobertura_e_volatilidade_5portes.png`, `peq_02_efeitos_pequenos_vs_grandes.png`, `peq_03_duracao_e_anomalias_pequenos.png`.

**Dados derivados**: `docs/research/data/ranking_alavancas.csv`.

**Motor de consulta (`youtube_seo/advisor/`)**: `idea_advisor.py`, `knowledge_base.json`, `INTEGRACAO.md`; testes em `tests/test_idea_advisor.py`; gerador da base de conhecimento em `scripts/research/build_knowledge_base.py`; exemplos de saída em `docs/research/advisor_examples/`.

