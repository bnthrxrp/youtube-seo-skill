"""Achados do estudo próprio (estudo-10k/, 17.882 vídeos, 23/11/2026).

Força do sinal, na versão conservadora descrita em estudo-10k/RESULTADOS.md e na
seção 17B de SKILL.md. Correlação, não causa. Nenhum traço de miniatura passou
na correção para múltiplos testes.
"""

from __future__ import annotations

NOTA_GERAL = (
    "Estudo observacional em estudo-10k/ (23/11/2026): 17.882 vídeos longos de 203 canais. "
    "Cada vídeo foi comparado à mediana do próprio canal. Correlação, não causa. "
    "Os 35 traços de metadados e miniatura juntos explicam cerca de 1,5% da variação "
    "dentro do canal (R² fora da amostra 0,015). "
    "Sinal forte: legenda enviada pelo canal (+28%, margem +15% a +42%) e duração "
    "(+14% a cada dobro, margem +8% a +21%). "
    "Tamanho de título, tamanho de descrição, número, pergunta, separador, parênteses "
    "e a maior parte dos traços de miniatura não têm efeito confirmado."
)

# forca: forte | provavel | fraco | incerto | sem_efeito
FINDINGS: dict[str, dict[str, str]] = {
    "legenda_canal": {
        "traco": "Legenda disponível (campo da API usado no estudo)",
        "forca": "forte",
        "efeito": "+28%",
        "margem": "+15% a +42%",
        "leitura": (
            "Único traço de metadado com sinal forte e estável (10 de 11 nichos; "
            "PT +45%, EN +24%). Pode haver causa reversa: o canal legenda o vídeo "
            "que já recebe mais cuidado. A API não separa legenda automática de manual."
        ),
    },
    "duracao": {
        "traco": "Duração",
        "forca": "forte",
        "efeito": "+14% por dobro",
        "margem": "+8% a +21%",
        "leitura": (
            "Abaixo de 5 min ficou cerca de 21% abaixo do normal do canal; "
            "15 a 60 min, cerca de 8% acima; acima de 60 min o ganho some."
        ),
    },
    "emoji_titulo": {
        "traco": "Emoji no título",
        "forca": "provavel",
        "efeito": "+11%",
        "margem": "+2% a +21%",
        "leitura": "Não passa na correção conservadora. Mais forte em PT (+17%) que em EN (+4%).",
    },
    "palavra_caps": {
        "traco": "Uma palavra em CAIXA ALTA no título",
        "forca": "provavel",
        "efeito": "+7%",
        "margem": "+1% a +13%",
        "leitura": "9 de 11 nichos. Título inteiro em caixa alta não tem efeito.",
    },
    "titulo_todo_caps": {
        "traco": "Título inteiro em caixa alta",
        "forca": "sem_efeito",
        "efeito": "0%",
        "margem": "−10% a +11%",
        "leitura": "Sem efeito detectável.",
    },
    "links_descricao": {
        "traco": "Mais links na descrição",
        "forca": "provavel",
        "efeito": "+7% por dobro",
        "margem": "+2% a +13%",
        "leitura": "Provável marca de vídeo patrocinado ou produção maior, não de um truque de descrição.",
    },
    "primeira_pessoa": {
        "traco": "Título em 1ª pessoa (eu/meu/I/my)",
        "forca": "fraco",
        "efeito": "−7%",
        "margem": "−13% a −1%",
        "leitura": "Sinal fraco e só em inglês (−10%). Em português, zero.",
    },
    "tamanho_titulo": {
        "traco": "Tamanho do título",
        "forca": "sem_efeito",
        "efeito": "+1% a cada 10 caracteres",
        "margem": "−1% a +3%",
        "leitura": "Sem efeito detectável.",
    },
    "tamanho_descricao": {
        "traco": "Tamanho da descrição",
        "forca": "sem_efeito",
        "efeito": "+0,3% por dobro",
        "margem": "−3% a +4%",
        "leitura": "Sem efeito detectável.",
    },
    "numero_titulo": {
        "traco": "Número no título",
        "forca": "sem_efeito",
        "efeito": "perto de zero",
        "margem": "cruza zero",
        "leitura": "Sem efeito detectável, junto com pergunta, você, separador e parênteses.",
    },
    "pergunta_titulo": {
        "traco": "Pergunta no título",
        "forca": "sem_efeito",
        "efeito": "perto de zero",
        "margem": "cruza zero",
        "leitura": "Sem efeito detectável.",
    },
    "voce_titulo": {
        "traco": "'Você' no título",
        "forca": "sem_efeito",
        "efeito": "perto de zero",
        "margem": "cruza zero",
        "leitura": "Sem efeito detectável.",
    },
    "separador_titulo": {
        "traco": "Separador no título",
        "forca": "sem_efeito",
        "efeito": "perto de zero",
        "margem": "cruza zero",
        "leitura": "Sem efeito detectável.",
    },
    "parenteses_titulo": {
        "traco": "Parênteses no título",
        "forca": "sem_efeito",
        "efeito": "perto de zero",
        "margem": "cruza zero",
        "leitura": "Sem efeito detectável.",
    },
    "tags": {
        "traco": "Quantidade de tags",
        "forca": "sem_efeito",
        "efeito": "sem prejuízo em não ter tag",
        "margem": "−6% a +38% para zero tags",
        "leitura": "Não ter tag não piorou. Dobrar as tags deu +3% incerto. Tags continuam secundárias.",
    },
    "capitulos": {
        "traco": "Capítulos na descrição",
        "forca": "incerto",
        "efeito": "+6%",
        "margem": "−6% a +20%",
        "leitura": "Incerto. PT +16%, EN −1%. Útil para busca e Ask, sem efeito confirmado em views.",
    },
    "rosto_grande": {
        "traco": "Rosto grande na miniatura",
        "forca": "fraco",
        "efeito": "+6% no detector simples; −1% na leitura por IA",
        "margem": "0% a +11% (detector); −5% a +3% (IA)",
        "leitura": "O sinal muda com a régua de medição. Tratar como fraco, não como regra.",
    },
    "ocr_repete_titulo": {
        "traco": "Texto da miniatura repete o título (OCR local)",
        "forca": "fraco",
        "efeito": "+5%",
        "margem": "0% a +10%",
        "leitura": "Sinal fraco. Na leitura por IA, texto que complementa o título foi +3% incerto.",
    },
    "contraste": {
        "traco": "Mais contraste na miniatura",
        "forca": "fraco",
        "efeito": "−3% por desvio",
        "margem": "−5% a −1%",
        "leitura": "Sinal fraco. Não passou na correção cautelosa.",
    },
    "ocr_muitas_palavras": {
        "traco": "5+ palavras na miniatura",
        "forca": "fraco",
        "efeito": "−4%",
        "margem": "−9% a +1%",
        "leitura": "Puxado pelo português (−9%). Em inglês, zero. Nenhum traço de miniatura passou na correção.",
    },
    "expressao_ia": {
        "traco": "Expressão, olhar, seta, estilo e fundo (leitura por IA)",
        "forca": "fraco",
        "efeito": "−8% a +9%",
        "margem": "todos cruzam ou encostam no zero",
        "leitura": (
            "Nenhum dos 27 traços lidos por IA passou na correção para múltiplos testes. "
            "Medo/tensão e expressão séria são hipóteses fracas para testar em A/B, não regra. "
            "Cara de choque, seta e 'sempre ter rosto' não se destacaram."
        ),
    },
}

ROTULOS_FORCA = {
    "forte": "sinal forte",
    "provavel": "provável, não passou na correção conservadora",
    "fraco": "correlação fraca",
    "incerto": "incerto",
    "sem_efeito": "sem efeito confirmado",
}


def achar(chave: str) -> dict[str, str]:
    item = FINDINGS[chave]
    return {**item, "chave": chave, "rotulo": ROTULOS_FORCA[item["forca"]]}
