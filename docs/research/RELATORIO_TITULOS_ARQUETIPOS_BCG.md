# Frente 2C · Engenharia reversa de títulos, título + thumbnail, arquétipos e oportunidades semânticas

Laboratório de Data Science de YouTube · 17.882 vídeos longos · 203 canais · PT e EN · 11 nichos · gerado em 23/11/2026 (horário de Brasília)

## Como ler este relatório

- **Desfecho principal:** `y_loo_idade` winsorizado em 0,5% e 99,5% (`y_li_w`), que é o log do múltiplo de views do vídeo contra o esperado do próprio canal para a mesma idade. "+10%" quer dizer 1,10x o normal do canal. Sensibilidade em `y` (alvo principal do laboratório) e em `y_passado` (sem olhar o futuro). O `y_loo_idade` cru tem caudas absurdas (máximo de 19,9 em log, ou seja 4 x 10^8 vezes), por isso os múltiplos exibidos usam a versão winsorizada; os exemplos mostram também o múltiplo pelo `y`.
- **Top 5% / Top 1% / Flop 20%:** percentis globais de `y_loo_idade` (top 5% ≥ 4,8x aproximadamente; flop = 20% piores).
- **Todos os efeitos:** efeito fixo de canal (só compara vídeos do mesmo canal), controle de log(duração), IC 95% por bootstrap de canais (500 reamostragens, canal inteiro), p cluster-robusto e correção de Benjamini-Hochberg (BH) por bateria. "Significativo" = q < 0,05; "sugestivo" = q < 0,10.
- **Causalidade:** nada aqui é causal. Título e capa são os atuais (podem ter sido trocados depois do lançamento), não há CTR nem impressões, e só existem canais de 200 mil inscritos para cima.
- **Arquivos:** scripts em `scripts/` (ordem 01 a 11), dados em `dados/`, tabelas em `resultados/`, gráficos em `graficos/`, gasto em `dados/uso_gemini_arquetipos.csv`.

## Resumo executivo

1. **O título sozinho explica quase nada do desempenho relativo.** Fora da amostra (GroupKFold por canal), embeddings do título dão R² = 0,000 (IC −0,012 a 0,011); o melhor modelo (embeddings + estrutura + duração) chega a R² = 0,018 (IC 0,005 a 0,031). Dentro do canal, o título acrescenta cerca de +0,01 de correlação de Spearman ao que a duração já explica (0,177 contra 0,165).
2. **Repetir o título na capa não é punido; alinhar é levemente melhor.** Capa que "repete" o título fica igual à que "complementa" (+1,1%, IC −9,5% a +13,4%). Cada +1 desvio-padrão de similaridade semântica título × texto da capa vale +4,1% (IC +0,9% a +7,4%, q = 0,034), robusto a OCR limpo e a controles. O que tende a perder é texto de capa **sem relação** com o título.
3. **Três traços de título sobrevivem ao rigor:** vocabulário abstrato (−15,4%, q = 0,005), 1ª pessoa em EN (−11,0%, q = 0,031) e emoji em PT (+23,5%, q = 0,09, concentrado em 45 canais). Afirmação contraintuitiva como gancho principal em EN: +14,2% (q = 0,015).
4. **Taxonomia em dois níveis.** Nível 1: 24 macro-arquétipos de formato, estáveis (ARI 0,94), mas quase 1 canal = 1 arquétipo e separados por idioma; servem para ler risco (cauda e flop), não ganho médio. Nível 2: 18 ângulos de vídeo que cruzam 72 a 197 canais (ARI 0,97); **nenhum** muda o desempenho médio dentro do canal após BH (q ≥ 0,89).
5. **Oportunidades:** nenhuma célula ângulo × nicho sobrevive ao BH. Não há arbitragem EN → PT comprovada. O melhor achado acionável para canais médios é o ângulo "Choque, Terror e Listas": −5,7 p.p. de flops (q = 0,088) e +16,3% de média (q = 0,37).
6. **Gasto Gemini desta frente:** R$ 14,71 (US$ 2,48) na tarifa cheia, abaixo do teto de R$ 20,00.

---

## Investigação B · Engenharia reversa de títulos e título + thumbnail como unidade

### 1. Pergunta
Que estruturas de título (abertura, gancho, léxico, pontuação, comprimento) se associam a desempenho acima do normal do canal, quanto o texto do título prevê fora da amostra, e o par título + capa funciona melhor quando é redundante ou complementar? Há interações título × capa que mudem o resultado por nicho e idioma?

### 2. Metodologia
- **NLP estrutural por regras PT + EN** (`02_estrutura_titulos.py`) nos 17.882 títulos: 9 ganchos de abertura (desafio/experimento, comparação/vs, lista/ranking, tutorial/como, pergunta direta, revelação/mistério, afirmação contraintuitiva, urgência/novidade, história pessoal), número/dinheiro, entidade/marca famosa, superlativo, negatividade, 1ª e 2ª pessoa, comprimento (palavras, caracteres e z-score dentro de idioma × nicho), comprimento médio de palavra, palavras funcionais, vocabulário abstrato, concretude, parênteses, separadores, exclamação, reticências, CAPS, emoji, hashtag, posição do elemento concreto e da palavra-chave. Um gancho principal exclusivo por prioridade.
- **Classificação por LLM** (`gemini-3.5-flash-lite`, só classificação) de 2.821 títulos: amostra estratificada de 1.304 (nicho × idioma × faixa top 5%/meio/flop 20%) mais 1.517 representantes dos arquétipos. Campos: abertura, gatilho psicológico, lacuna de curiosidade (0 a 3), especificidade (1 a 5), promessa clara, relação título × capa e papel da capa.
- **Embeddings** `gemini-embedding-2-preview` 768d: título (`title_embeddings_768.parquet`), título + capa estruturada (`multimodal_text_embeddings_768.parquet`), texto da capa por OCR (13.014 vídeos) e título + 250 caracteres limpos da descrição.
- **Poder preditivo** (`05_preditivo_titulos.py`): Ridge e LightGBM (n_jobs = 2) em GroupKFold de 5 dobras por canal, alvos `y_li_w` e `y_passado` (regressão) e top 5% (classificação); IC por bootstrap de canais; métricas também **dentro do canal** (Spearman médio por canal e AUC do top 5% do próprio canal).
- **Redundância vs complementaridade** (`04_b_titulos_sinergia.py`): categoria do Gemini (`g_texto_repete_titulo`), `ocr_repete_titulo`, cosseno entre embeddings do título e do OCR (contínuo e em quintis), checagem com OCR "limpo" (7.524 capas) e controle de repetição literal e nº de palavras.
- **Interações:** 7 estruturas de título × 16 elementos de capa, em 7 recortes (toda a base, PT, EN e 4 grupos de nicho): 649 testes com termo de interação e efeito fixo de canal, BH por recorte.

### 3. Resultado

**Poder preditivo fora da amostra (`resultados/b5_poder_preditivo_titulos_oos.csv`)**

| Conjunto | R² OOS (IC 95%) | Spearman global | Spearman dentro do canal | AUC top 5% global (IC) | AUC top 5% do canal |
|---|---|---:|---:|---|---:|
| Contexto (nicho, idioma, porte, duração) | 0,007 (−0,001 a 0,014) | 0,109 | 0,165 | 0,510 (0,467 a 0,558) | 0,549 |
| Estrutura do título por regras (LightGBM) | −0,011 (−0,016 a −0,006) | 0,033 | 0,026 | 0,580 (0,553 a 0,612) | 0,512 |
| Embeddings do título 768d (Ridge) | 0,000 (−0,012 a 0,011) | 0,134 | 0,161 | 0,628 (0,596 a 0,669) | 0,536 |
| Embeddings PCA64 (LightGBM) | 0,006 (−0,001 a 0,012) | 0,103 | 0,124 | 0,615 (0,586 a 0,649) | 0,531 |
| Embeddings + estrutura + duração (LightGBM) | **0,018 (0,005 a 0,031)** | 0,162 | **0,177** | 0,625 (0,595 a 0,665) | 0,533 |
| Título + capa estruturada, multimodal (Ridge) | 0,011 (0,003 a 0,020) | 0,128 | 0,158 | 0,610 (0,580 a 0,652) | 0,531 |

Com `y_passado` (sem informação futura) o melhor R² cai para 0,010. Por idioma (embeddings, Ridge): R² −0,002 em PT e 0,001 em EN; AUC 0,59 em PT e 0,65 em EN. **Leitura:** o AUC global de 0,63 para o top 5% vem sobretudo de identificar *tipos de canal* com caudas mais gordas (canais voláteis), não de distinguir o vídeo que estoura dentro do mesmo canal (AUC dentro do canal 0,53 a 0,54, quase moeda).

**Traços de título com efeito fixo de canal (`b1_tracos_titulo_efeitos.csv`, 30 traços × 9 recortes × 3 desfechos)**

| Traço | Recorte | Efeito | IC 95% | q (BH) | Vídeos / canais com o traço |
|---|---|---:|---|---:|---|
| Vocabulário abstrato (vida, sucesso, verdade, mente, mindset, sonho...) | toda a base | **−15,4%** | −22,9% a −7,9% | **0,005** | 814 / 142 |
| Vocabulário abstrato | PT | −20,2% | −30,4% a −10,2% | 0,054 | 501 / 71 |
| 1ª pessoa (eu, meu, I, my, we) | EN | **−11,0%** | −16,9% a −5,5% | **0,031** | 1.853 / 98 |
| 1ª pessoa | toda a base | −8,1% | −13,2% a −2,8% | 0,066 | 2.961 / 175 |
| Emoji no título | PT | +23,5% | +6,7% a +41,7% | 0,090 | 1.247 / 45 |
| Emoji no título | toda a base | +18,0% | +6,0% a +33,6% | 0,066 | 2.036 / 69 |
| Entidade/marca famosa (iPhone, Galaxy, GTA, Minecraft, Trump...) | tech + games | **+25,5%** | +11,6% a +40,1% | **0,014** | 1.000 / 35 |
| Afirmação contraintuitiva como gancho principal | EN | **+14,2%** | +3,8% a +23,7% | **0,015** | 299 vídeos |
| Palavra-chave no início | toda a base, chance de top 5% | +1,3 p.p. | +0,6 a +2,1 p.p. | 0,023 | 11.772 / 202 |

Comprimento do título não importa: nenhuma faixa de caracteres difere da faixa 46 a 60 (todas com q > 0,93, em PT e em EN). Pergunta direta, número/dinheiro, lista, tutorial, desafio, mistério, urgência, separadores, parênteses e reticências: todos com IC cruzando zero na base toda.

**Redundância vs complementaridade (`b2_redundancia_vs_complementaridade.csv`, `b2_quintis_similaridade_titulo_ocr.csv`)**

| Teste | Recorte | Efeito | IC 95% | q |
|---|---|---:|---|---:|
| Capa REPETE o título (ref.: complementa) | toda a base | +1,1% | −9,5% a +13,4% | 0,88 |
| Capa REPETE o título | EN / PT | +10,1% / −8,3% | −1,8% a +24,6% / −23,8% a +21,0% | 0,49 / 0,88 |
| Texto sem relação clara com o título | toda a base / PT | −2,4% / −5,5% | −6,4% a +1,2% / −11,5% a +1,0% | 0,62 / 0,49 |
| Capa sem texto | toda a base | −0,6% | −6,2% a +5,6% | 0,88 |
| Similaridade semântica título × capa (+1 DP do cosseno) | toda a base | **+4,1%** | +0,9% a +7,4% | **0,034** |
| idem | EN / PT | +4,9% / +3,5% | +1,4% a +8,7% / −1,3% a +9,1% | 0,034 / 0,36 |
| idem, só OCR limpo | toda a base | +4,0% | +0,4% a +8,0% | p = 0,042 |
| idem, OCR limpo + controle de repetição literal e nº de palavras | toda a base | +4,7% | +1,0% a +8,6% | p = 0,021 |
| Quintil mais redundante (Q5) vs Q3 | toda a base | +10,7% | +2,8% a +19,9% | 0,077 |

Dose-resposta monotônica: mediana de 0,94x no quintil mais "complementar" (semanticamente distante) até 0,995x no mais "redundante"; top 5% sobe de 4,6% para 7,2%.

**Interações título × capa (`b3_interacoes_titulo_thumb.csv`)**: 649 testes, só 2 com q < 0,10, ambos **negativos** e em amostras pequenas:
- Comparação/vs no título × objeto em destaque na capa, em lifestyle e culinária: −63% (IC −75% a −15%), q = 0,033, 79 vídeos, 17 canais.
- Comparação/vs × expressão séria/raiva, em tech e games: −31% (IC −43% a −4%), q = 0,069, 55 vídeos, 10 canais.

Sinais positivos que não passam no BH: pergunta direta × objeto em destaque na base toda, +15,4% (IC +6,2% a +26,0%, q = 0,135, 1.540 vídeos, 160 canais); pergunta direta × número na capa em tech/games, +36,4% (q = 0,13, 147 vídeos, 32 canais). História/1ª pessoa × foto real: −13,3% (q = 0,43).

**Classificação por LLM, top 5% vs flop 20% (`b4_llm_estruturas_top5_vs_flop20.csv`)**: "utilidade prática" como gatilho aparece +7,6 p.p. mais no top 5% (IC +0,6 a +14,1; q = 0,14); capa de "reação emocional" aparece −7,1 p.p. (IC −12,7 a −1,3; q = 0,14); abertura em desafio/experimento −3,7 p.p. (q = 0,17). Lacuna de curiosidade e especificidade médias **não** diferem entre topo e flop.

### 4. Evidência estatística
Bateria de traços: 30 traços × 9 recortes × 3 desfechos, BH por recorte e desfecho; só os listados acima passam q < 0,10 em `y_li_w`. Vocabulário abstrato e 1ª pessoa em EN se mantêm em `y` (−9,6% com q = 0,115 e −10,8% com q = 0,028). Emoji cai para +12,5% em `y` (q = 0,12). Similaridade semântica: 10.341 vídeos com 2+ palavras lidas na capa, 3 especificações concordantes. Interações: 649 testes, 2 com q < 0,10. Poder preditivo: 5 dobras por canal, IC por 300 bootstraps de canais. Concordância entre o gancho principal por regras e a abertura classificada pelo LLM: 29,4% (os dois enxergam coisas diferentes; o LLM é mais semântico e as regras são multirrótulo com prioridade).

### 5. Visualizações
`graficos/arq_01_sinergia_titulo_thumb.png`: (A) repetir vs complementar por idioma com IC 95%; (B) dose-resposta da similaridade semântica em quintis; (C) mapa de calor das 112 interações na base toda com marcação de q; (D) as 14 interações de menor p com IC.

### 6. Descobertas inesperadas
- **A regra de ouro "nunca repita o título na capa" não aparece nos dados.** Em EN, repetir tende a ser *melhor* (+10%, IC cruza zero); o que perde é texto que não conversa com o título. O achado anterior do laboratório (A-5, "capa complementar" ligada ao topo) é compatível: o contraste ruim é contra "outro" (sem relação), não contra "repete".
- **O título prevê tipos de canal, não vídeos.** O AUC de 0,63 some dentro do canal (0,53).
- **Contraintuitivo funciona em EN e não em PT** (+14% contra −2%).
- **Emoji em PT** se associa a +23%, mas concentrado em 45 canais (infantil, beleza, culinária); tratar como hipótese de teste.

### 7. Limitações e vieses
Causalidade reversa (títulos e capas trocados após flop ou hit). OCR com ruído (mitigado pela versão limpa). Regras léxicas são aproximadas; "vocabulário abstrato" usa lista curta de palavras. Sem CTR nem impressões: o efeito do título chega diluído no total de views. Recortes de nicho com 10 a 35 canais têm IC largos. A classificação por LLM usa amostra estratificada por faixa de desempenho; compara proporções entre faixas, não estima efeito médio.

### 8. Recomendação prática
1. Trocar palavras abstratas por objetos, números, nomes e cenas concretas no título.
2. Em EN, tirar o "I/my" do começo e colocar a premissa ou o objeto no centro; em PT o efeito da 1ª pessoa é nulo.
3. Usar o texto da capa para **reforçar a mesma ideia** do título (mesmas palavras-chave ou sinônimos), e não para abrir um assunto paralelo.
4. Em tech e games, citar a marca ou o produto famoso no título.
5. Evitar capa de "objeto isolado" ou "rosto bravo" quando o título é uma comparação; mostrar os dois lados.
6. Usar o título como filtro fino, não como alavanca principal: duração, tema e momento do canal pesam muito mais.

| Nota | Valor (0 a 10) |
|---|---:|
| Impacto potencial | 5 |
| Confiança estatística | 7 |
| Aplicabilidade prática | 8 |
| Facilidade de implementação | 9 |

---

## Investigação C · Descoberta automática de arquétipos (taxonomia própria)

### 1. Pergunta
Existem arquétipos reais de conteúdo e embalagem, além das categorias rasas do YouTube, e quais são consistentes, quais são "loteria" e quais são fracos quando se controla o canal?

### 2. Metodologia
- **Representação** (`06_arquetipos.py`): embeddings de título + 250 caracteres limpos da descrição (768d, PCA para 50 componentes, 47,3% da variância) com peso de 70%, mais vetor estruturado de embalagem e formato (log da duração, estilo, fundo e expressão da capa, rosto grande, sem texto, 5+ palavras, comparação, seta, número, objeto, olhar, nº de rostos, nº de palavras lidas, 13 traços de título) com peso de 30%.
- **UMAP** (10 dimensões para agrupar, 2 para o mapa; 30 vizinhos) + **HDBSCAN**, grade de 20 combinações (tamanho mínimo, `min_samples`, método eom/leaf) e escolha pela validade relativa, ruído e tamanho do maior grupo dentro de 12 a 25 grupos. Ruído atribuído ao grupo vizinho por kNN (15) e marcado em `nucleo_hdbscan`.
- **Estabilidade:** 10 subamostras de 80% (ARI e Jaccard por grupo) e 2 sementes alternativas de UMAP no pipeline completo.
- **Dois níveis**, porque a primeira rodada revelou que o grupo semântico é quase uma propriedade do canal:
  - **Nível 1, macro-arquétipos de formato:** vetor original.
  - **Nível 2, ângulos de vídeo:** o mesmo vetor menos o centróide do próprio canal (o que o vídeo tem de diferente do padrão do canal). É o nível em que comparar desempenho faz sentido, já que o desfecho é relativo ao canal.
- **Métricas por arquétipo** (`07_perfil_e_nomes_arquetipos.py`): n, % da base, canais, nichos, concentração no maior canal, P25 a P90 do múltiplo, top 5%, top 1%, flop 20%, efeito fixo de canal (média, chance de top 5% e de flop, com BH), duração, perfil de título e capa, curtidas e comentários por view, alcance por inscrito ajustado por idade, assinatura de traços e palavras típicas. Nomes e fichas pelo `gemini-4-hydrogen` a partir de 18 a 35 exemplos reais e das métricas.
- **Tipo de risco × retorno:** vencedor completo (top 5% ≥ 6%, flop < 18%, mediana acima da geral), consistente (mediana acima da geral e flop < 18%), loteria/cauda longa (top 5% ≥ 6%), fraco (top 5% < 4% e flop > 22%), neutro.

### 3. Resultado

**Escolhas e estabilidade (`c_grade_sensibilidade_hdbscan*.csv`, `c_estabilidade*.json`)**

| Nível | Configuração | Grupos | Ruído reatribuído | ARI subamostras (mín.) | ARI outras sementes UMAP | Canais por grupo |
|---|---|---:|---:|---|---|---|
| 1. Macro-formatos | tamanho mín. 250, min_samples 10, eom | 24 | 20,0% | 0,944 (0,893) | 0,918 e 0,929 | 3 a 42 |
| 2. Ângulos de vídeo | tamanho mín. 220, min_samples 10, leaf | 18 | 33,9% | 0,972 (0,923) | 0,977 e 0,980 | 72 a 197 |

**Nível 1: 24 macro-arquétipos (`c_arquetipos_metricas.csv`)**. 21 dos 24 são monolíngues; em 6 deles, 50% a 80% dos canais nunca aparecem em outro grupo. Por construção, a mediana do múltiplo fica perto de 1x (0,86x a 1,06x), então o que diferencia os formatos é a **forma da distribuição**:

| Grupo | Macro-arquétipo | n / canais | Top 5% | Top 1% | Flop 20% | P90 | Alcance por inscrito* | Tipo |
|---|---|---|---:|---:|---:|---:|---:|---|
| Mais consistentes | Finanças e Utilidade Prática EN | 779 / 14 | 1,9% | 0,0% | 14,1% | 2,46x | 1,57 | consistente |
| | Histórias Animadas e Listas Curtas (EN) | 463 / 12 | 1,1% | 0,4% | 15,1% | 2,12x | 3,65 | consistente |
| | Desafios e Aventuras em Escala (EN) | 941 / 31 | 3,3% | 0,9% | 14,4% | 2,59x | 2,43 | consistente |
| | Reviews e Testes de Hardware (EN) | 605 / 13 | 2,2% | 0,3% | 12,2% | 2,23x | 2,02 | neutro |
| | Análises e Narrativas de Games (EN) | 754 / 28 | 1,7% | 0,1% | 13,7% | 2,01x | 1,20 | neutro |
| Mais virais (loteria) | Canções e Desenhos Infantis PT | 491 / 10 | **11,4%** | 4,3% | **29,5%** | 5,31x | 1,51 | loteria |
| | Documentários True Crime Longos (EN) | 324 / 9 | 8,0% | 0,6% | 25,0% | 3,95x | 2,64 | loteria |
| | Mistérios e Histórias Sombrias (EN) | 423 / 13 | 7,8% | 2,6% | 14,0% | 2,85x | 3,65 | **vencedor completo** |
| | Beleza, Lifestyle e Opinião (PT) | 412 / 9 | 7,8% | 1,2% | 20,6% | 3,54x | 0,27 | loteria |
| | Nursery Rhymes Infantis em Inglês | 665 / 10 | 7,5% | 2,6% | 22,6% | 3,64x | 0,51 | loteria |
| | Finanças, Alertas e Tutoriais (PT) | 650 / 16 | 6,8% | 1,1% | 24,2% | 3,50x | 0,97 | loteria |
| Mais arriscados | Culinária Rural e Desafios EN | 298 / 3 | 7,1% | 2,7% | 28,5% | 3,58x | 2,45 | loteria (3 canais) |
| | Receitas Práticas e Caseiras (PT) | 592 / 9 | 6,1% | 1,0% | 25,2% | 3,36x | 0,15 | loteria |
| | Reviews e Novidades Tech (PT) | 1.149 / 19 | 4,8% | 1,2% | 23,4% | 2,94x | 0,52 | neutro |

\* mediana de views/inscritos ajustada por idade, relativa à base (1 = típico). Inscritos são do snapshot; EN tem audiência global, então comparar alcance entre idiomas mistura mercado e formato.

**Nível 2: 18 ângulos de vídeo (`c_arquetipos_metricas_video.csv`, exemplos em `c_arquetipos_exemplos_video.csv`)**

| ID | Ângulo | Assinatura principal | n / canais | Mediana | P90 | Top 5% | Flop 20% | Efeito fixo de canal (IC) | Tipo |
|---:|---|---|---|---:|---:|---:|---:|---|---|
| 11 | Duelo e Comparação Visual | capa dividida 99%, seta/círculo 28% | 524 / 137 | 0,98x | 3,34x | 6,3% | 16,6% | +6,9% (q = 0,89) | vencedor completo |
| 3 | Choque, Terror e Listas | expressão surpresa/medo 61%, lista 16% | 1.304 / 153 | 1,01x | 2,82x | 4,4% | 16,6% | +5,2% (−1,3% a +12,7%) | consistente |
| 1 | Conflito e Indignação Ilustrada | ilustração/3D 46%, raiva | 403 / 109 | 1,03x | 2,80x | 5,0% | 16,6% | +6,3% (−3,0% a +15,7%) | consistente |
| 0 | Desabafo e Drama Pessoal | 1ª pessoa, expressão triste | 308 / 99 | 1,00x | 2,20x | 4,2% | 15,9% | +2,0% (−7,6% a +12,8%) | consistente |
| 16 | Reação de Choque e Surpresa | surpresa/medo 96% | 2.032 / 178 | 0,97x | 2,63x | 3,9% | 18,5% | −1,9% | neutro |
| 17 | Sério e Complementar | expressão séria, texto que amplia | 2.008 / 191 | 0,98x | 2,84x | 4,4% | 19,3% | +0,2% | neutro |
| 8 | Afirmação Contraintuitiva e Objeto | foto, objeto, premissa inusitada | 1.116 / 162 | 0,98x | 2,88x | 4,8% | 20,5% | +0,1% | neutro |
| 13 | Foto Limpa Sem Texto | foto 45%, sem texto 36%, sem rosto 35% | 2.446 / 193 | 0,94x | 2,91x | 5,2% | 20,6% | +1,3% | neutro |
| 7 | Cena Real Sem Texto | foto 63%, sem texto 38% | 1.093 / 140 | 0,91x | 3,11x | 5,3% | 19,7% | +1,3% | neutro |
| 4 | Duelo e Comparação Direta | "vs" 99% no título, número 54% | 486 / 114 | 0,98x | 2,94x | 5,1% | 21,0% | −0,4% | neutro |
| 9 | Conversa Direta em Segunda Pessoa | 2ª pessoa 95%, pergunta 30% | 752 / 153 | 0,90x | 2,72x | 4,4% | 20,2% | −3,5% | neutro |
| 5 | Segredo Oculto e Revelação | mistério/segredo 100% | 611 / 147 | 0,94x | 3,61x | 6,4% | 20,5% | +2,8% | loteria |
| 6 | Tutorial e Guia Prático | tutorial/como 100% | 641 / 125 | 0,89x | 3,55x | **7,6%** | **23,7%** | −2,8% | loteria |
| 14 | Capa Densa Com Números | 5+ palavras, números, feliz | 1.616 / 197 | 0,96x | 3,22x | 6,5% | 21,8% | −2,5% | loteria |
| 15 | Alegria Ilustrada Com Emoji | feliz 91%, 3D, emoji | 1.253 / 172 | 0,93x | 2,97x | 4,9% | 23,0% | −2,0% | neutro |
| 12 | Ilustração Explicativa Sem Rosto | ilustração 98%, sem rosto | 475 / 72 | 0,90x | 2,97x | 5,7% | 23,8% | −3,2% | neutro |
| 10 | Desafio e Experimento em 1ª Pessoa | desafio 98%, 1ª pessoa 59% | 487 / 98 | 1,00x | 2,55x | **2,9%** | 20,1% | −3,1% | neutro |
| 2 | Análise Técnica Sem Rosto | sem rosto 30%, número na capa 43% | 327 / 72 | 0,92x | 2,49x | 3,7% | 20,2% | **−5,7%** (−15,2% a +2,7%) | neutro |

Exemplos reais (maior múltiplo pelo `y`, um por canal; lista completa em `c_arquetipos_exemplos_video.csv`):
- Duelo e Comparação Direta: `NHPJic61PRQ` Nath Finanças, "FLÁVIO vs LULA: O Plano Econômico" (199,6x); `hR3HJ9jCJ1o` Tecnoblog, "Galaxy A55 vs M55: o que muda..." (5,0x).
- Choque, Terror e Listas: `9hxbnb1jmpA` Mistérios do Mundo, "Por que você não pode pular na água para fugir de..." (154,2x).
- Segredo Oculto e Revelação: `j_g6eDi8J84` Desafio Aceito, "SEM MAQUIAGEM NA ESCOLA! 😱 Ela Tentou de TUDO..." (45,9x); `pdsS5gbxQPw` Me Poupe!, "Skincare Barato Funciona? Dr Ursinho Revela..." (11,2x).
- Tutorial e Guia Prático: `MDqqL6NQwEs` E se, "Como seria morrer em todos os planetas?" (134,1x); `DOjCrrrGa5s` The Lifestyle Co, "The Ultimate Guide to Finding Jeans for YOUR Body" (41,8x).
- Desafio e Experimento em 1ª Pessoa: `eAwnrGFsDIk` LuCr4zy Futebol, "JOGUEI FUTEBOL EM 10 CAMPOS DIFERENTES EM 24 HORAS" (14,8x); `l9lucWUVirU` Gesiel Taveira, "COMPREI um Xiaomi 17 Pro Max por R$400..." (20,2x).
- Conversa Direta em Segunda Pessoa: `OLLqXe0nIws` Além da Ciência, "INTELIGÊNCIA ARTIFICIAL VAI TE SUBSTITUIR?" (50,7x).
- Análise Técnica Sem Rosto: `GW_fdXHOWp4` Alan Becker, "Animation vs. Minecraft (original)" (33,9x).
- Conflito e Indignação Ilustrada: `Qam7GhAtcjg` Cartoon Network Brasil, "TRANSFORMAÇÕES ESTRANHAS NO COLÉGIO DE ELMORE" (94,7x); `szVhAmdryIs` Gordon Ramsay, "27 Minutes of Gordon Ramsay Eating Disastrous Dish..." (19,1x).

Fichas completas (nome, descrição, molde de título, estrutura de capa, leitura de risco, 3 regras e alerta) em `dados/fichas_arquetipos_video_hydrogen.json` e `dados/fichas_arquetipos_hydrogen.json`. Perfil retórico por LLM de cada arquétipo em `c_perfil_retorico_llm_por_arquetipo*.json`.

### 4. Evidência estatística
Nível 2: 18 efeitos fixos de canal na média, 18 na chance de top 5% e 18 na de flop, com BH: **nenhum q < 0,10** (média: q ≥ 0,889; flop: q ≥ 0,53). Estabilidade muito alta nos dois níveis (ARI ≥ 0,89 em todas as subamostras). Nível 1: efeitos fixos não são interpretáveis (quando o canal inteiro está num grupo, a média relativa é zero por definição); as diferenças de top 5% e flop entre formatos refletem a volatilidade dos canais e são descritivas, com 3 a 42 canais por grupo.

### 5. Visualizações
- `graficos/arq_02_mapa_umap_arquetipos.png`: (A) mapa dos 24 macro-formatos; (B) o mesmo mapa colorido pelo múltiplo, com o top 1% circulado (os hits estão espalhados por todos os formatos); (C) mapa dos 18 ângulos.
- `graficos/arq_03_ranking_arquetipos_risco_retorno.png`: quadrante taxa de top 5% × mediana, cor pelo tipo e % de flop no rótulo, para os dois níveis.

### 6. Descobertas inesperadas
- **Arquétipo de conteúdo é uma propriedade do canal, não do vídeo.** Clusterizar por semântica reproduz os canais (e o idioma). Isso quer dizer que "escolher o arquétipo certo" é uma decisão de posicionamento do canal, e a métrica relativa ao canal não consegue dizer qual formato rende mais em média.
- **Os formatos se diferenciam pelo risco, não pela média.** Infantil PT e true crime EN têm 8% a 11% de top 5% e 25% a 30% de flop; finanças EN, games EN e hardware EN têm 1% a 2% de top 5% e 12% a 14% de flop.
- **Os ângulos "clássicos de YouTube" são neutros dentro do canal.** Desafio/experimento em 1ª pessoa tem a menor taxa de top 5% entre os ângulos (2,9%); tutorial é o mais "loteria" (7,6% de top 5% e 23,7% de flop).

### 7. Limitações e vieses
O resultado depende da representação (pesos 70/30, PCA50 com 47% da variância) e de UMAP/HDBSCAN; a alta estabilidade mede reprodutibilidade, não verdade semântica. No Nível 2, 33,9% dos vídeos eram ruído e foram atribuídos por vizinhança; alguns ângulos se sobrepõem (7 e 13, 4 e 11) e três carregam viés de infantil (12, 14, 15). Os nomes vêm de um LLM e foram checados contra as assinaturas, mas são rótulos, não definições. Os canais pequenos (menos de 200 mil) não existem na base.

### 8. Recomendação prática
1. Escolher o macro-formato pelo **perfil de risco** que o canal aguenta: quem precisa de previsibilidade (marca, receita recorrente) vai para formatos consistentes (finanças utilitárias, reviews de hardware, análise de games); quem busca saltos de alcance aceita formatos loteria (infantil, true crime, mistério) e precisa de volume para tirar o bilhete premiado.
2. Dentro do canal, usar os ângulos como **cardápio de variação**, não como fórmula: nenhum ângulo vence na média. Os de melhor perfil de risco (menos flops) são Choque/Terror/Listas, Conflito Ilustrado, Desabafo e Duelo Visual.
3. Tratar tutorial e segredo/revelação como apostas: mais topo, mais flop.
4. Usar `dados/arquetipos_por_video.parquet` no motor de consulta (colunas `arquetipo_id/arquetipo_nome` = ângulo; `macro_id/macro_nome` = formato; coordenadas UMAP dos dois níveis; estrutura do título; similaridade título × capa).

| Nota | Valor (0 a 10) |
|---|---:|
| Impacto potencial | 6 |
| Confiança estatística | 6 (estrutura estável; efeitos no desempenho médio nulos) |
| Aplicabilidade prática | 6 |
| Facilidade de implementação | 6 |

---

## Investigação G semântica · Oportunidades de mercado e combinações pouco exploradas

### 1. Pergunta
Onde há desempenho relativo alto com pouca saturação (arquétipo × nicho × idioma × porte)? Que formatos funcionam em EN e são raros em PT? Que arquétipos ajudam canais médios a superar a própria base com consistência? O que é oportunidade real e o que é ruído?

### 2. Metodologia
`08_oportunidades.py`. Unidade de inferência = **canal**: média de `y_li_w` por canal dentro da célula (cada canal pesa igual), IC por bootstrap de canais (400), p bootstrap e BH entre células. Saturação = % dos canais do nicho que já usam o ângulo e % dos vídeos do nicho. Regras de honestidade: "real" exige 5+ canais, 40+ vídeos, IC 95% acima de zero **e** q < 0,10; "provável" = IC acima de zero sem passar no BH; "promissora" = tendência positiva com amostra pequena. EN → PT em três camadas: ângulos (Nível 2), traços estruturais de título e capa (efeito fixo de canal por idioma) e macro-formatos. Canais médios: efeito fixo dentro dos 83 canais médios, na média e na taxa de flop.

### 3. Resultado
- **Ângulo × nicho (`g1_arquetipo_x_nicho.csv`, 176 células com 15+ vídeos):** **nenhuma célula sobrevive ao BH** (menor q = 0,11). Com IC acima de zero, só duas, ambas no infantil e já saturadas: Conversa Direta em Segunda Pessoa (62 vídeos, 21 canais, 1,26x, q = 0,54, 88% dos canais do nicho já usam) e Capa Densa Com Números (294 vídeos, 24 canais, 1,26x, q = 0,28, 100% dos canais usam). Promissoras com amostra pequena (ruído provável): Duelo e Comparação Visual em histórias (25 vídeos, 10 canais, 1,47x) e Desafio em 1ª pessoa em esportes (38 vídeos, 5 canais, 1,20x).
- **Arbitragem EN → PT por ângulo (`g2_arbitragem_en_pt.csv`):** **0 de 18.** Nenhum ângulo tem IC acima de zero em EN; as prevalências em PT e EN são parecidas (razão de 0,3 a 1,6).
- **Arbitragem estrutural (`g7_arbitragem_estrutural_en_pt.csv`):** afirmação contraintuitiva rende +13,0% em EN (IC +3,0% a +22,3%, q = 0,12), aparece em 4,7% dos títulos EN e 3,3% dos PT, mas em PT o efeito medido é −1,9% (IC −14,3% a +11,7%). Superlativo (+8,7% em EN, IC +1,0% a +17,4%) e urgência/novidade (+10,2%, IC +0,1% a +21,9%) funcionam em EN e já são tão comuns em PT quanto em EN. Expressão séria/raiva na capa: +5,2% em EN (IC +0,3% a +9,9%), +3,6% em PT (IC cruza zero).
- **Macro-formatos EN × PT (`g6_macro_formatos_en_pt.csv`):** 15 dos 24 formatos só aparecem em EN, mas isso é em grande parte separação por idioma dos embeddings e da seleção de canais, não ausência real do formato em PT. Como pistas de mercado: "Mistérios e Histórias Sombrias" (13 canais EN, top 5% 7,8%, flop 14%, alcance por inscrito 3,65) e "Finanças e Utilidade Prática EN" (flop 14% contra 24% do equivalente PT "Finanças, Alertas e Tutoriais") mostram perfis de risco melhores que os equivalentes PT, mas a comparação mistura mercado, idioma e canal.
- **Canais médios (`g5_canais_medios_efeito_fixo.csv`):** Choque, Terror e Listas: +16,3% na média (IC +3,7% a +33,9%, q = 0,37) e **−5,7 p.p. de flop** (IC −9,8 a −2,1; q = 0,088), 463 vídeos de 62 canais médios. Cena Real Sem Texto: −5,4 p.p. de flop (q = 0,13). Na direção contrária: Análise Técnica Sem Rosto, +8,4 p.p. de flop (q = 0,13); Desafio e Experimento em 1ª Pessoa, −24% na média (IC −52% a +1%).

### 4. Evidência estatística
176 células ângulo × nicho com BH: 0 com q < 0,10. 18 testes de arbitragem por ângulo: 0 positivos. 33 traços × 2 idiomas: nenhum com q < 0,10 em EN além de 1ª pessoa (negativo, q = 0,03); contraintuitivo q = 0,12. Canais médios: 18 testes × 2 desfechos, 1 com q < 0,10 (flop em Choque/Terror/Listas).

### 5. Visualizações
`graficos/arq_04_matriz_oportunidades_nicho_idioma.png`: (A) matriz ângulo × nicho com múltiplo médio por canal, nº de canais e marcações de IC; (B) prevalência EN e PT de cada ângulo com o múltiplo em EN e IC.

### 6. Descobertas inesperadas
- **Não existe "oceano azul" de embalagem.** Os ângulos que performam um pouco melhor em algum nicho já são usados pela maioria dos canais desse nicho.
- **O que é raro e funciona é texto, não formato:** afirmação contraintuitiva em EN; mas a transferência para PT não se confirma nos dados atuais.
- **Para canais médios, o ganho mais defensável é reduzir flops**, não multiplicar a média.

### 7. Limitações e vieses
Sem volume de busca nem concorrência real (oferta e demanda são medidas só pelo que os 203 canais publicam). Células com 5 a 25 canais têm IC largos. Macro-formatos são separados por idioma, o que impede uma leitura limpa de "formato ausente em PT". Canais médios começam em 200 mil inscritos; nada aqui vale para canais pequenos.

### 8. Recomendação prática
1. Não montar estratégia em "célula vencedora" de arquétipo × nicho: nenhuma resiste à correção de múltiplos testes.
2. Para canais médios, incluir de forma recorrente o ângulo de choque/terror/lista (quando couber no nicho) para cortar flops, e evitar análise técnica sem rosto e desafios em 1ª pessoa como aposta principal.
3. Trazer a afirmação contraintuitiva de EN para PT só como **teste A/B controlado** (ela não mostrou efeito em PT).
4. Para quem pode escolher posicionamento em PT, os formatos EN de mistério narrativo e finanças utilitárias têm perfis de risco melhores que os equivalentes PT; vale estudar como formato de canal, não como truque de embalagem.

| Nota | Valor (0 a 10) |
|---|---:|
| Impacto potencial | 5 |
| Confiança estatística | 3 |
| Aplicabilidade prática | 5 |
| Facilidade de implementação | 5 |

---

## Hipóteses descartadas pelos dados

| ID | Hipótese | Teste | Resultado | Status |
|---|---|---|---|---|
| 2C-1 | O texto do título prevê bem o desempenho relativo | GroupKFold por canal, 6 conjuntos | R² ≤ 0,018; AUC dentro do canal 0,51 a 0,55 | descartada |
| 2C-2 | Capa que repete o título é punida | efeito fixo, 3 especificações | +1,1% (IC −9,5% a +13,4%); EN +10% | descartada |
| 2C-3 | Capa deve ser semanticamente "diferente" do título | cosseno título × OCR | quanto mais próximo, melhor: +4,1% por DP (q = 0,034) | descartada (é o contrário) |
| 2C-4 | Existe comprimento ideal de título | faixas de caracteres por idioma | todas q > 0,93 | descartada |
| 2C-5 | Pergunta, número/dinheiro, lista, tutorial, desafio, mistério ou urgência elevam a média | gancho principal vs descritivo | todos com IC cruzando zero na base toda | descartada |
| 2C-6 | Lacuna de curiosidade alta distingue o topo | LLM, top 5% vs flop | diferença nula | descartada |
| 2C-7 | Combinações título × capa "mágicas" (ex.: curiosidade + rosto chocado) | 649 interações + BH | 0 positivas com q < 0,10; 2 negativas pequenas | descartada |
| 2C-8 | Algum arquétipo de vídeo vence o padrão do próprio canal | efeito fixo, 18 ângulos | q ≥ 0,89 em todos | descartada |
| 2C-9 | Formatos de canal têm médias relativas diferentes | Nível 1 | não mensurável com alvo relativo ao canal; diferem só em risco | reformulada (risco, não média) |
| 2C-10 | Há nichos com arquétipo de alta performance e baixa saturação | 176 células + BH | 0 sobrevivem; as melhores já são saturadas | descartada |
| 2C-11 | Há arbitragem de formato EN → PT | 18 ângulos + 33 traços | 0 ângulos; contraintuitivo funciona em EN mas não em PT | descartada (fica como teste) |
| 2C-12 | Desafio/experimento em 1ª pessoa é o ângulo mais viral | Nível 2 | menor taxa de top 5% (2,9%) e −24% em canais médios (IC cruza zero) | descartada |
| 2C-13 | Vocabulário abstrato é neutro | efeito fixo | −15,4% (q = 0,005) | descartada (é negativo) |
| 2C-14 | 1ª pessoa no título ajuda em qualquer idioma | efeito fixo por idioma | EN −11% (q = 0,03); PT nulo | descartada |

## Síntese crítica (gemini-4-carbon, revisada)
A síntese completa está em `resultados/sintese_carbon.md`. Pontos que adotamos: o título é filtro fino, não alavanca; alinhamento semântico título × capa tem sinal pequeno e consistente; o Nível 1 captura identidade editorial e idioma; o Nível 2 tem famílias sobrepostas (prova visual limpa 7 e 13; conflito e comparação 4 e 11; emoção facial 0, 1, 3 e 16; densidade gráfica com viés infantil 12, 14 e 15) e deve ser lido como cardápio de variação. Ponto que corrigimos: o rótulo "vencedor completo" de Duelo e Comparação Visual é descritivo (efeito fixo +6,9% com q = 0,89). Fichas estratégicas por nicho em `dados/fichas_nichos_hydrogen.json`.

## Gasto exato da API Gemini nesta frente
Registro linha a linha em `dados/uso_gemini_arquetipos.csv` (inclui embeddings e testes de conectividade). Tarifa cheia, USD 1 = R$ 5,93.

| Modelo | Uso | Chamadas | Tokens de entrada | Tokens de saída | Tokens de raciocínio | US$ | R$ |
|---|---|---:|---:|---:|---:|---:|---:|
| gemini-embedding-2-preview | 4 conjuntos de embeddings 768d (título, multimodal, título + descrição, OCR), 66.660 textos | 674 | 3.311.201 | 0 | 0 | 0,662 | 3,93 |
| gemini-3.5-flash-lite | classificação de 2.821 títulos e relação título × capa | 145 | 388.994 | 244.175 | 0 | 0,727 | 4,31 |
| gemini-4-hydrogen | fichas de 42 arquétipos e 11 nichos | 34 | 161.661 | 27.627 | 71.503 | 0,986 | 5,85 |
| gemini-4-carbon | síntese crítica | 1 | 31.792 | 4.108 | 0 | 0,105 | 0,62 |
| **Total** | | **854** | | | | **2,480** | **14,71** |

Nota de transparência: cerca de R$ 3,6 do hydrogen foram gastos em 22 fichas individuais cujo raciocínio interno consumiu todo o limite de saída (resposta vazia). Corrigido com fichas em lote e raciocínio baixo, que custaram R$ 0,65 para as mesmas fichas. O total segue abaixo do teto de R$ 20,00.
