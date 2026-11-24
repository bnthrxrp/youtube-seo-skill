> **AVISO DE AUDITORIA E GOVERNANÇA ESTATÍSTICA (ERRATA ATIVA):**
> Este relatório contém estimativas geradas antes do fechamento da auditoria metodológica sênior. Ao consultar este material, aplique obrigatoriamente as seguintes travas:
> 1. **Teto preditivo:** Metadados estáticos (título, capa e horário) explicam menos de 2,5% da variância intra-canal ($R^2 \le 0,025$). Nenhum coeficiente deve ser lido como garantia causal de alcance.
> 2. **Recomendações firmes vs. Hipóteses A/B:** Como **recomendação prescritiva firme** (`faixa = validada` em `docs/research/data/ranking_alavancas_revisado.csv`), valem exclusivamente itens com $q < 0,05$, IC 95% limpo sem cruzar zero e penalização de endogeneidade. Itens na zona $0,05 \le q < 0,15$ (ou rebaixados por limites da base bruta) pertencem à faixa `hipotese_ab`: **hipótese A/B não é recomendação**, servindo apenas para experimentação controlada no *Testar e Comparar* do YouTube Studio. Ignore integralmente clusters visuais (`HDB-*`, `KM12-*`), ângulos de vídeo e qualquer item com $q \ge 0,15$ (`faixa = removida`).
> 3. **Reconciliações e pendências:** Em caso de conflito sobre alinhamento Capa × Título ou Momentum pós-hit, ou para verificar variáveis marcadas como `PENDENTE DE REPROCESSAMENTO` (vazamento temporal residual, filtro de canais pequenos e denominador de idade), prevalece o disposto em `docs/research/ERRATA_E_LIMITES.md`.

---

# Frente 2A · Modelagem preditiva e econometria (Investigações A, E, F e G)

Base: `laboratorio/dados/base_mestra.parquet` (17.882 vídeos longos, 203 canais, snapshot de 23/11/2026), só leitura. Tudo desta frente está em `laboratorio/frente_ml/`. Números completos em `resultados/*.csv` e no consolidado `resultados/resumo_frente_ml.json`.

## Padrão usado em todas as investigações

- **Desfecho principal:** `y_loo_idade` winsorizado em P0,5 e P99,5 (`yw`), porque o resíduo leave-one-out tem cauda de alavancagem (máximo 19,9). Sensibilidade com `y_passado` (só olha para trás) e `y_loo`.
- **Caudas:** top 1%, 5% e 10% global de `y_loo_idade` e top 5% e 10% **dentro do canal** (percentil de `y_loo_idade` no próprio canal).
- **Inferência:** OLS within (efeito fixo de canal) com erro padrão agrupado por canal e distribuição t com G−1 graus de liberdade; bootstrap de 1.000 réplicas reamostrando canais; Benjamini-Hochberg (BH) dentro de cada bateria.
- **Leitura dos efeitos:** coeficientes em log viram % por exp(b)−1. Probabilidade de top 5% do canal em pontos percentuais (pp).
- **Natureza:** associação, não causa. Sem CTR, impressões, retenção, origem de tráfego ou histórico de views por vídeo.

### Features (lista exata em `resultados/A_features_lista.json`)

**Incluídas (68):**
- *Estritamente pré-publicação (15):* log da duração, made for kids, licenciado, dia da semana, hora local, fim de semana, idioma declarado e coerência, log(1 + dias desde o vídeo anterior), vídeos nos 7 e 30 dias anteriores, categoria e três traços novos calculados **só com vídeos anteriores**: duração vs mediana dos 10 vídeos anteriores, intervalo vs hábito, percentil da duração no histórico do canal.
- *Editáveis de texto (24):* traços do título, descrição (tamanho, links, hashtags, timestamps, capítulos), tags e legenda própria.
- *Editáveis de miniatura (26):* brilho, contraste, saturação, colorido, bordas, rostos (detector e Gemini), OCR (texto, palavras, número, caixa alta, repetição do título) e as leituras do Gemini (expressão, olhar, rosto grande, palavras, objeto, seta ou círculo, elementos, comparação, número, fundo, estilo, relação texto e título).
- *Contexto do estrato (3):* nicho, idioma, porte, só como moduladores de interação.

**Excluídas:** views, curtidas, comentários e todas as taxas; `log_views`, `base_canal`, `y`, `y_loo`, `y_passado`, `y_pct_canal` (alvo ou pós-publicação); idade, timestamp e posição na janela (só controle de exposição); `y_prev` e `y_loo_idade_prev` (o alvo do vizinho usa o próprio vídeo na base); inscritos e totais do canal (snapshot contínuo, causalidade reversa); `n_audio_langs`, `n_chapters_ytdlp`, `multi_audio` e `tem_nome_proprio` (80% ou mais ausentes); redundantes e texto bruto.
**Sensibilidade "histórico":** `y_passado` dos vídeos anteriores medido no snapshot (fora do modelo principal).

---

## Investigação A · DNA dos virais e modelagem preditiva sem leakage

**1. Pergunta investigada.** Com informação disponível antes de publicar, dá para prever quanto um vídeo vai performar em relação ao próprio canal, e quem chega ao topo? O que generaliza para canais nunca vistos e o que só funciona no futuro do mesmo canal?

**2. Metodologia.**
- Dois regimes de validação: `GroupKFold(5)` por `channel_id` (canal nunca visto) e temporal dentro do canal (80% mais antigos treinam, 20% mais recentes testam).
- LightGBM, XGBoost e Ridge ou Logística regularizada (one-hot, imputação e indicador de ausência). Métricas: R², RMSE, Spearman global e dentro do canal; ROC-AUC, PR-AUC, Lift@5%, Lift@10%, Brier. IC 95% por bootstrap de 1.000 canais sobre as previsões fora da amostra.
- Ablações: só pré-publicação estrita, sem miniatura, sem contexto, com histórico.
- Baseline "só canal" no regime temporal: ranquear os vídeos futuros só pela taxa histórica de topo ou pela volatilidade do canal no treino.
- SHAP TreeSHAP out-of-fold (17.882 vídeos) e interações SHAP em 6.000 vídeos fora da amostra; importância por nicho, porte e idioma.
- Bateria within-canal de 80 traços × 2 desfechos (`yw` e top 5% do canal) com BH e bootstrap; 36 testes formais de interação (Wald conjunto, moderador de canal identificado só pela interação) com BH.

**3. Resultado encontrado.**
- **Previsibilidade baixa e honesta.** Em canais nunca vistos, o melhor modelo explica 1,6% a 1,9% da variância de `yw` (Spearman 0,16 a 0,17). Para o top 5% global, AUC 0,64 e Lift@5% de 1,9x a 2,1x.
- **O regime temporal parece melhor, mas é identificação do canal.** No futuro do mesmo canal, top 5% global sobe para AUC 0,71 e Lift@5% de 3,0x. Só que ranquear pela volatilidade histórica do canal, sem nenhum traço do vídeo, dá AUC 0,744 (taxa histórica de topo: 0,727), acima do modelo. O topo global é dominado por canais voláteis.
- **Dentro do canal o sinal é fraco.** Top 5% do próprio canal: AUC 0,58 em canais novos e 0,54 no futuro do mesmo canal (IC 0,50 a 0,58). O linear empata com as árvores nessa tarefa (0,581 contra 0,583).
- **O que pesa no SHAP é duração e ritmo.** 43% da importância vem de traços estritamente pré-publicação, 27% de miniatura, 26% de texto e 4% de contexto. Top 5 em `yw`: duração, percentil da duração no histórico, duração vs hábito do canal, dias desde o anterior e intervalo vs hábito, todos com efeito crescente.
- **Miniatura não acrescenta previsão.** Tirar todas as 26 variáveis de capa não muda o Spearman em canais novos (0,163 contra 0,162) e tira só 0,009 no temporal.
- **Interações.** As maiores interações SHAP são de duração com duração relativa ao hábito, com links na descrição e com intervalo. Pares pedidos: duração × nicho é o 59º de 2.278; palavras na capa × nicho 146º; hora × porte 788º; legenda × idioma 920º; rosto grande × porte 1.298º a 1.569º (praticamente zero).

**4. Evidência estatística.**

| Tarefa (LightGBM) | Canais nunca vistos | Futuro do mesmo canal |
|---|---|---|
| `yw` R² | 0,016 [−0,001; 0,031] | 0,029 [0,004; 0,054] (XGB 0,040 [0,015; 0,064]) |
| `yw` Spearman | 0,162 [0,135; 0,188] | 0,185 [0,144; 0,226] |
| `y_passado` R² / Spearman | 0,025 / 0,172 | 0,063 [0,039; 0,087] / 0,235 [0,196; 0,273] |
| Top 5% global AUC / PR-AUC / Lift@5% | 0,644 [0,615; 0,673] / 0,083 / 1,90 [1,42; 2,48] | 0,710 [0,656; 0,765] / 0,120 / 3,02 [2,11; 4,43] |
| Top 10% global AUC / Lift@10% | 0,627 / 1,74 | 0,682 / 2,41 |
| Top 1% global AUC | 0,714 [0,670; 0,762] | 0,842 [0,763; 0,901] |
| Top 5% do canal AUC / Lift@5% | 0,583 [0,562; 0,604] / 2,07 [1,73; 2,39] | 0,539 [0,502; 0,581] / 1,68 [1,12; 2,50] |
| Brier top 5% global (modelo / taxa base) | 0,0476 / 0,0475 | 0,0449 / 0,0453 |
| Baseline só canal, top 5% global | – | AUC 0,727 (taxa histórica), 0,744 (volatilidade) |

- LightGBM menos linear: Spearman `yw` +0,017 [0,001; 0,034] em canais novos e +0,063 [0,027; 0,101] no temporal; AUC top 5% +0,040 [0,014; 0,068].
- Contrastes de cauda (canais novos): top 5% contra mediana P40 a P60, AUC 0,68; contra bottom 20%, 0,64; top 1% contra mediana, 0,78.
- Bateria within-canal (q BH < 0,05, IC bootstrap): duração +18,6% por desvio padrão (q = 0,0001), dias desde o anterior +11,3% (q = 0,0001), duração vs hábito +11,5% (q = 0,0002), intervalo vs hábito +4,9% (q = 0,0006), legenda própria +28,5% [boot. +11,8%; +48,0%] (q = 0,006), links na descrição +8,4% (q = 0,050), emoji no título +18,1% (q = 0,050). Em top 5% do canal só sobrevivem duração (+2,5 pp por desvio padrão) e duração vs hábito (+1,9 pp), q < 0,0001.
- Interações formais com q < 0,05: duração × nicho (q = 0,006 em `yw`, 0,002 em top 5%; inclinação de +0,39 em finanças e +0,35 em educação contra −0,08 em tech), legenda × nicho (q = 0,015 e < 0,001), capítulos × nicho (q = 0,002 e 0,001), fim de semana × porte em top 5% (q = 0,040; +2,75 pp em médios, cerca de −0,6 pp nos demais). Rosto, palavras na capa, contraste, saturação e elementos por porte ou nicho: todos q ≥ 0,26.

**5. Visualizações.** `graficos/ml_01_shap_global_e_interacoes.png` (importância SHAP com direção, top 15 interações, AUC e Spearman com IC nos dois regimes com o baseline só canal marcado, Lift@5% e @10%).

**6. Descobertas inesperadas.**
- Um único número por canal (volatilidade passada) prevê o top 5% global melhor que 68 traços do vídeo. "Viral" no sentido global é traço do canal, não do vídeo.
- A queda de AUC do top 5% do canal no regime temporal tem uma parte mecânica: cada canal tem exatamente 5% de topo na janela inteira, então quem concentrou hits no início tem menos no final (baseline histórico com AUC 0,24, antipreditivo).
- Duração **relativa ao hábito do próprio canal** importa tanto quanto a duração absoluta: um vídeo mais longo que o normal do canal sai na frente.
- Título em 1ª pessoa fica perto do limiar (−8,3%, q = 0,062), na mesma direção do achado da Fase 1.

**7. Limitações e vieses.**
- `y_loo_idade` e os cortes de topo usam a série inteira do canal, inclusive os 20% de teste no regime temporal. Por isso o regime temporal também foi rodado com `y_passado` (estritamente passado): R² 0,063 e Spearman 0,235, coerente.
- Texto, legenda e miniatura foram lidos no snapshot: causalidade reversa possível (legenda subida depois do sucesso, capa trocada em teste A/B).
- BH por bateria, não entre baterias. Links e emoji (q = 0,0497) não sobreviveriam a um controle conjunto.
- Hiperparâmetros fixos e conservadores (sem busca), o que favorece estabilidade e não o máximo de desempenho.

**8. Recomendação prática.** Usar os modelos como **ordenador de rascunhos** (quintil esperado contra o próprio canal), nunca como previsão de views. A alavanca com mais sinal é duração e ritmo em relação ao próprio hábito, não a embalagem. Para "vai viralizar?", a resposta honesta é: o melhor preditor é a volatilidade do canal.

| Nota | 0 a 10 | Justificativa |
|---|---:|---|
| Impacto potencial | 5 | previsibilidade fora da amostra pequena |
| Confiança estatística | 7 | validação rigorosa em 2 regimes, IC por canal, baseline de controle; traços editáveis com causalidade reversa |
| Aplicabilidade prática | 6 | serve para ordenar opções e derrubar mitos de capa |
| Facilidade de implementação | 8 | modelos salvos em `dados/`, prontos para o motor de consulta |

---

## Investigação E · Duração e estrutura (relações não-lineares)

**1. Pergunta investigada.** Qual a forma da relação entre duração e desempenho relativo ao canal, por nicho, porte e idioma? Onde estão o ótimo, a inflexão e os retornos decrescentes? Capítulos, timestamps, legenda e multi-áudio importam depois de controlar a duração?

**2. Metodologia.**
- B-splines cúbicos de log(duração) em OLS within (efeito fixo de canal) + log(idade), EP agrupado por canal. Curvas relativas a um vídeo de 12 min do mesmo canal, com IC 95% (delta) e ótimo com IC por bootstrap de 1.000 canais.
- Desfechos: `yw`, probabilidade de top 5% do canal (modelo de probabilidade linear) e curtidas por view relativas ao canal (`log_like_rate_rel`). Sensibilidade com `y_passado` e `y_loo`.
- Grupos: geral, 11 nichos, 3 portes, 2 idiomas (17 grupos). Teste conjunto do spline (Wald) com BH entre os 51 testes.
- Faixas (<5, 5 a 8, 20 a 45, 45 a 60, >60 contra 8 a 20 min) com BH entre 255 testes.
- Checagem com pyGAM: s(log duração) + l(log idade) + f(canal).
- Estrutura: cada traço com e sem spline de duração e dentro de faixas de duração (BH entre 90 testes).

**3. Resultado encontrado.**
- **Curva geral em forma de sino assimétrico.** Contra um vídeo de 12 min do mesmo canal: 4 min −32%, 6 min −23%, 25 min +36%, 40 min +39%, 60 min +30%, 90 min +18%. Ótimo empírico em **34 min [IC 28 a 43]**; o ganho marginal cai pela metade a partir de cerca de 24 min (retornos decrescentes). Com `y_passado`: 35 min [27; 54]. pyGAM independente: ótimo em 40 min, correlação de 0,988 com a curva B-spline.
- **Top 5% do canal premia ainda mais longo:** ótimo em 72 min [40; 106]. Faixas 45 a 60 min: +5,9 pp (q < 0,001); >60 min: +5,5 pp (q = 0,002).
- **Curtidas por view vão na direção contrária:** ótimo em 13 min [4; 20]; 45 a 60 min −8,1% (q = 0,030) e >60 min −16,9% (q < 0,001). Vídeo longo ganha alcance e perde proporção de curtidas.
- **Por porte:** médio 28 min [24; 41], grande 31 min [26; 42], gigante plana e crescente até 109 min (sem ótimo interno). Médio: <5 min −41% (q = 0,007), 20 a 45 min +25% (q = 0,002), 45 a 60 min +9,6 pp em top 5% (q < 0,001).
- **Por idioma:** pt 31 min [26; 51] com ganho maior (25 min +54%), en 38 min [27; 60] com ganho menor (25 min +25%). A interação duração × idioma não passa (q = 0,54), então a diferença de forma não é significativa.
- **Por nicho (q BH do spline):** documentário 41 min (40 min = +142%, q < 0,001), histórias 52 min (q = 0,001), culinária 35 min (q < 0,001), educação 32 min (q = 0,002), finanças 31 min (25 min = +66%, q < 0,001), tech 24 min com queda forte depois (60 min = −48%, q < 0,001), esportes 24 min com curva instável (q = 0,004), lifestyle 32 min (q = 0,06), entretenimento crescente até 116 min (q = 0,013, ótimo na borda), games sem efeito claro (q = 0,093), infantil plano (q = 0,24).
- **Estrutura controlando duração:**
  - Capítulos: +16,9% sem controle vira +9,6% (IC −2,8% a +23,6%, q = 0,40). Em vídeos >45 min, capítulos se associam a **menos** topo do canal (−9,6 pp, q = 0,038).
  - Timestamps na descrição: +20,2% vira +12,5% (q = 0,36).
  - Legenda própria **resiste**: +27,9% [boot. +12,2%; +45,6%] (q = 0,024); maior em vídeos <8 min (+51%, q = 0,046).
  - Multi-áudio (77 canais do subconjunto yt-dlp): +28,4% (q = 0,061), sem diferença por faixa.

**4. Evidência estatística.** Spline geral: q do Wald < 0,001 em `yw`, top 5% e curtidas. Faixas gerais em `yw` contra 8 a 20 min: <5 min −33,5% [−45,7; −18,6] (q = 0,001); 5 a 8 −16,3% (q = 0,011); 20 a 45 +25,1% [+17,6; +33,0] (q < 0,001); 45 a 60 +19,0% (q = 0,084); >60 +10,0% (q = 0,47). Interação duração × nicho: q = 0,006; × porte: q = 0,75; × idioma: q = 0,54. Arquivos: `E_curvas_duracao_resumo.csv`, `E_curvas_duracao_pontos.csv`, `E_faixas_duracao_vs_8a20min.csv`, `E_estrutura_controlada_duracao.csv`, `E_meta.json`.

**5. Visualizações.** `graficos/ml_02_curvas_duracao_gam_nichos.png` (curva geral com `y_passado` e curtidas, porte, idioma, 11 nichos com IC 95% e painel de estrutura com e sem controle de duração).

**6. Descobertas inesperadas.**
- O ponto ótimo para **topo** (72 min) é o dobro do ponto ótimo para **média** (34 min): vídeo muito longo aumenta a variância.
- Tech é o único nicho com inclinação negativa: o vídeo de 60 min perde 48% contra o de 12 min.
- Capítulos parecem eficazes só porque vídeos com capítulos são mais longos. Em vídeos muito longos, ter capítulos se associa a menos topo (hipótese: vídeo de referência, navegável, consumido em pedaços).

**7. Limitações e vieses.**
- A duração carrega escopo de produção (vídeo longo costuma ser projeto maior). A curva mede o pacote duração mais esforço.
- Sem retenção: não dá para saber se o ganho vem de tempo assistido ou de mais impressões.
- Nichos com 13 a 24 canais: inferência agrupada com poucos clusters; ótimos na borda em games e entretenimento. Esportes tem curva instável.
- Legenda e capítulos são editáveis e lidos no snapshot.

**8. Recomendação prática.** Para canal médio, a faixa de trabalho é **20 a 45 min, com centro em 25 a 35 min**, e evitar <8 min como formato principal. Usar 45 a 60 min como aposta de topo (mais chance de hit, menos curtidas por view). Em tech, não passar de cerca de 30 min. Tratar capítulos como experiência do usuário, não como alavanca de alcance.

| Nota | 0 a 10 | Justificativa |
|---|---:|---|
| Impacto potencial | 8 | maior deslocamento de patamar observado (−41% em <5 min contra +25% em 20 a 45 min nos médios) |
| Confiança estatística | 7 | curva geral precisa e replicada por 3 alvos e 2 métodos; por nicho, poucos clusters |
| Aplicabilidade prática | 8 | regra de faixa direta por nicho e porte |
| Facilidade de implementação | 4 | alongar mantendo qualidade exige roteiro e edição |

---

## Investigação F · Longevidade, cadência, sequências e horários

**Limite dos dados (explícito).** Temos **um único snapshot**. Não existe série de views de nenhum vídeo ao longo do tempo.

| Medível com esta base | Continua hipótese |
|---|---|
| relação idade × views **entre vídeos** do mesmo canal (corte transversal) | curva de crescimento de um mesmo vídeo (explosivo, evergreen, crescimento tardio) |
| intervalo desde o vídeo anterior e volume nos 7 e 30 dias anteriores | se o algoritmo "pune" ritmo alto ou se é o público que cansa |
| sequência: desempenho do vídeo seguinte a um extremo (resíduo de tendência) | mecanismo do arrasto (inscritos novos, sessão, recomendação) |
| dia da semana e faixa de horário no fuso do público | efeito do horário nas primeiras 48 h |

**1. Pergunta investigada.** O desempenho tem memória dentro do canal? Qual o intervalo associado ao melhor resultado? Depois de um hit vem arrasto ou regressão à média? Dia e horário importam?

**2. Metodologia.**
- Resíduo da tendência linear do canal (`r_tend`, mesma definição da Fase 1) e robustez com tendência **quadrática** (`r_tend_q`). Nunca condicionar em `y` do vizinho (artefato F-4 da Fase 1).
- Autocorrelação nas defasagens 1 a 5 com nulo por 300 permutações dentro do canal e IC por bootstrap de canais; Ljung-Box (5 defasagens) em cada canal com BH.
- Pós-extremo: média do resíduo nos 5 vídeos seguintes a um top 5%, top 10%, bottom 5%, bottom 10% e faixa P40 a P60 (bootstrap 1.000). Assimetria: regressão within com parte positiva e negativa do resíduo anterior. Complemento: extremo × intervalo até o próximo (`F_pos_viral_x_intervalo.csv`).
- Intervalo: spline cúbico de log(1 + dias) within, controle de idade e duração, por porte, nicho e idioma, com `yw`, `y_passado` e `r_tend`.
- Dia e horário: dummies within (referências quarta e tarde), Wald conjunto com BH por grupo, e hora em seno e cosseno.
- Idade: elasticidade transversal log(views) ~ log(idade) within, por nicho, porte e faixa de idade.

**3. Resultado encontrado.**
- **Memória curta e fraca.** Autocorrelação de 0,069 na defasagem 1 (nulo −0,012) e 0,060 na 2; some na 5. Com tendência quadrática cai para 0,035 e zera na 3. Só 11% dos canais têm autocorrelação significativa (Ljung-Box, q < 0,05).
- **"Momentum" depois de um hit é quase todo fase do canal.** Vídeo seguinte a um top 5%: +8,1% pela tendência linear, mas **+2,4% e não significativo** pela quadrática.
- **Fracasso pesa mais que sucesso.** O coeficiente da parte negativa do resíduo anterior (0,116) é quase 4 vezes o da positiva (0,031); diferença p = 0,014. Depois de um bottom 5%: −9,3%.
- **O dano pós-fracasso depende de postar rápido.** Vídeo publicado em menos de 3 dias depois de um bottom 5%: −17,8% [−25,7; −9,0]. Esperar 3 a 10 dias neutraliza (interação +24,2%, p = 0,002; teste conjunto p = 0,008). Depois de um **hit**, esperar não traz ganho específico (teste conjunto p = 0,58): o ganho aparente é o efeito geral do intervalo.
- **Intervalo curto se associa a desempenho pior, em todos os portes.** Contra um intervalo de 7 dias: 1 dia −19% (`y_passado` −13%), 2 dias −13%, 3 dias −9%, 14 dias +8%, 30 dias +14% (`y_passado` +5%). A curva achata depois de cerca de 14 dias. O "ótimo" em 62 dias está na borda dos dados e não é robusto.
- **Volume recente:** dobrar o número de vídeos nos 7 dias anteriores se associa a −9,6% em `yw` (q = 0,003), −4,8% em `y_passado` (q = 0,013) e −6,5% em `r_tend` (q = 0,009). Gigantes: −16,2% (q = 0,041). Volume em 30 dias some em `y_passado` (q = 0,63).
- **Dia e horário não importam no agregado.** Wald geral: dia q = 0,31, faixa q = 0,86; hora circular p = 0,68 (amplitude 2,5%). Nenhum porte passa. Exceções com poucos canais: documentário (dia, q = 0,001, 13 canais) e histórias (faixa, q = 0,002, 20 canais). Sábado em inglês +20,3% (p = 0,003) não sobrevive a BH (q = 0,34). 76% dos vídeos de cada canal saem na mesma faixa de horário.
- **Idade transversal:** elasticidade 0,096 [0,020; 0,171]; mais alta em infantil (0,44), lifestyle (0,33) e entretenimento (0,25); negativa em tech (−0,18).

**4. Evidência estatística.** Autocorrelação defasagem 1: 0,069 [0,036; 0,098], p de permutação 0,003, q = 0,006. Pós-top 5% (defasagem 1): `r_tend` +8,1% [+2,5; +14,3]; `r_tend_q` +2,4% [−2,4; +7,6]; `yw` +7,4% [+1,7; +13,6]. Pós-bottom 5%: −9,3% [−14,6; −3,1]; quadrática −5,7% [−10,8; +0,4]. Spline de intervalo geral: q = 0,001 (`yw`), 0,004 (`y_passado`). Arquivos: `F_autocorrelacao_lags.csv`, `F_ljungbox_por_canal.csv`, `F_pos_viral.csv`, `F_pos_viral_x_intervalo.csv`, `F_intervalo_spline_*.csv`, `F_volume_recente.csv`, `F_dia_hora_*.csv`, `F_idade_elasticidade_transversal.csv`, `F_meta.json`.

**5. Visualizações.** `graficos/ml_03_cadencia_pos_viral_horario.png` (intervalo por porte, perfil pós-hit e pós-fracasso com robustez quadrática, autocorrelação contra nulo, dia da semana e faixa horária por idioma, elasticidade transversal por nicho).

**6. Descobertas inesperadas.**
- O que se chama de "embalo depois do viral" é, na maior parte, o canal estar numa fase boa. Não há bônus específico por surfar o hit.
- O risco real está do outro lado: lançar rápido depois de um vídeo fraco.
- Horário, a variável mais discutida por criadores, é a que menos aparece nos dados.

**7. Limitações e vieses.**
- Intervalo e volume não são aleatórios: pausa longa costuma preceder projeto grande, e ritmo alto pode coincidir com fases de conteúdo mais leve. O efeito de 1 a 3 dias é robusto entre alvos; o de pausas longas não (`y_passado` +5% aos 30 dias).
- O resíduo de tendência depende da forma da tendência; por isso o pós-hit é tratado como não robusto.
- Dia e horário variam pouco dentro do canal (agenda fixa), o que reduz poder estatístico.
- A elasticidade de idade mistura acúmulo de views com o canal ter crescido depois (vídeos velhos nasceram num canal menor) e possível remoção de vídeos fracos.

**8. Recomendação prática.** Manter pelo menos 3 dias entre vídeos longos e evitar dobrar o volume semanal. Depois de um vídeo fraco, não lançar o próximo em menos de 3 dias. Depois de um hit, não há ganho comprovado em "aproveitar a onda" com pressa. Não gastar energia com horário; fixar um que funcione para a equipe.

| Nota | 0 a 10 | Justificativa |
|---|---:|---|
| Impacto potencial | 7 | −13% a −19% em intervalos de 1 a 2 dias; −18% ao lançar rápido depois de fracasso |
| Confiança estatística | 6 | intervalo curto robusto em 3 alvos; pós-hit derrubado pela robustez; endogeneidade de agenda |
| Aplicabilidade prática | 9 | vira regra de calendário |
| Facilidade de implementação | 9 | custo zero, só reorganiza o calendário |

---

## Investigação G · Oportunidades de mercado e canais médios furando a bolha

**1. Pergunta investigada.** Em quais combinações de nicho, idioma, porte, faixa de duração e formato os canais conseguem múltiplos extremos (≥3x, ≥5x, ≥10x a mediana do próprio canal)? O que separa médios que rompem de médios estagnados, e quanto disso é oportunidade real?

**2. Metodologia.**
- Breakout **robusto**: múltiplo ≥ k tanto ajustado por idade (exp(`y_loo_idade`)) quanto bruto (exp(`y_loo`)).
- Mapas por célula com encolhimento empírico-Bayes beta-binomial e IC por bootstrap de canais; célula marcada como pouco confiável se tem menos de 3 canais ou só 1 canal com breakout. Células de 5 eixos só com 40 vídeos e 3 canais ou mais.
- GEE logístico (correlação permutável por canal, EP robusto): porte, nicho, idioma, faixa de duração, capítulos, legenda e idade; versão com porte × duração.
- Canais médios: tercil superior (rompedores, 28) contra tercil inferior (estagnados, 32) da taxa de vídeos ≥5x; 24 características com Mann-Whitney e BH.
- Armadilhas: persistência entre a 1ª e a 2ª metade cronológica de cada canal; breakout esperado só pela dispersão (normal); viés de tamanho de amostra e de inscritos.

**3. Resultado encontrado.**
- **Taxas gerais:** 8,6% dos vídeos fazem ≥3x, 3,8% fazem ≥5x e 1,4% fazem ≥10x a mediana do canal.
- **Médios rompem mais.** ≥3x: médio 10,9% [9,2; 12,6], grande 7,2%, gigante 6,7%. ≥10x: 2,2% contra 0,9% e 0,8%. GEE: médio contra grande OR 1,48 [1,12; 1,96] (≥3x) e 1,91 [1,25; 2,91] (≥5x).
- **Português rompe mais** (OR 1,64 [1,24; 2,17] em ≥3x; 1,88 em ≥5x), ajustando nicho, porte e duração.
- **Duração:** 20 a 45 min (OR 1,48 [1,23; 1,78]) e >45 min (OR 1,66 [1,16; 2,39]) contra 8 a 20 min. Interação porte × duração nula (todos q ≥ 0,23).
- **Nicho × porte (≥3x, EB):** entretenimento médio 14,9% (5 canais), infantil médio 13,7% (9), infantil grande 12,9%, educação médio 12,3% (10), lifestyle médio 12,3%, documentário médio 12,1%. Piores: entretenimento gigante 2,7%, tech gigante 4,1%, educação gigante 4,3%, games médio 5,0%. Games tem menos breakout que educação (OR 0,50, q = 0,084).
- **Só médios, nicho × duração:** histórias >45 min 21% (6 canais, só 4 com breakout), esportes 20 a 45 min 17,7%, entretenimento 8 a 20 min 17,5%, documentário 20 a 45 min 15,6% (7 canais).
- **Capítulos e legenda não mudam a chance de breakout** no GEE (OR 1,21 e 1,15, q ≥ 0,40).
- **A maior armadilha: romper a bolha é, sobretudo, volatilidade.** Correlação de 0,94 entre volatilidade e taxa de ≥3x nos médios, e a taxa observada acompanha a esperada só pela dispersão (excesso de cauda nulo, q = 0,45). Rompedores têm curtose **menor** (−0,29 contra 0,35).
- **Mas é um traço persistente do canal:** correlação de 0,57 [0,45; 0,67] entre a taxa de ≥3x na 1ª e na 2ª metade (médios 0,52 [0,33; 0,68]).
- **Rompedores são médios menores:** mediana de 565 mil contra 1,2 milhão de inscritos (q = 0,012); correlação de −0,36 entre inscritos e breakout nos médios. Têm títulos mais longos (66 contra 49 caracteres, q = 0,042) e, perto do limiar, mais colaborações, mais variedade de duração e menos 1ª pessoa (q de 0,067 a 0,085). Capa, capítulos, legenda, duração mediana, intervalo e rosto: nulos (q ≥ 0,25).

**4. Evidência estatística.** GEE ≥3x: porte médio q = 0,024; pt q = 0,004; 20 a 45 min q = 0,001; >45 min q = 0,024; log(idade) OR 1,20 (q = 0,001), lembrando que o múltiplo bruto favorece vídeos antigos. Persistência: Spearman 0,565 (p < 10⁻¹⁷). Arquivos: `G_mapa_*.csv`, `G_celulas_5_eixos_n40_3canais.csv`, `G_gee_breakout_odds.csv`, `G_medios_rompedores_vs_estagnados.csv`, `G_canais_breakout.csv`, `G_meta.json`.

**5. Visualizações.** `graficos/ml_04_mapa_oportunidades_breakout.png` (nicho × porte, nicho × duração nos médios, taxas por porte com IC, volatilidade × breakout com a curva esperada pela dispersão, persistência entre metades e rompedores contra estagnados).

**6. Descobertas inesperadas.**
- "Rompedor" e "volátil" são quase a mesma coisa. Canal de resultado previsível quase nunca faz 5x a própria mediana, e canal irregular faz com frequência, mas também flopa com frequência.
- Médios menores rompem mais: a mediana do canal é mais baixa e um vídeo bom a supera com mais facilidade.
- Títulos mais descritivos e colaborações aparecem nos rompedores, mas com N = 60 canais.

**7. Limitações e vieses.**
- Sobrevivência: só entram canais que chegaram a 200 mil inscritos; quem tentou ser volátil e não cresceu não está na base.
- Breakout é relativo à mediana do canal: um canal com muitos vídeos fracos rompe "mais" sem ter mais alcance absoluto.
- Células de 3 eixos com 5 a 10 canais; células de 5 eixos com 3 a 5 canais. Servem para gerar hipóteses, não para decidir.
- Sem dados de busca, oferta ou concorrência: "oportunidade" aqui é teto relativo, não demanda.

**8. Recomendação prática.** Para canal médio que quer romper: concentrar as apostas em 20 min ou mais, aceitar mais variância (formatos e durações diferentes, colaborações, temas fora do nicho) e medir sucesso por quantos vídeos passam de 3x, sabendo que isso vem junto com mais vídeos abaixo da mediana. Priorizar nichos com teto alto para médios (entretenimento, infantil, educação, lifestyle, documentário) e tratar games como nicho de teto baixo.

| Nota | 0 a 10 | Justificativa |
|---|---:|---|
| Impacto potencial | 6 | calibra onde há teto; poucas alavancas causais |
| Confiança estatística | 5 | taxas por porte e idioma robustas; células finas com poucos canais; breakout quase tautológico com volatilidade |
| Aplicabilidade prática | 6 | ajuda a escolher nicho, duração e apetite de risco |
| Facilidade de implementação | 6 | exige margem para absorver flops |

---

## Hipóteses descartadas pelos dados

| Hipótese | Teste | Resultado | Veredito |
|---|---|---|---|
| Existe um "DNA do viral" previsível nos metadados | top 5% do canal, 2 regimes | AUC 0,58 (canais novos) e 0,54 [0,50; 0,58] (futuro do canal) | descartada (sinal fraco) |
| Árvores captam interações que o linear não vê, dentro do canal | top 5% do canal | 0,583 contra 0,581 | descartada |
| Traços de miniatura melhoram a previsão | ablação sem as 26 variáveis de capa | Spearman 0,162 contra 0,163 | descartada |
| Rosto grande, palavras na capa, contraste ou saturação funcionam diferente por porte ou nicho | 12 testes de interação | todos q ≥ 0,26; interações SHAP perto de zero | descartada |
| Efeito da duração muda com porte ou idioma | Wald da interação | q = 0,75 e 0,54 | descartada (muda com nicho) |
| Legenda funciona diferente em pt e en | Wald | q = 0,87 | descartada |
| Capítulos ou timestamps aumentam views por si | FE com spline de duração | +9,6% (q = 0,40) e +12,5% (q = 0,36); negativo em >45 min | descartada |
| Momentum depois de um hit | resíduo com tendência quadrática | +2,4% [−2,4; +7,6] | descartada (era fase do canal) |
| Esperar alguns dias depois de um hit rende mais que o normal | extremo × intervalo | teste conjunto p = 0,58 | descartada |
| Existe um dia ou horário melhor no geral | Wald e hora circular | q = 0,31 e 0,86; p = 0,68 | descartada |
| Volume de 30 dias derruba o desempenho | FE com `y_passado` | −1,2% (q = 0,63) | descartada (só os 7 dias importam) |
| Vídeos continuam crescendo muito depois de 35 dias | elasticidade transversal | 0,096 no geral | fraca; não mensurável sem séries |
| Médios rompedores têm capas ou estrutura diferentes | 24 características | capa, capítulos, legenda, rosto: q ≥ 0,25 | descartada |
| Romper a bolha é habilidade além da variância | breakout observado contra esperado pela dispersão | excesso nulo (q = 0,45) | descartada (é volatilidade persistente) |
| Há um intervalo ótimo de cerca de 2 meses | spline de intervalo | ótimo na borda; com `y_passado` só +5% aos 30 dias | descartada como regra |

---

## Revisão crítica com gemini-4-carbon

Duas chamadas (arquivos `resultados/Z_carbon_1_revisao_critica.md` e `resultados/Z_carbon_2_recomendacoes.md`), registradas em `dados/uso_gemini_ml.csv`. Pontos incorporados a este relatório:
- O ganho do regime temporal no topo global é identificação do canal (confirmado pelo baseline só canal).
- A queda do top 5% do canal no temporal tem componente aritmético (5% fixos por canal na janela inteira).
- O momentum pós-hit não resiste à tendência quadrática; o arrasto é assimétrico (fracasso pesa mais).
- Capítulos e timestamps são confundidos pela duração.
- A classificação "rompedor" é quase tautológica com a volatilidade e enviesada para médios menores; o breakout bruto favorece vídeos antigos (OR de idade 1,20).
- O ótimo de 62 dias de intervalo não é regra operacional.
- Testes sugeridos e ainda não feitos: wild cluster bootstrap nos nichos com poucos canais, Romano-Wolf entre baterias, alvo de idade recalculado em janela expansiva dentro do split temporal, coleta prospectiva na hora da publicação para eliminar causalidade reversa de título, capa e legenda.

Correção feita sobre a sugestão do revisor: ele recomendou "esperar 3 a 10 dias depois de um hit". O teste complementar (`F_pos_viral_x_intervalo.csv`) mostrou que isso é o efeito geral do intervalo; o efeito específico existe depois de um **fracasso**, não de um hit.

| Chamada | Modelo | Entrada | Saída | Raciocínio | Custo (tarifa cheia) |
|---|---|---:|---:|---:|---:|
| Revisão crítica de vieses | gemini-4-carbon | 80.732 | 4.384 | 8.816 | R$ 1,74 |
| Recomendações e notas | gemini-4-carbon | 85.106 | 5.112 | 0 | R$ 1,31 |
| **Total da frente** | | | | | **R$ 3,05** (teto R$ 15,00) |

---

## Arquivos e reprodutibilidade

Ordem de execução (ambiente virtual local, `n_jobs=2`, BLAS limitado a 2 threads, semente 20261123):
1. `scripts/A1_modelagem_preditiva.py` (cerca de 11 min): métricas, IC e modelos salvos.
2. `scripts/A2_shap_interacoes.py` (cerca de 2 min): SHAP, interações, bateria within e `ml_01`.
3. `scripts/E_duracao_gam.py` (cerca de 1 min): curvas, faixas, estrutura, pyGAM e `ml_02`.
4. `scripts/F_cadencia_sequencia_horario.py` (cerca de 5 min) e `scripts/F2_pos_viral_x_intervalo.py`: autocorrelação, pós-extremo, intervalo, volume, dia e hora, idade e `ml_03`.
5. `scripts/G_oportunidades_breakout.py` (cerca de 15 s): mapas, GEE, rompedores e `ml_04`.
6. `scripts/Z_consolidar.py`: `resultados/resumo_frente_ml.json`.
7. `scripts/Z_revisao_carbon.py`: revisão crítica (usa `scripts/gemini_router_ml.py`, trava de R$ 15,00).

Modelos para o motor de consulta (`dados/`): `modelo_lgbm_yw.txt`, `modelo_xgb_yw.json`, `modelo_ridge_yw.pkl` (com a lista de colunas one-hot), `modelo_lgbm_top5_g.txt`, `modelo_lgbm_top10_g.txt`, `modelo_lgbm_top5_c.txt`. Entrada: as 68 colunas de `FEATURES` em `scripts/ml_utils.py`, montadas por `carregar()`. Também em `dados/`: previsões fora da amostra (`oof_preds.parquet`) e SHAP out-of-fold (`shap_oof_*.parquet`).
