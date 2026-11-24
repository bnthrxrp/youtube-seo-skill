# Parecer da ideia: Quanto rende R$ 10 mil no Tesouro Selic em 2026

Nicho **financas**, idioma **PT**, porte **grande** (2M a 10M). Base: 26.194 vídeos longos de 310 canais.

## 1. Diagnóstico geral

**Grau de confiança do parecer: baixo a moderado.** Cobertura da célula financas × PT × 200k+: 8 canais e 652 vídeos (boa).

> Teto da base: o título explica no máximo R² 0,018 fora da amostra, embeddings da capa R² 0,025 dentro do canal, e o melhor modelo acerta o top 5% do próprio canal com AUC 0,583 (0,5 é moeda). Este parecer ordena escolhas, não prevê views e nunca promete viralização.
> A base não tem CTR, impressões, retenção, tempo de exibição, origem de tráfego, inscritos por vídeo nem transcrições. Associação, não causa. Título, capa, legenda e capítulos foram lidos no dia da coleta (podem ter sido editados depois do resultado). Canais pequenos vêm da busca de vídeos recentes: representam pequenos ativos e visíveis, não o pequeno típico.

Contexto do porte grande: views medianas por vídeo 545.184; top 10% dos vídeos somam 31,0% das views; 12,0 vídeos de 10x ou mais por mil; intervalo mediano de 4,9 dias.

**A favor**

- Duração de 24 min dentro da faixa forte do nicho (23 a 45 min).
- Capa com 'Cor dominante verde': +14,6% dentro do canal (q = 0,136, confiança média).
- Capa com 'Peso visual à esquerda': +6,4% dentro do canal (q = 0,056, confiança média).
- Texto da capa reforça a ideia do título (alinhamento semântico se associa a +4,1% por DP, q = 0,034).

**Riscos**

- Menos de 2 dias desde o vídeo anterior em canal 200k+: −8,8% (q = 0,003). Espere pelo menos 3 dias.

## 2. Duração

Faixa forte do nicho (curva dentro do canal, 200k+): **23 a 45 min**.
Ótimo do nicho: 31 min (IC 23 a 50); retorno decrescente a partir de cerca de 18 min; q < 0,001.
Ótimo do porte grande: 31 min (IC 26 a 42).
Proposta de 24 min: curva do nicho +64,5% contra 12 min do mesmo canal; curva do grupo de porte (200k+) n/d contra cerca de 12 min.
Na base real (financas, grande), a faixa 20-30 min tem 210 vídeos de 7 canais, múltiplo mediano 1,09x a mediana do canal e 8,1% com 3x ou mais.
Duração mediana na célula: 18,6 min; no top 10% de cada canal: 20,0 min.
Faixa com mais vídeos de 3x na célula (3+ canais, 20+ vídeos): 30-45 min (15,5%; descritivo, sem controle de idade).
- Nos 200k+, contra 8 a 20 min: 20 a 45 min +25,1% (q < 0,001); menos de 5 min −33,5%. O ótimo para topo do canal (72 min) é o dobro do ótimo para média (34 min): vídeo muito longo aumenta a variância.
- Duração relativa ao hábito do próprio canal pesa tanto quanto a absoluta. Não estique: o ganho supõe retenção real, que a base não mede.

## 3. Título

47 caracteres, 10 palavras. O título é filtro fino, não alavanca: o melhor modelo de título tem R² fora da amostra de 0,018.

| Traço | Presente | Efeito no múltiplo do canal | IC 95% | q | Confiança |
|---|---|---:|---|---:|---|
| afirmação contraintuitiva como gancho | não | +4,9% | −10,1% a +23,2% | 0,889 | baixa (efeito não confirmado em PT) |
| emoji (PT) | não | +23,5% | +6,7% a +41,7% | 0,090 | baixa (concentrado em 45 canais) |

**O que não importa**

- 1ª pessoa em PT: −2,7% (q = 0,950), nulo.
- Comprimento do título: nenhuma faixa difere de 46 a 60 caracteres nos 200k+ (q > 0,93).
- Pergunta no título: −2,9% nos 200k+ e −4,9% nos pequenos, nulo (mas aumenta comentários por view).
- Lista, tutorial, mistério, urgência e lacuna de curiosidade: IC cruzando zero na base toda.

## 4. Thumbnail e alinhamento título + capa

Padrões lidos nas notas da capa (efeito dentro do canal, 200k+):
- Expressão seria: +3,9% (q = 0,465, confiança baixa; comparação ingênua entre canais +19,2%)
- Cor dominante verde: +14,6% (q = 0,136, confiança média; comparação ingênua entre canais +9,2%)
- Número/dinheiro visível: −4,9% (q = 0,483, confiança baixa; comparação ingênua entre canais −1,7%)
- Peso visual à esquerda: +6,4% (q = 0,056, confiança média; comparação ingênua entre canais −9,4%)

Melhores sinais no nicho financas (q alto, usar como teste):
- Expressão medo: +10,2% (q = 0,166, 105 vídeos)
- Sem rosto: +1,8% (q = 0,334, 35 vídeos)
- Texto 4-6 palavras: +9,5% (q = 0,346, 639 vídeos)
- Olhar para a câmera: +13,3% (q = 0,477, 957 vídeos)
- Peso no terço inferior: +11,9% (q = 0,569, 434 vídeos)
Sinais negativos no nicho: Muito colorida (top 20%) −23,3%; Estilo foto −17,0%; Paleta enxuta (<=2 cores) −10,4%.
Padrões de confiança média na base toda: HDB-87 Expressões Intensas e Elementos Bizarros +33,5%; KM12-07 Exibição de gadget em primeiro plano +28,8%; HDB-39 Prato em destaque com apresentador +25,5%; Cor dominante verde +14,6%; Peso visual à esquerda +6,4%.
Hipóteses raras para teste A/B: Cor dominante verde + Escura (bottom 20% brilho) +52,1% (24 canais); Cor dominante ciano + Fundo colagem +40,4% (30 canais); Texto repete o título + Cor dominante branco +37,8% (55 canais); Cor dominante azul + Comparação/antes-depois +35,5% (50 canais); Texto repete o título + Figura mais escura que o fundo +34,6% (34 canais).
Alinhamento título ↔ texto da capa ("R$ 10 MIL RENDE QUANTO?"): similaridade lexical 0,76, nível alto.
Mitos a ignorar: Rosto grande (entre canais +30,0%, dentro do canal −2,5%); Expressão surpresa (entre canais +17,4%, dentro do canal −2,7%); Seta ou círculo (entre canais +11,8%, dentro do canal +0,4%); Sem rosto (entre canais −40,7%, dentro do canal +4,6%); Saturação alta (top 20%) (entre canais −12,0%, dentro do canal −4,3%); Contraste global alto (top 20%) (entre canais −0,1%, dentro do canal −4,5%).
- Por nicho, nenhum padrão de capa sobrevive com folga à correção de múltiplos testes; use como ponto de partida de teste A/B.
- Repetir o título na capa não é punido (+1,1%, IC −9,5% a +13,4%). O que tende a perder é texto sem relação com o título.
- Fugir do visual habitual do próprio canal custa −7,4% por DP nos 200k+ (q < 0,001).

## 5. Cadência e consistência

1 dia desde o vídeo anterior; curva dos 200k+ contra 7 dias: −17,3%.
Faixas de intervalo do grupo (referência 5 a 9 dias): <2d −8,8% (q = 0,003); 2-4d −4,2% (q = 0,058); 10-20d +3,1% (q = 0,243); 21-45d +4,0% (q = 0,251); >45d +16,9% (q = 0,012).
Fugir do tema habitual do canal reduz views: −14,8% por DP nos pequenos e −10,5% nos 200k+ (p < 0,001); novidade não aumenta a chance de 10x.
- Depois de um hit, o vídeo seguinte tende a +9,4% (IC 95% +3,4% a +15,1%) se ficar no mesmo veio; nos 200k+ isso é quase todo fase do canal. Pressa ou espera não trazem ganho específico (p = 0,58).
- Dobrar o número de vídeos nos 7 dias anteriores se associa a −9,6% (q = 0,003) nos 200k+.
- Dia e horário de publicação não importam no agregado (nada sobrevive à correção em nenhum porte).

## 6. Exemplos reais parecidos de alto desempenho

| Título | Canal | Porte | Idioma | Múltiplo vs mediana do canal | Views | Duração | Similaridade |
|---|---|---|---|---:|---:|---:|---:|
| TESOURO SELIC / COMO FUNCIONA? | Tesouro Direto | emergente | PT | 2,3x | 84.511 | 5,1 min | 0,33 |
| Qual rende mais, LCI, LCA ou Tesouro Selic? | Riquezas e Finanças | pequeno | PT | 2,5x | 9.648 | 18,8 min | 0,29 |
| Tesouro Reserva ou Selic? Eu testei com R$9 mil | Me Poupe! | grande | PT | 3,1x | 413.949 | 16,6 min | 0,21 |
| Tesouro Selic, Tesouro Reserva ou CDB - Qual é melhor? | Riquezas e Finanças | pequeno | PT | 2,5x | 19.539 | 13,8 min | 0,24 |
| Quanto Rende 200 mil no CDB da Caixa? Descubra agora! | 10 Conto Educação Financeira | pequeno | PT | 13,7x | 20.786 | 9,4 min | 0,24 |

Exemplos são referências de tema e embalagem, não garantia: o múltiplo depende muito da volatilidade de cada canal.

## 7. Checklist pré-publicação

- [ ] Roteiro que sustente 23 a 45 min sem enchimento (faixa forte do nicho financas).
- [ ] Colocar a palavra-chave principal no início do título (+1,3 p.p. de chance de top 5% do canal, q = 0,023).
- [ ] Texto da capa curto e reforçando a mesma ideia do título; nada de assunto paralelo.
- [ ] Manter a identidade visual do canal; testar no máximo 1 variação de capa por vez.
- [ ] Reagendar para pelo menos 3 dias depois do vídeo anterior.
- [ ] Subir legenda própria (associação de +28,6% nos 200k+, com risco de causalidade reversa) e capítulos como experiência do usuário, não como alavanca.
- [ ] Depois de publicar, comparar CTR e retenção no YouTube Studio com a mediana do canal: é o dado que esta base não tem.
