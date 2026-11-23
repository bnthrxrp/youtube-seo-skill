# Custos do estudo

Teto autorizado: R$ 50 no total (lote completo do Gemini só se a projeção ficasse abaixo de R$ 40).

| Item | Quando (horário de Brasília) | Uso | Custo |
|---|---|---|---|
| YouTube Data API v3 (coleta de 22.405 vídeos, 257 canais) | 23/11/2026 | cota gratuita diária (~13% numa rodada + reforço) | R$ 0,00 |
| Miniaturas (i.ytimg.com, públicas) e medidas de cor/contraste/rosto (OpenCV local) | 23/11/2026 | local | R$ 0,00 |
| Gemini 2.5 Flash-Lite, piloto de 50 miniaturas | 23/11/2026 17:26 | 50 chamadas, todas recusadas com HTTP 402 "prepayment credits are depleted" | R$ 0,00 (0 tokens cobrados) |
| OCR local (RapidOCR/ONNX) no lugar do Gemini | 23/11/2026 17:33 | local, 22.405 miniaturas | R$ 0,00 |

Preço oficial consultado em ai.google.dev/gemini-api/docs/pricing (23/11/2026): gemini-2.5-flash-lite US$ 0,10 por 1M tokens de entrada (imagem/texto) e US$ 0,40 por 1M de saída; gemini-3.5-flash-lite US$ 0,30 / US$ 2,50.
Cotação do dia (AwesomeAPI, 23/11/2026 17:26): US$ 1 = R$ 5,93.

Projeção que não pôde ser medida: sem nenhuma resposta, não houve usageMetadata. Estimativa de referência (não medida): ~300 tokens de entrada e ~150 de saída por miniatura em resolução baixa com prompt e esquema JSON, ou seja ~US$ 0,00009 por imagem, ~US$ 2 (~R$ 12) para 22 mil miniaturas no 2.5 Flash-Lite. Para rodar, é preciso recarregar os créditos pré-pagos do projeto no AI Studio.

**Total gasto: R$ 0,00.**
