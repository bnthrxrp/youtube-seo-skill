"""Motor de consulta acionável para novas ideias de vídeo longo no YouTube.

Lê só o knowledge_base.json ao lado deste arquivo (gerado por build_knowledge_base.py a partir de
26.194 vídeos longos de 310 canais). Não usa rede, API paga nem dependências fora da biblioteca padrão.

Uso como biblioteca:
    from idea_advisor import Ideia, aconselhar, para_markdown
    parecer = aconselhar(Ideia(titulo="...", nicho="tech", idioma="pt", porte="pequeno", duracao_min=18))
    print(para_markdown(parecer))

Uso pela linha de comando:
    python idea_advisor.py --title "Título" --niche tech --lang pt --tier pequeno --duration-min 18 \
        --thumb-notes "fundo escuro, produto em destaque, sem rosto" --days-since-last 5 --format markdown

Limite permanente: a base não tem CTR, impressões, retenção, origem de tráfego nem transcrições.
O parecer compara a ideia com padrões observados dentro dos canais. Não prevê views nem viralização.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

KB_PADRAO = Path(__file__).resolve().with_name("knowledge_base.json")

NICHOS = {
    "culinaria": ["culinaria", "cooking", "food", "comida", "receitas", "recipes"],
    "documentario": ["documentario", "documentary", "docs", "true crime"],
    "educacao": ["educacao", "education", "edu", "ciencia", "science", "ensino"],
    "entretenimento": ["entretenimento", "entertainment", "humor", "comedia", "comedy"],
    "esportes": ["esportes", "esporte", "sports", "sport", "fitness", "futebol"],
    "financas": ["financas", "finance", "financas pessoais", "investimentos", "money", "dinheiro"],
    "games": ["games", "game", "gaming", "jogos"],
    "historias": ["historias", "stories", "story", "historia", "narrativa", "storytelling"],
    "infantil": ["infantil", "kids", "children", "criancas"],
    "lifestyle": ["lifestyle", "vlog", "casa", "home", "beleza", "beauty"],
    "tech": ["tech", "tecnologia", "technology", "gadgets"],
}
PORTES = {
    "pequeno": ["pequeno", "small", "5k-50k"],
    "emergente": ["emergente", "emerging", "50k-200k"],
    "medio": ["medio", "medium", "mid", "200k-2m"],
    "grande": ["grande", "large", "big", "2m-10m"],
    "gigante": ["gigante", "mega", "giant", "10m+"],
}
GRUPO = {"pequeno": "pequenos", "emergente": "pequenos", "medio": "200k+", "grande": "200k+", "gigante": "200k+"}

STOP = set(("a o os as de da do das dos e em um uma uns umas no na nos nas por para com que se ao aos ou mais "
            "the a an of to in on for and or is are with at by from it this that be my your you i me we our "
            "como pra pro sobre sem ser foi vai esta isso este essa voce eu meu minha seu sua").split())

# Regras léxicas: mesmas da Frente 2C (estrutura de títulos) e da base mestra (traços simples).
ABSTRATO = re.compile(r"\b(vida|sucesso|verdade|mente|mindset|felicidade|amor|sonho|proposito|liberdade|futuro|sabedoria|life|success|truth|mind|happiness|love|dream|purpose|freedom|future|wisdom|motivation|motivacao|reflexao|energia|energy|universo|universe|destino|fate|meaning|sentido)\b")
PRIMEIRA = re.compile(r"^(eu|i|we|nos)\b|\b(eu|meu|minha|meus|minhas|i|my|me|we|our|nossa|nosso)\b")
ENTIDADES = re.compile(r"\b(iphone|samsung|galaxy|apple|google|pixel|xiaomi|elon|musk|trump|lula|bolsonaro|mrbeast|neymar|messi|ronaldo|cristiano|nasa|tesla|chatgpt|openai|nvidia|minecraft|gta|fortnite|roblox|nintendo|switch|playstation|ps5|xbox|pokemon|disney|netflix|marvel|batman|harry potter|amazon|shein|mcdonald|ikea|walmart|costco|bitcoin|nubank|itau|petrobras|vale|copa|world cup|nba|nfl|ufc|f1|formula 1|brasil|brazil|eua|usa|china|japao|japan|russia|ucrania|ukraine|israel)\b")
CONTRA = re.compile(r"\bna verdade\b|\bactually\b|\bmentira|\bmito|\bmyth|\berrad|\bwrong\b|\bpare de\b|\bstop\b|\bnao (faca|compre|use|e)\b|\bdon'?t\b|\bnunca\b|\bnever\b|\bnot what\b|\bninguem\b|\bnobody\b|\bfake\b|\bgolpe\b|\bscam\b|\boverrated\b|\bsuperestimad|\bisn'?t\b")
COLAB = re.compile(r"\bft\.?\b|\bfeat\.?\b|\bvs\.?\b|\bx\b|@", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\U0001F1E6-\U0001F1FF]")
PERGUNTA = re.compile(r"\?")
COMO = re.compile(r"^(como|how to|how i|how we)\b|\bhow to\b|\btutorial\b|\bpasso a passo\b|\bstep by step\b")

# Palavras das notas de capa -> nome do padrão na Frente 2B (padroes_stats.csv)
CAPA_MAPA = [
    (r"sem rosto|no face|faceless|sem pessoa", "Sem rosto"),
    (r"rosto grande|close|rosto em destaque|big face", "Rosto grande"),
    (r"surpres|chocad|shock|surpris", "Expressão surpresa"),
    (r"raiva|bravo|angry", "Expressão raiva"),
    (r"medo|assustad|fear|scared", "Expressão medo"),
    (r"sorri|feliz|smil", "Expressão feliz"),
    (r"serio|seria|concentrad|serious", "Expressão seria"),
    (r"olhando para a camera|olhar para a camera|looking at (the )?camera", "Olhar para a câmera"),
    (r"fundo escuro|escura|escuro|dark", "Escura (bottom 20% brilho)"),
    (r"clara|claro|bright|fundo branco", "Clara (top 20% brilho)"),
    (r"verde|green", "Cor dominante verde"),
    (r"azul|blue", "Cor dominante azul"),
    (r"vermelh|red\b", "Cor dominante vermelho"),
    (r"amarel|yellow", "Cor dominante amarelo"),
    (r"ciano|cyan|turquesa", "Cor dominante ciano"),
    (r"roxo|rosa|purple|pink", "Cor dominante roxo_rosa"),
    (r"laranja|orange", "Cor dominante laranja"),
    (r"preto|black", "Cor dominante preto"),
    (r"produto|objeto|gadget|aparelho|celular|product|object|smartphone", "Objeto em destaque"),
    (r"seta|circulo|arrow|circle", "Seta ou círculo"),
    (r"sem texto|no text", "Sem texto"),
    (r"texto curto|1-3 palavras|poucas palavras|uma palavra|duas palavras|tres palavras|short text", "Texto 1-3 palavras"),
    (r"muito texto|7\+ palavras|frase longa|long text", "Texto 7+ palavras"),
    (r"caixa alta|caps|maiuscul", "Texto em CAIXA ALTA (OCR)"),
    (r"antes e depois|antes-depois|antes/depois|comparac|before.?after|versus|\bvs\b", "Comparação/antes-depois"),
    (r"tela dividida|split", "Tela dividida (CV)"),
    (r"dinheiro|cifr|numero|money|\$|valor", "Número/dinheiro visível"),
    (r"ilustra|desenho|cartoon|illustrat", "Estilo ilustracao"),
    (r"\b3d\b", "Estilo 3d"),
    (r"montagem|colagem|collage", "Estilo montagem"),
    (r"\bfoto\b|fotografia|photo", "Estilo foto"),
    (r"letterbox|barras pretas|black bars", "Barras pretas (letterbox)"),
    (r"desfocad|blur|bokeh", "Fundo desfocado (top 20%)"),
    (r"fundo liso|fundo solido|plain background|fundo limpo", "Fundo liso"),
    (r"saturad|vibrante|saturat", "Saturação alta (top 20%)"),
    (r"alto contraste|contrastad|high contrast", "Contraste global alto (top 20%)"),
    (r"esquerda|left", "Peso visual à esquerda"),
    (r"poluid|carregad|cluttered|busy", "Visual poluído (top 20% bordas)"),
    (r"minimal|limpo|clean", "Visual limpo (bottom 20% bordas)"),
]
MITOS_CAPA = ["Rosto grande", "Expressão surpresa", "Seta ou círculo", "Sem rosto", "Saturação alta (top 20%)", "Contraste global alto (top 20%)"]


# ---------------------------------------------------------------- utilidades
def norm(s: str) -> str:
    return unicodedata.normalize("NFKD", (s or "").lower()).encode("ascii", "ignore").decode()


def _radical(t: str) -> str:
    """Radical mínimo (plural simples PT/EN) para a busca lexical."""
    if len(t) > 4 and t.endswith("oes"):
        return t[:-3] + "ao"
    if len(t) > 4 and t.endswith("es") and t[-3] in "rlsz":
        return t[:-2]
    if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
        return t[:-1]
    return t


def tokens(s: str) -> list[str]:
    return [_radical(t) for t in re.findall(r"[a-z0-9]+", norm(s)) if t not in STOP and len(t) > 1]


def conf_txt(c: str | None) -> str:
    return {"Alto": "alta", "Médio": "média", "Baixo": "baixa"}.get(c or "", c or "n/d")


def fmt_pct(v: float | None, casas: int = 1) -> str:
    if v is None:
        return "n/d"
    s = f"{v:+.{casas}f}%".replace(".", ",")
    return s.replace("-", "−")


def fmt_num(v: float | None, casas: int = 1) -> str:
    if v is None:
        return "n/d"
    if casas == 0:
        return f"{v:,.0f}".replace(",", ".")
    return f"{v:.{casas}f}".replace(".", ",")


def fmt_q(q: float | None) -> str:
    if q is None:
        return "q n/d"
    return "q < 0,001" if q < 0.001 else f"q = {q:.3f}".replace(".", ",")


def ic_txt(ic: list | None) -> str:
    if not ic or ic[0] is None:
        return ""
    return f"IC 95% {fmt_pct(ic[0])} a {fmt_pct(ic[1])}"


def interp(curva: list[list[float]], x: float) -> float | None:
    """Interpolação linear em log(x) de uma curva [[x, y, ...], ...]."""
    pts = [(p[0], p[1]) for p in curva if p[0] and p[1] is not None]
    if not pts:
        return None
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    lx = math.log(x)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            t = (lx - math.log(x0)) / (math.log(x1) - math.log(x0))
            return y0 + t * (y1 - y0)
    return None


@lru_cache(maxsize=4)
def carregar_kb(caminho: str | None = None) -> dict:
    return json.loads(Path(caminho or KB_PADRAO).read_text(encoding="utf-8"))


def resolver(valor: str, tabela: dict[str, list[str]], nome: str) -> str:
    v = norm(valor).strip()
    for chave, aliases in tabela.items():
        if v == chave or v in aliases:
            return chave
    raise ValueError(f"{nome} desconhecido: {valor!r}. Use um de: {', '.join(tabela)}")


def porte_por_inscritos(n: int) -> str:
    if n < 50_000:
        return "pequeno"
    if n < 200_000:
        return "emergente"
    if n < 2_000_000:
        return "medio"
    if n < 10_000_000:
        return "grande"
    return "gigante"


# ---------------------------------------------------------------- entrada
@dataclass
class Ideia:
    titulo: str
    nicho: str
    idioma: str = "pt"
    porte: str = "pequeno"
    duracao_min: float | None = None
    thumb_notes: str = ""
    texto_capa: str | None = None
    dias_desde_ultimo: float | None = None
    ultimo_resultado: str | None = None  # "hit", "flop" ou "normal"
    titulos_recentes: list[str] = field(default_factory=list)

    def normalizar(self) -> "Ideia":
        self.nicho = resolver(self.nicho, NICHOS, "nicho")
        self.porte = resolver(self.porte, PORTES, "porte")
        self.idioma = "en" if norm(self.idioma).startswith("en") else "pt"
        if not self.titulo or not self.titulo.strip():
            raise ValueError("título vazio")
        if self.texto_capa is None:
            m = re.search(r"texto\s*[:=]\s*[\"“']([^\"”']+)[\"”']", self.thumb_notes or "", re.I)
            if m:
                self.texto_capa = m.group(1)
        if self.ultimo_resultado:
            self.ultimo_resultado = norm(self.ultimo_resultado)
            if self.ultimo_resultado not in ("hit", "flop", "normal"):
                raise ValueError("ultimo_resultado deve ser hit, flop ou normal")
        return self


# ---------------------------------------------------------------- busca TF-IDF
class IndiceReferencias:
    def __init__(self, kb: dict):
        ref = kb["referencias"]
        self.campos = ref["campos"]
        self.linhas = ref["linhas"]
        self.docs = [self._feat(l[0]) for l in self.linhas]
        df = Counter()
        for d in self.docs:
            df.update(set(d))
        n = len(self.docs)
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
        self.vecs = [self._vec(d) for d in self.docs]

    @staticmethod
    def _feat(titulo: str) -> list[str]:
        tk = tokens(titulo)
        return tk + [f"{a}_{b}" for a, b in zip(tk, tk[1:])]

    def _vec(self, feats: list[str]) -> dict[str, float]:
        tf = Counter(feats)
        v = {t: (1 + math.log(c)) * self.idf.get(t, math.log(len(self.docs) + 1) + 1) for t, c in tf.items()}
        nrm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / nrm for t, x in v.items()}

    def buscar(self, titulo: str, nicho: str, idioma: str, porte: str, k: int = 5) -> list[dict]:
        q = self._vec(self._feat(titulo))
        grupo = GRUPO[porte]
        cands = []
        for i, l in enumerate(self.linhas):
            if l[2] != nicho:
                continue
            v = self.vecs[i]
            cos = sum(w * v.get(t, 0.0) for t, w in q.items())
            bonus = (0.05 if l[3] == idioma else 0) + (0.03 if GRUPO[l[4]] == grupo else 0) + (0.02 if l[4] == porte else 0)
            cands.append((cos + bonus * (1 if cos > 0 else 0.5), cos, i))
        cands.sort(reverse=True)
        out = []
        for score, cos, i in cands[:k]:
            d = dict(zip(self.campos, self.linhas[i]))
            d["similaridade"] = round(cos, 3)
            out.append(d)
        return out


@lru_cache(maxsize=2)
def _indice(caminho: str) -> IndiceReferencias:
    return IndiceReferencias(carregar_kb(caminho))


def similaridade_cos(a: str, b: str) -> float:
    ta, tb = Counter(tokens(a)), Counter(tokens(b))
    if not ta or not tb:
        return 0.0
    num = sum(ta[t] * tb[t] for t in ta)
    return num / (math.sqrt(sum(v * v for v in ta.values())) * math.sqrt(sum(v * v for v in tb.values())))


# ---------------------------------------------------------------- consultas ao KB
def _linha(lista: list[dict], **filtros) -> dict | None:
    for l in lista:
        if all(l.get(k) == v for k, v in filtros.items()):
            return l
    return None


def _traco(kb, variavel, amostra="todos"):
    return _linha(kb["titulo"]["tracos_200k"]["linhas"], variavel=variavel, amostra=amostra)


def _peq(kb, variavel):
    return _linha(kb["titulo"]["pequenos_vs_200k"]["linhas"], variavel=variavel)


def _padrao(kb, nome):
    return kb["thumbnail"]["padroes"].get(nome)


# ---------------------------------------------------------------- seções
def secao_diagnostico(kb, ideia: Ideia, alertas: list[str], favor: list[str]) -> dict:
    meta = kb["meta"]
    cel = kb["nicho_idioma"]["celulas"].get(f"{ideia.nicho}|{ideia.idioma}|{GRUPO[ideia.porte]}", {})
    porte = kb["portes"][ideia.porte]
    canais = cel.get("canais", 0)
    cobertura = "boa" if canais >= 8 else ("limitada" if canais >= 4 else "fraca")
    grau = "baixo a moderado" if alertas or cobertura != "boa" else "moderado"
    teto = meta["teto_preditivo"]
    return {
        "grau_de_confianca": grau,
        "cobertura_da_celula": {"nicho": ideia.nicho, "idioma": ideia.idioma, "grupo": GRUPO[ideia.porte], "canais": canais,
                                 "videos": cel.get("videos", 0), "avaliacao": cobertura},
        "pontos_a_favor": favor,
        "riscos": alertas,
        "contexto_do_porte": {
            "porte": ideia.porte, "faixa": meta["faixas_porte"][ideia.porte],
            "views_mediana_video": porte["views_mediana_video"], "top10_share_pct": porte["top10_share"],
            "anomalias_10x_por_mil": porte["anomalias_10x_por_mil"], "dp_y": porte["dp_y"],
            "intervalo_mediano_dias": porte["intervalo_mediano_dias"],
        },
        "teto_preditivo": (
            f"Teto da base: o título explica no máximo R² {fmt_num(teto['titulo_r2_oos_melhor'], 3)} fora da amostra, "
            f"embeddings da capa R² {fmt_num(teto['thumb_r2_oos_intra_canal_embeddings'], 3)} dentro do canal, e o melhor modelo acerta o top 5% "
            f"do próprio canal com AUC {fmt_num(teto['ml_auc_top5_canal_canais_novos'], 3)} (0,5 é moeda). Este parecer ordena escolhas, não prevê views "
            "e nunca promete viralização."),
        "limites": meta["limites"],
    }


def secao_duracao(kb, ideia: Ideia, alertas, favor) -> dict:
    du = kb["duracao"]
    res = du["resumo_200k"]
    chave = f"nicho={ideia.nicho}"
    rn = res.get(f"{chave}|yw", {})
    rp = res.get(f"porte={ideia.porte}|yw") if GRUPO[ideia.porte] == "200k+" else None
    curva_n = du["curvas_200k_ref_12min"]["grupos"].get(chave, [])
    curva_p = du["curvas_pequenos_vs_200k"]["grupos"].get("pequenos" if GRUPO[ideia.porte] == "pequenos" else "200k+", [])
    # faixa ótima: duração onde a curva do nicho fica a 85% ou mais do pico (dentro dos dados)
    faixa = None
    if curva_n:
        pico = max(p[1] for p in curva_n)
        if pico > 0:
            ok = [p[0] for p in curva_n if p[1] >= 0.85 * pico]
            faixa = [round(min(ok)), round(max(ok))]
    if ideia.nicho == "tech" and faixa:
        faixa[1] = min(faixa[1], 30)
    emp = du["empirico_nicho_porte"]["celulas"].get(f"{ideia.nicho}|{ideia.porte}", {})
    faixas_emp = [f for f in emp.get("faixas", []) if f["canais"] >= 3 and f["n"] >= 20]
    melhor_emp = max(faixas_emp, key=lambda f: f["pct_3x"], default=None)
    out = {
        "otimo_nicho_200k": {"otimo_min": rn.get("otimo_min"), "ic": rn.get("otimo_ic"), "na_borda": rn.get("otimo_na_borda"),
                              "retorno_decrescente_min": rn.get("retorno_decrescente_min"), "q": rn.get("q_bh")},
        "otimo_porte_200k": rp,
        "faixa_recomendada_min": faixa,
        "celula_empirica": {"nicho": ideia.nicho, "porte": ideia.porte, "videos": emp.get("n"), "canais": emp.get("canais"),
                             "duracao_mediana": emp.get("duracao_mediana"), "duracao_mediana_top10_canal": emp.get("duracao_mediana_top10_canal"),
                             "melhor_faixa_por_pct_3x": melhor_emp},
        "notas": [],
    }
    notas = out["notas"]
    if ideia.duracao_min:
        d = ideia.duracao_min
        en = interp(curva_n, d)
        ep = interp(curva_p, d)
        e12n = 0.0
        out["proposta"] = {"duracao_min": d, "efeito_curva_nicho_vs_12min": None if en is None else round(en - e12n, 1),
                           "efeito_curva_porte": None if ep is None else round(ep, 1)}
        f_emp = next((f for f in emp.get("faixas", []) if f["lo"] <= d and (f["hi"] is None or d < f["hi"])), None)
        out["proposta"]["faixa_empirica"] = f_emp
        if faixa:
            if d < faixa[0]:
                alertas.append(f"Duração de {fmt_num(d, 0)} min abaixo da faixa forte do nicho ({faixa[0]} a {faixa[1]} min).")
            elif d > faixa[1]:
                alertas.append(f"Duração de {fmt_num(d, 0)} min acima da faixa forte do nicho ({faixa[0]} a {faixa[1]} min); só vale se o tema sustentar retenção.")
            else:
                favor.append(f"Duração de {fmt_num(d, 0)} min dentro da faixa forte do nicho ({faixa[0]} a {faixa[1]} min).")
        if d < 6:
            alertas.append("Vídeos de 3 a 6 min rendem cerca de 23% a 27% menos que 10 a 15 min do mesmo canal (pequenos e 200k+).")
        if ideia.nicho == "tech" and d > 30:
            alertas.append("Tech é o único nicho com inclinação negativa: 60 min rende cerca de 48% menos que 12 min nos 200k+.")
    if GRUPO[ideia.porte] == "pequenos":
        notas.append("Nos pequenos, dobrar a duração soma +30,2% dentro do canal (IC +19,7% a +41,6%) contra +14,9% nos 200k+, e duração é o único traço ligado a breakouts de 10x (+1,7 p.p. por dobro).")
        notas.append("Acima de 60 min a curva dos pequenos é puxada por formatos específicos (filmes completos, júris integrais, icebergs). Até 30 min o efeito é sólido.")
    else:
        notas.append("Nos 200k+, contra 8 a 20 min: 20 a 45 min +25,1% (q < 0,001); menos de 5 min −33,5%. O ótimo para topo do canal (72 min) é o dobro do ótimo para média (34 min): vídeo muito longo aumenta a variância.")
    notas.append("Duração relativa ao hábito do próprio canal pesa tanto quanto a absoluta. Não estique: o ganho supõe retenção real, que a base não mede.")
    return out


def analisar_titulo(titulo: str) -> dict:
    n = norm(titulo)
    palavras_caps = [w for w in re.findall(r"[A-Za-zÀ-ÿ]+", titulo) if len(w) >= 3 and w.isupper() and w.isalpha()]
    return {
        "caracteres": len(titulo), "palavras": len(titulo.split()),
        "abstrato": sorted(set(ABSTRATO.findall(n))),
        "primeira_pessoa": bool(PRIMEIRA.search(n)),
        "entidade_famosa": sorted(set(m if isinstance(m, str) else m[0] for m in ENTIDADES.findall(n))),
        "contraintuitivo": bool(CONTRA.search(n)),
        "numero": bool(re.search(r"\d", titulo)),
        "palavra_caixa_alta": palavras_caps,
        "colab_vs": bool(COLAB.search(titulo)),
        "emoji": bool(EMOJI.search(titulo)),
        "pergunta": bool(PERGUNTA.search(titulo)),
        "como_tutorial": bool(COMO.search(n)),
    }


def secao_titulo(kb, ideia: Ideia, alertas, favor) -> dict:
    t = analisar_titulo(ideia.titulo)
    pequeno = GRUPO[ideia.porte] == "pequenos"
    achados, nao_importa = [], []
    ab = _traco(kb, "abstrato")
    if t["abstrato"]:
        alertas.append(f"Vocabulário abstrato no título ({', '.join(t['abstrato'])}): {fmt_pct(ab['efeito'])} no múltiplo do canal ({fmt_q(ab['q'])}).")
        achados.append({"traco": "vocabulário abstrato", "presente": True, "efeito": ab["efeito"], "ic": ab["ic"], "q": ab["q"], "confianca": "média",
                        "acao": "Troque palavras abstratas por objeto, número, nome ou cena concreta."})
    pp = _traco(kb, "primeira_pessoa", "en")
    if ideia.idioma == "en":
        if t["primeira_pessoa"]:
            alertas.append(f"1ª pessoa em título EN: {fmt_pct(pp['efeito'])} ({fmt_q(pp['q'])}).")
        achados.append({"traco": "1ª pessoa (EN)", "presente": t["primeira_pessoa"], "efeito": pp["efeito"], "ic": pp["ic"], "q": pp["q"], "confianca": "média",
                        "acao": "Tire o I/my do começo e ponha a premissa ou o objeto no centro." if t["primeira_pessoa"] else "Ok: premissa no centro."})
    else:
        ppt = _traco(kb, "primeira_pessoa", "pt")
        nao_importa.append(f"1ª pessoa em PT: {fmt_pct(ppt['efeito'])} ({fmt_q(ppt['q'])}), nulo.")
    if ideia.nicho in ("tech", "games"):
        ent = _traco(kb, "h_autoridade_entidade", "tech_games")
        if t["entidade_famosa"]:
            favor.append(f"Marca ou produto famoso no título ({', '.join(t['entidade_famosa'])}): {fmt_pct(ent['efeito'])} em tech e games ({fmt_q(ent['q'])}).")
        else:
            alertas.append("Tech e games sem marca ou produto famoso no título; citar o nome que o público busca se associa a +25,5%.")
        achados.append({"traco": "marca/produto famoso (tech e games)", "presente": bool(t["entidade_famosa"]), "efeito": ent["efeito"], "ic": ent["ic"], "q": ent["q"], "confianca": "média"})
    gl = kb["titulo"]["ganchos_principais_vs_descritivo"]["linhas"]
    ci = _linha(gl, gancho="contraintuitivo", amostra=ideia.idioma)
    if ci:
        conf = "média" if ideia.idioma == "en" else "baixa (efeito não confirmado em PT)"
        achados.append({"traco": "afirmação contraintuitiva como gancho", "presente": t["contraintuitivo"], "efeito": ci["efeito"], "ic": ci["ic"], "q": ci["q"], "confianca": conf,
                        "acao": ("Bom em EN." if ideia.idioma == "en" else "Em PT, só como teste A/B controlado.")})
        if t["contraintuitivo"] and ideia.idioma == "en":
            favor.append(f"Afirmação contraintuitiva em EN: {fmt_pct(ci['efeito'])} ({fmt_q(ci['q'])}).")
    if pequeno:
        for var, chave, rot in (("tem_numero", "numero", "número no título"), ("tem_palavra_caps", "palavra_caixa_alta", "palavra em CAIXA ALTA"),
                                ("tem_colab", "colab_vs", "colab/versus no título")):
            l = _peq(kb, var)
            presente = bool(t[chave])
            achados.append({"traco": rot + " (pequenos)", "presente": presente, "efeito": l["pequenos"], "ic": l["pequenos_ic"], "q": l["pequenos_q"],
                            "confianca": "baixa (diferença contra 200k+ não confirmada; pode ser causalidade reversa)"})
            if var == "tem_colab" and presente:
                alertas.append(f"Colab/versus no título em canal pequeno: {fmt_pct(l['pequenos'])} ({fmt_q(l['pequenos_q'])}, confiança baixa).")
        l10 = _peq(kb, "titulo_10chars")
        achados.append({"traco": "+10 caracteres (pequenos)", "presente": None, "efeito": l10["pequenos"], "ic": l10["pequenos_ic"], "q": l10["pequenos_q"], "confianca": "baixa"})
    else:
        nao_importa.append("Comprimento do título: nenhuma faixa difere de 46 a 60 caracteres nos 200k+ (q > 0,93).")
    if ideia.idioma == "pt":
        em = _traco(kb, "emoji", "pt")
        achados.append({"traco": "emoji (PT)", "presente": t["emoji"], "efeito": em["efeito"], "ic": em["ic"], "q": em["q"], "confianca": "baixa (concentrado em 45 canais)"})
    pq = _peq(kb, "tem_pergunta")
    nao_importa.append(f"Pergunta no título: {fmt_pct(pq['grandes'])} nos 200k+ e {fmt_pct(pq['pequenos'])} nos pequenos, nulo (mas aumenta comentários por view).")
    nao_importa.append("Lista, tutorial, mistério, urgência e lacuna de curiosidade: IC cruzando zero na base toda.")
    return {"tracos_detectados": t, "achados": achados, "o_que_nao_importa": nao_importa,
            "nota": "O título é filtro fino, não alavanca: o melhor modelo de título tem R² fora da amostra de 0,018."}


def secao_thumb(kb, ideia: Ideia, alertas, favor) -> dict:
    notas = norm(ideia.thumb_notes or "")
    detectados = []
    vistos = set()
    for rx, nome in CAPA_MAPA:
        if nome in vistos:
            continue
        if re.search(rx, notas):
            if nome == "Rosto grande" and "sem rosto" in notas:
                continue
            if nome == "Clara (top 20% brilho)" and re.search(r"escur|dark", notas) and not re.search(r"fundo branco|bright", notas):
                continue
            p = _padrao(kb, nome)
            if p:
                vistos.add(nome)
                detectados.append({"padrao": nome, "efeito_intra_canal": p["efeito"], "ic": p["ic"], "q": p["q"], "efeito_ingenuo": p["efeito_ingenuo"], "confianca": conf_txt(p["confianca"])})
    for d in detectados:
        if d["q"] is not None and d["q"] < 0.15 and d["efeito_intra_canal"] > 0:
            favor.append(f"Capa com '{d['padrao']}': {fmt_pct(d['efeito_intra_canal'])} dentro do canal ({fmt_q(d['q'])}, confiança {d['confianca']}).")
        if d["padrao"] in ("Barras pretas (letterbox)", "Cor dominante ciano") or (d["efeito_intra_canal"] <= -9 and (d["q"] or 1) < 0.6):
            alertas.append(f"Capa com '{d['padrao']}': {fmt_pct(d['efeito_intra_canal'])} dentro do canal ({fmt_q(d['q'])}, confiança {d['confianca']}).")
    pn = kb["thumbnail"]["por_nicho"].get(ideia.nicho, {})
    rec_global = [p for p in kb["thumbnail"]["ranking"]["melhores"] if p["confianca"] in ("Médio", "Alto") and p["canais"] >= 10]
    raros = [r for r in kb["thumbnail"]["raros"]["linhas"] if r["tipo"] == "combinacao"][:5]
    alinh = None
    if ideia.texto_capa:
        s = similaridade_cos(ideia.titulo, ideia.texto_capa)
        nivel = "alto" if s >= 0.35 else ("médio" if s >= 0.12 else "baixo")
        alinh = {"texto_capa": ideia.texto_capa, "similaridade_lexical": round(s, 3), "nivel": nivel}
        if nivel == "baixo":
            alertas.append("Texto da capa quase sem relação lexical com o título; alinhar a mesma ideia tende a ser melhor (+4,1% por DP de similaridade, q = 0,034).")
        else:
            favor.append("Texto da capa reforça a ideia do título (alinhamento semântico se associa a +4,1% por DP, q = 0,034).")
    mitos = []
    for m in MITOS_CAPA:
        p = _padrao(kb, m)
        if p:
            mitos.append({"padrao": m, "efeito_ingenuo_entre_canais": p["efeito_ingenuo"], "efeito_intra_canal": p["efeito"], "q": p["q"]})
    out = {
        "padroes_detectados_nas_notas": detectados,
        "recomendados_no_nicho": pn.get("melhores", [])[:5],
        "evitar_no_nicho": pn.get("piores", [])[:3],
        "padroes_de_confianca_media_na_base": [{"padrao": p["nome"], "efeito": p["efeito"], "ic": p["ic"], "q": p["q"], "canais": p["canais"]} for p in rec_global],
        "hipoteses_raras_testaveis": [{"padrao": r["nome"], "efeito": r["efeito"], "ic": r["ic"], "canais": r["canais"], "q": r["q"]} for r in raros],
        "alinhamento_titulo_capa": alinh,
        "mitos_a_ignorar": mitos,
        "notas": [
            "Por nicho, nenhum padrão de capa sobrevive com folga à correção de múltiplos testes; use como ponto de partida de teste A/B.",
            "Repetir o título na capa não é punido (+1,1%, IC −9,5% a +13,4%). O que tende a perder é texto sem relação com o título.",
        ],
    }
    if GRUPO[ideia.porte] == "pequenos":
        out["notas"].append("Breakouts de canais pequenos têm menos rosto do que os controles do mesmo canal (72,9% contra 81,5%, q < 0,001): venda o assunto, não o criador.")
        out["notas"].append("Imitar a cara de capa de canal grande não rende (−2,6% por DP, q = 0,30). Fugir do visual habitual do próprio canal custa −10,9% por DP (q < 0,001).")
    else:
        out["notas"].append("Fugir do visual habitual do próprio canal custa −7,4% por DP nos 200k+ (q < 0,001).")
    if not ideia.thumb_notes:
        out["notas"].append("Sem notas de capa: descreva fundo, cor, rosto, texto e objeto para receber a leitura dos padrões.")
    return out


def secao_cadencia(kb, ideia: Ideia, alertas, favor) -> dict:
    cad = kb["cadencia"]
    grupo = GRUPO[ideia.porte]
    out: dict[str, Any] = {"notas": []}
    faixas = [f for f in cad["intervalo_faixas_ref_5a9d"] if f["grupo"] == ("pequenos" if grupo == "pequenos" else "200k_mais")]
    out["intervalo_por_faixa_ref_5a9d"] = faixas
    d = ideia.dias_desde_ultimo
    if d is not None:
        curva = cad["intervalo_200k_ref_7d"]["grupos"].get(f"porte={ideia.porte}") or cad["intervalo_200k_ref_7d"]["grupos"]["geral"]
        out["dias_desde_ultimo"] = d
        out["efeito_curva_200k_vs_7d"] = round(interp(curva, max(d, 0.1)) or 0, 1)
        if d < 2:
            f = _linha(faixas, faixa="<2d")
            if grupo == "200k+":
                alertas.append(f"Menos de 2 dias desde o vídeo anterior em canal 200k+: {fmt_pct(f['efeito'])} ({fmt_q(f['q'])}). Espere pelo menos 3 dias.")
            else:
                out["notas"].append(f"Menos de 2 dias em canal pequeno: {fmt_pct(f['efeito'])} ({fmt_q(f['q'])}), inconclusivo. A penalidade só é clara nos 200k+.")
        elif d >= 3:
            favor.append(f"Intervalo de {fmt_num(d, 0)} dias desde o vídeo anterior (fora da zona de risco de menos de 3 dias).")
    if ideia.ultimo_resultado == "flop":
        l = _linha(cad["pos_extremo_x_intervalo"], modelo="bot_prev", termo="bot_prev")
        if d is not None and d < 3:
            alertas.append(f"Publicar menos de 3 dias depois de um fracasso: {fmt_pct(l['efeito'])} (IC {fmt_pct(l['ic'][0])} a {fmt_pct(l['ic'][1])}). Esperar 3 a 10 dias neutraliza.")
        else:
            out["notas"].append("Depois de um fracasso, esperar 3 a 10 dias neutraliza a queda de −17,8% observada ao lançar em menos de 3 dias.")
    elif ideia.ultimo_resultado == "hit":
        m = _linha(cad["momentum"], grupo="pequenos" if grupo == "pequenos" else "200k_mais", condicao="prev_top5")
        out["notas"].append(f"Depois de um hit, o vídeo seguinte tende a {fmt_pct(m['efeito'])} ({ic_txt(m['ic'])}) se ficar no mesmo veio; nos 200k+ isso é quase todo fase do canal. Pressa ou espera não trazem ganho específico (p = 0,58).")
    vol = _linha(cad["volume_recente"], grupo="geral", variavel="log_n7", desfecho="yw")
    out["notas"].append(f"Dobrar o número de vídeos nos 7 dias anteriores se associa a {fmt_pct(vol['efeito_por_dobro'])} ({fmt_q(vol['q'])}) nos 200k+.")
    out["notas"].append("Dia e horário de publicação não importam no agregado (nada sobrevive à correção em nenhum porte).")
    nov_txt = "−14,8% por DP nos pequenos e −10,5% nos 200k+ (p < 0,001); novidade não aumenta a chance de 10x."
    out["consistencia_tematica"] = {"regra": f"Fugir do tema habitual do canal reduz views: {nov_txt}"}
    if ideia.titulos_recentes:
        sims = [similaridade_cos(ideia.titulo, t) for t in ideia.titulos_recentes]
        media = sum(sims) / len(sims)
        base = []
        for i, t in enumerate(ideia.titulos_recentes):
            outros = ideia.titulos_recentes[:i] + ideia.titulos_recentes[i + 1:]
            if outros:
                base.append(sum(similaridade_cos(t, o) for o in outros) / len(outros))
        ref = sum(base) / len(base) if base else None
        out["consistencia_tematica"].update({"similaridade_media_com_recentes": round(media, 3), "referencia_entre_recentes": None if ref is None else round(ref, 3)})
        if ref is not None and media < 0.5 * ref:
            alertas.append("Título lexicalmente distante dos vídeos recentes do canal: risco de desvio temático (−10,5% a −14,8% por DP de novidade).")
    return out


def secao_exemplos(kb, ideia: Ideia, caminho_kb: str) -> list[dict]:
    idx = _indice(caminho_kb)
    return idx.buscar(ideia.titulo, ideia.nicho, ideia.idioma, ideia.porte, k=5)


def secao_checklist(ideia: Ideia, dur: dict, tit: dict, thumb: dict, cad: dict) -> list[str]:
    c = []
    f = dur.get("faixa_recomendada_min")
    if f:
        c.append(f"Roteiro que sustente {f[0]} a {f[1]} min sem enchimento (faixa forte do nicho {ideia.nicho}).")
    t = tit["tracos_detectados"]
    if t["abstrato"]:
        c.append("Trocar as palavras abstratas do título por objeto, número, nome ou cena concreta.")
    if ideia.idioma == "en" and t["primeira_pessoa"]:
        c.append("Reescrever o título sem I/my no centro; a premissa vem primeiro.")
    if ideia.nicho in ("tech", "games") and not t["entidade_famosa"]:
        c.append("Citar no título a marca, produto ou jogo que o público procura.")
    c.append("Colocar a palavra-chave principal no início do título (+1,3 p.p. de chance de top 5% do canal, q = 0,023).")
    c.append("Texto da capa curto e reforçando a mesma ideia do título; nada de assunto paralelo.")
    if GRUPO[ideia.porte] == "pequenos":
        c.append("Capa centrada no assunto (objeto, cena, situação), mantendo o padrão visual do canal.")
        c.append("Teste A/B (Testar e comparar do YouTube) entre título com número/CAIXA ALTA e versão neutra: sinal de +15% com confiança baixa.")
    else:
        c.append("Manter a identidade visual do canal; testar no máximo 1 variação de capa por vez.")
    if cad.get("dias_desde_ultimo") is not None and cad["dias_desde_ultimo"] < 3:
        c.append("Reagendar para pelo menos 3 dias depois do vídeo anterior.")
    if ideia.ultimo_resultado == "flop":
        c.append("Último vídeo fraco: não lançar em menos de 3 dias.")
    c.append("Subir legenda própria (associação de +28,6% nos 200k+, com risco de causalidade reversa) e capítulos como experiência do usuário, não como alavanca.")
    c.append("Depois de publicar, comparar CTR e retenção no YouTube Studio com a mediana do canal: é o dado que esta base não tem.")
    return c


# ---------------------------------------------------------------- orquestração
def aconselhar(ideia: Ideia, kb_path: str | Path | None = None) -> dict:
    caminho = str(kb_path or KB_PADRAO)
    kb = carregar_kb(caminho)
    ideia.normalizar()
    alertas: list[str] = []
    favor: list[str] = []
    dur = secao_duracao(kb, ideia, alertas, favor)
    tit = secao_titulo(kb, ideia, alertas, favor)
    thumb = secao_thumb(kb, ideia, alertas, favor)
    cad = secao_cadencia(kb, ideia, alertas, favor)
    ex = secao_exemplos(kb, ideia, caminho)
    diag = secao_diagnostico(kb, ideia, alertas, favor)
    return {
        "ideia": asdict(ideia),
        "base": {"videos": kb["meta"]["videos"], "canais": kb["meta"]["canais"], "versao_kb": kb["meta"]["versao"]},
        "1_diagnostico": diag,
        "2_duracao": dur,
        "3_titulo": tit,
        "4_thumbnail": thumb,
        "5_cadencia": cad,
        "6_exemplos_reais": ex,
        "7_checklist": secao_checklist(ideia, dur, tit, thumb, cad),
    }


def para_markdown(p: dict) -> str:
    i = p["ideia"]
    d = p["1_diagnostico"]
    L = [f"# Parecer da ideia: {i['titulo']}", "",
         f"Nicho **{i['nicho']}**, idioma **{i['idioma'].upper()}**, porte **{i['porte']}** ({d['contexto_do_porte']['faixa']}). "
         f"Base: {fmt_num(p['base']['videos'], 0)} vídeos longos de {p['base']['canais']} canais.", "",
         "## 1. Diagnóstico geral", "",
         f"**Grau de confiança do parecer: {d['grau_de_confianca']}.** Cobertura da célula {i['nicho']} × {i['idioma'].upper()} × {d['cobertura_da_celula']['grupo']}: "
         f"{d['cobertura_da_celula']['canais']} canais e {fmt_num(d['cobertura_da_celula']['videos'], 0)} vídeos ({d['cobertura_da_celula']['avaliacao']}).", "",
         f"> {d['teto_preditivo']}", "> " + " ".join(d["limites"]), ""]
    cp = d["contexto_do_porte"]
    L.append(f"Contexto do porte {cp['porte']}: views medianas por vídeo {fmt_num(cp['views_mediana_video'], 0)}; top 10% dos vídeos somam {fmt_num(cp['top10_share_pct'])}% das views; "
             f"{fmt_num(cp['anomalias_10x_por_mil'])} vídeos de 10x ou mais por mil; intervalo mediano de {fmt_num(cp['intervalo_mediano_dias'])} dias.")
    L.append("")
    if d["pontos_a_favor"]:
        L += ["**A favor**", ""] + [f"- {x}" for x in d["pontos_a_favor"]] + [""]
    if d["riscos"]:
        L += ["**Riscos**", ""] + [f"- {x}" for x in d["riscos"]] + [""]
    du = p["2_duracao"]
    L += ["## 2. Duração", ""]
    if du.get("faixa_recomendada_min"):
        f = du["faixa_recomendada_min"]
        L.append(f"Faixa forte do nicho (curva dentro do canal, 200k+): **{f[0]} a {f[1]} min**.")
    o = du["otimo_nicho_200k"]
    if o.get("otimo_min"):
        borda = " (ótimo na borda dos dados)" if o.get("na_borda") else ""
        L.append(f"Ótimo do nicho: {fmt_num(o['otimo_min'], 0)} min (IC {fmt_num(o['ic'][0], 0)} a {fmt_num(o['ic'][1], 0)}){borda}; retorno decrescente a partir de cerca de {fmt_num(o['retorno_decrescente_min'], 0)} min; {fmt_q(o['q'])}.")
    if du.get("otimo_porte_200k"):
        op = du["otimo_porte_200k"]
        L.append(f"Ótimo do porte {i['porte']}: {fmt_num(op['otimo_min'], 0)} min (IC {fmt_num(op['otimo_ic'][0], 0)} a {fmt_num(op['otimo_ic'][1], 0)}).")
    if du.get("proposta"):
        pr = du["proposta"]
        L.append(f"Proposta de {fmt_num(pr['duracao_min'], 0)} min: curva do nicho {fmt_pct(pr['efeito_curva_nicho_vs_12min'])} contra 12 min do mesmo canal; curva do grupo de porte ({'pequenos' if GRUPO[i['porte']] == 'pequenos' else '200k+'}) {fmt_pct(pr['efeito_curva_porte'])} contra cerca de 12 min.")
        fe = pr.get("faixa_empirica")
        if fe:
            L.append(f"Na base real ({i['nicho']}, {i['porte']}), a faixa {fe['faixa']} min tem {fe['n']} vídeos de {fe['canais']} canais, múltiplo mediano {fmt_num(fe['mult_mediana'], 2)}x a mediana do canal e {fmt_num(fe['pct_3x'])}% com 3x ou mais.")
    ce = du["celula_empirica"]
    if ce.get("videos"):
        L.append(f"Duração mediana na célula: {fmt_num(ce['duracao_mediana'])} min; no top 10% de cada canal: {fmt_num(ce['duracao_mediana_top10_canal'])} min.")
        mb = ce.get("melhor_faixa_por_pct_3x")
        if mb:
            L.append(f"Faixa com mais vídeos de 3x na célula (3+ canais, 20+ vídeos): {mb['faixa']} min ({fmt_num(mb['pct_3x'])}%; descritivo, sem controle de idade).")
    L += [f"- {x}" for x in du["notas"]] + [""]
    t = p["3_titulo"]
    td = t["tracos_detectados"]
    L += ["## 3. Título", "", f"{td['caracteres']} caracteres, {td['palavras']} palavras. {t['nota']}", "",
          "| Traço | Presente | Efeito no múltiplo do canal | IC 95% | q | Confiança |", "|---|---|---:|---|---:|---|"]
    for a in t["achados"]:
        pres = "n/a" if a["presente"] is None else ("sim" if a["presente"] else "não")
        ic = f"{fmt_pct(a['ic'][0])} a {fmt_pct(a['ic'][1])}" if a.get("ic") and a["ic"][0] is not None else ""
        L.append(f"| {a['traco']} | {pres} | {fmt_pct(a['efeito'])} | {ic} | {fmt_q(a['q']).replace('q = ', '').replace('q ', '')} | {a['confianca']} |")
    L += ["", "**O que não importa**", ""] + [f"- {x}" for x in t["o_que_nao_importa"]] + [""]
    th = p["4_thumbnail"]
    L += ["## 4. Thumbnail e alinhamento título + capa", ""]
    if th["padroes_detectados_nas_notas"]:
        L.append("Padrões lidos nas notas da capa (efeito dentro do canal, 200k+):")
        L += [f"- {x['padrao']}: {fmt_pct(x['efeito_intra_canal'])} ({fmt_q(x['q'])}, confiança {x['confianca']}; comparação ingênua entre canais {fmt_pct(x['efeito_ingenuo'])})" for x in th["padroes_detectados_nas_notas"]]
        L.append("")
    if th["recomendados_no_nicho"]:
        L.append(f"Melhores sinais no nicho {i['nicho']} (q alto, usar como teste):")
        L += [f"- {x['nome']}: {fmt_pct(x['efeito'])} ({fmt_q(x['q'])}, {x['n']} vídeos)" for x in th["recomendados_no_nicho"]]
    if th["evitar_no_nicho"]:
        L.append("Sinais negativos no nicho: " + "; ".join(f"{x['nome']} {fmt_pct(x['efeito'])}" for x in th["evitar_no_nicho"]) + ".")
    L.append("Padrões de confiança média na base toda: " + "; ".join(f"{x['padrao']} {fmt_pct(x['efeito'])}" for x in th["padroes_de_confianca_media_na_base"]) + ".")
    L.append("Hipóteses raras para teste A/B: " + "; ".join(f"{x['padrao']} {fmt_pct(x['efeito'])} ({x['canais']} canais)" for x in th["hipoteses_raras_testaveis"]) + ".")
    al = th["alinhamento_titulo_capa"]
    if al:
        L.append(f"Alinhamento título ↔ texto da capa (\"{al['texto_capa']}\"): similaridade lexical {fmt_num(al['similaridade_lexical'], 2)}, nível {al['nivel']}.")
    L.append("Mitos a ignorar: " + "; ".join(f"{m['padrao']} (entre canais {fmt_pct(m['efeito_ingenuo_entre_canais'])}, dentro do canal {fmt_pct(m['efeito_intra_canal'])})" for m in th["mitos_a_ignorar"]) + ".")
    L += [f"- {x}" for x in th["notas"]] + [""]
    c = p["5_cadencia"]
    L += ["## 5. Cadência e consistência", ""]
    if "dias_desde_ultimo" in c:
        L.append(f"{fmt_num(c['dias_desde_ultimo'], 0)} {'dia' if c['dias_desde_ultimo'] == 1 else 'dias'} desde o vídeo anterior; curva dos 200k+ contra 7 dias: {fmt_pct(c['efeito_curva_200k_vs_7d'])}.")
    L.append("Faixas de intervalo do grupo (referência 5 a 9 dias): " + "; ".join(f"{f['faixa']} {fmt_pct(f['efeito'])} ({fmt_q(f['q'])})" for f in c["intervalo_por_faixa_ref_5a9d"]) + ".")
    L.append(c["consistencia_tematica"]["regra"])
    if "similaridade_media_com_recentes" in c["consistencia_tematica"]:
        ct = c["consistencia_tematica"]
        L.append(f"Similaridade com os títulos recentes: {fmt_num(ct['similaridade_media_com_recentes'], 2)} (entre os recentes: {fmt_num(ct['referencia_entre_recentes'], 2)}).")
    L += [f"- {x}" for x in c["notas"]] + [""]
    L += ["## 6. Exemplos reais parecidos de alto desempenho", "", "| Título | Canal | Porte | Idioma | Múltiplo vs mediana do canal | Views | Duração | Similaridade |", "|---|---|---|---|---:|---:|---:|---:|"]
    for e in p["6_exemplos_reais"]:
        tit = e["titulo"].replace("|", "/")
        L.append(f"| {tit} | {e['canal']} | {e['porte']} | {e['idioma'].upper()} | {fmt_num(e['mult'])}x | {fmt_num(e['views'], 0)} | {fmt_num(e['dur_min'])} min | {fmt_num(e['similaridade'], 2)} |")
    if p["6_exemplos_reais"] and max(e["similaridade"] for e in p["6_exemplos_reais"]) < 0.05:
        L.append("")
        L.append("Pouca sobreposição de palavras com os títulos de referência do nicho: os exemplos acima são os mais próximos disponíveis, não equivalentes diretos.")
    L += ["", "Exemplos são referências de tema e embalagem, não garantia: o múltiplo depende muito da volatilidade de cada canal.", "",
          "## 7. Checklist pré-publicação", ""] + [f"- [ ] {x}" for x in p["7_checklist"]]
    return "\n".join(L) + "\n"


def construir_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="idea_advisor", description="Parecer acionável para uma nova ideia de vídeo longo (sem API, sem rede).")
    ap.add_argument("--title", required=True, help="Título proposto")
    ap.add_argument("--niche", required=True, help="Nicho: " + ", ".join(NICHOS))
    ap.add_argument("--lang", default="pt", help="pt ou en")
    ap.add_argument("--tier", default=None, help="pequeno, emergente, medio, grande ou gigante")
    ap.add_argument("--subscribers", type=int, default=None, help="Inscritos (define o porte se --tier não vier)")
    ap.add_argument("--duration-min", type=float, default=None, help="Duração planejada em minutos")
    ap.add_argument("--thumb-notes", default="", help="Descrição livre da capa; texto da capa entre aspas após 'texto:'")
    ap.add_argument("--thumb-text", default=None, help="Texto que vai escrito na capa")
    ap.add_argument("--days-since-last", type=float, default=None, help="Dias desde o último vídeo longo")
    ap.add_argument("--last-result", choices=["hit", "flop", "normal"], default=None, help="Resultado do último vídeo")
    ap.add_argument("--recent-titles", default=None, help="Títulos recentes do canal separados por ||")
    ap.add_argument("--kb", default=None, help="Caminho alternativo do knowledge_base.json")
    ap.add_argument("--format", choices=["markdown", "json"], default="markdown")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = construir_parser().parse_args(argv)
    porte = a.tier or (porte_por_inscritos(a.subscribers) if a.subscribers else "pequeno")
    ideia = Ideia(titulo=a.title, nicho=a.niche, idioma=a.lang, porte=porte, duracao_min=a.duration_min, thumb_notes=a.thumb_notes,
                  texto_capa=a.thumb_text, dias_desde_ultimo=a.days_since_last, ultimo_resultado=a.last_result,
                  titulos_recentes=[t.strip() for t in (a.recent_titles or "").split("||") if t.strip()])
    try:
        p = aconselhar(ideia, a.kb)
    except ValueError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(p, ensure_ascii=False, indent=2) + "\n" if a.format == "json" else para_markdown(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
