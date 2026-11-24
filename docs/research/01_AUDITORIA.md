# 01 · Auditoria da base

Gerado por `scripts/01_auditoria.py` (roda em cerca de 7 s, sem rede). Números completos em `resultados/auditoria.json` e nos CSVs `resultados/auditoria_*.csv`. Gráfico: `graficos/01_funil_e_cobertura.png`.

## 1. Fontes e reconciliação

| Fonte | Linhas | Duplicatas | Observação |
|---|---:|---:|---|
| `dados/canais_selecionados.csv` | 257 canais | 0 | estratos nicho × idioma × porte |
| `dados/api/*.jsonl` (257 arquivos) | 22.405 vídeos | 0 `video_id` | 7 arquivos vazios (canal não encontrado na API); 207 de 250 canais bateram o limite de 100 vídeos |
| `dados/dataset.parquet` | 17.882 × 88 | 0 | reproduzido exatamente pelo funil abaixo (checagem automática = verdadeiro) |
| `dados/thumb_features.csv` / `thumb_ocr.csv` | 22.405 cada | 0 | cobrem 100% da base final |
| `dados/thumbs_gemini.jsonl` | 17.876 | 0 | 0 fora da base; 6 vídeos da base sem leitura (0,03%) |

Coleta: YouTube Data API v3, playlist `UULF` (só vídeos longos) de cada canal, do mais recente para o mais antigo, até 100 vídeos publicados há mais de 35 dias, pulando transmissões ao vivo. Snapshot único em 23/11/2026, entre 16h23 e 16h56 (horário de Brasília).

## 2. Funil de perdas

| Etapa | Vídeos | Canais |
|---|---:|---:|
| Canais selecionados | – | 257 |
| Registros brutos | 22.405 | 250 |
| Com views > 0 | 22.403 | 250 |
| Duração > 3 min | 21.099 | 250 |
| Sem `#shorts` no título/descrição | 21.073 | 250 |
| Idade ≥ 30 dias | 21.073 | 250 |
| Idioma do canal coerente com o estrato | 18.004 | 217 |
| Canal com ≥ 15 vídeos válidos | **17.882** | **203** |

Canais excluídos (lista em `resultados/auditoria_canais_excluidos.csv`): 33 por idioma divergente, 14 por ter menos de 15 vídeos longos válidos, 7 sem registros na API.

### Vieses de seleção encontrados

1. **Sobrevivência de formato longo.** Os gigantes que saíram por falta de vídeos longos são justamente canais que vivem de vídeo curto ou de clipe curto: Enaldinho, rezendeevil, Ms Rachel, Galinha Pintadinha e Turma da Mônica. A base representa canais em que o vídeo longo (> 3 min) é central. Qualquer conclusão sobre "gigantes" vale para gigantes de vídeo longo.
2. **Perda desigual por nicho.** Lifestyle perdeu 45% dos canais e 40% dos vídeos, documentário 41% e 42%, entretenimento 32% e 28%, infantil 23% e 32%. Tech (2%), finanças (3%) e educação (4%) quase não perderam nada. A maior parte da perda vem do filtro de idioma, sinal de que a semente desses nichos tinha muitos canais multilíngues ou dublados (um canal coreano chegou a entrar no estrato `pt`).
3. **Perda desigual por porte.** Médio perdeu 28% dos canais, gigante 22% e grande 11%. Restaram 83 canais médios, 82 grandes e 38 gigantes.
4. **Duração mínima pesa no infantil.** O corte de 3 min removeu 24% dos vídeos do infantil e 12% de esportes, contra menos de 3% na maioria dos nichos.
5. **Não existem canais pequenos.** O menor porte é "médio", de 200 mil a 2 milhões de inscritos. Perguntas sobre canais com menos de 200 mil inscritos **não são respondíveis** com esta base.
6. **Estratos rasos.** 12 células nicho × idioma × porte ficaram com 0 ou 1 canal (`resultados/auditoria_canais_por_estrato_final.csv`). Recortes de três níveis não são confiáveis.
7. **Janela temporal desigual.** A janela de cada canal vai de 5 dias a 13,3 anos (mediana de 599 dias). Educação (1.381 dias) e entretenimento (1.009) cobrem anos; documentário (218) e esportes (283) cobrem meses. Comparar nichos mistura épocas diferentes da plataforma. 178 canais têm a janela truncada em 100 vídeos e 25 têm o histórico longo completo.
8. **Peso por canal equilibrado.** Os 10 maiores canais somam só 5,6% dos vídeos (mediana de 100 vídeos por canal), então nenhum canal domina a amostra.

## 3. Qualidade, consistência e duplicidades

- **Duplicidades:** 0 `video_id` repetido em qualquer arquivo. 142 vídeos repetem o título exato de outro vídeo do mesmo canal (158 depois de normalizar), quase todos séries e episódios de canais infantis e de música. Só 1 título é idêntico entre canais. Nenhuma URL de miniatura se repete. Decisão: manter, porque são vídeos distintos, e listar em `resultados/auditoria_titulos_repetidos_no_canal.csv`.
- **Consistência lógica:** 0 vídeos com views ≤ 0, 0 com curtidas > views, 0 publicados depois da coleta. 5 vídeos têm mais comentários que curtidas (é possível, mantidos). 78 vídeos têm mais de 3 horas e 2 mais de 10 horas (máximo de 16,5 h, que são compilações e lives reaproveitadas): ficam, e a análise de sensibilidade corta os extremos de `y`. Mínimo de 157 views; nenhum vídeo com menos de 100.
- **Idade:** de 35 a 5.397 dias, com mediana de 303. 5% dos vídeos têm menos de 47 dias e 5% têm mais de 7 anos.
- **Alvo `y`:** mediana 0,006, assimetria 0,53, curtose 3,5. 321 vídeos fizeram 10x ou mais o normal do canal e 127 fizeram 10x ou menos; 159 têm |y| > 3.
- **Inscritos:** o snapshot da API bate com o da seleção em todos os canais (nenhum desvio acima de 10%) e nenhum canal mudaria de porte.

### Ausências estruturais (não são dado faltante aleatório)

| Campo | Ausente | Explicação |
|---|---:|---|
| Comentários | 427 ausentes + 1.613 zeros | **Todos** os 1.879 vídeos `made_for_kids` têm 0 ou nenhum comentário visível (0,0% com comentário), porque o YouTube desativa comentários nesses vídeos. Na base mestra viraram `NaN` (`comment_count_valido`); não significam "zero engajamento". Fora do infantil restam 58 ausentes e 103 zeros. |
| Curtidas | 486 (2,7%) | 4 canais escondem curtidas em 100% dos vídeos e 5 em parte deles; 100 casos são infantis. |
| Faixas de áudio / capítulos (yt-dlp) | 14.220 | só existem no subconjunto coletado antes da troca para a API (3.662 vídeos). Não usar na base toda. |
| `tem_nome_proprio` | 14.511 | heurística não se aplica a títulos em Title Case (comuns em inglês). Variável praticamente inutilizável. |
| Gemini (miniatura) | 6 | falhas pontuais de leitura. |

## 4. Auditoria do alvo e vazamento de dados

**Como `y` foi calculado** (`scripts/04_features.py`): `y = log(views) − mediana(log(views) dos 10 vídeos do mesmo canal mais próximos em data, sem o próprio vídeo)`.

- Recalculei a base para todos os 17.882 vídeos e ela é **idêntica** à salva.
- **O próprio vídeo não entra** na própria base (não há vazamento direto).
- **Mas a janela é bilateral:** em média 49,3% dos 10 vizinhos foram publicados **depois** do vídeo. Isso é aceitável para descrever o passado ("acima do normal daquela fase do canal"), mas tem duas consequências:
  1. não pode ser usado como alvo de um preditor em tempo real;
  2. cria **dependência mecânica entre vídeos vizinhos**. Se o vídeo seguinte foi fraco, ele baixa a base do anterior e infla o `y` do anterior. Na prática isso produziu uma falsa "ressaca depois do hit" (−8%, IC 95% −13% a −2%), que **some e inverte de sinal** quando o hit é definido por um resíduo que não usa vizinhos (ver Investigação F). Regra: nunca condicionar em `y` de um vídeo e medir `y` do vizinho.
- `y_loo_idade` (definido abaixo) tem caudas pesadas (máximo 19,9) em canais com poucos vídeos e idade concentrada; use-o com corte ou só como sensibilidade.

**Alvos alternativos criados na base mestra:**

| Alvo | Definição | Uso recomendado | Correlação de Spearman com `y` |
|---|---|---|---:|
| `y` | original, 10 vizinhos bilaterais | descrição retrospectiva | 1 |
| `y_loo` | log(views) − mediana dos demais vídeos do canal | sensibilidade sem janela | 0,82 |
| `y_passado` | log(views) − mediana dos 10 vídeos **anteriores** (NaN se houver menos de 5) | preditor sem olhar o futuro; motor de consulta | 0,89 |
| `y_loo_idade` | resíduo leave-one-out exato de log(views) ~ log(idade) dentro do canal | controle de exposição | 0,87 |

Para os modelos da Fase 2: **GroupKFold por canal** (nenhum canal no treino e no teste ao mesmo tempo) e **validação temporal** (treino com vídeos até uma data e teste depois, usando `y_passado`).

### Taxonomia das 129 variáveis da base mestra

Lista completa em `resultados/auditoria_taxonomia_variaveis.csv`.

| Classe | Nº | Exemplos | Risco |
|---|---:|---|---|
| 1. Pré-publicação estrita | 28 | duração, categoria, `made_for_kids`, dia e hora, idioma declarado, intervalo desde o vídeo anterior, publicações nos 30 dias anteriores | baixo |
| 2a. Pré-publicação **editável** (texto e legenda) | 32 | título e traços, descrição, tags, capítulos, `legenda_manual` | **causalidade reversa**: tudo foi lido na coleta, não na publicação. Canais trocam título de vídeo que flopou e sobem legenda ou tradução em vídeo que já performou. O +28% da legenda pode ser em parte efeito, não causa. |
| 2b. Pré-publicação **editável** (miniatura) | 32 | brilho, OCR, as 13 leituras do Gemini | mesmo risco: a capa vista é a atual, não necessariamente a do lançamento (testes A/B de miniatura, trocas). |
| 3. Canal no snapshot | 12 | inscritos, porte, total de vídeos, nicho, idioma | posterior a quase todos os vídeos. Um vídeo que estoura aumenta os inscritos (causalidade reversa) e há viés de sobrevivência (só entra quem chegou a 200 mil). Usar só como estrato. |
| 4. Pós-publicação, alvo ou vazamento | 22 | views, curtidas, comentários, taxas, `y` e variantes, idade | nunca como preditor. Idade entra **só como controle de exposição**. |

## 5. Base mestra (`dados/base_mestra.parquet`, 17.882 × 129)

Acrescenta ao `dataset.parquet`:
- **13 leituras do Gemini** com prefixo `g_` (mais `g_tem_rosto`, `g_5mais_palavras` e `g_sem_texto`).
- **Flags de cobertura:** `tem_gemini`, `tem_thumb_local`, `likes_disp`, `comentarios_disp`.
- **Engajamento:** `like_rate`, `comment_rate` (com infantil = NaN), `log_like_rate`, `log_comment_rate` e versões relativas ao próprio canal por leave-one-out (`*_rel`, exigindo pelo menos 10 vídeos com o dado).
- **Alvos alternativos:** `y_loo`, `y_passado`, `y_loo_idade` e `y_pct_canal` (percentil dentro do canal).
- **Cadência estritamente passada,** calculada sobre **todos os 22.405 registros brutos** (inclusive os vídeos filtrados depois, porque também foram publicações):
  - `gap_ant_dias` (NaN no 1º vídeo da janela: 184 casos) e `gap_faixa`;
  - `n_pub_7d_ant` e `n_pub_30d_ant`, com NaN quando a janela truncada não cobre o período (2.106 casos);
  - `pos_janela`, `prev_video_id`, `y_prev`, `janela_truncada`, `n_bruto_canal`.
  
  A janela é consecutiva dentro dos uploads longos, exceto lives e itens indisponíveis na API. Shorts nunca entram, então a cadência medida é a **de vídeos longos**. 2 pares foram publicados no mesmo segundo (intervalo 0).

## 6. Viabilidade estatística das 8 frentes

| Frente | Viável já | Exige cautela ou amostra reduzida | Não mensurável |
|---|---|---|---|
| A. DNA dos virais | top 10% e top 5% (1.789 e 895 vídeos), modelos com GroupKFold | top 1% = 179 vídeos de 62 canais: só efeitos grandes; interações apenas com correção forte | causa do estouro; origem do tráfego |
| B. Título + miniatura | texto completo, OCR, 13 traços do Gemini, imagens salvas (embeddings locais viáveis) | causalidade reversa (capa e título atuais) | CTR e impressões |
| C. Arquétipos | embeddings de título e miniatura + UMAP/HDBSCAN em 17.882 vídeos | estabilidade dos clusters (bootstrap) | – |
| D. Anomalias | 321 vídeos ≥ 10x (267 robustos a 3 baselines) em 88 canais | "canais pequenos" = só médios de 200 mil a 2 milhões | canais com menos de 200 mil inscritos |
| E. Duração | 17.882 vídeos, 3 min a 16 h, GAM e splines por nicho e porte | recortes nicho × porte com 1 a 3 canais | retenção |
| F. Longevidade e ritmo | intervalos, cadência, sequência e idade em corte transversal | idade confundida com crescimento do canal | curvas de views no tempo (só um snapshot): explosivo, evergreen e crescimento tardio continuam **hipóteses** |
| G. Oportunidades | nicho × arquétipo × porte com desempenho relativo | oferta e demanda sem dados de busca | volume de busca, concorrência real |
| H. Engajamento | curtidas em 97% e comentários em 89% (sem infantil) | razão com views no denominador; 9 canais escondem curtidas | texto dos comentários, retenção |

**Ausentes em toda a base:** CTR, impressões, retenção, origem do tráfego, transcrições e histórico de views ao longo do tempo.

## 7. Pacotes no ambiente virtual local

| Pacote | Versão |
|---|---|
| scikit-learn | 1.9.1 |
| statsmodels | 0.15.0 |
| scipy | 1.18.1 |
| pandas / numpy / pyarrow / matplotlib | 3.1.1 / 2.5.5 / 26.0.1 / 3.11.2 |
| xgboost, lightgbm, shap, umap-learn, hdbscan, sentence-transformers, pygam, torch | **não instalados** (instalar na Fase 2: `pip install xgboost lightgbm shap umap-learn hdbscan pygam sentence-transformers torch --index-url` CPU) |

Observação: o scikit-learn 1.9 já traz `HistGradientBoosting` e `sklearn.cluster.HDBSCAN`, que servem de plano B se algum pacote não instalar.
