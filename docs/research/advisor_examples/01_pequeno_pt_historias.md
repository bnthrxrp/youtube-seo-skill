# Parecer da ideia: O MISTÉRIO do navio que sumiu no Triângulo das Bermudas

Nicho **historias**, idioma **PT**, porte **pequeno** (5k a 49.999 inscritos). Base: 26.194 vídeos longos de 310 canais.

## 1. Diagnóstico geral

**Grau de confiança do parecer: baixo a moderado.** Cobertura da célula historias × PT × pequenos: 5 canais e 453 vídeos (limitada).

> Teto da base: o título explica no máximo R² 0,018 fora da amostra, embeddings da capa R² 0,025 dentro do canal, e o melhor modelo acerta o top 5% do próprio canal com AUC 0,583 (0,5 é moeda). Este parecer ordena escolhas, não prevê views e nunca promete viralização.
> A base não tem CTR, impressões, retenção, tempo de exibição, origem de tráfego, inscritos por vídeo nem transcrições. Associação, não causa. Título, capa, legenda e capítulos foram lidos no dia da coleta (podem ter sido editados depois do resultado). Canais pequenos vêm da busca de vídeos recentes: representam pequenos ativos e visíveis, não o pequeno típico.

Contexto do porte pequeno: views medianas por vídeo 6.700; top 10% dos vídeos somam 45,6% das views; 31,1 vídeos de 10x ou mais por mil; intervalo mediano de 2,0 dias.

**A favor**

- Texto da capa reforça a ideia do título (alinhamento semântico se associa a +4,1% por DP, q = 0,034).
- Intervalo de 3 dias desde o vídeo anterior (fora da zona de risco de menos de 3 dias).

**Riscos**

- Duração de 32 min abaixo da faixa forte do nicho (36 a 84 min).

## 2. Duração

Faixa forte do nicho (curva dentro do canal, 200k+): **36 a 84 min**.
Ótimo do nicho: 52 min (IC 34 a 95); retorno decrescente a partir de cerca de 4 min; q = 0,001.
Proposta de 32 min: curva do nicho +56,7% contra 12 min do mesmo canal; curva do grupo de porte (pequenos) +53,4% contra cerca de 12 min.
Na base real (historias, pequeno), a faixa 30-45 min tem 67 vídeos de 3 canais, múltiplo mediano 0,93x a mediana do canal e 11,9% com 3x ou mais.
Duração mediana na célula: 53,3 min; no top 10% de cada canal: 53,9 min.
Faixa com mais vídeos de 3x na célula (3+ canais, 20+ vídeos): 60+ min (13,1%; descritivo, sem controle de idade).
- Nos pequenos, dobrar a duração soma +30,2% dentro do canal (IC +19,7% a +41,6%) contra +14,9% nos 200k+, e duração é o único traço ligado a breakouts de 10x (+1,7 p.p. por dobro).
- Acima de 60 min a curva dos pequenos é puxada por formatos específicos (filmes completos, júris integrais, icebergs). Até 30 min o efeito é sólido.
- Duração relativa ao hábito do próprio canal pesa tanto quanto a absoluta. Não estique: o ganho supõe retenção real, que a base não mede.

## 3. Título

55 caracteres, 10 palavras. O título é filtro fino, não alavanca: o melhor modelo de título tem R² fora da amostra de 0,018.

| Traço | Presente | Efeito no múltiplo do canal | IC 95% | q | Confiança |
|---|---|---:|---|---:|---|
| afirmação contraintuitiva como gancho | não | +4,9% | −10,1% a +23,2% | 0,889 | baixa (efeito não confirmado em PT) |
| número no título (pequenos) | não | +15,4% | +4,5% a +27,3% | 0,023 | baixa (diferença contra 200k+ não confirmada; pode ser causalidade reversa) |
| palavra em CAIXA ALTA (pequenos) | sim | +15,3% | +5,6% a +25,9% | 0,020 | baixa (diferença contra 200k+ não confirmada; pode ser causalidade reversa) |
| colab/versus no título (pequenos) | não | −21,6% | −33,2% a −7,8% | 0,020 | baixa (diferença contra 200k+ não confirmada; pode ser causalidade reversa) |
| +10 caracteres (pequenos) | n/a | +2,5% | +0,5% a +4,6% | 0,060 | baixa |
| emoji (PT) | não | +23,5% | +6,7% a +41,7% | 0,090 | baixa (concentrado em 45 canais) |

**O que não importa**

- 1ª pessoa em PT: −2,7% (q = 0,950), nulo.
- Pergunta no título: −2,9% nos 200k+ e −4,9% nos pequenos, nulo (mas aumenta comentários por view).
- Lista, tutorial, mistério, urgência e lacuna de curiosidade: IC cruzando zero na base toda.

## 4. Thumbnail e alinhamento título + capa

Padrões lidos nas notas da capa (efeito dentro do canal, 200k+):
- Sem rosto: +4,6% (q = 0,727, confiança baixa; comparação ingênua entre canais −40,7%)
- Escura (bottom 20% brilho): −3,3% (q = 0,638, confiança baixa; comparação ingênua entre canais −4,7%)

Melhores sinais no nicho historias (q alto, usar como teste):
- KM12-09 Apresentador masculino e elementos financeiros: +30,0% (q = 0,084, 49 vídeos)
- Foco disperso (bottom 20%): +18,4% (q = 0,122, 343 vídeos)
- Comparação/antes-depois: +21,2% (q = 0,240, 66 vídeos)
- HDB-50 Cenários espaciais com texto destacado: +32,2% (q = 0,334, 53 vídeos)
- Texto repete o título: +30,6% (q = 0,346, 144 vídeos)
Sinais negativos no nicho: KM12-02 Rostos expressivos com textos destacados −39,5%; Peso visual à direita −16,6%; Foco concentrado (top 20%) −11,2%.
Padrões de confiança média na base toda: HDB-87 Expressões Intensas e Elementos Bizarros +33,5%; KM12-07 Exibição de gadget em primeiro plano +28,8%; HDB-39 Prato em destaque com apresentador +25,5%; Cor dominante verde +14,6%; Peso visual à esquerda +6,4%.
Hipóteses raras para teste A/B: Cor dominante verde + Escura (bottom 20% brilho) +52,1% (24 canais); Cor dominante ciano + Fundo colagem +40,4% (30 canais); Texto repete o título + Cor dominante branco +37,8% (55 canais); Cor dominante azul + Comparação/antes-depois +35,5% (50 canais); Texto repete o título + Figura mais escura que o fundo +34,6% (34 canais).
Alinhamento título ↔ texto da capa ("SUMIU"): similaridade lexical 0,45, nível alto.
Mitos a ignorar: Rosto grande (entre canais +30,0%, dentro do canal −2,5%); Expressão surpresa (entre canais +17,4%, dentro do canal −2,7%); Seta ou círculo (entre canais +11,8%, dentro do canal +0,4%); Sem rosto (entre canais −40,7%, dentro do canal +4,6%); Saturação alta (top 20%) (entre canais −12,0%, dentro do canal −4,3%); Contraste global alto (top 20%) (entre canais −0,1%, dentro do canal −4,5%).
- Por nicho, nenhum padrão de capa sobrevive com folga à correção de múltiplos testes; use como ponto de partida de teste A/B.
- Repetir o título na capa não é punido (+1,1%, IC −9,5% a +13,4%). O que tende a perder é texto sem relação com o título.
- Breakouts de canais pequenos têm menos rosto do que os controles do mesmo canal (72,9% contra 81,5%, q < 0,001): venda o assunto, não o criador.
- Imitar a cara de capa de canal grande não rende (−2,6% por DP, q = 0,30). Fugir do visual habitual do próprio canal custa −10,9% por DP (q < 0,001).

## 5. Cadência e consistência

3 dias desde o vídeo anterior; curva dos 200k+ contra 7 dias: −9,3%.
Faixas de intervalo do grupo (referência 5 a 9 dias): <2d −4,4% (q = 0,592); 2-4d −3,5% (q = 0,592); 10-20d +15,9% (q = 0,061); 21-45d +2,9% (q = 0,687); >45d +31,7% (q = 0,017).
Fugir do tema habitual do canal reduz views: −14,8% por DP nos pequenos e −10,5% nos 200k+ (p < 0,001); novidade não aumenta a chance de 10x.
Similaridade com os títulos recentes: 0,17 (entre os recentes: 0,00).
- Dobrar o número de vídeos nos 7 dias anteriores se associa a −9,6% (q = 0,003) nos 200k+.
- Dia e horário de publicação não importam no agregado (nada sobrevive à correção em nenhum porte).

## 6. Exemplos reais parecidos de alto desempenho

| Título | Canal | Porte | Idioma | Múltiplo vs mediana do canal | Views | Duração | Similaridade |
|---|---|---|---|---:|---:|---:|---:|
| Sombras de um Desejo / Filme Completo Dublado / Suspense/Mistério (HD) | Cine Emoção | pequeno | PT | 8,8x | 378.495 | 85,5 min | 0,07 |
| 35 MISTÉRIOS que a CIÊNCIA NÃO CONSEGUE EXPLICAR | Você Sabia? | gigante | PT | 9,5x | 6.056.620 | 67,0 min | 0,08 |
| RELATOS DOS INSCRITOS / Histórias assustadoras | Cibele na Terra do Medo | pequeno | PT | 2,1x | 19.765 | 27,7 min | 0,00 |
| IMPOSSÍVEL NÃO SE EMOCIONAR! 😭 Edward Norton e Naomi Watts em um romance inesquecível (Dublado) | Cine Emoção | pequeno | PT | 2,2x | 92.952 | 124,9 min | 0,00 |
| DEPOIS DISSO, DESISTI DE SER BABÁ / REDDIT DO MEDO | Cibele na Terra do Medo | pequeno | PT | 2,3x | 26.898 | 34,4 min | 0,00 |

Exemplos são referências de tema e embalagem, não garantia: o múltiplo depende muito da volatilidade de cada canal.

## 7. Checklist pré-publicação

- [ ] Roteiro que sustente 36 a 84 min sem enchimento (faixa forte do nicho historias).
- [ ] Colocar a palavra-chave principal no início do título (+1,3 p.p. de chance de top 5% do canal, q = 0,023).
- [ ] Texto da capa curto e reforçando a mesma ideia do título; nada de assunto paralelo.
- [ ] Capa centrada no assunto (objeto, cena, situação), mantendo o padrão visual do canal.
- [ ] Teste A/B (Testar e comparar do YouTube) entre título com número/CAIXA ALTA e versão neutra: sinal de +15% com confiança baixa.
- [ ] Subir legenda própria (associação de +28,6% nos 200k+, com risco de causalidade reversa) e capítulos como experiência do usuário, não como alavanca.
- [ ] Depois de publicar, comparar CTR e retenção no YouTube Studio com a mediana do canal: é o dado que esta base não tem.
