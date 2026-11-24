# Guia Prático de Criação de Thumbnails (baseado nos 17.882 vídeos)

> Regras derivadas estritamente dos dados desta base. **Não há CTR na base**; nada aqui promete clique ou viralização. O que a thumbnail muda dentro de um canal é pequeno (R² out-of-sample intra-canal de no máximo 0,02 a 0,03). Use as regras como ponto de partida e valide com testes no seu canal. Entre parênteses: evidência e confiança.

## Princípios

- Priorize a pauta e o objeto central do vídeo sobre truques gráficos: recursos visuais sozinhos explicam no máximo 2.45% da variação intra-canal (ridge_embeddings_768_intra_canal = 0.0245, Confiança Média).
- Ignore modismos copiados de canais gigantes sem testar no seu público: padrões famosos como rosto grande têm +30.0% de efeito ingênuo entre canais, mas -2.5% dentro do mesmo canal (n=11.539, q_bh=0.6431, Confiança Baixa).
- Elimine clichês de clickbait desgastados que não agregam valor: setas, círculos e caras de choque exageradas têm efeito intra-canal nulo ou levemente negativo (Seta ou círculo: +0.4%, q_bh=0.9501; Expressão surpresa: -2.7%, q_bh=0.6378, Confiança Baixa).
- Hipótese a testar: Use a thumbnail para tangibilizar imediatamente a entrega do vídeo (o produto físico, o prato pronto ou a cena bizarra) em vez de focar apenas na reação isolada do apresentador (KM12-07 +28.8%, q_bh=0.0882; HDB-39 +25.5%, q_bh=0.3425, Confiança Média).

## Composição

- Quando houver um produto físico ou objeto concreto como tema, coloque-o em primeiro plano claro com fundo mais limpo (KM12-07 Exibição de gadget: +28.8%, IC +7.9% a +53.7%, q_bh=0.0882, Confiança Média).
- Hipótese a testar: Sinta-se livre para criar capas sem rosto humano quando o objeto, lugar ou conceito for o verdadeiro atrativo, pois omitir o rosto não gera punição intra-canal (Sem rosto: +4.6%, IC -5.3% a +15.6%, q_bh=0.7273; Nenhuma pessoa real OR=1.548, Confiança Baixa).
- Hipótese a testar: Mantenha hierarquia visual clara evitando telas divididas ao meio ou grades de colagem complexas, que tendem a reduzir o impacto dos elementos (Tela dividida CV: -5.5%, q_bh=0.5195; Grade/colagem lpm_canal_pp = -26.818, q_canal=0.372, Confiança Baixa).

## Texto

- Hipótese a testar: Teste repetir ou alinhar diretamente uma promessa curta do título sobre composições de cor dominante branca para reforço rápido de leitura (Texto repete o título + Cor dominante branco: +37.8%, IC +13.7% a +67.0%, q_bh=0.059, Confiança Média/Baixa).
- Hipótese a testar: Prefira textos curtos de 1 a 3 palavras ou ausência total de texto caso a imagem já seja autoexplicativa, evitando blocos longos de 7+ palavras (Texto 1-3 palavras: +2.5%, q_bh=0.6378; Sem texto: +0.6%, q_bh=0.9398; Texto 7+ palavras: -2.5%, q_bh=0.7373, Confiança Baixa).
- Hipótese a testar: Evite prender o texto sistematicamente dentro de tarjas ou caixas coloridas pesadas sem necessidade estética (Texto em tarja/caixa colorida: OR=0.722 no top 5% vs bottom 20%, lpm_canal_pp = -9.302, q_canal=0.444, Confiança Baixa).

## Cores

- Explore o uso de cor dominante verde na composição ou cenário para diferenciar o vídeo na interface do YouTube (Cor dominante verde: +14.6%, IC +3.2% a +27.3%, q_bh=0.1364, Confiança Média; combinada a contraste global baixo: +30.2%, q_bh=0.035, Confiança Média).
- Teste composições com cor dominante azul em cenários ricos em detalhes para destacar a peça no feed (Cor dominante azul + Visual poluído: +32.3%, IC +15.2% a +51.9%, q_bh=0.01, Confiança Média).
- Hipótese a testar: Evite estourar artificialmente a saturação ou depender de vermelho dominante, que pode se misturar à identidade visual do próprio YouTube (Saturação alta top 20%: -4.3%, q_bh=0.4385; Cor dominante vermelho: -5.9%, q_bh=0.4649, Confiança Baixa).

## Contraste

- Em paletas verdes e frias, permita um contraste global mais suave e orgânico em vez de forçar sombras duras (Cor dominante verde + Contraste global baixo: +30.2%, IC +12.8% a +50.3%, q_bh=0.035, Confiança Média).
- Hipótese a testar: Não force contraste extremo artificial entre figura e fundo escuro com vinhetas pesadas achando que isso garante cliques, pois o quintil superior de Delta-E não mostrou vantagem (Figura-fundo alto contraste top 20%: -3.9%, IC -8.9% a +1.5%, q_bh=0.5195, Confiança Baixa).

## Posicionamento

- Concentre o peso visual e o elemento de maior saliência no lado esquerdo do quadro (pelo menos 12 p.p. a mais que na direita), liberando a direita de sobreposições da interface como o marcador de tempo do vídeo (Peso visual à esquerda: +6.4%, IC +2.2% a +10.9%, q_bh=0.0555, Confiança Média).
- Hipótese a testar: Ao exibir objetos ou produtos, posicione o item em destaque à frente ou ao lado do apresentador mantendo área de respiro (KM12-07: +28.8%, q_bh=0.0882, Confiança Média).

## Evitar

- Hipótese a testar: Evitar ocultar o tema principal com silhuetas pretas, borrões artificiais ou pontos de interrogação apelativos (Mistério oculto/borrado: OR=0.49 no top 5% vs bottom 20%, lpm_canal_pp = -15.85, q_canal=0.372, Confiança Baixa).
- Hipótese a testar: Evitar desenhar setas e círculos vermelhos sem função informativa real apenas para imitar clickbait antigo (Seta ou círculo: +0.4%, q_bh=0.9501; Círculo desenhado OR=0.502, Confiança Baixa).
- Hipótese a testar: Evitar forçar expressões faciais de choque artificial e rostos gigantes em todo vídeo por mera inércia criativa (Expressão surpresa: -2.7%, q_bh=0.6378; Rosto grande: -2.5%, q_bh=0.6431, Confiança Baixa).
- Hipótese a testar: Evitar estourar o controle de saturação no máximo e cobrir a capa de vermelho dominante sem respiro (Saturação alta: -4.3%, q_bh=0.4385; Cor dominante vermelho: -5.9%, q_bh=0.4649, Confiança Baixa).

## Diferenças por nicho

- **tech:** Destaque o smartphone ou gadget segurado em primeiro plano sobre fundo liso ou desfocado com apresentador ao fundo (KM12-07: geral +28.8%, q_bh=0.0882, nicho tech +32%, q=0.34, Confiança Média).
- **historias:** Teste composições ilustradas ou saturadas com expressões intensas de medo/seriedade diante de elementos bizarros, evitando colagens de apresentador com personagens de games (HDB-87: geral +33.5%, nicho historias +206%, n=17, q=0.01, Confiança Média; evitar HDB-89 em historias: -73%, q=0.00, Confiança Baixa).
- **culinaria:** Hipótese a testar: Priorize o prato pronto bem iluminado em primeiro plano acompanhado do apresentador na cozinha em paleta quente natural, sem exagerar na saturação artificial (HDB-39: geral +25.5%, q_bh=0.3425, culinaria +55%, q=0.35, Confiança Média).
- **games:** Hipótese a testar: Evite depender apenas de retratos escuros de personagens ou de números/valores grandes na capa; teste cenas de tensão/elementos inusitados (HDB-90: -11.6%, q_bh=0.7273; Número/dinheiro em games: -22%, q=0.12; HDB-87 em games: +27%, q=0.54, Confiança Baixa).
- **educacao:** Hipótese a testar: Diagramas limpos em fundo escuro ou ilustrações conceituais são neutros e seguros para identidade de marca, mas foque no tema pois o ganho visual isolado é incerto (HDB-80: +10.4%, q_bh=0.5111; HDB-79 educacao: +16%, q=0.73, Confiança Baixa).
- **esportes:** Hipótese a testar: Evite colagens caóticas com excesso de jogadores, pouco respiro e 7+ palavras; prefira composições com peso à esquerda ou verde de gramado (HDB-31: -14.1%, q_bh=0.7273; HDB-59: -13.0%, q_bh=0.8222; Peso à esquerda esportes: +15%, q=0.80, Confiança Baixa).
- **infantil:** Hipótese a testar: Mantenha cenários 3D claros e vibrantes com poucos protagonistas bem definidos em vez de aglomerar múltiplos atores em montagens poluídas (KM12-00: +40.5%, q_bh=0.7059 vs HDB-41: -11.1%, q_bh=0.7352, Confiança Baixa).
- **documentario:** Hipótese a testar: Prefira fotografia com fundo desfocado ou montagens dramáticas contextuais em vez de vetores minimalistas chapados (Fundo desfocado doc: +19%, q=0.39; HDB-51 doc: +37%, q=0.71 vs HDB-79 doc: -45%, q=0.13, Confiança Baixa).
- **lifestyle:** Hipótese a testar: Explore cenas focadas no ambiente/objeto sem obrigação de rosto grande em close e teste tons verdes naturais (Sem rosto lifestyle: +70%, q=0.48; Cor verde lifestyle: +37%, q=0.40 vs Rosto grande: -12%, q=0.73, Confiança Baixa).
- **entretenimento:** Hipótese a testar: Evite colagens esportivas/múltiplos recortes com textos longos e ilustrações genéricas desconectadas do apresentador (HDB-59 entretenimento: -48%, q=0.07; Estilo ilustracao: -50%, q=0.84, Confiança Baixa).
- **financas:** Hipótese a testar: Não abuse de números gigantes, setas ou comparações batidas de antes/depois; teste apresentador olhando para a câmera com foco limpo (Olhar câmera financas: +13%, q=0.48 vs Comparação: -13%, q=0.79 e Seta: -11%, q=0.71, Confiança Baixa).

## Checklist pré-publicação

- [ ] O peso visual principal da imagem está concentrado na metade esquerda do quadro para fugir do carimbo de duração?
- [ ] O canto inferior direito está livre de palavras, rostos ou objetos cruciais?
- [ ] Se o vídeo trata de um produto físico, prato ou objeto tangível, ele aparece claramente em primeiro plano?
- [ ] Você removeu setas, círculos ou pontos de interrogação que não adicionam informação real?
- [ ] Caso haja rosto humano, a expressão condiz organicamente com o tom do vídeo em vez de repetir um choque artificial padronizado?
- [ ] Se optou por colocar texto, ele é legível em tamanho reduzido (idealmente até 3 palavras) ou reforça diretamente o título sem poluir?
- [ ] A saturação de cores parece natural e evita camuflagem excessiva com o vermelho da interface do YouTube?
- [ ] É possível testar uma variação cromática fria (como verde ou azul dominante) para destacar esta peça no feed?
- [ ] A composição tem um foco dominante claro em vez de uma grade confusa ou tela dividida desnecessária?
- [ ] A imagem comunica o tema real do vídeo mesmo se vista sem ler o título?

## Como testar no seu canal

1. Use a ferramenta nativa 'Testar e comparar' (Teste A/B de thumbnails) do YouTube Studio dentro do mesmo vídeo, único método que isola 100% os confundidores de canal, tema, duração e sazonalidade que dominam bases históricas.
2. Suba sempre de 2 a 3 variantes que mudem apenas um eixo estrutural claro por vez: por exemplo, Variante A (padrão atual com rosto grande central) contra Variante B (objeto/cena em destaque com peso visual à esquerda) e Variante C (variação de paleta fria verde/azul).
3. Mantenha o título rigorosamente fixo durante o experimento e aguarde acumular volume relevante de impressões por pelo menos 7 a 14 dias antes de declarar vencedor, evitando encerrar o teste no ruído das primeiras horas.
4. Avalie o vencedor combinando participação no tempo de exibição (watch time share) e CTR interno do Studio, pois uma capa apelativa que atrai o clique errado derruba a retenção e não sustenta views totais.
5. Registre os resultados em uma planilha própria do canal separando por linha editorial (ex: reviews vs opinativos), construindo evidência causal específica para a sua audiência após 10 a 15 testes consecutivos.

Referências visuais: `catalogo_visual/catalogo_geral_ranking.png` e mosaicos por padrão em `catalogo_visual/`. Detalhes estatísticos: `RELATORIO_THUMBS_VISUAL.md`.