# Custos do laboratório (consolidado)

Gerado automaticamente por `consolidacao/consolidar_custos.py`, que soma **todos** os arquivos `uso_gemini*.csv` do laboratório (cada chamada registrada pelo roteador de cada frente, na tarifa cheia) e as unidades da YouTube Data API da coleta de canais pequenos. Câmbio: US$ 1 = R$ 5,93. Teto autorizado: **R$ 100,00**.

Preços por 1M de tokens (entrada / saída, incluindo raciocínio): gemini-4-carbon US$ 2,00 / 10,00; gemini-4-hydrogen US$ 1,50 / 7,50; gemini-3.5-flash-lite US$ 0,30 / 2,50; gemini-embedding-2-preview cobrado por entrada.

## Por frente

| Frente | Arquivo | Linhas registradas | USD | BRL |
|---|---|---:|---:|---:|
| Fase 1 (auditoria e primeiras descobertas) | `dados/uso_gemini_lab.csv` | 751 | US$ 2,3650 | R$ 14,02 |
| Frente 2A (ML, GAM, cadência, breakout) | `frente_ml/dados/uso_gemini_ml.csv` | 2 | US$ 0,5148 | R$ 3,05 |
| Frente 2B (thumbnails visuais) | `frente_thumbs/dados/uso_gemini_thumbs.csv` | 18.817 | US$ 4,6220 | R$ 27,42 |
| Frente 2C (títulos, arquétipos, oportunidades) | `frente_arquetipos/dados/uso_gemini_arquetipos.csv` | 854 | US$ 2,4800 | R$ 14,71 |
| Frente 2D (canais pequenos 5k a 200k) | `frente_pequenos/dados/uso_gemini_pequenos.csv` | 4.681 | US$ 1,0268 | R$ 6,09 |
| **Total** | | **25.105** | **US$ 11,0086** | **R$ 65,29** |

## Por modelo

| Modelo | Linhas registradas | USD | BRL |
|---|---:|---:|---:|
| gemini-embedding-2-preview | 22.498 | US$ 3,3079 | R$ 19,62 |
| gemini-4-hydrogen | 143 | US$ 3,0448 | R$ 18,06 |
| gemini-3.5-flash-lite | 2.456 | US$ 2,3309 | R$ 13,82 |
| gemini-4-carbon | 8 | US$ 2,3251 | R$ 13,79 |

## Frente × modelo (BRL)

| Frente | gemini-3.5-flash-lite | gemini-4-hydrogen | gemini-4-carbon | gemini-embedding-2-preview |
|---|---:|---:|---:|---:|
| Fase 1 (auditoria e primeiras descobertas) | R$ 1,43 | R$ 3,74 | R$ 8,86 | R$ 0,00 |
| Frente 2A (ML, GAM, cadência, breakout) | R$ 0,00 | R$ 0,00 | R$ 3,05 | R$ 0,00 |
| Frente 2B (thumbnails visuais) | R$ 5,20 | R$ 8,47 | R$ 0,91 | R$ 12,84 |
| Frente 2C (títulos, arquétipos, oportunidades) | R$ 4,31 | R$ 5,85 | R$ 0,62 | R$ 3,93 |
| Frente 2D (canais pequenos 5k a 200k) | R$ 2,88 | R$ 0,00 | R$ 0,35 | R$ 2,86 |

## YouTube Data API (coleta da Frente 2D)

**1.280 unidades** da cota gratuita diária (10.000), nenhuma chamada `search.list`:

- `playlistItems`: 556 unidades
- `channels`: 399 unidades
- `videos`: 325 unidades

A descoberta de canais pequenos usou buscas públicas via `yt-dlp` (sem cota). As bases 200k+ vieram da coleta anterior do estudo e não entram aqui.

## Saldo

- Gasto registrado: **R$ 65,29** (US$ 11,0086).
- Saldo até o teto de R$ 100,00: **R$ 34,71**.
- Consolidação final: R$ 0,00 em Gemini (nenhuma chamada; o motor de consulta e o pacote não usam API paga).
- O total inclui R$ 7,12 de reserva conservadora da Fase 1 (pior caso de uma revisão carbon desconectada sem devolver consumo). Se essa tentativa não tiver sido cobrada, o gasto efetivo cai para R$ 58,17.
- Todas as chamadas foram síncronas na tarifa cheia; nenhum Batch foi usado.
