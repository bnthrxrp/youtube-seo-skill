# Estudo próprio: o que acompanha vídeos que vão acima do normal do canal

Estudo observacional com **17.882 vídeos longos de 203 canais** (11 nichos, português e inglês, 3 portes), coletados em 23/11/2026 pela YouTube Data API v3. Miniaturas lidas também por IA (Gemini 3.5 Flash-Lite, 17.876 imagens). Custo total: R$ 21,74 (ver CUSTOS.md).

**Leia isto primeiro:** o estudo mostra o que *acompanha* vídeos que foram melhor que o normal do próprio canal. Não prova que o traço *causa* o resultado. Para provar causa, só teste A/B (o "Testar e comparar" do YouTube Studio).

## Como foi feito, em linguagem simples

1. **Cada vídeo foi comparado com o próprio canal, não com outros canais.** O MrBeast tem milhões de views por ser o MrBeast, não por causa do título. Então a pergunta foi: este vídeo foi melhor ou pior que os 10 vídeos do mesmo canal publicados mais perto dele no tempo?
2. **A conta:** views do vídeo dividido pela mediana de views desses 10 vizinhos (em escala log). Um vídeo com o dobro do normal do canal recebe nota +100%; com metade, −50%. A idade do vídeo também entrou como controle.
3. **Quem ficou de fora:** Shorts (só pegamos a lista de vídeos longos do canal, mais duração acima de 3 min e sem #shorts), lives, vídeos com menos de 30 dias, canais com menos de 15 vídeos válidos e 33 canais cujo idioma real não batia com o estrato (ex.: canal "PT" que na verdade publica em espanhol).
4. **Modelo:** regressão com efeitos mistos (cada canal tem seu próprio nível; nicho, idioma, porte, categoria, idade e faixa de hora como controles) e, como versão conservadora, a mesma conta só com variação dentro de cada canal e margem de erro agrupada por canal. **Os números abaixo usam a versão conservadora.** Como testamos 35 traços de uma vez, aplicamos a correção de Benjamini-Hochberg para não cair em achado por acaso.
5. **Checagens:** se o efeito aponta para o mesmo lado em cada nicho e em cada idioma, e quanto o modelo acerta em canais que ele não viu (validação por grupos de canais).

## Amostra final

| Idioma | Porte | Canais | Vídeos |
|---|---|---|---|
| Inglês | gigante | 27 | 2.425 |
| Inglês | grande | 43 | 4.040 |
| Inglês | médio | 41 | 3.628 |
| Português | gigante | 11 | 1.072 |
| Português | grande | 39 | 3.204 |
| Português | médio | 42 | 3.513 |
| **Total** | | **203** | **17.882** |

Por nicho (canais / vídeos): culinária 20/1.786, documentário 13/1.016, educação 24/2.173, entretenimento 19/1.765, esportes 14/1.028, finanças 15/1.348, games 20/1.982, histórias 20/1.609, infantil 24/1.828, lifestyle 16/1.567, tech 18/1.780. Detalhe por estrato em `resultados/amostra_por_estrato.csv`.

Gigantes em português são poucos (11) porque existem poucos canais desse tamanho; alguns (ex.: Enaldinho, rezendeevil) tinham poucos vídeos longos recentes e saíram pelo corte de 15 vídeos.

## O achado mais importante: o SEO explica pouco

- Dentro de um mesmo canal, os vídeos variam muito: **18% fizeram mais que o dobro do normal do canal e 15% fizeram menos da metade.**
- Todos os 35 traços de título, descrição, tags, duração, horário e miniatura juntos explicam **cerca de 1,5%** dessa variação em canais que o modelo não viu (R² fora da amostra 0,015).
- Em português claro: **o que está escrito no título, na descrição e nas tags quase não diferencia um vídeo que estoura de um que flopa no mesmo canal.** O que pesa é o tema, a ideia e quanto as pessoas assistem, coisas que metadados não medem.

## Achados principais (versão conservadora, intervalo de 95%)

**Fortes (passam na correção, repetem em 10 de 11 nichos e nos dois idiomas):**

1. **Legenda enviada pelo próprio canal:** vídeos com legenda própria tiveram em média **28% mais views** que o normal do canal (margem: de +15% a +42%). Em português o efeito foi maior (+45%) que em inglês (+24%). Cuidado: pode ser o contrário (o canal capricha na legenda dos vídeos que já está dando mais atenção, ou adiciona depois que o vídeo vai bem). Só 22% dos vídeos tinham.
2. **Duração:** cada vez que a duração dobra dentro do mesmo canal, o vídeo teve em média **14% mais views** (de +8% a +21%). Na prática, vídeos de 15 a 60 minutos ficaram cerca de 8% acima do normal do canal; vídeos com menos de 5 minutos, cerca de 21% abaixo; acima de 60 minutos o ganho some (gráfico 04).

**Prováveis, mas incertos (passam no modelo misto e repetem na maioria dos nichos, mas não passam na versão conservadora):**

3. **Mais links na descrição:** dobrar o número de links acompanhou **+7%** de views (de +2% a +13%; mesmo sentido em 10 de 11 nichos). Provável explicação: vídeos com patrocínio/produtos têm mais links e são produções maiores.
4. **Uma palavra em CAIXA ALTA no título:** **+7%** (de +1% a +13%; 9 de 11 nichos). Título *inteiro* em caixa alta: zero efeito (de −10% a +11%).
5. **Emoji no título:** **+11%** (de +2% a +21%), mais forte em português (+17%) que em inglês (+4%). Só 11% dos títulos têm.
6. **Título em 1ª pessoa ("eu", "meu", "I", "my"):** **−7%** (de −13% a −1%), mas só em inglês (−10%); em português, zero.
7. **Publicar no fim de semana:** **+6%** (de 0% a +11%), mais em inglês. Hora do dia: nada (gráfico 06).

**Sem efeito detectável (o intervalo inclui zero e é estreito o bastante para dizer "pouco ou nada"):**

8. **Tamanho do título** (+1% a cada 10 caracteres, margem de −1% a +3%), **tamanho da descrição** (dobrar: +0,3%, de −3% a +4%), **número no título**, **pergunta no título**, **"você" no título**, **separadores**, **parênteses**. **Tags:** não ter nenhuma tag não piorou (+14%, de −6% a +38%, ou seja, sem sinal de prejuízo), e dobrar as tags deu +3% incerto. **Capítulos:** +6% incerto (de −6% a +20%), +16% em português e −1% em inglês.

## Padrões de miniatura

Medidos de duas formas: (1) local e grátis: OpenCV para cor, contraste e rosto, OCR RapidOCR para o texto; (2) leitura por IA (Gemini 3.5 Flash-Lite, 17.876 das 17.882 miniaturas): rostos, expressão, olhar para a câmera, seta/círculo, objeto em destaque, estilo, fundo, antes/depois, número/dinheiro, palavras e relação do texto com o título. A IA conta personagens desenhados e rostos pequenos, por isso acha bem mais rostos (86%) que o detector simples (52%).

### Como são as miniaturas (leitura por IA)

- 86% têm rosto (humano ou personagem), 65% rosto grande, 46% rosto olhando para a câmera. Expressão: feliz 27%, surpresa/choque 21%, séria 18%, medo 4%, raiva 2%, triste 2%.
- 78% têm texto escrito, 30% com 5+ palavras. O texto quase nunca repete o título (5%); 41% complementam (dizem algo que o título não diz).
- 55% têm objeto/produto em destaque, 25% número ou dinheiro, 17% seta ou círculo, 8% antes/depois.
- Estilo: 57% montagem/foto editada, 14% ilustração, 8% animação 3D. Fundo: 44% liso/desfocado, 25% ilustrado, 20% colagem.
- Por nicho (gráfico 10): finanças tem 97% de rosto, 88% rosto grande, 71% olhando para a câmera, 53% com 5+ palavras e 93% montagem. Culinária e tech: 93% com objeto em destaque. Infantil: 60% feliz, 40% animação 3D. Histórias: 61% ilustração e 17% medo/tensão. Educação e finanças usam mais seta/círculo (27-30%).

### O que muda o resultado dentro do canal

**Nenhum traço de miniatura passou na correção para muitos testes**, nem na leitura por IA (27 traços), nem na medição local. Comparando os 20% melhores com os 20% piores vídeos de cada canal, nenhum traço difere mais que 2,3 pontos percentuais (gráficos 07 e 09).

Sinais fracos (margem encosta no zero; tratar como ideia para testar, não regra):
- **Expressões "negativas" e sérias:** medo/tensão **+9%** (de 0% a +18%), raiva +9% (−1% a +19%), triste +8% (−2% a +20%), séria/concentrada +6% (0% a +12%; mesmo sentido em 9 de 11 nichos). Feliz −2% e surpresa/choque 0%: a famosa "cara de choque" não se destacou.
- **Fundo ilustrado −8%** (de −15% a +1%; 9 de 11 nichos) e **montagem/foto editada −6%** (de −12% a +1%). Fundo em colagem −7% (−15% a +2%).
- **5+ palavras na miniatura −4%** (de −9% a +1%), puxado pelo português (−9%); em inglês, zero.
- **Objeto em destaque +4%** (−1% a +8%); **texto que complementa o título +3%** (−1% a +7%).
- Sem efeito: ter rosto (−3%, de −11% a +6%), rosto grande (−1%), olhar para a câmera (+2%, de −2% a +5%), seta/círculo (+1%, de −5% a +7%), antes/depois (−1%), número/dinheiro (−3%, de −7% a +2%), ter texto (+1%).

Medição local (mantida para comparação): rosto grande pelo detector simples +6% (0% a +11%), texto que repete palavras do título pelo OCR +5% (0% a +10%), mais contraste −3% por desvio (−5% a −1%); nenhum passa na correção cautelosa. A diferença entre "rosto grande" no detector simples (+6%) e na IA (−1%) mostra que o resultado depende de como se mede: mais um motivo para tratar tudo como fraco.

**Leitura honesta:** o estilo da miniatura é decisão do canal e varia pouco entre os vídeos dele. Traços genéricos ("ter rosto", "ter seta", "cara de choque") não separam vídeo que estoura de vídeo que flopa no mesmo canal. O que o YouTube mede é se *esta* imagem faz *este* público clicar e ficar satisfeito, e isso só teste A/B mede.

## Limitações

- **Correlação, não causa.** Canais podem caprichar em legenda, links e duração justamente nos vídeos que já sabem que vão bem.
- **Só views públicas.** Não temos CTR, retenção nem impressões (isso só o Studio de cada canal mostra).
- **Sobrevivência:** pegamos os 100 vídeos longos mais recentes de cada canal com mais de 30 dias; vídeos apagados ou privados não entram.
- **Detector de rosto simples** (erra rostos de perfil e desenhos). OCR erra textos estilizados.
- **Leitura por IA** em baixa resolução (miniatura 320x180): pode errar expressão e contar personagens como rostos; 6 imagens sem resposta válida. Não houve conferência manual de uma amostra.
- **Shorts:** não analisados (a coleta pegou só a lista de vídeos longos; 26 vídeos com #shorts foram removidos).
- **Idioma do áudio:** todos os vídeos da amostra final declaravam idioma, então não deu para comparar com quem não declara; dublagem (áudio em 2+ idiomas) só existia num subconjunto pequeno coletado por yt-dlp e ficou fora do modelo.
- O modelo misto achou variação entre canais praticamente zero porque a nota já é relativa ao próprio canal; por isso usamos como principal a versão com margem de erro agrupada por canal, mais conservadora.

## Arquivos

- `dados/dataset.parquet` (17.882 linhas, uma por vídeo, com todas as variáveis) e `dados/canais_selecionados.csv`.
- `resultados/tabela_final.csv`: todos os 35 traços, com efeito no modelo misto e na versão conservadora, intervalos, q de Benjamini-Hochberg, sinal por nicho e efeito em PT e EN.
- `graficos/01` a `11` (PNG); 09 a 11 são da leitura por IA.
- `resultados/gemini_*.csv` e `dados/thumbs_gemini.jsonl` (leitura por IA de cada miniatura).
- `scripts/` na ordem: 01 candidatos, 02 seleção, 03_api coleta, 04_features, 04b miniaturas, 04c OCR, 04d leitura por IA pela Batch API (04c_thumbs_gemini.py é a versão de chamadas avulsas usada nos pilotos), 05 modelo, 06 descritivo, 07 miniaturas lidas por IA.
