# 02 · Primeiras descobertas (Fase 1)

Gerado por `scripts/02_primeiras_descobertas.py` (cálculo, cerca de 4 min), `scripts/03_anomalias_classificacao.py` (classificação de tema das anomalias), `scripts/04_grafico_topo.py` (gráfico 03) e `scripts/05_sintese_llm.py` (revisão crítica). Números completos em `resultados/primeiras_descobertas.json` e `resultados/02_*.csv` / `03_*.csv`.

## Padrão estatístico usado em tudo

- **Desfecho:** desempenho relativo ao próprio canal (`y`), com `y_passado` (só olha para trás) e `y_loo` (todos os outros vídeos do canal) como sensibilidade.
- **Comparação dentro do canal:** efeito fixo de canal, com erro padrão agrupado por canal (203 grupos).
- **Controles:** log da idade e duração. As regressões logísticas também controlam nicho, porte e idioma.
- **Intervalos:** bootstrap por canal com 1.000 a 2.000 reamostragens quando o estimador não é linear.
- **Múltiplos testes:** correção de Benjamini-Hochberg (BH) dentro de cada bateria. "Significativo" quer dizer q < 0,05.
- **Sensibilidade:** sem `made_for_kids` e sem |y| > 3. Nas taxas de engajamento, também controlando o próprio `y`.
- **Natureza dos resultados:** tudo é associação, não causa. Não existe CTR, impressões, retenção, origem de tráfego nem transcrição na base, e nada aqui fala desses indicadores.

---

## Investigação H · Engajamento (curtidas/views e comentários/views)

**1. Pergunta.** Engajamento e views andam juntos? Quando divergem, o que caracteriza cada regime? Que traços mexem no engajamento?

**2. Metodologia.**
- **Cobertura:** separei a ausência estrutural (comentários desativados em todo o infantil) da ausência real.
- **Elasticidade dentro do canal:** `log(curtidas) ~ log(views) + log(idade)` com efeito fixo de canal. Elasticidade 1 quer dizer que as curtidas crescem na mesma proporção das views. É a medida limpa, porque a taxa tem as views no denominador.
- **Correlação dentro do canal** entre engajamento relativo (leave-one-out) e `y`, com bootstrap por canal, por porte e por nicho.
- **Regimes por percentis dentro do canal:**
  - "engajado sem alcance": top 10% de comentários/view ou curtidas/view do canal, com views no máximo no percentil 60;
  - "alcance frio": top 10% em views e ambas as taxas no máximo no percentil 30.
- **Bateria de 40 traços × 2 taxas** em três especificações (principal, controlando alcance e sem infantil e outliers), com BH.

**3. Resultado.**
- **Cobertura:** curtidas visíveis em 97,6% dos vídeos gerais e 94,7% dos infantis. Comentários: 99,0% dos gerais e **0% dos infantis** (estrutural). Ficam 17.393 vídeos analisáveis em curtidas e 15.945 em comentários.
- **Taxas típicas:** a mediana é de 29,9 curtidas e 1,54 comentários a cada mil views. Games (40,9) e educação (39,1) têm mais curtidas por view; finanças (2,35) e tech (1,91) mais comentários.
- **Achado central:** quando um vídeo tem o dobro de views de outro do mesmo canal, ele **não** tem o dobro de curtidas.
  - Elasticidade das curtidas: **0,80** (IC 95% 0,77 a 0,83).
  - Elasticidade dos comentários: **0,69** (IC 0,66 a 0,73).
  - O padrão vale para todos os portes e para pt e en. Comentários em gigantes: 0,65.
- **Correlação negativa dentro do canal** entre engajamento relativo e `y`: −0,35 em curtidas (IC −0,39 a −0,31) e −0,35 em comentários (IC −0,38 a −0,30). É negativa nos 11 nichos; a mais forte está em lifestyle e documentário (cerca de −0,5) e a mais fraca em games (−0,15 a −0,18).
- **Divergência:**
  - 76,9% dos vídeos com engajamento top 10% do canal ficaram com views no máximo no percentil 60, contra 60% esperados se as duas coisas fossem independentes.
  - 35,1% dos top 10% em views são "frios", contra 9% esperados.
  - 2.281 vídeos (12,8%) são "engajados sem alcance" e 675 (3,8%) são "alcance frio".
- **Correção depois da revisão crítica (`scripts/02b_regimes_residuais.py`): essa divergência é quase toda efeito de escala.**
  - Como as interações crescem menos que as views, a taxa por view cai mecanicamente quando o vídeo escala. Um vídeo com 10x as views do normal tem, só por isso, cerca de metade da taxa de comentários (10^(0,69−1) ≈ 0,49).
  - Medindo o engajamento **acima do esperado para aquele volume de views** (resíduo de log(interações) ~ log(views) + log(idade) dentro do canal), a divergência some. 56,6% (curtidas) e 54,9% (comentários) dos top 10% em engajamento residual ficam no percentil 60 ou abaixo em views, contra 60% esperados. Entre os top 10% em views, 35,4% e 30,2% têm engajamento residual baixo, contra 30% esperados.
  - A correlação entre engajamento residual e `y` é praticamente zero (Spearman 0,014 e 0,038).
  - **Conclusão: engajamento acima do esperado e alcance acima do normal são dimensões praticamente independentes.** Os perfis de regime abaixo descrevem a taxa bruta e devem ser lidos com isso em mente.
- **O que caracteriza cada regime** (dentro do canal, BH):
  - "Engajado sem alcance": título em 1ª pessoa (+5,2 pp), vídeos mais curtos (−3,4 pp a cada dobro de duração), menos legenda (−7,8 pp) e menos capa que complementa o título (−1,8 pp).
  - "Alcance frio": vídeos mais longos (+1,4 pp a cada dobro).
- **Traços robustos no engajamento** (passam BH nas 3 especificações), todos em **comentários por view**:
  - expressão triste na miniatura: **+17,9%** (IC +8,9% a +27,6%);
  - título com pergunta: **+10,4%** (IC +5,2% a +15,9%);
  - rosto grande na miniatura: **+7,7%** (IC +3,3% a +12,3%).
  
  Nenhum traço passou nas 3 especificações para curtidas. A 1ª pessoa no título dá +8,8% em comentários e +4,3% em curtidas, mas cai quando se controla o alcance.
  
  No engajamento residual (sem viés de razão), os três sinais de comentários se mantêm: triste +17,8%, pergunta +9,6% e rosto grande +6,3%, todos com q ≤ 0,004. A 1ª pessoa entra com +5,3% (q = 0,03). Em curtidas aparecem triste +6,9% (q = 0,009), "você" no título +3,5% e rosto grande +3,1% (q = 0,045).

**4. Evidência estatística.** Elasticidades e correlações acima com N de 15.945 a 17.396 vídeos e 178 a 199 canais. Traços: as 3 especificações com q_BH ≤ 0,014. A especificação controlando `y` mantém os três efeitos: +19,0%, +9,2% e +6,9%. Arquivos: `02_H_elasticidade.csv`, `02_H_correlacao_engajamento_y.csv`, `02_H_regimes_tracos.csv` e `02_H_tracos_engajamento.csv`.

**5. Visualização.** `graficos/02_engajamento.png`.

**6. Descobertas inesperadas.**
- O vídeo que estoura dentro do canal é, em média, **menos** engajado por view. O alcance extra vem de gente menos ligada ao canal.
- A taxa bruta engana: parece que engajamento e alcance brigam, mas, descontada a escala, eles são independentes. Um vídeo pode ser ótimo em conversa e mediano em views, e vice-versa, sem que uma coisa explique a outra.
- Pergunta no título e rosto triste ou grande na capa geram conversa, mas **não** geram views (não aparecem no efeito médio de `y`).

**7. Limitações.**
- Curtidas e comentários são cumulativos, e a idade entra só como controle.
- Pode haver causalidade reversa (vídeos polêmicos atraem comentários e o algoritmo distribui de forma diferente).
- 9 canais escondem curtidas.
- O infantil não tem comentários.
- A elasticidade abaixo de 1 também pode refletir menor proporção de inscritos entre os espectadores de um hit. Não há como separar isso sem dados de origem.

**8. Recomendação prática.**
- Para **meta de comunidade** (comentários), testar pergunta direta no título e capa com rosto grande e emoção negativa ou vulnerável.
- Para **meta de alcance**, não usar engajamento por view como termômetro: um hit legítimo tem taxa menor só por escala.
- Nos relatórios, comparar o engajamento com o **esperado para aquele volume de views** do canal (curva com expoentes 0,80 e 0,69), não com uma taxa fixa.

| Impacto | Confiança | Aplicabilidade | Facilidade |
|---|---|---|---|
| Médio | Alta (elasticidade; independência depois da correção) / Média (traços) | Alta | Alta |

---

## Investigações A & D (parte 1) · Anatomia do topo, concentração e anomalias positivas

**1. Pergunta.** Quanto das views vem de poucos vídeos? O que separa os top 1%, 5% e 10% da faixa mediana e dos piores 10%? Que padrões têm os vídeos que fizeram 10x ou mais o normal do canal?

**2. Metodologia.**
- **Concentração:** fração das views do canal vinda do top 5%, 10% e 20% dos vídeos, mais o índice de Gini. Também uma versão ajustada por idade, `exp(y_loo_idade)`. Mediana por porte, nicho e idioma, com bootstrap de 1.000 iterações.
- **Caudas:** pelos percentis globais de `y` (top 1% = y ≥ 2,69, ou seja 14,8x; top 5% ≥ 4,8x; top 10% ≥ 2,9x; mediana = 40 a 60%; bottom 10% ≤ 0,40x). Regressão logística por traço (40 traços × 6 comparações = 240 testes) com controles e erro agrupado por canal, mais BH.
- **Mesmas comparações dentro do canal:** modelo linear de probabilidade com efeito fixo, top 5% e 10% do próprio canal contra os 40 a 60% do próprio canal.
- **Volatilidade de canal:** desvio de `y` por canal regredido na fração de títulos em 1ª pessoa e de capas com rosto grande, com controles de porte, nicho e idioma (erro HC3 e bootstrap).
- **Anomalias:** y ≥ log(10). Também uma versão robusta que exige 5x ou mais em `y_passado` e em `y_loo`. Traços contra o resto do mesmo canal (efeito fixo + BH), palavras super-representadas (log-odds com prior de Dirichlet) e classificação de formato e tema por LLM barato. A comparação é contra 2 controles medianos do mesmo canal e da mesma época, com bootstrap pareado por canal de 2.000 iterações e BH em 31 testes.

**3. Resultado.**
- **Concentração moderada, não extrema.**
  - No canal mediano, os 10% melhores vídeos trazem **33,9%** das views (IC 31,2% a 36,3%) e os 5% melhores trazem **20,8%**. Ajustado por idade, quase não muda (33,1%).
  - Maior em médios (37,1%), pt (38,1%), esportes (42,9%) e infantil (40,5%). Menor em gigantes (30,4%), en (30,2%) e games (25,1%).
- **Topo dentro do canal.** Só três traços distinguem o top 5% do próprio canal da faixa mediana:
  - legenda enviada pelo canal: +12,9 pp de chance (q = 0,011);
  - duração: +6,4 pp a cada dobro (q < 0,001);
  - texto da capa que **complementa** (não repete) o título: +4,8 pp (q = 0,037).
  
  São os mesmos sinais que aparecem no efeito médio (legenda +28,6% e duração +14,9% por dobro). **Não há efeitos de cauda escondidos dentro do canal:** nenhum traço separa o top 1% ou 5% sem também aparecer na média.
- **O "sinal de cauda" entre canais é composição.** Na comparação global:
  - capa com rosto grande **reduz** a chance de estar no top 5% (razão de chances 0,63, IC 0,49 a 0,81, q = 0,042);
  - título em 1ª pessoa reduz a chance de estar no top 10% (0,60, IC 0,45 a 0,80, q = 0,043).
  
  Dentro do canal, porém, os dois são nulos. A explicação está no nível do canal: a cada +10 pp de títulos em 1ª pessoa, o desvio de `y` do canal cai 0,036 (IC bootstrap −0,056 a −0,015, p = 0,0005). Rosto grande vai na mesma direção (−0,019, IC −0,039 a −0,0001). **Canais centrados no criador têm desempenho mais estável: menos estouros e também menos fracassos.**
- **Volatilidade por porte e nicho:** a mediana do desvio de `y` é 0,93 em médios, 0,78 em grandes e 0,70 em gigantes. Infantil (1,12), documentário (0,99) e esportes (0,98) são os mais voláteis; games (0,51) e entretenimento (0,59) os mais estáveis. Canais em pt oscilam mais que em en (+0,12, p = 0,023).
- **Anomalias positivas:**
  - 321 vídeos (1,8%) fizeram 10x ou mais o normal do canal; 267 são robustos aos três baselines. Estão espalhados por 88 dos 203 canais, e os 5 canais com mais anomalias somam só 19,6% delas.
  - Taxa por mil vídeos: **26,5 nos médios** (IC 19,4 a 34,8), contra 12,0 nos grandes (IC 6,7 a 18,8) e 12,9 nos gigantes (IC 6,0 a 22,3). Canais médios furam a bolha cerca de 2x mais.
  - **Nenhum** dos 40 traços de título, miniatura, duração ou legenda distingue a anomalia dos outros vídeos do mesmo canal depois de BH (0 de 40).
  - A classificação de formato e tema também não passa BH. O mais perto foi "assunto que interessa a quem está fora do nicho": 58,6% nas anomalias contra 47,4% nos controles, diferença pareada de **+9,5 pp** (IC +3,1 a +15,7, p = 0,002, q = 0,06).
  - Anomalias têm **menos** legenda que a base (12,8% contra 21,8%) e a mesma duração mediana (16,4 contra 16,3 min).
  - Palavras super-representadas (z > 2,5, em pelo menos 3 canais): infantis, escola, músicas, família, português, bebê, song, futebol, minutos, compilation, rhyme, chicken. Ou seja, temas infantis e musicais e compilações, mas concentrados em poucos canais.
- **Exemplos reais de canais médios** (todos verificáveis em `resultados/02_AD_anomalias_lista.csv`):

  | Canal | Vídeo | Views | Normal do canal | Multiplicador | Publicação |
  |---|---|---:|---:|---:|---|
  | TudoCelular | "OPPO RENO16 F inicia NOVA ERA… \| Hands-on" | 6,32 mi | 9,1 mil | 696x | 03/08/2026 |
  | Tecnoblog | "MUDOU O FORMATO: Galaxy Z Fold 8 EM MÃOS!…" | 3,78 mi | 8,6 mil | 442x | 22/07/2026 |
  | Polin Lifestyle | "Amazing cooking deep fried chicken gizzard…" | 2,55 mi | 6,0 mil | 428x | 15/09/2026 |
  | Nursery Rhyme Street | "Spooky PIZZA PARTY With Skeletons…" | 14,2 mi | 34,5 mil | 411x | 27/05/2026 |
  | TudoCelular | "GALAXY Z FOLD 8 é a PROVA…" | 2,64 mi | 7,7 mil | 345x | 22/07/2026 |
  | Investidor de Verdade | "Como investir seu dinheiro – Guia para iniciantes (2026)" | 4,43 mi | 16,2 mil | 274x | 07/03/2024 |
  | Nath Finanças | "FLÁVIO vs LULA: O Plano Econômico" | 179 mil | 899 | 200x | 15/10/2026 |
  | Mistérios do Mundo | "Por que você não pode pular na água para fugir de abelhas?" | 426 mil | 2,8 mil | 154x | 25/10/2025 |
  | Mundo Conectado | "Galaxy Z Fold8 não é mais do mesmo…" | 2,29 mi | 14,9 mil | 154x | 22/07/2026 |

  Três canais de tech diferentes tiveram anomalias de 154x a 442x com o **mesmo** lançamento (Galaxy Z Fold 8), publicadas no mesmo dia (22/07/2026) com minutos de diferença. Multiplicadores dessa ordem num vídeo de lançamento são compatíveis com mídia paga do fabricante, que conta views. **É hipótese, não verificável na base.** Para a Fase 2, sinalizar "possível impulsionamento" (hands-on de lançamento com 100x ou mais) e rodar as análises com e sem esses casos.

**4. Evidência estatística.** Caudas: 240 testes, só 3 com q < 0,05 (rosto grande top5 vs mediana e vs bottom10 com q = 0,042; 1ª pessoa top10 vs mediana com q = 0,043). Dentro do canal: 160 testes, com legenda, duração e capa complementar significativas, estáveis também sem infantil. Volatilidade: 203 canais, R² = 0,30. Anomalias: 40 testes, 0 significativos; classificação: 31 testes, 0 significativos. Arquivos: `02_AD_concentracao_resumo.csv`, `02_AD_caudas_odds_ratio.csv`, `02_AD_sensibilidade_percentil_canal.csv`, `02_AD_volatilidade_canal.csv`, `02_AD_anomalia_tracos.csv`, `02_AD_palavras_anomalias.csv` e `03_anomalias_vs_controles.csv`.

**5. Visualização.** `graficos/03_anatomia_do_topo.png`: à esquerda, o mesmo traço medido entre canais e dentro do canal; à direita, a volatilidade do canal contra a fração de títulos em 1ª pessoa.

**6. Descobertas inesperadas.**
- **Não existe "DNA do viral" visível nos metadados.** Hits extremos não se distinguem por título, capa, duração ou formato dentro do canal. O que mais se aproxima é o tema falar com quem está fora do nicho.
- **Rosto grande e 1ª pessoa não atrapalham o vídeo;** eles caracterizam canais de personalidade, que trocam teto por piso.
- **Médios estouram 2x mais que gigantes,** em termos relativos.
- Anomalias de lançamento em tech aparecem em sincronia entre canais concorrentes.

**7. Limitações.**
- Percentis globais misturam canais voláteis e estáveis (por isso a comparação dentro do canal é a principal).
- O top 1% tem só 179 vídeos de 62 canais.
- A classificação por LLM usa só título e início da descrição.
- Possível mídia paga não identificável.
- Não há canais com menos de 200 mil inscritos.
- Títulos e capas atuais podem ter sido trocados depois do estouro.

**8. Recomendação prática.**
- Não perseguir "fórmula de viral" no título ou na capa.
- Usar como regra o que move a média e o topo do próprio canal: legenda própria, vídeo mais longo dentro da faixa do canal e texto de capa que **complementa** o título.
- Para buscar um estouro, testar pautas que interessem a quem está **fora** do nicho (sinal fraco, q = 0,06, só como hipótese de A/B).
- Para escolher o posicionamento: um canal de personalidade dá previsibilidade, e um canal de tema dá mais chance de outlier.

| Impacto | Confiança | Aplicabilidade | Facilidade |
|---|---|---|---|
| Alto (muda o que procurar) | Alta (nulos e composição) / Média (público amplo) | Alta | Média |

---

## Investigação F (parte 1) · Ritmo, intervalos, sequência e idade

**1. Pergunta.** O intervalo desde o vídeo anterior e a cadência recente se associam ao desempenho? Existe momentum ou ressaca depois de um hit? O que a idade permite dizer?

**2. Metodologia.**
- **Intervalo:** calculado sobre todos os 22.405 registros brutos. O 1º vídeo da janela de cada canal fica NaN (184 casos). Faixas de menos de 2 dias, 2 a 4, 5 a 9 (referência), 10 a 20, 21 a 45 e mais de 45 dias. Efeito fixo de canal, controle de idade, erro agrupado e BH, em 3 alvos (`y`, `y_passado`, `y_loo`) × 2 amostras.
- **Cadência:** log(1 + vídeos longos nos 30 dias anteriores), com censura quando a janela não cobre o período.
- **Sequência:** resíduo de log(views) depois de retirar, por canal, uma tendência linear no tempo e o log da idade.
  - Autocorrelação entre vídeos consecutivos, comparada com um nulo de 1.000 permutações da ordem dentro de cada canal.
  - Média do vídeo seguinte a um top 5% ou bottom 5% do canal, também definidos pelo resíduo, com bootstrap por canal.
- **Idade:** elasticidade de log(views) em relação ao log(idade) dentro do canal, e perfil por faixa de idade.

**3. Resultado.**
- **Intervalo curto se associa a desempenho pior.** Publicar menos de 2 dias depois do vídeo anterior fica **−8,8%** em relação a 5 a 9 dias (IC −13,5% a −3,9%, q = 0,003). A direção se mantém nos 6 cenários: −10,8% sem infantil e outliers, −12,9% em `y_passado` e −22,1% em `y_loo`, todos com q < 0,001. Com 2 a 4 dias fica −4,2% (q = 0,058; significativo em `y_passado` e `y_loo`).
- **Pausa longa** (mais de 45 dias) dá +16,9% em `y` (IC +4,9% a +30,2%, q = 0,012), mas **não** se sustenta em `y_passado` (+6%, q = 0,58) nem em `y_loo` (q = 0,14). Fica como inconclusivo.
- **Cadência dos últimos 30 dias:** dobrar a quantidade de vídeos longos se associa a −3,8% em `y` (q = 0,005) e −11,3% em `y_loo` (q = 0,003), mas é nulo em `y_passado` (−2,3%, q = 0,26). Efeito pequeno e dependente do alvo.
- **Momentum, não ressaca.**
  - A autocorrelação entre vídeos consecutivos é de **0,070** (IC 0,037 a 0,101), contra um nulo de −0,012 (p de permutação = 0,001; 17.074 pares).
  - O vídeo logo depois de um top 5% do canal fica **+9,4%** acima da tendência (IC +3,4% a +15,1%), e dois vídeos depois ainda fica +10,1% (IC +4,2% a +16,4%).
  - Depois de um bottom 5% fica **−9,2%** (IC −15,0% a −2,9%).
- **A "ressaca" é artefato.** Se o hit for definido pelo próprio `y`, aparece −8,1% (IC −13,2% a −2,3%). É um efeito mecânico do alvo com vizinhos bilaterais (ver auditoria). Com `y` bruto, a autocorrelação seria −0,034, também artefato.
- **Idade (corte transversal):**
  - Elasticidade de 0,077 (IC 0,003 a 0,150). Depois de 35 dias, um vídeo 2x mais velho tem só cerca de 5% mais views que outro do mesmo canal.
  - O perfil tem forma de U: 35 a 59 dias +9,9%; 120 a 364 dias −13,6%; 4 anos ou mais +11,3%, sempre contra a média do canal.
  - A elasticidade é negativa em finanças (−0,20) e tech (−0,18), e positiva em infantil (+0,44), lifestyle (+0,29) e entretenimento (+0,23).

**4. Evidência estatística.** Arquivos `02_F_intervalo_entre_videos.csv` (30 estimativas com BH por bloco) e `02_F_idade_elasticidade.csv`, além do bloco `F` do JSON. N = 17.698 vídeos com intervalo e 15.776 com cadência censurada corretamente.

**5. Visualização.** `graficos/04_cadencia_e_sequencia.png`.

**6. Descobertas inesperadas.**
- Hits vêm em sequência: o vídeo seguinte a um hit tende a ir bem, e o seguinte a um fracasso tende a ir mal.
- A métrica ingênua mostraria o contrário (ressaca), o que ensina a nunca medir sequência com um alvo de janela bilateral.
- A idade pesa pouco depois de 35 dias, e em finanças e tech o vídeo velho tem **menos** views que o recente, sinal de conteúdo perecível ou de canais crescendo.

**7. Limitações.**
- **Momentum pode ser fase do canal** (tendência não linear, temporada boa) e não efeito do hit. A tendência linear não remove ondas.
- O intervalo curto pode refletir lotes de vídeos menores ou séries (não necessariamente canibalização).
- Cadência mede só vídeos longos; Shorts e lives ficaram fora.
- A idade em corte transversal confunde acúmulo de views com crescimento do canal.
- O perfil em U por faixa de idade é em boa parte composição: com a janela truncada em 100 vídeos, só os 54 canais que postam devagar chegam a vídeos de 4 anos ou mais. Não é a curva de vida de um vídeo. Padrões explosivo, evergreen e crescimento tardio **não são mensuráveis** sem snapshots repetidos.

**8. Recomendação prática.**
- **[Usar como regra]** Evitar soltar dois vídeos longos com menos de 48 h entre eles. Espaçar pelo menos 5 dias quando possível.
- **[Testar]** Depois de um hit, publicar rápido uma continuação ou um vídeo do mesmo tema, aproveitando a fase boa (por exemplo, até 7 dias), sem abrir mão do intervalo mínimo.
- **[Usar como regra]** Não julgar um vídeo com mais de 35 dias esperando "crescimento tardio": o grosso já aconteceu.
- **[Infraestrutura]** Iniciar snapshots semanais de views dos próprios canais e de concorrentes para medir longevidade de verdade.

| Impacto | Confiança | Aplicabilidade | Facilidade |
|---|---|---|---|
| Médio | Alta (menos de 2 dias, momentum) / Baixa (pausa longa, cadência) | Alta | Alta |

---

## Revisão crítica independente

A revisão por um modelo de raciocínio está em `resultados/05_carbon_revisao.md`. Ela recebeu só os resultados acima, e nenhum número novo veio dela. Os resumos repetitivos das anomalias por porte estão em `resultados/05_hydrogen_anomalias_*.md`.
