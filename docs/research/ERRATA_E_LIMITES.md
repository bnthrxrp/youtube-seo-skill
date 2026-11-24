# Errata Formal, Limites Metodológicos e Plano de Reprocessamento

Este documento unifica a auditoria sênior do laboratório de pesquisa e do motor offline (`Idea Advisor`). Nenhum problema dependente dos dados brutos foi declarado como resolvido na base analítica. As correções de código aplicáveis sem reprocessamento já estão validadas no motor offline (152 testes automatizados aprovados), enquanto os itens econométricos e amostrais permanecem estritamente marcados como **PENDENTE DE REPROCESSAMENTO**, acompanhados do protocolo exato de execução e aceite.

---

## 1. Modelo de Banner de Revisão Obrigatório (Aplicado no topo dos relatórios históricos)

O banner abaixo já está aplicado no topo dos relatórios históricos (02_PRIMEIRAS_DESCOBERTAS, HIPOTESES_LOG, RELATORIO_ML_AEFG, RELATORIO_THUMBS_VISUAL, RELATORIO_TITULOS_ARQUETIPOS_BCG, RELATORIO_CANAIS_PEQUENOS, RELATORIO_FINAL_CONSOLIDADO, GUIA_PRATICO_THUMBNAILS). Se algum relatório for regenerado e perder o cabeçalho, reaplique. Os 7 relatórios congelados originais (`02_PRIMEIRAS_DESCOBERTAS.md`, `HIPOTESES_LOG.md`, `RELATORIO_2A.md`, `RELATORIO_THUMBS_VISUAL.md` (2B), `RELATORIO_2C.md`, `RELATORIO_2D.md` e `CONSOLIDADO.md`) não forem editados em lote na etapa de regeneração documental, aplique obrigatoriamente o cabeçalho abaixo ao consultá-los:

```markdown
> **AVISO DE AUDITORIA E GOVERNANÇA ESTATÍSTICA (ERRATA ATIVA):**
> Este relatório contém estimativas geradas antes do fechamento da auditoria metodológica sênior. Ao consultar este material, aplique obrigatoriamente as seguintes travas:
> 1. **Teto preditivo:** Metadados estáticos (título, capa e horário) explicam menos de 2,5% da variância intra-canal ($R^2 \le 0,025$). Nenhum coeficiente deve ser lido como garantia causal de alcance.
> 2. **Recomendações firmes vs. Hipóteses A/B:** Como **recomendação prescritiva firme** (`faixa = validada` em `docs/research/data/ranking_alavancas_revisado.csv`), valem exclusivamente itens com $q < 0,05$, IC 95% limpo sem cruzar zero e penalização de endogeneidade. Itens na zona $0,05 \le q < 0,15$ (ou rebaixados por limites da base bruta) pertencem à faixa `hipotese_ab`: **hipótese A/B não é recomendação**, servindo apenas para experimentação controlada no *Testar e Comparar* do YouTube Studio. Ignore integralmente clusters visuais (`HDB-*`, `KM12-*`), ângulos de vídeo e qualquer item com $q \ge 0,15$ (`faixa = removida`).
> 3. **Reconciliações e pendências:** Em caso de conflito sobre alinhamento Capa × Título ou Momentum pós-hit, ou para verificar variáveis marcadas como `PENDENTE DE REPROCESSAMENTO` (vazamento temporal residual, filtro de canais pequenos e denominador de idade), prevalece o disposto em `docs/research/ERRATA_E_LIMITES.md`.
```

---

## 2. Reconciliação Explícita de Contradições Documentais

Até que o reprocessamento integral das bases seja executado, as seguintes determinações revogam interpretações conflitantes entre fases:

### 2.1. Alinhamento Capa × Título (`02_PRIMEIRAS_DESCOBERTAS.md` vs. `CONSOLIDADO.md` / Frente 2C)
* **O conflito:** Na Fase 1 (`02_PRIMEIRAS_DESCOBERTAS.md` e `HIPOTESES_LOG.md`, ID `A-5`), afirmou-se que texto de capa que *complementa* (não repete) o título ganha $+4,8\text{ p.p.}$ na chance de Top 5% ($q = 0,037$). Na Fase 2 (`CONSOLIDADO.md` #14 e `RELATORIO_2C.md`), afirmou-se o oposto: *aproximar/alinhar* o texto da capa ao título ganha $+4,1\%$ na média ($q = 0,034$) e complementar tem efeito nulo.
* **Qual versão vale até o reprocessamento:** Vale a versão da **Frente 2C / Consolidado** (repetir ou alinhar os termos centrais do título na capa não é punido pelo algoritmo e associa-se a leve ganho médio de $+4,1\%$; a proibição de repetir palavras do título está refutada).
* **Por quê:** A Fase 1 avaliou apenas um corte binário de cauda (Top 5% contra a faixa 40% a 60%, descartando 75% da amostra) usando correspondência léxica bruta e misturando capas sem nenhum texto OCR no grupo de referência (zero sobreposição literal era lido como "complementaridade"). A Frente 2C utilizou embeddings densos contínuos sobre a distribuição completa intra-canal. O ajuste definitivo (regressão conjunta restrita apenas às capas com OCR válido) permanece pendente de reprocessamento no Item 4.

### 2.2. Momentum Pós-Hit (`HIPOTESES_LOG.md` / Frente 2D vs. Frente 2A / `CONSOLIDADO.md`)
* **O conflito:** Em `HIPOTESES_LOG.md` (ID `F-5`, $+9,4\%$) e em `RELATORIO_2D.md` ($+12,3\%$ nos canais pequenos, rotulado como "Universal de alta confiança"), o efeito positivo de publicar logo após um sucesso consta como sustentado. Já em `RELATORIO_2A.md` e no `CONSOLIDADO.md`, consta como **descartado** nos canais `200k+` ($+2,4\%$, IC cruzando zero após controle de tendência quadrática).
* **Qual versão vale até o reprocessamento:** O efeito fica classificado como **INCONCLUSIVO / HIPÓTESE NÃO CONFIRMADA** (removido do ranking principal e rebaixado no inventário).
* **Por quê:** Ambas as pontas sofreram distorções metodológicas opostas. Nos canais `200k+` (2A), o ajuste de uma parábola quadrática bilateral em séries curtas ($\le 100$ vídeos) usou informação futura e absorveu picos reais de curto prazo (*over-detrending*). Nos canais pequenos (2D), não se aplicou controle de tendência local e a amostra sofre de viés de captura por busca recente (*ascertainment bias*, ver Item 3). Portanto, nem a validação universal da 2D nem o descarte por parábola bilateral da 2A são limpos o suficiente para prescrição.

---

## 3. Fórmula de Prioridade Revisada no Ranking

No arquivo `docs/research/data/ranking_alavancas_revisado.csv`, o peso somado de `Aplicabilidade` e `Facilidade` foi reduzido de 30% para **15%** (7,5% cada), impedindo que ações triviais, porém ruidosas ou endógenas, inflem o topo da lista. O peso de `Confiança` subiu para 45% e `Impacto` manteve 40%:

$$\text{Prioridade Revisada} = 0,40 \times \text{Impacto} + 0,45 \times \text{Confiança} + 0,075 \times \text{Aplicabilidade} + 0,075 \times \text{Facilidade}$$

Regras adicionais aplicadas ao CSV:
1. **Trava de entrada (`faixa = validada`, 7 itens):** Exige $q < 0,05$ (teste formal BH na coluna `q_bh`, vedado $p$-valor bruto sem ajuste, bootstrap sem multiplicidade ou mineração de pares sem validação fora da amostra), IC 95% limpo sem cruzar zero, ausência de vazamento temporal por alvo/centroide bilateral e estimativa agregada quando não há interação formal por porte ou idioma. Apenas esta faixa constitui recomendação firme (#2, #5, #6, #9, #11, #14 e #15). Os itens #1 (amostra 5k a 200k contaminada e sem interação vs 200k+), #3, #4, #7, #8 (regras de cadência e desvio com look-ahead residual ou sem $q$ BH disponível) e #10 (1ª pessoa unificada na estimativa agregada de $-8,1\%$, $q = 0,066$, por falta de interação formal idioma $\times$ traço) permanecem em `hipotese_ab` (15 itens no total).
2. **Faixa experimental (`faixa = hipotese_ab`, 8 itens):** Itens com $0,05 \le q < 0,15$, oriundos de mineração exploratória de 1.802 pares sem split de validação, sem interação confirmada contra `200k+`, ou cuja estimativa limpa em `y_passado` não traz IC parametrizado na tabela congelada (#12) saem da prescrição direta. Hipótese A/B não é recomendação: indica apenas candidata legítima para teste controlado no YouTube Studio.
3. **Remoção (`faixa = removida`, 4 itens):** Itens com $q \ge 0,15$ (#21), sem $q$-valor formal validado (#20), baseados em clusters visuais `HDB-*`/`KM12-*` (#16) ou na taxonomia contaminada de ângulos de vídeo (#25) são excluídos tanto das recomendações quanto das hipóteses A/B.
4. **Teto de endogeneidade:** Alavancas de duração, cadência/intervalo e legenda manual tiveram `Confiança` limitada ao teto máximo de **5**.

---

## 4. Auditoria Item a Item (1 a 17)

### Item 1: Corrupção numérica no denominador de `y_loo_idade` [CRÍTICO]
* **Status:** `PENDENTE DE REPROCESSAMENTO` (documentado nos relatórios; bloqueado no motor).
* **Onde está o texto antigo errado:**
  * `RELATORIO_THUMBS_VISUAL.md` (Fichas 20 e 22): cita exemplos com `"457.079.214,97x a mediana do canal"`.
  * `RELATORIO_2C.md` (análise de extremos): reporta resíduos logarítmicos $\ln = 19,9$.
* **Texto correto:** O cálculo sem piso de segurança para `y_loo_idade` gerou divisão por quase-zero nas bordas de idade (baseline implícito de $0,0033$ views), batendo artificialmente no teto de winsorização ($\pm 4$) e contaminando cortes de Top 5% e amostragens visuais. Múltiplos acima de $1.000\text{x}$ nessas fichas são artefatos numéricos e devem ser desconsiderados.
* **Procedimento de reprocessamento:**
  * *Script esperado:* `scripts/reprocess/01_rebuild_targets.py`
  * *Entradas:* `data/raw/videos_26194.parquet`, `data/raw/channels_310.parquet`
  * *Operação:* Truncar `log(idade_dias)` nos percentis P2 e P98 intra-canal antes da regressão de ajuste etário; impor piso estrito no denominador esperado `views_esperadas = np.maximum(pred_views, 250.0)` antes de extrair a razão logarítmica e aplicar winsorização em $\pm 4$.
  * *Critério de aceite numérico:* `max(exp(y_loo_idade_raw)) < 5000`, zero valores `NaN`/`Inf`, e fração de vídeos cravados no teto de winsorização ($+4,0$) inferior a $0,5\%$ da base.

### Item 2: Vazamento temporal residual (`look-ahead bias`) no alvo principal e nos centroides [CRÍTICO]
* **Status:** `PENDENTE DE REPROCESSAMENTO` (faixa espúria $>45\text{d}$ bloqueada em `normalizar_kb` e `secao_cadencia` do motor; linha #12 de volume semanal no CSV revisado ancorada diretamente em `y_passado` de $-4,8\%$, $q = 0,013$, e movida para `hipotese_ab` até reestimação do IC limpo).
* **Onde está o texto antigo errado:**
  * `CONSOLIDADO.md` (Ranking #3, #4, #7, #8, #12): usa coeficientes estimados sobre `y` bilateral (onde 49,3% dos vizinhos são futuros), reportando `"-9,6% por dobro"` no volume semanal e penalidades infladas de novidade.
  * `RELATORIO_2A.md` (seção de ML temporal 80/20): estima média do canal e ajuste de idade na série completa antes do corte temporal, gerando `"AUC = 0,24 no baseline histórico"`.
  * `RELATORIO_2C.md` e `RELATORIO_2D.md` (`peq_05_novidade_tematica.csv` e `peq_05b_visual_embeddings.csv`): calculam o centroide habitual do canal usando todos os vídeos da janela, incluindo os futuros.
* **Texto correto:** Regressões prescritivas de sequência, cadência, desvio temático/visual e validação 80/20 não podem usar vizinhos futuros. Se um canal pivota após um acerto, o centroide futuro migra na direção do novo tema, criando causalidade reversa mecânica contra vídeos exploratórios anteriores. Até o reprocessamento, considere o efeito de dobrar volume como $-4,8\%$ (`y_passado`, $q = 0,013$), pausa $>45\text{d}$ como nula e as penalidades de novidade como limites superiores superestimados.
* **Procedimento de reprocessamento:**
  * *Script esperado:* `scripts/reprocess/02_strict_expanding_window.py`
  * *Entradas:* `data/processed/videos_clean_targets.parquet`, matrizes de embeddings de título e imagem.
  * *Operação:* Construir `y_expanding_idade` e centroides `c_tema_past`, `c_vis_past` usando exclusivamente vídeos $t' < t$ do mesmo canal, exigindo histórico mínimo de 10 vídeos anteriores (descartando os 10 primeiros vídeos de cada canal da estimação, mantendo-os apenas na formação de histórico). Reestimar Frentes 2A (cadência e ML 80/20), 2C e 2D (novidade).
  * *Critério de aceite numérico:* Correlação zero por construção com choques futuros (teste unitário alterando views de $t+1 \dots T$ deve produzir variação de $0,000000$ nas features e no alvo em $t$); AUC do baseline histórico no split temporal 80/20 deve ficar $\ge 0,50$.

### Item 3: Contaminação por pirataria/terceiros e viés de busca recente em Canais Pequenos [CRÍTICO]
* **Status:** `PENDENTE DE REPROCESSAMENTO` (projeções $>60\text{ min}$ bloqueadas no motor; Alavanca #1 rebaixada para `hipotese_ab` no ranking revisado, com a observação sobre breakout de 10x reescrita como limitação por falta de pareamento por duração).
* **Onde está o texto antigo errado:**
  * `RELATORIO_2D.md` e `CONSOLIDADO.md` (Alavanca #1): `"Dobrar a duração (5k a 200k): +30,2%, único traço ligado a breakout de 10x nos pequenos"`, citando ganho de `"+111,7% em 60+ min"` e menor presença de rosto em breakouts sobre 107 canais pequenos.
* **Texto correto:** Os 107 canais pequenos foram capturados via busca recente (`yt-dlp` com filtro semanal/mensal) sem o funil de auditoria da Fase 1. Isso gerou viés de verificação (*ascertainment bias*) pró-canais hiperativos (mediana de 410 vídeos) e incluiu canais de filmes completos dublados (*NetMovies*, *Cine Emoção*), canais de cortes de terceiros (*Sacani Cortes*) e idioma incorreto (*MooMelloKids* em hindi). O salto em $60+\text{ min}$ está contaminado por longas-metragens não-autorais.
* **Procedimento de reprocessamento:**
  * *Script esperado:* `scripts/reprocess/03_audit_small_channels.py`
  * *Entradas:* `data/raw/small_channels_107.parquet`, metadados completos dos vídeos da Frente 2D.
  * *Operação:* Auditar manualmente e por heurística os 107 canais, expurgando reuploads de filmes/séries/TV, canais de cortes não-oficiais e canais fora de PT/EN; remover de cada canal remanescente o vídeo-semente publicado na janela da busca que originou sua descoberta (eliminando o pico artificial de captura); reestimar toda a bateria `peq_01` a `peq_06`.
  * *Critério de aceite numérico:* $100\%$ dos canais retidos classificados como autorais e em PT ou EN ($N$ esperado $\ge 75$ canais); zero vídeos-semente na amostra de regressão; recálculo completo da curva de duração acima de 45 minutos.

### Item 4: Esquizofrenia sobre Capa × Título e vazamento de Clusters Visuais no código [CRÍTICO]
* **Status:** `CORRIGIDO NO MOTOR` (expurgo total de `HDB-*` e `KM12-*`) / `DOCUMENTADO` (reconciliação na Seção 2.1) / `PENDENTE DE REPROCESSAMENTO` (regressão conjunta restrita a capas com texto).
* **Onde está o texto antigo errado:**
  * `02_PRIMEIRAS_DESCOBERTAS.md` e `HIPOTESES_LOG.md` (`A-5`): `"Texto da capa que complementa o título se associa ao topo (+4,8 pp, q = 0,037)"`.
  * `idea_advisor.py` (versão anterior, `secao_thumb`): recomendava clusters `HDB-87`, `KM12-07`, `HDB-39` e `KM12-09` mesmo após o `CONSOLIDADO.md` (`2B-10`) descartá-los como identidade de canal único.
* **Texto correto:** Clusters visuais não são receitas transferíveis entre canais e foram banidos do `knowledge_base.json` e do motor offline. Quanto à relação Capa × Título, prevalece que alinhar/repetir termos-chave do título na capa é seguro e levemente positivo ($+4,1\%$, $q = 0,034$), refutando o mito de punição por redundância.
* **Procedimento de reprocessamento (para cravar o efeito líquido de OCR):**
  * *Script esperado:* `scripts/reprocess/04_title_ocr_joint_fe.py`
  * *Entradas:* `data/processed/frente_2c_ocr_embeddings.parquet`
  * *Operação:* Rodar modelo de efeito fixo intra-canal em duas etapas: (1) dummy `tem_texto_ocr` na base completa; (2) subamostra estrita `len(ocr_limpo) >= 3` testando simultaneamente sobreposição lexical e similaridade cosseno densa (`embedding_titulo` vs. `embedding_ocr`), com erros agrupados por canal.
  * *Critério de aceite numérico:* Subamostra restrita a $100\%$ de capas com texto detectado ($\ge 3$ caracteres alfanuméricos), reportando $\beta$, IC 95% e $q$-valor BH unificado.

### Item 5: Bugs estruturais no `idea_advisor.py` (`n/d`, spline errada por porte e corte de 2M) [CRÍTICO]
* **Status:** `CORRIGIDO NO MOTOR`
* **Onde está o texto antigo errado:**
  * `idea_advisor.py` (versão anterior) e saídas de exemplo (`03_grande_pt_financas.md`, `02_emergente_en_tech.md`): chaveamento divergente (`"200k+"` vs. `"200k_mais"`) imprimia `"n/d"` em produção; canais `< 200k` recebiam alertas de duração da curva de grandes (punindo 14 min em Tech emergente onde o top 10% empírico tinha 11,9 min); dicionário `GRUPO` juntava `medio` (200k a 2M) com gigantes.
* **Texto correto:** Chaves padronizadas no JSON e no código, curvas de duração e de intervalo contínuo de `200k+` bloqueadas para canais `5k a 200k` (pequenos e emergentes ancoram na própria célula empírica), regime de alta volatilidade unificado de `5k a 2M` (separado de `2M+`), e suíte de testes impedindo qualquer ocorrência da string `"n/d"` nas saídas.
* **Procedimento de reprocessamento:** Não aplicável (resolvido integralmente na refatoração do motor offline).

### Item 6: Endogeneidade de escopo, investimento e mídia paga tratadas como alavancas simples [ALTO]
* **Status:** `CORRIGIDO NO MOTOR` (travas anti-enrolação e avisos de demanda/mídia paga) / `DOCUMENTADO` (confiança rebaixada para $\le 5$ no CSV revisado) / `PENDENTE DE REPROCESSAMENTO` (modelos controlados por formato e exclusão de lançamentos sincronizados).
* **Onde está o texto antigo errado:**
  * `CONSOLIDADO.md` (Ranking #1, #4, #5, #8, #9, #11): atribui `Confiança = 6 ou 7` para duração, intervalo curto, marca famosa em Tech e legenda manual como se fossem intervenções isoladas de custo zero.
* **Texto correto:** Vídeos longos (20 a 45 min) e com legenda manual refletem projetos de maior orçamento/escopo (ou adição de legenda após início de viralização). Lançamentos sincronizados de hardware (ex.: *Galaxy Z Fold 8* batendo 154x a 442x no mesmo dia em múltiplos canais) carregam forte confundimento de mídia paga (*Google Ads* de fabricantes). No CSV revisado, a confiança de duração, cadência e legenda foi limitada ao teto **5**.
* **Procedimento de reprocessamento:**
  * *Script esperado:* `scripts/reprocess/06_endogeneity_sensitivity.py`
  * *Entradas:* `data/processed/frente_2a_2c_merged.parquet`
  * *Operação:* (a) Reestimar efeito de duração controlando por dummies de formato/arquétipo do vídeo e densidade de cortes visuais; (b) Reestimar efeito de `marca_famosa` em Tech/Games excluindo dias de lançamento global sincronizado (clusters onde $\ge 2$ canais citam o mesmo modelo inédito numa janela de 48h com múltiplo $> 50\text{x}$).
  * *Critério de aceite numérico:* Reportar a razão de atenuação $|\beta_{\text{controlado}} / \beta_{\text{bruto}}|$ para duração e confirmar se `marca_famosa` mantém $q < 0,05$ fora de janelas de lançamento sincronizado.

### Item 7: Multiplicidade global descontrolada e inclusão de ruído ($q > 0,10$) no Ranking e Guia [ALTO]
* **Status:** `CORRIGIDO NO MOTOR` / `DOCUMENTADO` (aplicado integralmente em `ranking_alavancas_revisado.csv`).
* **Onde está o texto antigo errado:**
  * `CONSOLIDADO.md` (Ranking #16, #21, #22, #23, #24, #25, #26): inclui `Capítulos` (#21, $q = 0,399$, contradizendo o próprio descarte `2A-7`), `Cor verde` (#22, $q = 0,136$), `Gadget KM12-07` (#16, $q = 0,088$) e `Azul + carregado` (#26, pinçado entre 1.802 pares).
  * `RELATORIO_THUMBS_VISUAL.md`: rotula `HDB-39` ($q = 0,342$) como `"Confiança Média"`.
  * `idea_advisor.py` (versão anterior): disparava alertas com corte `q < 0.60`.
* **Texto correto:** Apenas traços com $q < 0,05$ (em bateria pré-especificada), IC 95% limpo sem cruzar zero e livres de vazamento temporal ou segmentação sem interação permanecem como alavancas validadas (7 itens: #2, #5, #6, #9, #11, #14 e #15). Traços com $0,05 \le q < 0,15$ (incluindo #10 na estimativa agregada de $-8,1\%$, $q = 0,066$), regras de cadência/desvio com look-ahead residual ou apenas $p$ bruto sem $q$ BH (#3, #4, #7, #8, #12), recortes de pequenos sem interação confirmada (#1, #17, #18, #19), ganchos instáveis (#13) ou pares minerados (#26) ficam restritos à faixa `hipotese_ab` (15 itens, apenas para teste A/B, nunca recomendação direta). Foram movidos para `removida` 4 itens: #16 (`KM12-07`, cluster banido), #20 (sem $q$-valor formal), #21 ($q = 0,399$) e #25 (ângulo contaminado por duração).
* **Procedimento de reprocessamento (para os 1.802 pares raros da Frente 2B):**
  * *Script esperado:* `scripts/reprocess/07_split_sample_rare_combos.py`
  * *Entradas:* `data/processed/frente_2b_features.parquet`
  * *Operação:* Dividir os canais aleatoriamente em Descoberta (50% dos canais) e Confirmação (50% dos canais, estratificado por nicho); minerar os pares com $q < 0,05$ na metade de Descoberta e testar exclusivamente os sobreviventes na metade de Confirmação com correção BH.
  * *Critério de aceite numérico:* Só promover da faixa `hipotese_ab` para `validada` combinações que atinjam $q_{\text{confirmacao}} < 0,05$ com mesmo sinal.

### Item 8: Falácia de subgrupo (Gelman & Stern) em recortes por porte e idioma [ALTO]
* **Status:** `CORRIGIDO NO MOTOR` / `DOCUMENTADO` (marcado e reajustado no CSV revisado) / `PENDENTE DE REPROCESSAMENTO` (estimação *pooled* formal).
* **Onde está o texto antigo errado:**
  * `CONSOLIDADO.md` e `RELATORIO_2D.md` (#17 Número, #18 CAIXA ALTA, #19 Colab): cria regras específicas para `5k a 200k` embora a coluna `Diferença q BH` contra `200k+` seja não-significativa ($0,29$, $0,71$ e $0,074$).
  * `RELATORIO_2C.md` (#10 1ª pessoa em EN, #13 Contraintuitivo em EN): restringe regras a inglês porque o subgrupo PT deu nulo, sem testar a interação `traço × idioma` (além de #13 oscilar entre $q = 0,015$ e $q = 0,12$ entre tabelas da 2C). No ranking revisado e no motor offline, #10 e #13 seguem o mesmo critério unificado: na ausência de interação formal idioma $\times$ traço com $q < 0,05$, #10 usa a estimativa agregada ($-8,1\%$, IC 95% $-13,1\%$ a $-3,0\%$, $q = 0,066$) e entra em `hipotese_ab` ao lado de #13.
* **Texto correto:** Diferença entre "significativo num estrato" e "não-significativo noutro" não prova diferença entre estratos. Na ausência de interação com $q < 0,05$, é proibido criar prescrições opostas por porte ou idioma; os itens afetados foram marcados com alerta explícito de ausência de interação no CSV revisado.
* **Procedimento de reprocessamento:**
  * *Script esperado:* `scripts/reprocess/08_pooled_interactions_wald.py`
  * *Entradas:* Bases unificadas 2A+2D e 2C (PT+EN).
  * *Operação:* Estimar na amostra completa `y_expanding ~ traco + traco:estrato + FE_canal` com erros agrupados por canal; aplicar BH sobre os termos de interação `traco:estrato`. Onde $q_{\text{interacao}} \ge 0,05$, substituir os números segmentados pela estimativa combinada (*pooled*).
  * *Critério de aceite numérico:* Tabela completa com $\beta_{\text{pooled}}$ para $100\%$ dos traços sem interação ($q_{\text{interacao}} \ge 0,05$) e reconciliação única do $q$-valor da afirmação contraintuitiva.

### Item 9: Vazamento de pré-processamento em CV e contaminação da Taxonomia de Ângulos [ALTO]
* **Status:** `CORRIGIDO NO MOTOR` (ângulos banidos de pontuação de performance) / `PENDENTE DE REPROCESSAMENTO` (pipelines por dobra e reclusterização sem duração).
* **Onde está o texto antigo errado:**
  * `RELATORIO_THUMBS_VISUAL.md` (2B): ajusta PCA, UMAP, HDBSCAN, K-means e quantis na base inteira antes do `GroupKFold(5)`.
  * `RELATORIO_2C.md` (Taxonomia de 18 ângulos): injeta `log(duração)` com peso de 30% nos embeddings semânticos, força 33,9% de ruído via kNN-15 e atribui rótulos como `"vencedor completo"` e `"melhor perfil de risco"` a clusters cujo efeito intra-canal é nulo ($q \ge 0,89$ na média; $q \ge 0,53$ em flops).
* **Texto correto:** Pré-processamento fora das dobras gera *double dipping*, e misturar duração em arquétipos de texto atribui ao "ângulo narrativo" o ganho que pertence apenas aos minutos de vídeo. Os 18 ângulos têm efeito próprio nulo dentro do canal e servem apenas para descrição temática, jamais para ranking de desempenho.
* **Procedimento de reprocessamento:**
  * *Script esperado:* `scripts/reprocess/09_clean_cv_and_angles.py`
  * *Entradas:* Matrizes brutas de features visuais (2B) e embeddings de título/descrição (2C).
  * *Operação:* Encapsular `StandardScaler`, `PCA`, `QuantileTransformer` e `KMeans` dentro de `sklearn.pipeline.Pipeline` ajustado exclusivamente nos canais de treino de cada dobra do `GroupKFold(5)`; reconstruir os ângulos da 2C com peso $0,0$ para `log(duração)` e manter pontos de baixa densidade de HDBSCAN no rótulo `-1 (ruido)` sem imputação kNN-15.
  * *Critério de aceite numérico:* Zero chamada de `.fit()` fora do loop de treino do `GroupKFold`; correlação de Spearman entre atribuição de ângulo semântico e `log(duração)` reduzida ao nível natural do texto (sem colinearidade forçada) e fração de ruído preservada explicitamente.

### Item 10: Fragilidade severa de NLP/Regex e busca TF-IDF no motor offline [ALTO]
* **Status:** `CORRIGIDO NO MOTOR`
* **Onde está o texto antigo errado:**
  * `idea_advisor.py` (versão anterior): chamava sobreposição de radicais truncados (`t[:-1]`) de `"alinhamento semântico"`; falhava quando `ref == 0.00`; punia `"universe"`/`"energy"` em canais de ciência; marcava `"iPhone X"` e `"1920 x 1080"` como colaboração; lia `"nos EUA"` como 1ª pessoa; apagava dígitos únicos (`"5 erros"`); acusava falta de marca em `"RTX 5090"`; dizia buscar em 26.194 vídeos quando o índice tinha 4.639 e exibia exemplos com `Similaridade: 0,00`.
* **Texto correto:** No motor reescrito (validado pelos 152 testes), as regexes foram separadas por idioma e contextualizadas por nicho, `\bx\b` e `tokens()` foram corrigidos para preservar números e evitar falsos positivos de colab/pronome, ausência de entidade virou lembrete neutro, a métrica lexical foi renomeada com transparência, `ref == 0` é tratado com segurança, a contagem real do índice é informada e exemplos com `similaridade < 0,05` são bloqueados.
* **Procedimento de reprocessamento:** Não aplicável ao motor léxico atual (resolvido em código).

### Item 11: Confundimento mecânico em "Curtidas × Duração" e confundimento Pauta × Capa [ALTO]
* **Status:** `DOCUMENTADO` / `PENDENTE DE REPROCESSAMENTO`
* **Onde está o texto antigo errado:**
  * `RELATORIO_2A.md` (Investigação E): conclui que vídeos longos reduzem o engajamento da audiência (`">60 min: -16,9% na taxa de curtidas"`).
  * `RELATORIO_THUMBS_VISUAL.md` (`KM12-07`, gadget na mão $+28,8\%$) e `RELATORIO_2D.md` (caso-controle de breakouts 10x contra $|y| < 0,3$ sem parear duração): atribuem ao layout visual o que decorre do produto no título ou da duração do vídeo.
* **Texto correto:** Como vídeos longos têm mais views e a elasticidade intra-canal de curtidas é $0,80$ (`HIPOTESES_LOG.md`, `H-1`), qualquer aumento de alcance reduz mecanicamente a razão bruta `likes/views`. A queda de $-16,9\%$ viola a Decisão Técnica 3 do próprio estudo e deve ser tratada como artefato de escala até ser recalculada sobre o resíduo. Da mesma forma, foto de gadget reflete pauta de review de produto novo, não design gráfico isolado.
* **Procedimento de reprocessamento:**
  * *Script esperado:* `scripts/reprocess/11_likes_residual_and_matching.py`
  * *Entradas:* `data/processed/videos_clean_targets.parquet`, embeddings de título (2C) e features visuais (2B/2D).
  * *Operação:* (a) Regredir o resíduo de escala `r_likes = log(likes + 1) - 0.80 * log(views)` contra as faixas de duração com efeito fixo de canal; (b) Reestimar os efeitos das métricas de capa controlando pelos 10 primeiros componentes principais do embedding do título; (c) Refazer o caso-controle de breakouts 10x pareando cada caso com controles do mesmo canal e mesmo tercil de duração.
  * *Critério de aceite numérico:* Verificação direta da significância de duração sobre `r_likes` (esperado próximo de zero), reporte de atenuação visual pós-controle semântico e diferença mediana de duração entre casos e controles $< 15\%$.

### Item 12: Contradição de status em "Momentum pós-hit" e artefato da tendência quadrática [MÉDIO]
* **Status:** `DOCUMENTADO` (reconciliado na Seção 2.2 e removido do ranking ativo) / `PENDENTE DE REPROCESSAMENTO`.
* **Onde está o texto antigo errado:**
  * `HIPOTESES_LOG.md` (`F-5`, status `sustentada`), `RELATORIO_2D.md` (`peq_04f_momentum.csv`, `"Universal (Alta confiança)"`, $+12,3\%$) vs. `RELATORIO_2A.md` / `CONSOLIDADO.md` (`+2,4%`, descartado com tendência quadrática).
* **Texto correto:** Status unificado como **INCONCLUSIVO** até reestimação sem parábola bilateral (que usa dados futuros e absorve momentum genuíno em séries curtas) e em canais pequenos auditados.
* **Procedimento de reprocessamento:**
  * *Script esperado:* `scripts/reprocess/12_clean_momentum_event_study.py`
  * *Entradas:* Bases 2A e 2D auditadas, ordenadas cronologicamente por canal.
  * *Operação:* Definir *hit* em $t-1$ estritamente contra a baseline pré-evento ($t-11$ a $t-2$); medir o excesso de performance de $t$, $t+1$ e $t+2$ contra a mesma baseline pré-evento ($t-11$ a $t-2$), sem ajustar polinômio sobre pontos futuros, aplicando *Wild Cluster Bootstrap* por canal.
  * *Critério de aceite numérico:* Estimativa única e comparável entre portes, acompanhada de teste de falsificação (placebo em $t-2$ deve ter efeito médio estatisticamente indistinguível de zero, $p > 0,20$).

### Item 13: Inferência frágil em nichos pequenos ($G < 20$), bug de derivada aos "4 min" e bug de texto em 13 fichas [MÉDIO]
* **Status:** `CORRIGIDO NO MOTOR` (derivada absurda aos 4 min eliminada) / `DOCUMENTADO` (erro das 13 fichas registrado) / `PENDENTE DE REPROCESSAMENTO` (modelo hierárquico e regeneração das fichas Markdown).
* **Onde está o texto antigo errado:**
  * Saída antiga do Advisor (`01_pequeno_pt_historias.md`): apontava ótimo de 52 min, mas `"retorno decrescente a partir de 4 min"` (erro ao tomar derivada segunda de $\ln(\text{duração})$ sem converter para minutos).
  * `RELATORIO_THUMBS_VISUAL.md` (13 das 34 fichas): lista exatamente os mesmos nichos como `"onde funciona melhor"` e `"onde funciona pior"` (bug de fatiamento `top_k`/`bottom_k` quando o padrão ocorre em $\le 3$ nichos).
  * Curvas por nicho com $5 \le G \le 18$ canais: usam erro padrão assintótico agrupado sem encolhimento (*shrinkage*).
* **Texto correto:** Em `RELATORIO_THUMBS_VISUAL.md`, ignore as listas de melhores/piores nichos sempre que o número total de nichos avaliados na ficha for $\le 5$. Em nichos com menos de 20 canais, trate ótimos locais de duração como ruidosos e priorize a faixa global de 20 a 35 min.
* **Procedimento de reprocessamento:**
  * *Script esperado:* `scripts/reprocess/13_hierarchical_splines_and_cards.py`
  * *Entradas:* Base analítica unificada e `padroes_stats_por_nicho.csv`.
  * *Operação:* (a) Ajustar modelo linear misto (*partial pooling* / efeitos aleatórios de nicho nas bases de B-spline de duração) com *Wild Cluster Bootstrap* (999 réplicas de Webb) para nichos com $G < 25$; (b) Corrigir gerador de fichas visuais exigindo mínimo de 6 nichos com $G \ge 5$ para exibir `top 2` vs. `bottom 2` disjuntos.
  * *Critério de aceite numérico:* Interseção vazia (`set(melhores) & set(piores) == set()`) em $100\%$ das 34 fichas geradas e amplitude de IC 95% calibrada via bootstrap em todos os estratos com $G < 25$.

### Item 14: Truncamento em 100 vídeos (Viés Idade-Período-Coorte) e *Snapshot Bias* em `y_passado` [MÉDIO]
* **Status:** `CORRIGIDO NO MOTOR` (regra de estagnação aos 35 dias removida) / `DOCUMENTADO` / `PENDENTE DE REPROCESSAMENTO`.
* **Onde está o texto antigo errado:**
  * `HIPOTESES_LOG.md` (`F-6`) e relatórios derivados: inferem da elasticidade transversal de $0,077$ que `"vídeos não continuam crescendo muito depois de 35 dias"` (tratado na prática como morte do vídeo após 35 dias).
  * Comparações de Gini entre canais diários (100 vídeos = 3 meses) e mensais (100 vídeos = 8 anos).
* **Texto correto:** Um único snapshot transversal confunde idade do vídeo com crescimento histórico da base do canal (vídeos de 3 anos atrás foram lançados quando o canal era menor, mascarando ganho *evergreen* na regressão `log(views) ~ log(idade)`). É matematicamente inválido declarar que um vídeo para de crescer após 35 dias sem painel longitudinal. Além disso, `y_passado` observa as views acumuladas de $t-1$ na data futura da coleta, não no dia em que $t$ foi publicado.
* **Procedimento de reprocessamento:**
  * *Script esperado:* `scripts/reprocess/14_cohort_gini_and_snapshot_check.py`
  * *Entradas:* `data/processed/videos_clean_targets.parquet`
  * *Operação:* (a) Recalcular Gini e DP intra-canal restritos à janela fixa de vídeos publicados entre 30 e 395 dias antes do snapshot (12 meses homogêneos, exigindo $\ge 12$ vídeos no período); (b) Testar sensibilidade das alavancas sequenciais ($t-1 \to t$, intervalos $< 2\text{d}$ e pós-flop $< 3\text{d}$) na subamostra madura publicada entre 35 e 150 dias antes do snapshot, onde o acúmulo adicional pós-$t$ de $t-1$ é mínimo.
  * *Critério de aceite numérico:* Consistência da ruptura em 2M de inscritos no Gini de 12 meses fixos e desvio relativo $|\beta_{35\text{--}150\text{d}} - \beta_{\text{total}}| < 25\%$ para o intervalo $< 2\text{ dias}$.

### Item 15: Defasagem de Visão Computacional (`Haar Cascade`), subcobertura visual em pequenos e LightGBM descalibrado [MÉDIO]
* **Status:** `CORRIGIDO NO MOTOR` (proibido exibir "% de chance de viralizar") / `PENDENTE DE REPROCESSAMENTO`.
* **Onde está o texto antigo errado:**
  * `RELATORIO_THUMBS_VISUAL.md` (2B): usa `Haar Cascade` em imagens `320x180`, gerando anomalia onde `"Peso visual à esquerda"` possui mais rostos detectados à direita (32% vs. 20%), e deixa de fora os 8.312 vídeos de canais pequenos.
  * `RELATORIO_2A.md` (ML): LightGBM reporta Brier Score de $0,0476$, pior que chutar a taxa base constante ($0,0475$).
* **Texto correto:** `Haar Cascade` em baixa resolução falha em rostos inclinados ou expressivos (atenuando efeitos reais por erro de medida) e sugere que o "peso visual à esquerda" capturou manchas de texto/contraste gráfico em vez do sujeito humano. Árvores não calibradas sobre features de baixíssimo sinal ($R^2 \le 0,025$) não produzem probabilidades válidas.
* **Procedimento de reprocessamento:**
  * *Script esperado:* `scripts/reprocess/15_modern_cv_and_calibration.py`
  * *Entradas:* Miniaturas em `hqdefault`/`maxresdefault` dos 310 canais (incluindo pequenos autorais).
  * *Operação:* Substituir `Haar Cascade` por `MediaPipe Face Detection` / `RetinaFace` separando explicitamente máscara de pessoa (`SelfieSegmentation`), caixa de texto (`PaddleOCR`/`EasyOCR`) e saliência de fundo; calibrar o classificador ML via `CalibratedClassifierCV(method='isotonic')` aninhado por canal no `GroupKFold`.
  * *Critério de aceite numérico:* Precisão/revocação facial $> 90\%$ em amostra auditada de 200 capas, decomposição exata de `peso_esquerda` entre texto vs. rosto, e Brier Score calibrado estritamente menor que o baseline ingênuo ($< 0,0475$) com *Expected Calibration Error* (ECE) $< 0,015$.

### Item 16: Cálculo invertido do `grau_de_confianca` em `idea_advisor.py` [MÉDIO]
* **Status:** `CORRIGIDO NO MOTOR`
* **Onde está o texto antigo errado:**
  * `idea_advisor.py` (versão anterior, linha 229): `grau = "baixo a moderado" if alertas or cobertura != "boa" else "moderado"`, rebaixando a confiança estatística do relatório sempre que a ideia do usuário acionava um alerta de risco (mesmo quando apoiado em $q = 0,003$ e ampla amostra).
* **Texto correto:** No motor reescrito, `calcular_grau_de_confianca` avalia exclusivamente a cobertura amostral da célula (número de canais e vídeos) e o $q$ médio das regras auditadas disponíveis no KB para aquele recorte (`qs_referencia_do_recorte`), sem ler `qs_acionados` pelos gatilhos do título, duração ou capa da ideia avaliada.
* **Procedimento de reprocessamento:** Não aplicável (resolvido em código).

### Item 17: Perda de eficiência em LPM/amostragem semântica, flags mortas na CLI e anacronismo de datas/modelos [BAIXO]
* **Status:** `CORRIGIDO NO MOTOR` (flags mortas removidas da CLI) / `DOCUMENTADO` (registro de ambiente) / `PENDENTE DE REPROCESSAMENTO` (regressão quantílica e amostragem pareada intra-canal).
* **Onde está o texto antigo errado:**
  * CLI `youtube-seo advise` (versão anterior): herdava flags `-o`/cache inoperantes de `parents=[comum]`.
  * Relatórios da Fase 1 e 2D: comparam Top 5% contra faixa 40% a 60% (jogando 75% dos dados fora), amostram 1.633 capas por nicho sem parear dentro do canal, e registram datas como `23/11/2026` (com janela de coleta de 8 minutos na 2D) e nomes internos de modelos (`gemini-4-carbon/hydrogen`).
* **Texto correto:** As flags mortas da CLI foram limpas. Fica registrado para fins de auditoria que os timestamps `2026` refletem deslocamento do relógio/ambiente virtual de execução no momento do snapshot local (a duração de 8 minutos na 2D corresponde à leitura local dos metadados em lote, não à janela histórica dos vídeos) e que `carbon/hydrogen` são aliases internos do pipeline de roteamento de LLMs.
* **Procedimento de reprocessamento (eficiência estatística de cauda e LLM):**
  * *Script esperado:* `scripts/reprocess/17_quantile_fe_and_paired_llm.py`
  * *Entradas:* `data/processed/videos_clean_targets.parquet`
  * *Operação:* Substituir cortes LPM (Top 5% vs. meio) por regressão quantílica com efeitos fixos intra-canal ($\tau = 0,90$ e $\tau = 0,95$, método Machado-Santos Silva) usando $100\%$ da amostra; em novas anotações visuais por LLM, amostrar estritamente pares discordantes dentro do mesmo canal (2 vídeos Top 5% pareados com 2 vídeos medianos por canal).
  * *Critério de aceite numérico:* $100\%$ dos vídeos válidos utilizados na estimação de cauda e $100\%$ dos canais amostrados com variância intra-canal garantida ($\ge 4$ vídeos anotados por canal).
