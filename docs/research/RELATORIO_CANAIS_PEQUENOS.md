# Frente 2D · Canais pequenos (5 mil a 200 mil inscritos) x médios, grandes e gigantes

Snapshot de coleta: 23/11/2026, das 19h53 às 20h01 (horário de Brasília). Scripts em `scripts/` (01 a 10), tabelas em `resultados/`, gráficos em `graficos/`. Revisão crítica independente em `resultados/revisao_carbon.md` (gemini-4-carbon). Gasto Gemini da frente: **R$ 6,09** de R$ 8,00 (US$ 1,027). YouTube Data API: **1.280 unidades**, sem nenhum `search.list`.

## 1. Pergunta

Os padrões encontrados na base principal (203 canais com 200 mil inscritos ou mais) valem para quem ainda não tem audiência? O que é universal de 5 mil a 50 milhões de inscritos e o que só importa (ou importa mais) quando o canal é pequeno?

## 2. Metodologia

**Descoberta sem gastar cota.** 528 buscas públicas do YouTube via `yt-dlp` (filtros "este mês" e "esta semana", hl/gl do idioma), com as 4 consultas originais de cada célula nicho × idioma (`estudo-10k/scripts/seeds.py`) mais 8 consultas de cauda longa por célula. Resultado: 40.442 vídeos e 19.660 canais únicos. A busca por relevância sem filtro de data devolvia quase só canais grandes, por isso o filtro de vídeos recentes.

**Validação.** `channels.list` em lotes de 50 (1 unidade por lote). Regras: fora dos 257 canais originais, inscritos públicos entre 5.000 e 199.999, pelo menos 30 vídeos no total, idioma dos títulos coerente com o estrato, sem idioma estrangeiro explícito no nome, país BR/PT/AO/MZ ou vazio no estrato `pt`. 2.905 canais elegíveis; 176 escolhidos (até 4 por célula × subfaixa, priorizando tópico coerente e mais vídeos longos encontrados).

**Coleta e funil idênticos à base principal.** Playlist `UULF` (só vídeos longos), até 100 vídeos publicados há mais de 35 dias, sem lives; depois views > 0, duração > 3 min, sem `#shorts`, idade ≥ 30 dias, idioma do canal coerente (mesma regra de `04_features.py`), canal com ≥ 15 vídeos válidos, e teto de 5 canais por célula (meta de 80 a 110 canais).

**Features e alvos.** Réplica exata de `04_features.py`, `04b_miniaturas.py` (OpenCV), `04c_ocr_miniaturas.py` (RapidOCR) e da construção da base mestra em `01_auditoria.py`: `y`, `y_loo`, `y_passado`, `y_loo_idade`, `y_pct_canal`, `gap_ant_dias`, `n_pub_30d_ant`, `y_prev`, `like_rate`, `comment_rate` e os demais. `dados/base_pequenos.parquet` tem as mesmas 130 colunas da base mestra, na mesma ordem, mais `subfaixa` e `fonte_coleta`. Os rótulos `g_*` do Gemini foram harmonizados com os rótulos curtos da base mestra.

**Gemini (R$ 6,09 no total).** Embeddings 768d de 8.312 títulos (R$ 0,22); embeddings visuais de 3.710 thumbnails (todas as 261 anomalias de 10x ou mais e uma amostra igual por canal; R$ 2,64); classificação dos 13 campos `g_*` com gemini-3.5-flash-lite em 885 thumbnails (piloto de 20 + 261 anomalias + controles do mesmo canal + amostra aleatória estratificada por canal; R$ 2,88); 1 revisão crítica com gemini-4-carbon (R$ 0,35).

**Estatística.** Efeito fixo de canal (comparação dentro do canal) com erro padrão agrupado por canal; diferença pequenos x 200k+ por termo de interação no mesmo modelo; bootstrap clusterizado por canal (1.000 reamostras) para medianas e taxas; regressões no nível do canal com ajuste por nicho, idioma e nº de vídeos (HC3); Benjamini-Hochberg (BH) por família de testes. Na amostra visual, pesos de probabilidade inversa corrigem a sobreamostragem das anomalias.

**O que não existe na base.** CTR, impressões, retenção, tempo de exibição, fonte de tráfego e inscritos ganhos por vídeo são dados privados do YouTube Studio e **não estão** em nenhuma das duas bases. Todo "desempenho" aqui é views relativas ao normal do próprio canal.

### Auditoria da nova base

| Etapa do funil | Vídeos | Canais | Pequeno | Emergente |
|---|---:|---:|---:|---:|
| Canais escolhidos para coleta | | 176 | 88 | 88 |
| Registros brutos na API | 12.432 | 162 | 79 | 83 |
| Duração > 3 min | 11.781 | 162 | 79 | 83 |
| Sem `#shorts` | 11.663 | 162 | 79 | 83 |
| Idade ≥ 30 dias | 11.663 | 162 | 79 | 83 |
| Idioma do canal coerente | 10.573 | 148 | 75 | 73 |
| Canal com ≥ 15 vídeos válidos | 10.487 | 133 | 68 | 65 |
| Teto de 5 canais por célula | **8.312** | **107** | **50** | **57** |

Exclusões (69 canais, em `resultados/auditoria_canais_excluidos.csv`): 26 excedentes do teto por célula, 15 com menos de 15 vídeos longos válidos, 14 com idioma divergente, 14 sem playlist de vídeos longos na API.

| Subfaixa | Canais | Vídeos |
|---|---:|---:|
| Pequeno (5k a 49.999) | 50 | 3.730 |
| Emergente (50k a 199.999) | 57 | 4.582 |
| **Total** | **107** | **8.312** |

| Nicho | Canais | Vídeos | | Nicho | Canais | Vídeos |
|---|---:|---:|---|---|---:|---:|
| Culinária | 10 | 599 | | Finanças | 10 | 876 |
| Documentário | 9 | 777 | | Games | 10 | 781 |
| Educação | 9 | 607 | | Histórias | 10 | 880 |
| Entretenimento | 9 | 763 | | Infantil | 10 | 612 |
| Esportes | 10 | 862 | | Lifestyle | 10 | 734 |
| Tech | 10 | 821 | | | | |

Idiomas: EN 53 canais (3.962 vídeos), PT 54 canais (4.350 vídeos). 19 das 22 células nicho × idioma têm 5 canais; documentário EN, educação PT e entretenimento EN têm 4. Detalhe completo em `resultados/auditoria_cobertura_nicho_idioma_subfaixa.csv`.

Outros pontos da auditoria: zero sobreposição com os 257 canais e com os vídeos da base mestra; zero duplicatas; inscritos de 5.000 a 196.000; mediana de 11.739 views por vídeo (981 vídeos com menos de 1.000 views e 127 com menos de 100); curtidas visíveis em 98,6% e comentários válidos em 90,8% (infantil `made_for_kids` vira NaN por regra da plataforma, igual à base mestra); miniatura e OCR em 98,5% (126 miniaturas indisponíveis); 67 canais com janela truncada em 100 vídeos. Janela mediana por canal de 273 dias (209 no pequeno, 346 no emergente) contra 539 a 683 dias nos portes 200k+, e publicações de 11/08/2015 a 19/10/2026. Canais pequenos publicam mais seguido: intervalo mediano de 2,0 dias (pequeno) e 2,5 (emergente) contra 4,0 a 4,9 nos 200k+.

**Viés de descoberta (crítico).** Os canais vieram da busca de vídeos recentes. Isso exclui canais inativos, canais que a busca não mostra e canais sem SEO, e favorece quem publica muito (mediana de 410 vídeos no total, canal criado em média em abr/2021) e já ranqueia. A base representa **pequenos ativos e visíveis**, não o "canal pequeno típico". Isso tende a subestimar a volatilidade e o fracasso reais e a superestimar o quanto "dá certo".

## 3. Resultado

### 3.1 Os 5 portes

| Porte | Canais | Top 10% das views (mediana, IC 95%) | Gini | DP de y | Anomalias ≥ 5x por mil | ≥ 10x por mil (IC 95%) | ≥ 10x robustas por mil |
|---|---:|---|---:|---:|---:|---|---:|
| Pequeno 5k–50k | 50 | 45,6% (37,3 a 53,0) | 0,54 | 1,04 | 76,4 | 31,1 (21,5 a 42,0) | 26,3 |
| Emergente 50k–200k | 57 | 41,5% (33,7 a 50,4) | 0,51 | 1,00 | 66,8 | 31,6 (21,0 a 43,4) | 24,0 |
| Médio 200k–2M | 83 | 37,1% (34,0 a 44,7) | 0,50 | 0,93 | 64,7 | 26,5 (19,5 a 34,8) | 21,7 |
| Grande 2M–10M | 82 | 31,0% (29,0 a 34,7) | 0,42 | 0,78 | 38,2 | 12,0 (6,8 a 18,8) | 10,2 |
| Gigante (mega) 10M+ | 38 | 30,4% (25,4 a 36,6) | 0,42 | 0,70 | 31,2 | 12,9 (6,1 a 22,4) | 10,9 |

Robusta = 10x ou mais confirmada também pelo baseline só do passado (≥ 5x) e pelo leave-one-out (≥ 5x).

### 3.2 Fatores dentro do canal: pequenos (5k–200k) x 200k+

| Fator | Pequenos: efeito em views (IC 95%) | q BH | 200k+: efeito (IC 95%) | q BH | Diferença q BH |
|---|---|---:|---|---:|---:|
| Duração: dobro | **+30,2%** (+19,7 a +41,6) | <0,001 | **+14,9%** (+8,6 a +21,7) | <0,001 | 0,20 |
| Legenda enviada pelo canal | +26,7% (−6,2 a +71,2) | 0,44 | **+28,6%** (+15,3 a +43,5) | <0,001 | 0,94 |
| Título com número | **+15,4%** (+4,5 a +27,4) | 0,023 | +2,3% | 0,61 | 0,29 |
| Título com palavra em CAIXA ALTA | **+15,3%** (+5,6 a +25,9) | 0,020 | +8,2% (+1,8 a +15,1) | 0,10 | 0,71 |
| Título com colab/versus | **−21,6%** (−33,2 a −7,8) | 0,020 | +4,4% | 0,61 | 0,074 |
| Capítulos na descrição | **+27,1%** (+8,6 a +48,6) | 0,020 | +8,4% | 0,60 | 0,71 |
| Título +10 caracteres | +2,5% (+0,5 a +4,6) | 0,060 | +1,0% | 0,61 | 0,71 |
| Título com pergunta | −4,9% | 0,49 | −2,9% | 0,61 | 0,89 |
| Título em 1ª pessoa | −0,5% | 0,92 | −7,1% | 0,12 | 0,71 |
| Título "como/how" | +6,3% | 0,69 | −4,6% | 0,61 | 0,71 |
| Título de curiosidade/lacuna | +8,3% | 0,49 | +1,8% | 0,75 | 0,75 |
| Capa com texto (OCR) | +0,5% | 0,92 | +2,4% | 0,61 | 0,89 |
| Capa com 5+ palavras (OCR) | +4,9% | 0,49 | −0,1% | 0,97 | 0,71 |
| Texto da capa não repete o título (OCR) | −4,6% | 0,49 | −4,9% | 0,17 | 0,94 |
| Capa com rosto / rosto grande (OpenCV) | −3,6% / +3,7% | 0,59 | −0,5% / +4,0% | ≥0,31 | ≥0,84 |
| Saturação, contraste, brilho (+1 dp) | +1,1% / +0,5% / +2,1% | ≥0,69 | −0,9% / −2,0% / +1,4% | ≥0,22 | ≥0,71 |
| Menos de 2 dias desde o anterior | −4,1% | 0,54 | −5,7% | 0,12 | 0,89 |
| Fim de semana | +1,6% | 0,72 | +5,7% | 0,15 | 0,71 |

Fonte: `resultados/peq_06_universal_vs_especifico.csv` e `peq_04_fatores_within_pequenos_vs_200k.csv` (controle de idade e duração; também estimado com `y_loo_idade`, com as mesmas direções). Por subfaixa, só sobrevivem a BH: duração (pequeno +23,1%, q = 0,004; emergente +38,0%, q < 0,001), título com número no pequeno 5k–50k (+25,5%, q = 0,026) e título +10 caracteres no pequeno (+4,5%, q = 0,026).

**Duração por faixas** (dentro do canal, referência 10 a 15 min; `peq_04c_duracao_faixas.csv`):

| Faixa | Pequenos | 200k+ |
|---|---|---|
| 3–6 min | −26,6% (−43,7 a −4,5) | −23,0% (−35,4 a −8,2) |
| 6–10 min | −11,3% | −6,6% |
| 15–20 min | +15,3% | +26,2% |
| 20–30 min | +40,2% (+17,2 a +67,8) | +34,7% (+25,8 a +44,2) |
| 30–60 min | +58,5% (+26,1 a +99,4) | +36,2% (+24,0 a +49,6) |
| 60+ min | +111,7% (+48,9 a +201,0) | +21,6% (+1,8 a +45,4) |

Nos 200k+ a curva achata e cai depois de 30 a 40 min; nos pequenos ela continua subindo, mas o trecho acima de 60 min é dominado por formatos específicos (filmes completos dublados, júris integrais, compilações), ver Limitações.

**Intervalo desde o vídeo anterior** (referência 5 a 9 dias; `peq_04e`): nos 200k+, menos de 2 dias = −8,8% (q = 0,003); nos pequenos, −4,4% (q = 0,59), inconclusivo. Pausa acima de 45 dias = +31,7% nos pequenos (q = 0,017) e +16,9% nos 200k+ (q = 0,012), provavelmente relançamentos ou projetos maiores, não "descansar faz bem".

**Momentum** (resíduo de tendência, sem o artefato mecânico do alvo; `peq_04f`): vídeo logo após um top 5% do canal = +12,3% nos pequenos (IC +0,9 a +25,7) e +9,4% nos 200k+; logo após um bottom 5% = −13,3% (−22,9 a −3,2) e −9,2%. Mesmo padrão, um pouco mais forte nos pequenos e com IC largo dentro de cada subfaixa.

**Engajamento x alcance** (elasticidade dentro do canal, `peq_03`): curtidas crescem 0,77 por 1 de views nos pequenos (pequeno 0,73; emergente 0,81) contra 0,80 nos 200k+ (diferença p = 0,32). Comentários: 0,64 contra 0,69 (diferença −0,057, p = 0,046, marginal). Taxas medianas: 31 a 33 curtidas por mil views em todos os portes até grande (21 no gigante); comentários caem com o porte: 3,3 por mil no pequeno, 2,7 no emergente, 1,8 no médio, 1,6 no grande, 1,0 no gigante.

**Idade do vídeo** (`peq_04g`): elasticidade de views em relação à idade é −0,28 no pequeno, −0,05 no emergente e +0,05 a +0,18 nos 200k+ (diferença p = 0,003). Isso **não** quer dizer que vídeo velho perde views: nos pequenos, vídeos mais antigos foram publicados quando o canal era menor. É sinal de crescimento do canal, não efeito de idade.

**Horário e dia** (`peq_04h`): nada sobrevive a BH em nenhum grupo.

**Novidade temática** (distância do título ao centro temático do próprio canal, embeddings 768d; `peq_05`): fugir do assunto habitual reduz views nos dois grupos. Por +1 dp de novidade: −0,16 em log nos pequenos (cerca de −15%) e −0,11 nos 200k+ (cerca de −11%), p < 0,001 nos dois, diferença p = 0,054. Novidade **não** aumenta breakouts: taxa de 10x+ por tercil de novidade nos pequenos é 32,6 (baixa), 36,2 (média) e 25,4 (alta) por mil.

**Visual (embeddings das thumbnails; `peq_05b`)**: um classificador separa capas de pequenos e de 200k+ com AUC 0,757 (validação agrupada por canal), então existe uma "cara" de capa de canal grande. Mas, dentro do canal, ter mais "cara de grande" não rende mais: −2,6% por dp nos pequenos (q = 0,30), −1,7% nos 200k+ (q = 0,28). Já fugir do visual habitual do próprio canal custa views: −10,9% por dp nos pequenos (IC −15,3 a −6,3; q < 0,001), −14,4% no pequeno 5k–50k, −8,6% no emergente, −7,4% nos 200k+ (q < 0,001). Nenhuma das duas medidas muda a chance de breakout.

**Campos Gemini (rosto, expressão, texto, setas) na amostra aleatória dos pequenos** (418 a 428 vídeos; `peq_04b`): nenhum efeito sobrevive a BH. Poder estatístico baixo; tratar como inconclusivo.

### 3.3 Universal x específico

| Classe | Fatores | Confiança |
|---|---|---|
| **Universal (vale de 5k a mega)** | Vídeos mais longos rendem mais dentro do canal (até 20 a 30 min com certeza); momentum após hit e queda após fracasso; fugir do tema habitual (título) e do visual habitual (capa) reduz views; elasticidade de curtidas ~0,8; brilho, saturação, contraste, rosto e quantidade de texto na capa não movem views dentro do canal; horário de publicação irrelevante | Alta |
| **Específico de canais pequenos (5k–200k)** | Concentração e volatilidade maiores que as de grandes e gigantes (top 10% +5,8 pp, Gini +0,061, DP de y +0,133 contra 200k+, q = 0,014, ajustado por nicho e idioma); 2,5x mais anomalias 10x+ que grandes e gigantes; mais comentários por view; curva de duração que continua subindo depois de 30 min | Média (a fronteira real fica entre médio e grande: pequeno e emergente **não** diferem do médio, q ≥ 0,35) |
| **Sinais só nos pequenos, sem diferença confirmada** | Título com número (+15,4%), CAIXA ALTA (+15,3%), capítulos (+27,1%), colab/versus (−21,6%) | Baixa: significativos dentro dos pequenos, mas o teste de interação contra 200k+ não confirma (q da diferença de 0,07 a 0,71) |
| **Só aparece em canais grandes** | Legenda própria (+28,6% nos 200k+; nos pequenos só 3,8% dos vídeos e 14 canais têm, IC de −6% a +71%); penalidade de postar com menos de 2 dias (−8,8%); fim de semana +5,7% (q = 0,15, fraco) | Média para legenda e intervalo; baixa para fim de semana |

### 3.4 Anomalias em canais pequenos

261 vídeos com 10x ou mais o normal do próprio canal (208 robustos), 72 com 30x ou mais e 12 com 100x ou mais, em 66 dos 107 canais. São concentrados: os 8 canais com mais anomalias somam 88 (34%). Breakouts têm duração mediana de 21 min (contra 17 min nos demais vídeos dos pequenos) e idade mediana de 171 dias (143 na base).

**O que separa os breakouts dentro do mesmo canal** (LPM com efeito fixo, BH; `peq_02_anomalias_tracos_within.csv`): só a duração. Dobrar a duração soma +1,7 ponto percentual na chance de 10x+ (IC +0,8 a +2,7; q = 0,010). Nenhum traço de título, texto de capa, rosto, cor, intervalo ou dia sobrevive.

**Capas de breakouts x controles do mesmo canal** (leitura Gemini, diferença dentro do canal, 66 canais; `peq_02_anomalias_vs_controles_gemini.csv`): breakouts têm **menos** rosto (72,9% contra 81,5%; −9,4 pp, IC −14,2 a −4,4, q < 0,001) e menos expressão séria/concentrada (−7,5 pp, q < 0,001). Rosto grande, olhar para a câmera e estilo foto também aparecem menos (q ≈ 0,15). Texto, setas, números e comparação não diferem. Leitura: o vídeo que fura a bolha de um canal pequeno tende a vender **o assunto** (objeto, cena, situação), não o criador, o que combina com a ideia de que esse público ainda não conhece a pessoa.

**Palavras super-representadas nos títulos de breakouts** (`peq_02_palavras_anomalias_pequenos.csv`): "filme", "completo", "dublado", "iceberg", "ultimate", "accessories", "júri". Quase todas vêm de 1 ou 2 canais, portanto refletem formatos de canais específicos, não fórmulas gerais.

**Exemplos reais de canais pequenos furando a bolha**

| Canal | Subfaixa | Inscritos | Nicho | Título | Views | Normal do canal | Múltiplo | Duração |
|---|---|---:|---|---|---:|---:|---:|---:|
| CASOS REAIS DE TRIBUNAL DO JÚRI | pequeno | 11.300 | documentário PT | TESTEMUNHA É PRESA EM FLAGRANTE APÓS MENTIR DURANTE JULGAMENTO I JUIZ THIAGO FLORES NÃO PERDOOU | 877.734 | 3.221 | 272x | 19 min |
| MooMelloKids (rimas em hindi; ver limitações) | emergente | 56.300 | infantil EN | Meow Meow Billi Karti, Hindi Rhyme For Kids | 2.288.687 | 4.303 | 532x | 11 min |
| NetMovies Comédia | emergente | 165.000 | entretenimento PT | VIVER, AMAR E APRENDER (2020), Filme de Comédia Completo Dublado | 784.114 | 2.956 | 265x | 99 min |
| Dalton Litz | emergente | 90.500 | finanças EN | The Research Tools Robinhood Doesn't Give You | 622.922 | 2.771 | 225x | 12 min |
| Ruthinha Fitness | pequeno | 17.800 | esportes PT | Como fazer halteres de cimento, peso caseiro para malhar em casa | 156.849 | 755 | 208x | 5 min |
| Navigating Geography | pequeno | 19.500 | educação EN | 50 Geography Facts You Won't Believe Are Real | 419.999 | 2.399 | 175x | 21 min |
| Shiny Days | emergente | 62.000 | lifestyle EN | Aesthetic room + desk makeover, Pinterest & Korean-inspired, IKEA haul | 463.317 | 2.885 | 161x | 21 min |
| Viroscopo | emergente | 75.100 | documentário PT | O ICEBERG DE CASOS CRIMINAIS BRASILEIROS | 736.045 | 6.567 | 112x | 135 min |
| O Essencial com Camila | pequeno | 26.600 | lifestyle PT | FAXINA EM 30 MINUTOS: O Método Que Salvou Minha Casa | 187.301 | 1.775 | 106x | 17 min |
| Ashley M. Fox | emergente | 153.000 | finanças EN | My Top 3 REITs for Passive Income in 2026 | 182.561 | 1.886 | 97x | 46 min |
| Sacani Cortes | emergente | 90.600 | educação PT | A ORIGEM DA ÁGUA E DA VIDA, AMBAS SÃO EXTRATERRESTRES | 571.916 | 7.752 | 74x | 37 min |
| Riquezas e Finanças | pequeno | 38.000 | finanças PT | Os 3 PIORES INVESTIMENTOS para depois dos 40 anos! | 178.274 | 2.465 | 72x | 20 min |
| OLEKSII WILD COOKING | pequeno | 48.400 | culinária EN | Garlic Butter Steak Cooked Over a Campfire in Rainy Alaska Forest | 2.504.779 | 35.281 | 71x | 20 min |
| The Top Tech Insider | pequeno | 8.620 | tech EN | 5 Phone Brands ROBBING You Blind and 5 That Are Worth The Money | 234.882 | 4.587 | 51x | 19 min |

Padrão comum: tema de interesse amplo e concreto (dinheiro, casa, julgamento, curiosidade), promessa clara no título, frequentemente com número ou palavra em caixa alta, duração de 15 a 45 min, capa centrada no assunto. "O Essencial com Camila" teve 4 breakouts na mesma fórmula (faxina com método ou segredos de profissional), sinal de série que funciona. Lista completa: `resultados/peq_02_anomalias_pequenos_lista.csv`.

## 4. Evidência estatística

- Volatilidade e concentração, nível do canal, ajustado por nicho, idioma e nº de vídeos (HC3): pequenos x 200k+: top 10% +5,8 pp, Gini +0,061, DP de y +0,133 (q = 0,014 nos três). Pequeno e emergente contra médio: diferenças pequenas e não significativas (q de 0,35 a 0,98). Grande e gigante contra médio: top 10% −8,9 e −9,3 pp (q ≤ 0,006).
- Anomalias 10x+, LPM vídeo a vídeo ajustado por nicho, idioma e idade, EP por canal: pequeno +6,2 e emergente +6,6 por mil contra médio (q = 0,52); grande −13,7 por mil (q = 0,014), gigante −12,4 (q = 0,068).
- Ruído de contagem: restringindo a canais com mediana de 1.000 views ou mais, o DP de y fica 1,07 (pequeno), 1,02 (emergente), 0,93, 0,78 e 0,70, então a volatilidade não é só artefato de vídeos com poucas views.
- Dentro dos pequenos, o DP de y quase não varia com o log de inscritos (−0,02), o que reforça que o salto acontece por volta de 2 milhões, não entre 5 mil e 200 mil.
- Todos os efeitos dentro do canal: efeito fixo de canal, EP agrupado por canal, BH por família (grupo × alvo). Bootstrap clusterizado de 1.000 reamostras nas medianas, taxas e momentum.

## 5. Visualizações

- `graficos/peq_01_cobertura_e_volatilidade_5portes.png`: cobertura, concentração no top 10%, DP de y e anomalias 10x+ (com as robustas) nos 5 portes, com IC 95%.
- `graficos/peq_02_efeitos_pequenos_vs_grandes.png`: efeitos dentro do canal lado a lado (duração, legenda, título, capa, intervalo, momentum) com IC 95%; ◆ marca diferença significativa.
- `graficos/peq_03_duracao_e_anomalias_pequenos.png`: curva de duração (spline) pequenos x 200k+, breakouts por múltiplo (10x, 30x, 100x) e anatomia descritiva dos breakouts.

## 6. Descobertas inesperadas

1. **A fronteira não é 200 mil, é por volta de 2 milhões.** Pequeno, emergente e médio formam um bloco parecido em concentração, volatilidade e anomalias; grandes e gigantes formam outro, bem mais estável.
2. **Breakouts de canal pequeno mostram menos o rosto do criador.** Dentro do mesmo canal, o vídeo que estoura tem rosto em 73% das capas contra 82% nos vídeos normais.
3. **Imitar a "cara" de capa de canal grande não ajuda.** O visual é distinguível (AUC 0,76), mas aproximar-se dele não rende nada dentro do canal; manter o padrão visual próprio, sim.
4. **Duração pesa mais para pequenos** (+30% por dobro contra +15%) e é o único traço que prevê breakouts dentro do canal.
5. **Legenda própria, forte nos grandes, praticamente não existe nos pequenos** (3,8% dos vídeos), então não dá para testá-la ali.
6. **Pequenos publicam duas vezes mais seguido** (intervalo mediano de 2 dias contra 4 a 5), mas a penalidade de postar com menos de 2 dias só aparece com clareza nos 200k+.

## 7. Limitações e vieses (incluindo a revisão do gemini-4-carbon)

A revisão independente (`resultados/revisao_carbon.md`, gerada às 21h11 sobre os mesmos números finais de duração, novidade, volatilidade, momentum e títulos; a única mudança posterior foi harmonizar rótulos `g_*`, o que não altera nenhum número citado acima) apontou, e esta frente incorpora:

- **Viés de descoberta e sobrevivência**: só canais ativos e visíveis na busca (ver Auditoria). Resultados não valem para o pequeno parado ou invisível.
- **Ruído de contagem e mecânica do alvo**: com bases de 1 a 5 mil views, um vídeo que pega na busca vira facilmente 10x. Mitigado pela versão robusta (dois baselines) e pelo corte de 1.000 views, mas não eliminado.
- **Causalidade reversa**: título, capa, capítulos e legenda são lidos no dia da coleta. Criadores editam vídeos que estouraram ou que floparam. Capítulos, legenda, número e caixa alta no título podem ser consequência, não causa.
- **Composição de formato na duração**: o +112% acima de 60 min nos pequenos é puxado por filmes completos (NetMovies Comédia, Cine Emoção), júris integrais e icebergs longos. Até 30 min o efeito é sólido e parecido nos dois grupos; acima disso, depende do formato.
- **Idade e janela temporal**: janela de 209 a 346 dias nos pequenos contra 539 a 683 nos 200k+, e 67 canais truncados em 100 vídeos. A elasticidade negativa de idade nos pequenos reflete crescimento do canal e foi descartada como "efeito de idade".
- **Concentração de anomalias**: 34% dos breakouts vêm de 8 canais; palavras de breakout são de 1 ou 2 canais.
- **Pré-filtro de idioma imperfeito**: MooMelloKids (rimas em hindi com títulos parcialmente em inglês) passou na regra de idioma idêntica à da base principal. Fica registrado; remover esse canal não muda nenhuma conclusão de nível de canal, mas o exemplo de 532x deve ser lido com isso em mente.
- **Medição visual**: rosto por OpenCV (Haar) erra perfil e desenho; o Gemini leu 885 capas com prompt de rótulos longos, equivalente em significado ao esquema curto da base principal (rótulos harmonizados). Na amostra aleatória (cerca de 420 vídeos) o poder para efeitos de capa é baixo.
- **Discordância com a revisão**: o Carbon sugeriu descartar a comparação Gemini de breakouts x controles por "não ter efeito fixo". Ela é feita dentro do canal (diferença média entre breakouts e controles do mesmo canal, bootstrap por canal), então foi mantida, com confiança moderada (66 canais, controles escolhidos com |y| < 0,3).
- **Sem CTR, impressões, retenção ou inscritos por vídeo.** Nenhuma conclusão sobre "taxa de clique".
- Correlação não é causalidade em nenhum item deste relatório.

## 8. Recomendação prática (canal de 5k a 200k)

1. **Faça vídeos de 15 a 30 min quando o tema sustentar.** Dentro do canal, 20 a 30 min rende +40% sobre 10 a 15 min, e duração é o único traço ligado a breakouts. Ressalva: não esticar; o ganho supõe retenção real.
2. **Fique no seu tema e no seu padrão visual.** Fugir do assunto habitual custa cerca de 15% por dp e fugir do visual habitual cerca de 11%; copiar a estética de canal grande não compensa.
3. **Na capa, venda o assunto, não o rosto.** Breakouts dos pequenos têm menos rosto e menos expressão séria. Teste capas centradas no objeto ou na cena em vídeos de tema amplo.
4. **Títulos concretos com número** (lista, valor, prazo) e uma palavra de ênfase em caixa alta são candidatos fortes a teste A/B, com ganho estimado de 15% (confiança baixa, pode ser causalidade reversa).
5. **Quando um vídeo estourar, publique o próximo no mesmo veio rapidamente** (+12% no vídeo seguinte a um hit) e transforme a fórmula em série, como "O Essencial com Camila" fez com faxina. Evite colabs/versus como aposta de alcance até testar no seu canal (−22% nos pequenos, confiança baixa).

### Notas

| Critério | Nota (0 a 10) | Justificativa |
|---|---:|---|
| Impacto | 8 | Mostra que a lógica de distribuição muda por volta de 2M, não em 200k, e dá 3 alavancas universais (duração, consistência temática, consistência visual) |
| Confiança | 6 | Efeitos dentro do canal, EP agrupado, BH e bootstrap; mas viés de descoberta, snapshot único e metadados editáveis |
| Aplicabilidade | 8 | Recomendações acionáveis já no próximo vídeo, testáveis no próprio canal |
| Facilidade | 7 | Duração, tema e padrão visual são baratos de ajustar; séries a partir de hits exigem planejamento |

## Hipóteses descartadas

1. **"Canais pequenos são um mundo à parte de 200 mil para baixo."** Pequeno e emergente não diferem do médio em concentração, volatilidade nem anomalias (q ≥ 0,35). A ruptura está entre médio e grande.
2. **"Pequenos dependem mais de capa chamativa (cor, contraste, rosto, muito texto)."** Nenhum desses traços move views dentro do canal em nenhum porte.
3. **"Ter cara de canal grande na capa ajuda o pequeno a crescer."** Nulo (−2,6% por dp, q = 0,30).
4. **"Mudar de assunto é o caminho para o breakout."** Novidade temática reduz views e não aumenta a chance de 10x.
5. **"Postar todo dia ou quase todo dia prejudica o canal pequeno."** Menos de 2 dias desde o anterior: −4,4%, q = 0,59 nos pequenos (só nos 200k+ a penalidade é clara).
6. **"Vídeo antigo de canal pequeno perde views com o tempo."** A elasticidade negativa de idade é artefato do crescimento do canal.
7. **"Horário ou dia certo destrava canal pequeno."** Nada sobrevive a BH.
8. **"Engajamento e alcance brigam mais em canais pequenos."** Elasticidade de curtidas igual (0,77 x 0,80, p = 0,32); comentários só levemente menor (p = 0,046).
9. **"Texto da capa que complementa o título rende mais."** Pela leitura OCR, efeito nulo nos pequenos (−4,6%, q = 0,49) e levemente negativo nos 200k+ (q = 0,17).

## Arquivos

- Dados: `dados/base_pequenos.parquet` (8.312 × 132), `dados/canais_pequenos.csv`, `dados/uso_gemini_pequenos.csv`, `dados/uso_youtube_api.csv`, `dados/title_embeddings_768_pequenos.parquet`, `dados/thumb_embeddings_768_pequenos.parquet`, `dados/thumbs_gemini_pequenos.jsonl`, `dados/amostra_gemini.csv`, `dados/thumbs/`, `dados/api/`.
- Resultados: `resultados/peq_01` a `peq_06`, `auditoria_*.csv`, `revisao_carbon.md`, `resumo_frente_pequenos.json`.
- Scripts: `01_descoberta.py`, `02_selecao.py`, `03_coleta_api.py`, `04_thumbs_cv_ocr.py`, `05_base.py`, `05b_auditoria.py`, `06_classif_gemini.py`, `07_embeddings.py`, `08_comparativo.py`, `08b_visual_embeddings.py`, `09_graficos.py`, `10_revisao_carbon.py`, `peq_utils.py`, `stats_utils.py`.
