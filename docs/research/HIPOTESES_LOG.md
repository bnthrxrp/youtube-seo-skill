> **AVISO DE AUDITORIA E GOVERNANÇA ESTATÍSTICA (ERRATA ATIVA):**
> Este relatório contém estimativas geradas antes do fechamento da auditoria metodológica sênior. Ao consultar este material, aplique obrigatoriamente as seguintes travas:
> 1. **Teto preditivo:** Metadados estáticos (título, capa e horário) explicam menos de 2,5% da variância intra-canal ($R^2 \le 0,025$). Nenhum coeficiente deve ser lido como garantia causal de alcance.
> 2. **Recomendações firmes vs. Hipóteses A/B:** Como **recomendação prescritiva firme** (`faixa = validada` em `docs/research/data/ranking_alavancas_revisado.csv`), valem exclusivamente itens com $q < 0,05$, IC 95% limpo sem cruzar zero e penalização de endogeneidade. Itens na zona $0,05 \le q < 0,15$ (ou rebaixados por limites da base bruta) pertencem à faixa `hipotese_ab`: **hipótese A/B não é recomendação**, servindo apenas para experimentação controlada no *Testar e Comparar* do YouTube Studio. Ignore integralmente clusters visuais (`HDB-*`, `KM12-*`), ângulos de vídeo e qualquer item com $q \ge 0,15$ (`faixa = removida`).
> 3. **Reconciliações e pendências:** Em caso de conflito sobre alinhamento Capa × Título ou Momentum pós-hit, ou para verificar variáveis marcadas como `PENDENTE DE REPROCESSAMENTO` (vazamento temporal residual, filtro de canais pequenos e denominador de idade), prevalece o disposto em `docs/research/ERRATA_E_LIMITES.md`.

---

# Registro de hipóteses

Cada linha registra uma hipótese testada, o teste, o resultado e o status. Status possíveis: **sustentada**, **descartada**, **inconclusiva** ou **artefato** (a métrica criava o efeito). Use este registro para não repetir testes nem reabrir conclusões sem dado novo.

| ID | Hipótese | Teste (arquivo) | Resultado | Status |
|---|---|---|---|---|
| AUD-1 | `base_canal` usa o próprio vídeo (vazamento direto) | recálculo exato (`auditoria.json` › alvo) | base idêntica e sem o próprio vídeo | descartada |
| AUD-2 | `base_canal` usa informação futura | fração de vizinhos publicados depois | 49,3% dos vizinhos são futuros | sustentada (uso só retrospectivo; `y_passado` para predição) |
| AUD-3 | Comentários zero ou ausentes no infantil são engajamento baixo | `made_for_kids` × comentários | 0% dos 1.879 infantis com comentário visível | descartada (é estrutural, virou NaN) |
| AUD-4 | Filtros de seleção são neutros entre estratos | funil por nicho e porte | lifestyle −45% de canais, documentário −41%, médio −28%, grande −11%; gigantes de formato curto saíram | descartada (há viés; documentado) |
| AUD-5 | O porte da seleção ainda vale no snapshot | inscritos da seleção × API | 0 canais mudariam de porte | sustentada |
| H-1 | Engajamento cresce na mesma proporção das views dentro do canal | elasticidade (`02_H_elasticidade.csv`) | curtidas 0,80 [0,77; 0,83]; comentários 0,69 [0,66; 0,73] | descartada (cresce menos) |
| H-2 | Vídeos acima do normal em views são mais engajados por view | correlação dentro do canal | −0,35 [−0,39; −0,31], negativa nos 11 nichos | descartada (é o contrário) |
| H-3 | Engajamento e alcance divergem (regimes "engajado sem alcance" e "alcance frio") | taxa bruta × resíduo de escala (`02b_regimes_residuais.json`) | taxa bruta: 76,9% contra 60% esperado; resíduo: 54,9% a 56,6% contra 60%, correlação ≈ 0 | artefato de razão (escala); as dimensões são independentes |
| H-4 | Pergunta no título aumenta comentários por view | bateria de traços, 3 especificações | +10,4% [+5,2; +15,9], q = 0,003 | sustentada (associação) |
| H-5 | Expressão triste na capa aumenta comentários por view | idem | +17,9% [+8,9; +27,6], q = 0,003 | sustentada (associação) |
| H-6 | Rosto grande na capa aumenta comentários por view | idem | +7,7% [+3,3; +12,3], q = 0,010 | sustentada (associação) |
| H-7 | 1ª pessoa no título aumenta engajamento | idem | +8,8% em comentários, mas some ao controlar alcance; curtidas instável | inconclusiva |
| H-8 | Algum traço aumenta curtidas por view de forma robusta | idem | nenhum passa nas 3 especificações | descartada |
| A-1 | Existem "efeitos de cauda" (traços que só aparecem no top 1% ou 5%) dentro do canal | modelo linear com efeito fixo top 5% e top 10% do canal | nada além do que já aparece na média (legenda, duração, capa complementar) | descartada |
| A-2 | Rosto grande e 1ª pessoa reduzem a chance de topo | logística global × dentro do canal | global: OR 0,63 e 0,60 (q ≈ 0,04); dentro do canal: nulo | artefato de composição (são traços de canais estáveis) |
| A-3 | Canais "de personalidade" são menos voláteis | desvio de `y` por canal × % 1ª pessoa | −0,036 por +10 pp [−0,056; −0,015], p = 0,0005 | sustentada |
| A-4 | Legenda própria se associa ao topo do canal | modelo linear com efeito fixo top 5% do canal | +12,9 pp, q = 0,011; efeito médio +28,6% | sustentada (risco de causalidade reversa) |
| A-5 | Texto da capa que complementa o título se associa ao topo | idem | +4,8 pp, q = 0,037 | sustentada (fraca) |
| A-6 | Concentração extrema (poucos vídeos = quase todas as views) | fração do top 10% | 33,9% das views no canal mediano | descartada (moderada) |
| D-1 | Canais médios produzem mais anomalias de 10x ou mais | taxa com bootstrap | 26,5 por mil [19,4; 34,8] contra 12,0 e 12,9 | sustentada |
| D-2 | Anomalias têm um traço de título, capa, duração ou legenda próprio | modelo linear com efeito fixo, 40 traços + BH | 0 de 40 | descartada |
| D-3 | Anomalias têm formato próprio (tutorial, review, desafio…) | classificação por LLM + bootstrap pareado | nenhum formato passa BH | descartada |
| D-4 | Anomalias falam com público de fora do nicho | idem | +9,5 pp [+3,1; +15,7], p = 0,002, q = 0,06 | inconclusiva (testar na Fase 2 com amostra maior) |
| D-5 | Anomalias dependem de gancho temporal | idem | +2,3 pp, q = 0,97 | descartada |
| D-6 | Parte das anomalias de tech é mídia paga de lançamento | sincronia de 3 canais no mesmo lançamento e dia | 154x a 442x no Galaxy Z Fold 8 em 22/07/2026 | hipótese não testável na base |
| F-1 | Intervalo de menos de 2 dias desde o vídeo anterior se associa a desempenho pior | efeito fixo, 3 alvos × 2 amostras | −8,8% a −22,1%, sempre q ≤ 0,003 | sustentada |
| F-2 | Pausa longa (mais de 45 dias) se associa a desempenho melhor | idem | +16,9% em `y`, nulo em `y_passado` e `y_loo` | inconclusiva |
| F-3 | Mais vídeos nos 30 dias anteriores reduzem o desempenho | efeito fixo | −3,8% por dobro em `y`; nulo em `y_passado` | inconclusiva (efeito pequeno) |
| F-4 | Ressaca depois de um hit | vídeo seguinte a um top 5% definido por `y` | −8,1% | artefato (vizinhos bilaterais de `y`) |
| F-5 | Momentum depois de um hit | top 5% definido por resíduo de tendência; permutação | +9,4% [+3,4; +15,1]; autocorrelação 0,070 contra nulo −0,012 | sustentada (pode ser fase do canal) |
| F-6 | Vídeos continuam crescendo muito depois de 35 dias | elasticidade log(views) ~ log(idade) dentro do canal | 0,077 [0,003; 0,150] | descartada no geral (só infantil, lifestyle e entretenimento têm elasticidade relevante) |
| F-7 | Padrões explosivo, evergreen e crescimento tardio | – | exigem snapshots repetidos | não mensurável |
| ANT-1 | Legenda +28% e duração (estudo anterior) | repetido no efeito médio | +28,6% e +14,9% por dobro, q = 0,0001 | sustentada (replicada) |
| ANT-2 | Expressões tensas na capa puxam views (estudo anterior) | bateria de efeito médio com BH | nenhuma expressão passa BH em `y` | descartada para views (mas triste aumenta comentários) |

## Decisões técnicas registradas

1. **Desfecho principal:** `y` com efeito fixo de canal. Sensibilidade com `y_passado` e `y_loo`. `y_loo_idade` só como apoio, porque tem caudas pesadas.
2. **Erro padrão sempre agrupado por canal.** BH dentro de cada bateria (não entre baterias).
3. **Engajamento:** comparar sempre pelo resíduo de escala dentro do canal, nunca pela taxa bruta (ver H-3).
4. **Comentários do infantil:** NaN estrutural.
5. **Sequência:** medida por resíduo de tendência, nunca por `y`, por causa do artefato F-4.
6. **Classificação de tema:** LLM barato aplicado só às 321 anomalias e a 2 controles por anomalia (piloto de 50 antes). Escala total fica para a Fase 2, via Batch.
7. **Perfil por faixa de idade** não é ciclo de vida: com a janela truncada em 100 vídeos, só canais de postagem lenta chegam a 4 anos ou mais (54 canais). Usar só a elasticidade dentro do canal.
8. **Revisão crítica por LLM** (`resultados/05_carbon_revisao.md`) foi tratada como parecer. Só entraram nos documentos as críticas reproduzidas com cálculo próprio (regimes, H-3). Números citados pela revisão que não vieram dos arquivos de resultado não foram usados.
