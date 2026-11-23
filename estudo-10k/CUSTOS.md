# Custos do estudo

Teto autorizado: R$ 50 no total (lote completo do Gemini só se a projeção ficasse abaixo de R$ 40; parar se o gasto medido passasse de R$ 40).
Cotação usada: US$ 1 = R$ 5,93 (AwesomeAPI, 23/11/2026 17:26).

| Item | Quando (horário de Brasília) | Uso | Custo |
|---|---|---|---|
| YouTube Data API v3 (22.405 vídeos, 257 canais) | 23/11/2026 | cota gratuita | R$ 0,00 |
| Miniaturas (i.ytimg.com) e medidas locais (OpenCV, OCR RapidOCR) | 23/11/2026 | local | R$ 0,00 |
| Gemini 2.5 Flash-Lite, piloto 50 (chave antiga) | 17:30 | 50 recusas HTTP 402 (sem crédito), 0 tokens | R$ 0,00 |
| Gemini 3.5 Flash-Lite, piloto 50, esquema completo | 17:56 | 20.391 tokens entrada, 12.230 saída | US$ 0,0367 = R$ 0,22 |
| Gemini 3.5 Flash-Lite, piloto 50, esquema enxuto | 17:57 | 19.391 / 8.670 | US$ 0,0275 = R$ 0,16 |
| Gemini 3.5 Flash-Lite, piloto 50, chaves curtas (versão final) | 17:59 | 25.379 / 4.962 | US$ 0,0200 = R$ 0,12 |
| Gemini 3.5 Flash-Lite, Batch API, 8 lotes | 18:00-18:17 | 17.826 imagens válidas; 9.017.200 tokens entrada, 1.782.859 saída | US$ 3,58 = R$ 21,24 |
| **Total** | | | **US$ 3,67 = R$ 21,74** |

Preços oficiais (ai.google.dev/gemini-api/docs/pricing, 23/11/2026): gemini-3.5-flash-lite US$ 0,30 por 1M tokens de entrada e US$ 2,50 por 1M de saída (padrão); Batch API com 50% de desconto. O gemini-2.5-flash-lite (US$ 0,10/0,40) deixou de aceitar contas novas (HTTP 404).

As 50 miniaturas do piloto com esquema enxuto (17:57) eram do dataset final e entraram na análise, somando 17.876 miniaturas lidas.

Decisões de custo: projeção do piloto final = R$ 42,46 em chamadas normais (acima de R$ 40) e R$ 21,23 pela Batch API, por isso o lote completo foi pela Batch API e só nos 17.882 vídeos do dataset final. Saída cobrada por token: o esquema JSON com chaves de uma letra cortou o custo de saída por imagem de ~245 para ~100 tokens. Resolução de imagem baixa (264 tokens por miniatura) e raciocínio mínimo (0 tokens de "pensamento").

Os valores acima são calculados pelos tokens que a própria API devolveu (usageMetadata) e pela tabela de preços; o valor cobrado de fato aparece no painel de faturamento do AI Studio. Se o desconto do Batch não tivesse sido aplicado, o total seria cerca de R$ 43.
