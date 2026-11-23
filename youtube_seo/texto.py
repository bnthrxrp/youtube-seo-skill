"""Traços de título, capítulos e OCR. A lógica segue estudo-10k/scripts/04_features.py e 04c_ocr_miniaturas.py."""

from __future__ import annotations

import re
from collections import Counter

EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\U0001F1E6-\U0001F1FF]")
STOP = set(
    """
    a o os as de do da dos das e em no na um uma para por com que se não nao
    the an of to in on and for with is my i you how what this it
    el la los las y un una del
    """.split()
)
_EU = {"eu", "meu", "minha", "me", "comprei", "i", "my", "i'm", "im", "we", "our", "nós", "nosso"}
_VOCE = {"você", "voce", "vc", "seu", "sua", "vocês", "voces", "you", "your", "you're"}


def tokens(texto: str) -> list[str]:
    return re.findall(r"[\wÀ-ÿ']+", (texto or "").lower())


def extrair_titulo(titulo: str) -> dict:
    s = titulo or ""
    palavras = s.split()
    letras = [c for c in s if c.isalpha()]
    return {
        "chars": len(s),
        "palavras": len(palavras),
        "tem_numero": int(bool(re.search(r"\d", s))),
        "tem_pergunta": int("?" in s),
        "tem_exclamacao": int("!" in s),
        "tem_palavra_caps": int(
            any(len(w) >= 3 and w.isupper() and w.isalpha() for w in re.findall(r"[A-Za-zÀ-ÿ]+", s))
        ),
        "titulo_todo_caps": int(len(letras) > 5 and all(not c.islower() for c in letras)),
        "tem_emoji": int(bool(EMOJI.search(s))),
        "tem_separador": int(bool(re.search(r"\||:| - | – | — ", s))),
        "tem_parenteses": int(bool(re.search(r"[\(\[]", s))),
        "tem_eu": int(bool(set(tokens(s)) & _EU)),
        "tem_voce": int(bool(set(tokens(s)) & _VOCE)),
    }


def tem_capitulos(descricao: str) -> bool:
    """Regra do YouTube usada no estudo: começa em 0:00 e tem ao menos 3 marcas."""
    texto = descricao or ""
    marcas = re.findall(r"(?m)^\s*\(?\d{1,2}:\d{2}(:\d{2})?", texto)
    comeca = re.search(r"(?m)^\s*\(?0?0:00", texto)
    return len(marcas) >= 3 and bool(comeca)


def termo_no_titulo(titulo: str, termo: str) -> bool:
    if not termo:
        return False
    return termo.casefold() in (titulo or "").casefold()


def termo_no_inicio(titulo: str, termo: str) -> bool:
    if not termo:
        return False
    if (titulo or "").casefold().startswith(termo.casefold()):
        return True
    primeiras = tokens(titulo)[:3]
    alvo = [t for t in tokens(termo) if len(t) > 2 and t not in STOP]
    return any(t in primeiras for t in alvo)


def intencao(termo: str) -> str:
    """Heurística de intenção, rotulada como inferência. Não é volume de busca."""
    t = f" {(termo or '').casefold()} "
    if any(x in t for x in [" como ", " how to ", " tutorial ", " aprende", " learn "]):
        return "aprender"
    if any(x in t for x in [" vs ", " versus ", " ou ", " compar"]):
        return "comparar"
    if any(x in t for x in [" melhor ", " best ", " review ", " vale a pena ", " worth "]):
        return "avaliar"
    if any(x in t for x in [" erro ", " conserta", " fix ", " não funciona ", " not working "]):
        return "resolver"
    return "indefinida"


def metricas_ocr(texto: str, titulo: str) -> dict:
    """Mesmos limiares de estudo-10k/scripts/04c_ocr_miniaturas.py."""
    txt = texto or ""
    palavras = re.findall(r"\S+", txt)

    def tok(s: str) -> set[str]:
        return set(re.findall(r"[a-záéíóúãõâêôçñ0-9]{3,}", s.lower()))

    ot, tt = tok(txt), tok(titulo or "")
    letras = [c for c in txt if c.isalpha()]
    return {
        "ocr_texto": txt[:200],
        "ocr_tem_texto": int(len(palavras) > 0),
        "ocr_n_palavras": len(palavras),
        "ocr_repete_titulo": int(bool(ot) and len(ot & tt) / len(ot) >= 0.5),
        "ocr_numero": int(bool(re.search(r"\d", txt))),
        "ocr_dinheiro": int(bool(re.search(r"\$|R\$|€|£", txt))),
        "ocr_caps": int(len(letras) >= 4 and sum(c.isupper() for c in letras) / len(letras) > 0.8),
    }


def temas(titulos: list[str], top: int = 12) -> dict:
    termos: Counter[str] = Counter()
    bigramas: Counter[str] = Counter()
    for titulo in titulos:
        toks = [t for t in tokens(titulo) if t not in STOP and len(t) > 2]
        termos.update(toks)
        bigramas.update(f"{a} {b}" for a, b in zip(toks, toks[1:]))
    return {
        "termos": [{"termo": t, "vezes": n} for t, n in termos.most_common(top)],
        "bigramas": [{"termo": t, "vezes": n} for t, n in bigramas.most_common(top)],
    }


def prefixos_de_idioma(hl: str | None) -> list[str]:
    lang = (hl or "en").lower().split("-")[0]
    tabela = {
        "pt": [
            "como",
            "como fazer",
            "por que",
            "melhor",
            "vale a pena",
            "para iniciantes",
            "review",
            "vs",
        ],
        "en": [
            "how to",
            "why",
            "best",
            "for beginners",
            "review",
            "vs",
            "tutorial",
            "without",
        ],
        "es": [
            "cómo",
            "por qué",
            "mejor",
            "para principiantes",
            "review",
            "vs",
            "tutorial",
            "sin",
        ],
    }
    return list(tabela.get(lang, ["how to", "best", "vs", "review", "tutorial"]))
