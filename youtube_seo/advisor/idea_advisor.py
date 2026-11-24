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

NOTA PARA O CLI DO PACOTE (youtube_seo/cli.py):
    O subcomando `advise`/`idea` NÃO deve herdar `parents=[comum]` (que expõe flags mortas
    como `-o/--output`, `--cache-dir`, `--no-cache`, `--api-key`, `--timeout` ignoradas pelo motor offline).
    Construa o subparser de `advise`/`idea` sem `parents=[comum]` ou delegue diretamente a
    `idea_advisor.construir_parser()` / `popular_parser(subparser)`.

Limite permanente: a base não tem CTR, impressões, retenção, origem de tráfego nem transcrições.
O parecer compara a ideia com padrões observados dentro dos canais. Não prevê views nem viralização.
"""
from __future__ import annotations

import argparse
import copy
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

# GRUPO reflete a partição das tabelas legadas do KB (5k-200k vs 200k+);
# REGIME_ESTRUTURAL reflete a ruptura real do estudo em 2M de inscritos (5k-2M vs 2M+).
GRUPO = {"pequeno": "pequenos", "emergente": "pequenos", "medio": "200k+", "grande": "200k+", "gigante": "200k+"}
REGIME_ESTRUTURAL = {"pequeno": "5k_2m", "emergente": "5k_2m", "medio": "5k_2m", "grande": "2m_mais", "gigante": "2m_mais"}

LIMITES_CONHECIDOS_BASE = [
    "[Item 1] Corrupção numérica residual no denominador de y_loo_idade nas bordas de idade (mitigada por winsorização, mas infla extremos; rebaixada confiança de tamanhos de efeito pontuais).",
    "[Item 2] Vazamento temporal residual (look-ahead bias) no alvo bilateral y e nos centroides de novidade temática/visual (regras de cadência, volume e desvio tratadas apenas como hipóteses, nunca recomendação firme).",
    "[Item 3] Amostra de canais pequenos (5k a 200k) capturada via busca recente e com presença parcial de reuploads/cortes (curva >60 min e sinal de rosto em pequenos rebaixados para hipótese).",
    "[Item 9] Pré-processamento visual/semântico ajustado fora das dobras de validação cruzada; clusters HDB/KM12 e arquétipos de ângulo expurgados das recomendações.",
    "[Item 11] Confundimento entre pauta e capa (ex.: produto novo vs foto do objeto) e ausência de pareamento por duração em breakouts de pequenos.",
    "[Item 13] Curvas de nichos com poucos canais (G < 20) têm incerteza assintótica subestimada e derivada em log sensível perto da borda inferior.",
    "[Item 14] Truncamento nos últimos 100 vídeos por canal (viés idade-período-coorte entre canais diários e mensais) e views de t-1 lidas na data do snapshot.",
    "[Item 15] Detecção facial legada (Haar Cascade em 320x180) atenua sinais de expressão/rosto e subcobre canais pequenos; modelos preditivos sem calibração de probabilidade.",
]

STOP_PT = set(
    "a o os as de da do das dos e em um uma uns umas no na nos nas por para com que se ao aos ou mais "
    "como pra pro sobre sem ser foi vai esta isso este essa voce eu meu minha seu sua num numa pelo pela pelos pelas".split()
)
STOP_EN = set(
    "the a an of to in on for and or is are was were with at by from it its this that these those be been being "
    "my your you i me we our us he she they them his her their as into about than".split()
)
STOP = STOP_PT | STOP_EN

# Regexes separadas por idioma e contextualizadas para evitar falsos positivos
ABSTRATO_PT_GERAL = re.compile(
    r"\b(vida|sucesso|verdade|mente|mindset|felicidade|amor|sonho|proposito|liberdade|sabedoria|motivacao|reflexao|destino|sentido)\b"
)
ABSTRATO_EN_GERAL = re.compile(
    r"\b(life|success|truth|mind|mindset|happiness|love|dream|purpose|freedom|wisdom|motivation|fate|meaning)\b"
)
# Termos físicos/técnicos só contam como abstratos fora de educação/tech/documentário
ABSTRATO_FISICA_PT = re.compile(r"\b(energia|universo|futuro)\b")
ABSTRATO_FISICA_EN = re.compile(r"\b(energy|universe|future)\b")
NICHOS_TERMOS_TECNICOS = {"educacao", "tech", "documentario"}

# Em PT sem acento, "nos" pode ser "nós" ou contração "em + os" ("nos EUA", "nos jogos").
# Só marcamos "nos" se vier seguido de verbo em 1ª pessoa do plural ou início pronominal claro; caso contrário focamos em eu/meu/minha/nossa/nosso.
PRIMEIRA_PT = re.compile(
    r"\b(eu|meu|minha|meus|minhas|nosso|nossa|nossos|nossas|comigo|conosco)\b"
    r"|\bnos\s+(testamos|fizemos|fomos|criamos|compramos|tentamos|descobrimos|erramos|perdemos|ganhamos|mudamos|vivemos|passamos|construimos)\b"
)
PRIMEIRA_EN = re.compile(r"\b(i|my|me|mine|myself|we|our|ours|ourselves)\b")

ENTIDADES = re.compile(
    r"\b(iphone|ipad|macbook|airpods|samsung|galaxy|apple|google|pixel|android|windows|xiaomi|motorola|asus|lenovo|sony|"
    r"elon|musk|trump|lula|bolsonaro|mrbeast|neymar|messi|ronaldo|cristiano|nasa|spacex|tesla|chatgpt|openai|claude|gemini|"
    r"nvidia|geforce|rtx|radeon|ryzen|intel|amd|playstation|ps4|ps5|ps6|xbox|nintendo|switch|steam|"
    r"minecraft|gta|fortnite|roblox|valorant|zelda|pokemon|elden ring|cyberpunk|baldurs gate|call of duty|fifa|ea fc|league of legends|"
    r"disney|netflix|marvel|dc|batman|spiderman|star wars|harry potter|amazon|shopee|mercado livre|aliexpress|shein|"
    r"mcdonald|burger king|ikea|walmart|costco|bitcoin|ethereum|cripto|nubank|itau|bradesco|santander|banco do brasil|tesouro|selic|cdi|ipca|petrobras|vale|b3|"
    r"copa|world cup|champions|libertadores|brasileirao|nba|nfl|ufc|f1|formula 1|"
    r"brasil|brazil|eua|usa|china|japao|japan|russia|ucrania|ukraine|israel|europa)\b"
)
# Heurística complementar restrita a códigos reais de modelo/produto (ex.: RTX 5090, S24, M4 Pro, Ryzen 7),
# bloqueando palavras comuns capitalizadas seguidas de número (Top 10, Dia 1, For 30, Parte 2).
PADRAO_PRODUTO_MODELO = re.compile(
    r"\b("
    r"[A-Z]{1,4}\d{1,4}(?:\s?(?:Pro|Max|Ultra|Plus|Mini|Ti|Super|XT|FE))?"
    r"|(?:RTX|GTX|RX|MX|GT)\s?\d{3,4}(?:\s?(?:Ti|Super|XT|M))?"
    r"|(?:iPhone|iPad|Galaxy|Pixel|Ryzen|Core|Xiaomi|Redmi|Poco|OnePlus|ThinkPad|IdeaPad|Legion|ROG|TUF|Zenbook|MacBook|AirPods|PlayStation|Switch|Quest|GoPro|Kindle|Surface)\s+(?:\d[A-Za-z0-9]*|[A-Z]\d[A-Za-z0-9]*)(?:\s+(?:Pro|Max|Ultra|Plus|Mini|Ti|Super|FE))?"
    r")\b"
)

CONTRA_PT = re.compile(
    r"\bna verdade\b|\bmentira\b|\bmentiras\b|\bmito\b|\bmitos\b|\berrado\b|\berrada\b|\bpare de\b|"
    r"\bnao (faca|compre|use|invista|acredite|caia)\b|\bnunca\b|\bninguem te conta\b|\bfake\b|\bgolpe\b|\bsuperestimad[oa]s?\b"
)
CONTRA_EN = re.compile(
    r"\bactually\b|\bmyth\b|\bmyths\b|\bwrong\b|\bstop\b|\bdon'?t\b|\bnever\b|\bnot what\b|\bnobody tells\b|"
    r"\bfake\b|\bscam\b|\boverrated\b|\bisn'?t\b|\blie\b|\blies\b"
)

# Colaboração/versus: proíbe marcar resoluções (1920 x 1080), multiplicadores (3x, 10 x) ou modelos ("iPhone X", "Xbox Series X", "Model X")
COLAB_EXPLICITA = re.compile(r"\b(?:ft\.?|feat\.?|featuring|vs\.?|versus|contra|collab)\b|@[A-Za-z0-9_]{2,}", re.I)
PRODUTO_COM_X = re.compile(
    r"\b(?:iphone|model|series|xbox|final cut|os|mac\s?os|direct|space|moto|surface|hyper|cloud|alienware|thinkpad|xperia)\s+x\b",
    re.I,
)
COLAB_X_ENTRE_NOMES = re.compile(r"\b([A-ZÀ-Ý][A-Za-zÀ-ÿ]{1,})\s+[xX]\s+([A-ZÀ-Ý][A-Za-zÀ-ÿ]{1,})\b")

EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\U0001F1E6-\U0001F1FF]")
PERGUNTA = re.compile(r"\?")
COMO_PT = re.compile(r"^(como)\b|\btutorial\b|\bpasso a passo\b|\bguia completo\b")
COMO_EN = re.compile(r"^(how to|how i|how we)\b|\bhow to\b|\btutorial\b|\bstep by step\b")

CAPA_MAPA = [
    (r"sem rosto|no face|faceless|sem pessoa", "Sem rosto"),
    (r"rosto grande|close|rosto em destaque|big face", "Rosto grande"),
    (r"surpres|chocad|shock|surpris", "Expressão surpresa"),
    (r"raiva|bravo|angry", "Expressão raiva"),
    (r"medo|assustad|fear|scared", "Expressão medo"),
    (r"sorri|feliz|smil", "Expressão feliz"),
    (r"\b(?:serio|concentrad[oa]|serious)\b|expressao\s+seria|rosto\s+serio|cara\s+seria", "Expressão seria"),
    (r"olhando para a camera|olhar para a camera|looking at (the )?camera", "Olhar para a câmera"),
    (r"fundo escuro|capa escura|cena escura|\bescura\b|dark background|low key", "Escura (bottom 20% brilho)"),
    (r"fundo claro|fundo branco|capa clara|iluminad[oa]|\bclara\b|\bbright\b|white background|light background", "Clara (top 20% brilho)"),
    (r"verde|green", "Cor dominante verde"),
    (r"azul|blue", "Cor dominante azul"),
    (r"vermelh|red\b", "Cor dominante vermelho"),
    (r"amarel|yellow", "Cor dominante amarelo"),
    (r"ciano|cyan|turquesa", "Cor dominante ciano"),
    (r"roxo|rosa|purple|pink", "Cor dominante roxo_rosa"),
    (r"laranja|orange", "Cor dominante laranja"),
    (r"fundo preto|fundo escuro|capa preta|cor dominante preta|cor preta|predominantemente pret[oa]|tudo preto|black background|dark background|all black", "Cor dominante preto"),
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
MITOS_CAPA = [
    "Rosto grande",
    "Expressão surpresa",
    "Seta ou círculo",
    "Sem rosto",
    "Saturação alta (top 20%)",
    "Contraste global alto (top 20%)",
]

CLUSTER_BANIDO_RE = re.compile(r"^(?:HDB|KM12)-", re.I)


# ---------------------------------------------------------------- utilidades e estatística
def norm(s: str) -> str:
    return unicodedata.normalize("NFKD", (s or "").lower()).encode("ascii", "ignore").decode()


def tokens(s: str, idioma: str | None = None) -> list[str]:
    """Tokenização honesta sem stemmer destrutivo (preserva 'paris', siglas e dígitos de 1 caractere)."""
    stop = STOP_EN if idioma == "en" else (STOP_PT if idioma == "pt" else STOP)
    out: list[str] = []
    for t in re.findall(r"[a-z0-9]+", norm(s)):
        if t.isdigit():
            out.append(t)
        elif len(t) > 1 and t not in stop:
            out.append(t)
    return out


def ic_nao_cruza_zero(ic: list | tuple | None) -> bool:
    if not ic or len(ic) < 2 or ic[0] is None or ic[1] is None:
        return False
    return (ic[0] > 0 and ic[1] > 0) or (ic[0] < 0 and ic[1] < 0)


def classificar_evidencia(
    q: float | None,
    ic: list | tuple | None = None,
    afetada_por_limite_bruto: bool = False,
) -> str:
    """Gate estrito de evidência (Item 7 + restrição de dados brutos):
    - 'firme': q < 0,05, IC 95% não cruza zero e não depende de métrica corrompida/look-ahead.
    - 'hipotese_ab': (0,05 <= q < 0,15) ou regra com q < 0,05 rebaixada por limite bruto ou sem IC válido.
    - 'descartado': q is None ou q >= 0,15 (ou IC cruza zero quando disponível em teste candidato).
    """
    if q is None or q >= 0.15:
        return "descartado"
    tem_ic = ic is not None and len(ic) >= 2 and ic[0] is not None and ic[1] is not None
    if tem_ic and not ic_nao_cruza_zero(ic):
        return "descartado"
    if q < 0.05 and tem_ic and ic_nao_cruza_zero(ic):
        if afetada_por_limite_bruto:
            return "hipotese_ab"
        return "firme"
    if q < 0.15:
        return "hipotese_ab"
    return "descartado"


def _eh_cluster_banido(item: dict | str) -> bool:
    if isinstance(item, str):
        return bool(CLUSTER_BANIDO_RE.match(item.strip()))
    padrao = str(item.get("padrao") or "")
    nome = str(item.get("nome") or "")
    grupo = str(item.get("grupo") or "")
    return (
        bool(CLUSTER_BANIDO_RE.match(padrao))
        or bool(CLUSTER_BANIDO_RE.match(nome))
        or grupo in ("cluster_hdbscan", "cluster_kmeans12")
    )


def normalizar_kb(kb: dict) -> dict:
    """Saneia o knowledge_base.json em memória (sem precisar regenerar dados brutos):
    (a) unifica chaves '200k+' e '200k_mais' em todas as tabelas;
    (b) expurga clusters visuais HDB-* e KM12-* (identidade de canal / vazamento em CV);
    (c) anota/filtra listas de ranking visual pelo gate de evidência (q < 0,15).
    """
    d = copy.deepcopy(kb)

    # (a) Unificar chaves '200k+' <-> '200k_mais' em dicionários e listas de registros
    du = d.get("duracao", {})
    grupos_p200 = du.get("curvas_pequenos_vs_200k", {}).get("grupos", {})
    if "200k_mais" in grupos_p200 and "200k+" not in grupos_p200:
        grupos_p200["200k+"] = grupos_p200["200k_mais"]
    elif "200k+" in grupos_p200 and "200k_mais" not in grupos_p200:
        grupos_p200["200k_mais"] = grupos_p200["200k+"]

    for linha in du.get("faixas_ref_10a15", {}).get("linhas", []):
        if linha.get("grupo") == "200k_mais":
            linha["grupo"] = "200k+"

    cad = d.get("cadencia", {})
    for chave_lista in ("intervalo_faixas_ref_5a9d", "momentum", "volume_recente"):
        for linha in cad.get(chave_lista, []):
            if linha.get("grupo") == "200k_mais":
                linha["grupo"] = "200k+"
    if "intervalo_faixas_ref_5a9d" in cad:
        cad["intervalo_faixas_ref_5a9d"] = [
            linha for linha in cad["intervalo_faixas_ref_5a9d"] if linha.get("faixa") != ">45d"
        ]

    ni_cel = d.get("nicho_idioma", {}).get("celulas", {})
    novas_cel = {}
    for k, v in ni_cel.items():
        if k.endswith("|200k_mais"):
            k_norm = k[: -len("|200k_mais")] + "|200k+"
            novas_cel[k_norm] = v
    ni_cel.update(novas_cel)

    # (b) Expurgar clusters HDB-* e KM12-* de todo o bloco thumbnail
    th = d.get("thumbnail", {})
    padroes = th.get("padroes", {})
    th["padroes"] = {
        k: v for k, v in padroes.items() if not _eh_cluster_banido(k) and not _eh_cluster_banido(v)
    }

    rk = th.get("ranking", {})
    for lado in ("melhores", "piores"):
        if lado in rk:
            rk[lado] = [p for p in rk[lado] if not _eh_cluster_banido(p)]

    por_nicho = th.get("por_nicho", {})
    for nicho_k, listas in por_nicho.items():
        for lado in ("melhores", "piores"):
            if lado in listas:
                # Filtra clusters banidos e também ruído puro (q >= 0,15)
                listas[lado] = [
                    p
                    for p in listas[lado]
                    if not _eh_cluster_banido(p) and (p.get("q") is not None and p.get("q") < 0.15)
                ]

    raros = th.get("raros", {})
    if "linhas" in raros:
        raros["linhas"] = [
            r
            for r in raros["linhas"]
            if not _eh_cluster_banido(r) and (r.get("q") is not None and r.get("q") < 0.15)
        ]

    # (c) Anotar nível de evidência nos padrões sobreviventes
    for p in th.get("padroes", {}).values():
        p["_nivel_evidencia"] = classificar_evidencia(p.get("q"), p.get("ic"))
    for lado in ("melhores", "piores"):
        for p in rk.get(lado, []):
            p["_nivel_evidencia"] = classificar_evidencia(p.get("q"), p.get("ic"))

    d["_normalizado"] = True
    return d


def conf_txt(c: str | None, teto_nota: int | None = None) -> str:
    base = {"Alto": "alta", "Médio": "média", "Baixo": "baixa"}.get(c or "", c or "sem classificação")
    if teto_nota is not None:
        return f"{base} (máx. {teto_nota}/10)"
    return base


def fmt_pct(v: float | None, casas: int = 1) -> str:
    if v is None:
        return "sem dados para esta célula"
    s = f"{v:+.{casas}f}%".replace(".", ",")
    return s.replace("-", "−")


def fmt_num(v: float | None, casas: int = 1) -> str:
    if v is None:
        return "sem dados para esta célula"
    if casas == 0:
        return f"{v:,.0f}".replace(",", ".")
    return f"{v:.{casas}f}".replace(".", ",")


def fmt_q(q: float | None) -> str:
    if q is None:
        return "q não disponível"
    return "q < 0,001" if q < 0.001 else f"q = {q:.3f}".replace(".", ",")


def ic_txt(ic: list | None) -> str:
    if not ic or len(ic) < 2 or ic[0] is None or ic[1] is None:
        return ""
    return f"IC 95% {fmt_pct(ic[0])} a {fmt_pct(ic[1])}"


def interp(curva: list[list[float]], x: float) -> float | None:
    """Interpolação linear em log(x) de uma curva [[x, y, ...], ...]."""
    pts = [(p[0], p[1]) for p in curva if p and p[0] and p[1] is not None]
    if not pts:
        return None
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    lx = math.log(x)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y0
            t = (lx - math.log(x0)) / (math.log(x1) - math.log(x0))
            return y0 + t * (y1 - y0)
    return None


@lru_cache(maxsize=4)
def _carregar_kb_cache(caminho_resolvido: str) -> dict:
    bruto = json.loads(Path(caminho_resolvido).read_text(encoding="utf-8"))
    return normalizar_kb(bruto)


def carregar_kb(caminho: str | None = None) -> dict:
    caminho_resolvido = str(Path(caminho or KB_PADRAO).resolve())
    return copy.deepcopy(_carregar_kb_cache(caminho_resolvido))


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


# ---------------------------------------------------------------- sobreposição lexical e índice TF-IDF
def sobreposicao_lexical(a: str, b: str, idioma: str | None = None) -> float:
    """Cosseno de sobreposição exata de palavras/números (não mede sinônimos nem semântica)."""
    ta, tb = Counter(tokens(a, idioma=idioma)), Counter(tokens(b, idioma=idioma))
    if not ta or not tb:
        return 0.0
    num = sum(ta[t] * tb[t] for t in ta)
    return num / (math.sqrt(sum(v * v for v in ta.values())) * math.sqrt(sum(v * v for v in tb.values())))


# Alias preservado por retrocompatibilidade caso algum código externo importe o nome antigo
similaridade_cos = sobreposicao_lexical


class IndiceReferencias:
    def __init__(self, kb: dict):
        ref = kb["referencias"]
        self.campos = ref["campos"]
        self.linhas = ref["linhas"]
        self.n_total = len(self.linhas)
        self.docs = [self._feat(l[0], l[3] if len(l) > 3 else None) for l in self.linhas]
        df = Counter()
        for d in self.docs:
            df.update(set(d))
        n = len(self.docs)
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
        self.vecs = [self._vec(d) for d in self.docs]

    @staticmethod
    def _feat(titulo: str, idioma: str | None = None) -> list[str]:
        tk = tokens(titulo, idioma=idioma)
        return tk + [f"{a}_{b}" for a, b in zip(tk, tk[1:])]

    def _vec(self, feats: list[str]) -> dict[str, float]:
        tf = Counter(feats)
        if not tf:
            return {}
        v = {t: (1 + math.log(c)) * self.idf.get(t, math.log(len(self.docs) + 1) + 1) for t, c in tf.items()}
        nrm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / nrm for t, x in v.items()}

    def buscar(self, titulo: str, nicho: str, idioma: str, porte: str, k: int = 5) -> list[dict]:
        q = self._vec(self._feat(titulo, idioma=idioma))
        if not q:
            return []
        grupo = GRUPO[porte]
        cands = []
        for i, l in enumerate(self.linhas):
            if l[2] != nicho:
                continue
            v = self.vecs[i]
            cos = sum(w * v.get(t, 0.0) for t, w in q.items())
            # Bloqueio estrito (Item 10): descartar candidatos com sobreposição lexical < 0,05
            if cos < 0.05:
                continue
            bonus = (
                (0.04 if l[3] == idioma else 0.0)
                + (0.02 if GRUPO.get(l[4]) == grupo else 0.0)
                + (0.02 if l[4] == porte else 0.0)
            )
            cands.append((cos + bonus, cos, i))
        cands.sort(reverse=True)
        out = []
        for _score, cos, i in cands[:k]:
            d = dict(zip(self.campos, self.linhas[i]))
            d["sobreposicao_lexical"] = round(cos, 3)
            d["similaridade"] = round(cos, 3)  # chave mantida para compatibilidade de schema
            out.append(d)
        return out


@lru_cache(maxsize=2)
def _indice(caminho: str) -> IndiceReferencias:
    caminho_resolvido = str(Path(caminho or KB_PADRAO).resolve())
    return IndiceReferencias(_carregar_kb_cache(caminho_resolvido))


# ---------------------------------------------------------------- consultas ao KB e células vizinhas
def _linha(lista: list[dict], **filtros) -> dict | None:
    for l in lista:
        if all(l.get(k) == v for k, v in filtros.items()):
            return l
    return None


def _traco(kb: dict, variavel: str, amostra: str = "todos") -> dict | None:
    return _linha(kb["titulo"]["tracos_200k"]["linhas"], variavel=variavel, amostra=amostra)


def _peq(kb: dict, variavel: str) -> dict | None:
    return _linha(kb["titulo"]["pequenos_vs_200k"]["linhas"], variavel=variavel)


def _padrao(kb: dict, nome: str) -> dict | None:
    return kb["thumbnail"]["padroes"].get(nome)


VIZINHOS_PORTE = {
    "pequeno": ["emergente", "medio", "grande", "gigante"],
    "emergente": ["pequeno", "medio", "grande", "gigante"],
    "medio": ["emergente", "grande", "pequeno", "gigante"],
    "grande": ["medio", "gigante", "emergente", "pequeno"],
    "gigante": ["grande", "medio", "emergente", "pequeno"],
}


def _celula_nicho_idioma_com_vizinha(kb: dict, nicho: str, idioma: str, grupo: str) -> dict:
    celulas = kb["nicho_idioma"]["celulas"]
    chave = f"{nicho}|{idioma}|{grupo}"
    cel = celulas.get(chave)
    if cel and cel.get("canais", 0) > 0:
        return {
            "nicho": nicho,
            "idioma": idioma,
            "grupo": grupo,
            "canais": cel["canais"],
            "videos": cel.get("videos", 0),
            "usou_vizinha": False,
            "nota_vizinha": None,
        }
    outro_idioma = "en" if idioma == "pt" else "pt"
    outro_grupo = "200k+" if grupo == "pequenos" else "pequenos"
    candidatas = [
        (f"{nicho}|{idioma}|{outro_grupo}", f"{nicho} × {idioma.upper()} × {outro_grupo} (mesmo nicho e idioma, porte vizinho)"),
        (f"{nicho}|{outro_idioma}|{grupo}", f"{nicho} × {outro_idioma.upper()} × {grupo} (mesmo nicho e porte, idioma vizinho)"),
        (f"{nicho}|{outro_idioma}|{outro_grupo}", f"{nicho} × {outro_idioma.upper()} × {outro_grupo} (célula disponível do nicho)"),
    ]
    for ch_viz, desc_viz in candidatas:
        cv = celulas.get(ch_viz)
        if cv and cv.get("canais", 0) > 0:
            return {
                "nicho": nicho,
                "idioma": idioma,
                "grupo": grupo,
                "canais": 0,
                "videos": 0,
                "usou_vizinha": True,
                "vizinha_descricao": desc_viz,
                "vizinha_canais": cv["canais"],
                "vizinha_videos": cv.get("videos", 0),
            }
    return {
        "nicho": nicho,
        "idioma": idioma,
        "grupo": grupo,
        "canais": 0,
        "videos": 0,
        "usou_vizinha": True,
        "vizinha_descricao": "agregado geral da base (310 canais)",
        "vizinha_canais": kb["meta"]["canais"],
        "vizinha_videos": kb["meta"]["videos"],
    }


def _celula_empirica_duracao_com_vizinha(kb: dict, nicho: str, porte: str) -> dict:
    celulas = kb["duracao"]["empirico_nicho_porte"]["celulas"]
    emp = celulas.get(f"{nicho}|{porte}")
    if emp and emp.get("n", 0) > 0:
        return {**emp, "porte_referencia": porte, "usou_vizinha": False, "nota_vizinha": None}
    for p_viz in VIZINHOS_PORTE[porte]:
        ev = celulas.get(f"{nicho}|{p_viz}")
        if ev and ev.get("n", 0) > 0:
            return {
                **ev,
                "porte_referencia": p_viz,
                "usou_vizinha": True,
                "nota_vizinha": f"sem dados para esta célula ({nicho} × {porte}); usando célula vizinha documentada ({nicho} × {p_viz}).",
            }
    return {
        "n": 0,
        "canais": 0,
        "duracao_mediana": None,
        "duracao_mediana_top10_canal": None,
        "faixas": [],
        "porte_referencia": porte,
        "usou_vizinha": True,
        "nota_vizinha": f"sem dados para esta célula ({nicho} × {porte}).",
    }


def _interacao_significativa_peq_vs_200k(linha_peq: dict | None) -> tuple[bool, float | None]:
    """Verifica se há interação formal significativa entre porte pequeno e 200k+ no KB (Item 8)."""
    if not linha_peq:
        return False, None
    for k in ("diff_q", "q_diff", "interacao_q", "diferenca_q", "q_interacao"):
        if k in linha_peq and linha_peq[k] is not None:
            q_int = float(linha_peq[k])
            return q_int < 0.05, q_int
    # Quando a coluna explícita não está serializada ou como documentado na auditoria da Frente 2D
    # (nenhum traço de título teve Diferença q BH < 0,05: mínimo foi Colab com q = 0,074), retorna False.
    return False, None


# ---------------------------------------------------------------- cálculo de confiança epistêmica (Item 16)
def qs_referencia_do_recorte(kb: dict, nicho: str, idioma: str, porte: str) -> list[float]:
    """Coleta os valores-q das regras auditadas disponíveis no KB para o recorte (nicho, idioma, porte).
    Propriedade fixa da célula consultada: independe totalmente do texto, duração ou capa da ideia.
    """
    qs: list[float] = []
    grupo = GRUPO[porte]
    du_res = kb["duracao"]["resumo_200k"]
    rn = du_res.get(f"nicho={nicho}|yw") or du_res.get("geral|yw", {})
    if rn.get("q_bh") is not None and rn["q_bh"] < 0.15:
        qs.append(float(rn["q_bh"]))

    for var in ("abstrato", "primeira_pessoa", "tem_numero", "tem_palavra_caps", "tem_colab"):
        tr = _traco(kb, var, "todos")
        if tr and tr.get("q") is not None and tr["q"] < 0.15:
            qs.append(float(tr["q"]))
    if nicho in ("tech", "games"):
        ent = _traco(kb, "h_autoridade_entidade", "tech_games")
        if ent and ent.get("q") is not None and ent["q"] < 0.15:
            qs.append(float(ent["q"]))

    pn = kb["thumbnail"]["por_nicho"].get(nicho, {})
    for lado in ("melhores", "piores"):
        for item in pn.get(lado, []):
            if item.get("q") is not None and item["q"] < 0.15:
                qs.append(float(item["q"]))

    for f in kb["cadencia"]["intervalo_faixas_ref_5a9d"]:
        if f.get("grupo") == grupo and f.get("faixa") != ">45d" and f.get("q") is not None and f["q"] < 0.15:
            qs.append(float(f["q"]))
    return qs


def calcular_grau_de_confianca(canais_celula: int, videos_celula: int, qs_celula: list[float]) -> tuple[str, dict]:
    """Mede exclusivamente a solidez estatística da base para o recorte consultado.
    NUNCA depende de quantos alertas, elogios ou gatilhos a ideia recebeu.
    """
    q_medio = (sum(qs_celula) / len(qs_celula)) if qs_celula else None

    if canais_celula >= 15 and videos_celula >= 1000:
        pts_cel = 3
    elif canais_celula >= 8 and videos_celula >= 400:
        pts_cel = 2
    elif canais_celula >= 4 and videos_celula >= 150:
        pts_cel = 1
    else:
        pts_cel = 0

    if q_medio is None:
        pts_q = 1
    elif q_medio < 0.015:
        pts_q = 2
    elif q_medio < 0.05:
        pts_q = 1
    else:
        pts_q = 0

    total = pts_cel + pts_q
    # Teto honesto: sem CTR/retenção e com limites de snapshot, o máximo offline é "moderado a alto"
    if pts_cel == 0:
        grau = "baixo (célula com poucos canais na base)"
    elif total >= 4:
        grau = "moderado a alto"
    elif total >= 2:
        grau = "moderado"
    else:
        grau = "baixo a moderado"

    detalhes = {
        "canais_na_celula": canais_celula,
        "videos_na_celula": videos_celula,
        "n_regras_da_celula_com_q": len(qs_celula),
        "q_medio_regras_da_celula": None if q_medio is None else round(q_medio, 4),
        "nota_metodologica": "Mede apenas a cobertura amostral da célula e o q médio das regras auditadas disponíveis para o recorte; independe de a ideia ter riscos.",
    }
    return grau, detalhes


# ---------------------------------------------------------------- seções
def secao_diagnostico(
    kb: dict,
    ideia: Ideia,
    alertas: list[str],
    favor: list[str],
    hipoteses_ab: list[str],
) -> dict:
    meta = kb["meta"]
    grupo = GRUPO[ideia.porte]
    regime = REGIME_ESTRUTURAL[ideia.porte]
    cel = _celula_nicho_idioma_com_vizinha(kb, ideia.nicho, ideia.idioma, grupo)
    porte = kb["portes"][ideia.porte]
    canais = cel["canais"]
    videos = cel["videos"]
    cobertura = "boa" if canais >= 8 else ("limitada" if canais >= 4 else ("sem dados próprios (usando célula vizinha)" if canais == 0 else "fraca"))

    canais_ref_conf = canais if canais > 0 else min(cel.get("vizinha_canais", 0), 3)
    videos_ref_conf = videos if videos > 0 else min(cel.get("vizinha_videos", 0), 100)
    qs_recorte = qs_referencia_do_recorte(kb, ideia.nicho, ideia.idioma, ideia.porte)
    grau, detalhes_conf = calcular_grau_de_confianca(canais_ref_conf, videos_ref_conf, qs_recorte)

    teto = meta["teto_preditivo"]
    regime_txt = (
        "regime 5k a 2M de inscritos: maior dependência de descoberta/tema e maior volatilidade por vídeo"
        if regime == "5k_2m"
        else "regime 2M+ de inscritos: audiência fiel instalada, ruptura estrutural do estudo em 2M"
    )
    return {
        "grau_de_confianca": grau,
        "metricas_de_confianca": detalhes_conf,
        "cobertura_da_celula": {
            "nicho": ideia.nicho,
            "idioma": ideia.idioma,
            "grupo": grupo,
            "regime_estrutural": regime_txt,
            "canais": canais,
            "videos": videos,
            "avaliacao": cobertura,
            "usou_vizinha": cel.get("usou_vizinha", False),
            "vizinha_descricao": cel.get("vizinha_descricao"),
            "vizinha_canais": cel.get("vizinha_canais"),
            "vizinha_videos": cel.get("vizinha_videos"),
        },
        "pontos_a_favor": favor,
        "riscos": alertas,
        "hipoteses_ab": hipoteses_ab,
        "contexto_do_porte": {
            "porte": ideia.porte,
            "faixa": meta["faixas_porte"][ideia.porte],
            "regime_estrutural": regime_txt,
            "views_mediana_video": porte["views_mediana_video"],
            "top10_share_pct": porte["top10_share"],
            "anomalias_10x_por_mil": porte["anomalias_10x_por_mil"],
            "dp_y": porte["dp_y"],
            "intervalo_mediano_dias": porte["intervalo_mediano_dias"],
        },
        "teto_preditivo": (
            f"Teto da base: o título explica no máximo R² {fmt_num(teto['titulo_r2_oos_melhor'], 3)} fora da amostra, "
            f"embeddings da capa R² {fmt_num(teto['thumb_r2_oos_intra_canal_embeddings'], 3)} dentro do canal, e o melhor modelo acerta o top 5% "
            f"do próprio canal com AUC {fmt_num(teto['ml_auc_top5_canal_canais_novos'], 3)} (0,5 é moeda; não exibimos % de chance de viralizar por falta de calibração). "
            "Este parecer ordena escolhas, não prevê views e nunca promete viralização."
        ),
        "limites": meta["limites"],
        "limites_conhecidos_desta_base": list(LIMITES_CONHECIDOS_BASE),
    }


def secao_duracao(
    kb: dict,
    ideia: Ideia,
    alertas: list[str],
    favor: list[str],
    hipoteses_ab: list[str],
) -> dict:
    du = kb["duracao"]
    res = du["resumo_200k"]
    chave = f"nicho={ideia.nicho}"
    rn = res.get(f"{chave}|yw") or res.get("geral|yw", {})
    usou_nicho_geral = f"{chave}|yw" not in res
    grupo = GRUPO[ideia.porte]
    regime = REGIME_ESTRUTURAL[ideia.porte]
    rp = res.get(f"porte={ideia.porte}|yw") if grupo == "200k+" else None

    curva_n_200k = du["curvas_200k_ref_12min"]["grupos"].get(chave) or du["curvas_200k_ref_12min"]["grupos"].get("geral", [])
    # Chaves normalizadas por normalizar_kb: tanto "pequenos" quanto "200k+" estão presentes
    curva_p = du["curvas_pequenos_vs_200k"]["grupos"].get("pequenos" if grupo == "pequenos" else "200k+", [])

    emp = _celula_empirica_duracao_com_vizinha(kb, ideia.nicho, ideia.porte)
    faixas_emp = [f for f in emp.get("faixas", []) if f.get("canais", 0) >= 3 and f.get("n", 0) >= 20]
    melhor_emp = max(faixas_emp, key=lambda f: f["pct_3x"], default=None)

    # Ancoragem correta por porte (Item 5b):
    # Canais pequenos/emergentes NÃO usam a spline dos 200k+ como régua punitiva;
    # ancoram na distribuição empírica da própria célula (mediana geral a mediana do top 10% / melhor faixa empírica)
    # e na curva própria dos pequenos (limitada a <= 35 min por causa da contaminação >60 min do Item 3).
    faixa_200k = None
    if curva_n_200k:
        pico = max(p[1] for p in curva_n_200k if p[1] is not None)
        if pico > 0:
            ok = [p[0] for p in curva_n_200k if p[1] is not None and p[1] >= 0.85 * pico]
            if ok:
                faixa_200k = [round(min(ok)), round(max(ok))]
    if ideia.nicho == "tech" and faixa_200k:
        faixa_200k[1] = min(faixa_200k[1], 30)

    if grupo == "pequenos":
        med_cel = emp.get("duracao_mediana")
        top10_cel = emp.get("duracao_mediana_top10_canal")
        if med_cel is not None and top10_cel is not None:
            lo = max(8, round(min(med_cel, top10_cel) * 0.85))
            hi_cand = max(med_cel, top10_cel) * 1.35
            if melhor_emp and melhor_emp.get("hi"):
                hi_cand = max(hi_cand, min(melhor_emp["hi"], 35))
            hi = min(35, max(lo + 4, round(hi_cand)))
            faixa = [lo, hi]
            origem_faixa = f"célula empírica de canais {emp['porte_referencia']} em {ideia.nicho}, limitada a 35 min pelo viés de longas >60 min"
        elif curva_p:
            pts_ate_35 = [p for p in curva_p if p[0] <= 35 and p[1] is not None]
            pico_p = max((p[1] for p in pts_ate_35), default=0)
            ok_p = [p[0] for p in pts_ate_35 if p[1] >= 0.80 * pico_p] if pico_p > 0 else [12, 25]
            faixa = [round(min(ok_p)), round(max(ok_p))]
            origem_faixa = "curva própria de canais pequenos (5k a 200k, até 35 min)"
        else:
            faixa = [10, 25]
            origem_faixa = "referência agregada de canais pequenos"
        if ideia.nicho == "tech":
            faixa[1] = min(faixa[1], 25)
    elif regime == "5k_2m":
        # Porte medio (200k a 2M) pertence ao regime estrutural 5k_2m (antes da ruptura de 2M de inscritos):
        # nunca recomendar teto pratico de 60+ min de canais gigantes.
        teto_medio = 30 if ideia.nicho == "tech" else 45
        if faixa_200k:
            lo_m = min(faixa_200k[0], teto_medio - 5)
            hi_m = min(faixa_200k[1], teto_medio)
            if hi_m <= lo_m:
                lo_m = max(12, hi_m - 10)
            faixa = [lo_m, hi_m]
            sufixo_teto = f", com teto prático de {teto_medio} min no regime 5k a 2M" if faixa_200k[1] > teto_medio else ""
            base_origem = f"curva intra-canal 200k+ do nicho {ideia.nicho}" if not usou_nicho_geral else "curva agregada 200k+, sem curva isolada do nicho"
            origem_faixa = base_origem + sufixo_teto
        else:
            faixa = [15, min(35, teto_medio)]
            origem_faixa = f"referência do regime 5k a 2M (teto prático de {teto_medio} min)"
    else:
        faixa = faixa_200k
        origem_faixa = f"curva intra-canal 200k+ do nicho {ideia.nicho}" if not usou_nicho_geral else "curva agregada 200k+, sem curva isolada do nicho"

    q_nicho = rn.get("q_bh")
    canais_nicho_200k = rn.get("canais", 0)

    out: dict[str, Any] = {
        "confianca_maxima_alavanca": "5/10 (confundimento de escopo/produção: vídeos mais longos costumam ter maior investimento editorial)",
        "origem_faixa_recomendada": origem_faixa,
        "faixa_recomendada_min": faixa,
        "otimo_nicho_200k": {
            "otimo_min": rn.get("otimo_min"),
            "ic": rn.get("otimo_ic"),
            "na_borda": rn.get("otimo_na_borda"),
            "retorno_decrescente_min": rn.get("retorno_decrescente_min"),
            "q": q_nicho,
            "canais": canais_nicho_200k,
        },
        "otimo_porte_200k": rp,
        "celula_empirica": {
            "nicho": ideia.nicho,
            "porte": ideia.porte,
            "porte_referencia": emp.get("porte_referencia", ideia.porte),
            "usou_vizinha": emp.get("usou_vizinha", False),
            "nota_vizinha": emp.get("nota_vizinha"),
            "videos": emp.get("n", 0),
            "canais": emp.get("canais", 0),
            "duracao_mediana": emp.get("duracao_mediana"),
            "duracao_mediana_top10_canal": emp.get("duracao_mediana_top10_canal"),
            "melhor_faixa_por_pct_3x": melhor_emp,
        },
        "notas": [],
    }
    notas = out["notas"]
    notas.append(
        "Aviso de confundimento de escopo (confiança máx. 5/10): duração reflete profundidade de produção (documentário/projeto completo vs vídeo rápido). "
        "Proibido 'encher linguiça': esticar roteiro sem sustentar retenção destrói o efeito observado."
    )
    notas.append(
        "Sem interação estatística significativa de duração entre portes (Diferença q = 0,20 na Frente 2D): a direção positiva de vídeos mais substanciais vale no agregado, mas a faixa prática respeita a realidade empírica do seu porte."
    )
    if canais_nicho_200k and canais_nicho_200k < 20:
        notas.append(
            f"Atenção (Item 13): o nicho {ideia.nicho} tem apenas {canais_nicho_200k} canais na curva 200k+ (< 20); trate o ponto ótimo exato com cautela e priorize a média geral (~25 a 34 min para 200k+)."
        )

    if ideia.duracao_min is not None:
        d = ideia.duracao_min
        en = interp(curva_n_200k, d)
        ep = interp(curva_p, d)
        f_emp = next((f for f in emp.get("faixas", []) if f["lo"] <= d and (f["hi"] is None or d < f["hi"])), None)
        out["proposta"] = {
            "duracao_min": d,
            "efeito_curva_nicho_200k_vs_12min": None if en is None else round(en, 1),
            "efeito_curva_porte_vs_12min": None if ep is None else round(ep, 1),
            "faixa_empirica": f_emp,
        }
        # Gate de evidência: como duração tem confundimento de escopo (conf. máx 5/10) e nos pequenos tem viés de coleta (Item 3),
        # só emitimos alerta firme em < 6 min (queda consistente em todas as frentes, q < 0,001) ou tech > 30 min em 200k+.
        if d < 6:
            alertas.append(
                f"Duração muito curta ({fmt_num(d, 0)} min): vídeos de 3 a 6 min rendem −23% a −27% contra 10 a 15 min do mesmo canal (q < 0,001; confiança 5/10 por confundimento de escopo)."
            )
        elif faixa:
            if d < faixa[0]:
                hipoteses_ab.append(
                    f"Duração de {fmt_num(d, 0)} min está abaixo da faixa típica ancorada para {ideia.nicho}/{ideia.porte} ({faixa[0]} a {faixa[1]} min; confiança 5/10, testar roteiro mais denso sem enrolação)."
                )
            elif d > faixa[1]:
                if ideia.nicho == "tech" and d > 30:
                    alertas.append(
                        f"Duração de {fmt_num(d, 0)} min em tech: único nicho com inclinação negativa em vídeos muito longos (−48% aos 60 min vs 12 min nos 200k+; confiança 5/10)."
                    )
                else:
                    hipoteses_ab.append(
                        f"Duração de {fmt_num(d, 0)} min acima da faixa ancorada ({faixa[0]} a {faixa[1]} min): só mantenha se cada bloco tiver escopo real (confiança 5/10; acima de 60 min em pequenos há contaminação por filmes/reuploads na base)."
                    )
            else:
                if grupo == "200k+" and q_nicho is not None and q_nicho < 0.05:
                    favor.append(
                        f"Duração de {fmt_num(d, 0)} min alinhada à faixa de melhor desempenho intra-canal ({faixa[0]} a {faixa[1]} min, {fmt_q(q_nicho)}; confiança 5/10, exige sustentar retenção real)."
                    )
                else:
                    hipoteses_ab.append(
                        f"Duração de {fmt_num(d, 0)} min alinhada à célula empírica ({faixa[0]} a {faixa[1]} min; mantida como hipótese de escopo, confiança máx. 5/10)."
                    )

    if grupo == "pequenos":
        notas.append(
            "Nos canais pequenos (5k a 200k), a recomendação usa a célula empírica e a curva própria até 35 min. Acima de 60 min o ganho aparente da base bruta está contaminado por uploads de filmes/terceiros (Item 3)."
        )
    elif regime == "5k_2m":
        notas.append(
            "Porte médio (200k a 2M) pertence ao regime estrutural 5k a 2M (antes da ruptura de 2M de inscritos): vídeos longos aumentam a variância; não copie formatos de 60+ min de canais gigantes sem demanda comprovada."
        )
    else:
        notas.append(
            "No regime 2M+ de inscritos, a base instalada tolera aprofundamento maior (20 a 45 min soma +25,1% contra 8 a 20 min, q < 0,001; confiança 5/10 por efeito escopo)."
        )
    return out


def analisar_titulo(titulo: str, idioma: str = "pt", nicho: str | None = None) -> dict:
    """Análise léxica separada por idioma, contextualizada por nicho e sem falsos positivos em 'x'."""
    id_norm = "en" if norm(idioma).startswith("en") else "pt"
    n = norm(titulo)
    palavras_caps = [w for w in re.findall(r"[A-Za-zÀ-ÿ]+", titulo) if len(w) >= 3 and w.isupper() and w.isalpha()]

    # Abstratos por idioma + isenção de termos técnicos/físicos em nichos científicos/tech
    if id_norm == "en":
        abs_set = set(ABSTRATO_EN_GERAL.findall(n))
        if nicho not in NICHOS_TERMOS_TECNICOS:
            abs_set |= set(ABSTRATO_FISICA_EN.findall(n))
        prim = bool(PRIMEIRA_EN.search(n))
        contra = bool(CONTRA_EN.search(n))
        como = bool(COMO_EN.search(n))
    else:
        abs_set = set(ABSTRATO_PT_GERAL.findall(n))
        if nicho not in NICHOS_TERMOS_TECNICOS:
            abs_set |= set(ABSTRATO_FISICA_PT.findall(n))
        prim = bool(PRIMEIRA_PT.search(n))
        contra = bool(CONTRA_PT.search(n))
        como = bool(COMO_PT.search(n))

    entidades_lista = sorted(set(m if isinstance(m, str) else m[0] for m in ENTIDADES.findall(n)))
    modelos_extras = [m.strip() for m in PADRAO_PRODUTO_MODELO.findall(titulo)]

    # Colaboração/versus: ignora "iPhone X", "Xbox Series X", "1920 x 1080", "10x"
    colab = bool(COLAB_EXPLICITA.search(titulo))
    if not colab:
        titulo_sem_prod_x = PRODUTO_COM_X.sub("", titulo)
        for m_x in COLAB_X_ENTRE_NOMES.finditer(titulo_sem_prod_x):
            esq, dir_ = m_x.group(1), m_x.group(2)
            if not esq.isdigit() and not dir_.isdigit():
                colab = True
                break

    return {
        "idioma_analise": id_norm,
        "caracteres": len(titulo),
        "palavras": len(titulo.split()),
        "abstrato": sorted(abs_set),
        "primeira_pessoa": prim,
        "entidade_famosa": entidades_lista,
        "modelo_ou_produto_detectado": modelos_extras,
        "contraintuitivo": contra,
        "numero": bool(re.search(r"\d", titulo)),
        "palavra_caixa_alta": palavras_caps,
        "colab_vs": colab,
        "emoji": bool(EMOJI.search(titulo)),
        "pergunta": bool(PERGUNTA.search(titulo)),
        "como_tutorial": como,
    }


def secao_titulo(
    kb: dict,
    ideia: Ideia,
    alertas: list[str],
    favor: list[str],
    hipoteses_ab: list[str],
) -> dict:
    t = analisar_titulo(ideia.titulo, idioma=ideia.idioma, nicho=ideia.nicho)
    pequeno = GRUPO[ideia.porte] == "pequenos"
    achados: list[dict] = []
    lembretes: list[str] = []
    nao_importa: list[str] = []

    # 1. Vocabulário abstrato (pooled: estimativa agregada, sem interação por idioma/porte)
    ab = _traco(kb, "abstrato", "todos")
    if ab:
        niv = classificar_evidencia(ab.get("q"), ab.get("ic"))
        if niv != "descartado":
            achados.append({
                "traco": "vocabulário abstrato (estimativa agregada)",
                "presente": bool(t["abstrato"]),
                "efeito": ab["efeito"],
                "ic": ab["ic"],
                "q": ab["q"],
                "nivel_evidencia": niv,
                "confianca": "média (agregado 200k+)",
                "acao": "Troque palavras abstratas por objeto, número, nome ou cena concreta." if t["abstrato"] else "Ok: título concreto.",
            })
            if t["abstrato"]:
                msg = f"Vocabulário abstrato no título ({', '.join(t['abstrato'])}): {fmt_pct(ab['efeito'])} no múltiplo do canal ({fmt_q(ab['q'])}, {ic_txt(ab['ic'])}; estimativa agregada)."
                if niv == "firme":
                    alertas.append(msg)
                else:
                    hipoteses_ab.append(msg)

    # 2. Primeira pessoa (Item 8: sem teste formal de interação idioma x traço significativo -> usar estimativa agregada 'todos' primeiro)
    pp_all = _traco(kb, "primeira_pessoa", "todos")
    pp_lang = _traco(kb, "primeira_pessoa", ideia.idioma)
    pp_ref = pp_all if (pp_all and pp_all.get("q") is not None) else pp_lang
    if pp_ref:
        niv_pp = classificar_evidencia(pp_ref.get("q"), pp_ref.get("ic"))
        nota_escopo_pp = "estimativa agregada, sem interação formal idioma × 1ª pessoa com q < 0,05"
        if niv_pp != "descartado":
            achados.append({
                "traco": f"1ª pessoa no título ({nota_escopo_pp})",
                "presente": t["primeira_pessoa"],
                "efeito": pp_ref["efeito"],
                "ic": pp_ref["ic"],
                "q": pp_ref["q"],
                "nivel_evidencia": niv_pp,
                "confianca": "média" if niv_pp == "firme" else "hipótese A/B",
                "acao": "Prefira colocar o assunto/objeto antes do pronome pessoal." if t["primeira_pessoa"] else "Ok: premissa no centro.",
            })
            if t["primeira_pessoa"]:
                msg_pp = f"1ª pessoa no título: {fmt_pct(pp_ref['efeito'])} ({fmt_q(pp_ref['q'])}, {ic_txt(pp_ref['ic'])}; {nota_escopo_pp})."
                if niv_pp == "firme":
                    alertas.append(msg_pp)
                else:
                    hipoteses_ab.append(msg_pp)
        else:
            nao_importa.append(
                f"1ª pessoa no agregado geral: efeito {fmt_pct(pp_ref['efeito'])} ({fmt_q(pp_ref['q'])}), não sobrevive ao corte estrito sem segmentação ad-hoc."
            )

    # 3. Entidades / marcas em Tech e Games (Item 6 e Item 10: confundimento de lançamento/mídia paga + lista léxica não exaustiva -> lembrete neutro quando ausente)
    if ideia.nicho in ("tech", "games"):
        ent = _traco(kb, "h_autoridade_entidade", "tech_games")
        tem_ent = bool(t["entidade_famosa"] or t["modelo_ou_produto_detectado"])
        nomes_ent = t["entidade_famosa"] or t["modelo_ou_produto_detectado"]
        if ent:
            niv_ent = classificar_evidencia(ent.get("q"), ent.get("ic"))
            if niv_ent != "descartado":
                achados.append({
                    "traco": "marca/produto específico no título (tech e games)",
                    "presente": tem_ent,
                    "efeito": ent["efeito"],
                    "ic": ent["ic"],
                    "q": ent["q"],
                    "nivel_evidencia": niv_ent,
                    "confianca": "média (sujeito a confundimento de lançamentos/mídia paga)",
                    "acao": "Manter o nome exato buscado pelo público." if tem_ent else "Se o vídeo aborda um produto/jogo específico, cite o nome exato no título.",
                })
                if tem_ent:
                    msg_e = (
                        f"Nome de produto/marca identificado ({', '.join(nomes_ent[:3])}): associação de {fmt_pct(ent['efeito'])} em tech/games "
                        f"({fmt_q(ent['q'])}; parte do efeito na base vem de grandes lançamentos)."
                    )
                    if niv_ent == "firme":
                        favor.append(msg_e)
                    else:
                        hipoteses_ab.append(msg_e)
                else:
                    # Item 10: NUNCA disparar alerta de risco por ausência na lista congelada; vira lembrete neutro
                    lembretes.append(
                        "Lembrete neutro (tech/games): o dicionário offline não detectou marca conhecida (pode ser produto novo fora da lista, ex.: lançamento recente). Se houver produto/jogo central, inclua o nome exato no título."
                    )

    # 4. Gancho contraintuitivo (Item 8: usar amostra 'todos' agregada; só mostrar se q < 0,15)
    gl = kb["titulo"]["ganchos_principais_vs_descritivo"]["linhas"]
    ci_all = _linha(gl, gancho="contraintuitivo", amostra="todos") or _linha(gl, gancho="contraintuitivo", amostra=ideia.idioma)
    if ci_all:
        niv_ci = classificar_evidencia(ci_all.get("q"), ci_all.get("ic"))
        if niv_ci != "descartado":
            achados.append({
                "traco": "gancho contraintuitivo (estimativa agregada)",
                "presente": t["contraintuitivo"],
                "efeito": ci_all["efeito"],
                "ic": ci_all["ic"],
                "q": ci_all["q"],
                "nivel_evidencia": niv_ci,
                "confianca": "hipótese A/B (oscila entre subamostras no estudo)",
                "acao": "Testar contra título direto no Testar e Comparar do YouTube.",
            })
            if t["contraintuitivo"]:
                # Oscila entre q=0,015 e q=0,12 no relatório 2C -> manter em hipóteses A/B por prudência
                hipoteses_ab.append(
                    f"Gancho contraintuitivo no título: {fmt_pct(ci_all['efeito'])} na estimativa agregada ({fmt_q(ci_all['q'])}); validar em teste A/B."
                )

    # 5. Traços pequenos vs 200k+ (Item 8: Gelman & Stern! Nenhum traço tem interação q < 0,05 contra 200k+, além do Item 3 contaminar pequenos)
    for var, chave, rotulo in (
        ("tem_numero", "numero", "número no título"),
        ("tem_palavra_caps", "palavra_caixa_alta", "palavra em CAIXA ALTA"),
        ("tem_colab", "colab_vs", "colaboração/versus no título"),
    ):
        l_peq = _peq(kb, var)
        l_200 = _traco(kb, var, "todos")
        tem_int, q_int = _interacao_significativa_peq_vs_200k(l_peq)
        presente = bool(t[chave])

        if tem_int and pequeno and l_peq:
            ef, ic_v, q_v = l_peq.get("pequenos"), l_peq.get("pequenos_ic"), l_peq.get("pequenos_q")
            escopo_str = f"específico pequenos, interação q = {fmt_num(q_int, 3)}"
            afetado_bruto = True
        elif l_200:
            ef, ic_v, q_v = l_200.get("efeito"), l_200.get("ic"), l_200.get("q")
            escopo_str = "estimativa agregada, interação por porte não significativa com q ≥ 0,05"
            afetado_bruto = False
        elif l_peq:
            # Fallback para a linha combinada documentando ausência de interação
            ef, ic_v, q_v = l_peq.get("pequenos"), l_peq.get("pequenos_ic"), l_peq.get("pequenos_q")
            escopo_str = "amostra 5k a 200k, sem interação significativa vs 200k+, tratado apenas como hipótese A/B"
            afetado_bruto = True
        else:
            continue

        niv_v = classificar_evidencia(q_v, ic_v, afetada_por_limite_bruto=afetado_bruto)
        if niv_v == "descartado":
            continue
        achados.append({
            "traco": f"{rotulo} ({escopo_str})",
            "presente": presente,
            "efeito": ef,
            "ic": ic_v,
            "q": q_v,
            "nivel_evidencia": niv_v,
            "confianca": "média" if niv_v == "firme" else "hipótese A/B",
        })
        if presente and q_v is not None:
            txt_item = f"Traço '{rotulo}': {fmt_pct(ef)} ({fmt_q(q_v)}, {ic_txt(ic_v)}; {escopo_str})."
            if niv_v == "firme":
                (favor if (ef or 0) > 0 else alertas).append(txt_item)
            else:
                hipoteses_ab.append(txt_item)

    # 6. Emoji (agregado 'todos'; se só existir recorte com 0,05 <= q < 0,15 vai exclusivamente para hipótese A/B)
    em_all = _traco(kb, "emoji", "todos") or _traco(kb, "emoji", ideia.idioma)
    if em_all:
        niv_em = classificar_evidencia(em_all.get("q"), em_all.get("ic"))
        if niv_em != "descartado":
            achados.append({
                "traco": "emoji no título (concentrado em poucos canais)",
                "presente": t["emoji"],
                "efeito": em_all["efeito"],
                "ic": em_all["ic"],
                "q": em_all["q"],
                "nivel_evidencia": "hipotese_ab",
                "confianca": "hipótese A/B",
            })
            if t["emoji"]:
                hipoteses_ab.append(
                    f"Emoji no título: {fmt_pct(em_all['efeito'])} ({fmt_q(em_all['q'])}); concentrado em poucos canais, testar com cautela."
                )

    nao_importa.append("Comprimento do título: nenhuma faixa difere estatisticamente de 46 a 60 caracteres (q > 0,93 nos 200k+; sem interação significativa por porte).")
    pq = _peq(kb, "tem_pergunta")
    if pq:
        nao_importa.append(
            f"Pergunta no título: efeito nulo em views ({fmt_pct(pq['grandes'])} nos 200k+ e {fmt_pct(pq['pequenos'])} nos pequenos; útil apenas para estimular comentários)."
        )
    nao_importa.append("Fórmulas prontas (lista, tutorial, mistério, urgência, lacuna de curiosidade): IC 95% cruza zero na base inteira.")

    return {
        "tracos_detectados": t,
        "achados": achados,
        "lembretes_neutros": lembretes,
        "o_que_nao_importa": nao_importa,
        "nota": "O título é filtro fino, não alavanca isolada: o melhor modelo de título tem R² fora da amostra de 0,018. Só listamos acima regras com q < 0,15.",
    }


def secao_thumb(
    kb: dict,
    ideia: Ideia,
    alertas: list[str],
    favor: list[str],
    hipoteses_ab: list[str],
) -> dict:
    notas = norm(ideia.thumb_notes or "")
    detectados_validos: list[dict] = []
    detectados_nulos: list[dict] = []
    vistos: set[str] = set()

    for rx, nome in CAPA_MAPA:
        if nome in vistos:
            continue
        if re.search(rx, notas):
            if nome == "Rosto grande" and "sem rosto" in notas:
                continue
            if nome == "Clara (top 20% brilho)" and re.search(r"escur|dark", notas) and not re.search(r"fundo branco|bright", notas):
                continue
            p = _padrao(kb, nome)
            if p and not _eh_cluster_banido(p):
                vistos.add(nome)
                # Item 9 e Item 15: features visuais tiveram CV sem pipeline isolado e Haar Cascade 320x180
                niv = classificar_evidencia(p.get("q"), p.get("ic"))
                reg = {
                    "padrao": nome,
                    "efeito_intra_canal": p["efeito"],
                    "ic": p.get("ic"),
                    "q": p.get("q"),
                    "efeito_ingenuo": p.get("efeito_ingenuo"),
                    "nivel_evidencia": niv,
                    "confianca": conf_txt(p.get("confianca")),
                }
                if niv == "descartado":
                    detectados_nulos.append(reg)
                else:
                    detectados_validos.append(reg)
                    resumo_p = f"Capa com '{nome}': {fmt_pct(p['efeito'])} dentro do canal ({fmt_q(p['q'])}, {ic_txt(p.get('ic'))})."
                    if niv == "firme":
                        if p["efeito"] > 0:
                            favor.append(resumo_p)
                        else:
                            alertas.append(resumo_p)
                    else:
                        # 0,05 <= q < 0,15 (ex.: Cor dominante verde q=0,136, Peso visual à esquerda q=0,056) -> Hipóteses A/B!
                        hipoteses_ab.append(f"{resumo_p} [0,05 ≤ q < 0,15: tratar como hipótese para teste A/B]")

    # Listas por nicho e globais (já expurgadas de HDB/KM12 e de q >= 0,15 em normalizar_kb)
    pn = kb["thumbnail"]["por_nicho"].get(ideia.nicho, {})
    rec_nicho = [x for x in pn.get("melhores", []) if classificar_evidencia(x.get("q"), x.get("ic")) != "descartado"][:5]
    evitar_nicho = [x for x in pn.get("piores", []) if classificar_evidencia(x.get("q"), x.get("ic")) != "descartado"][:3]

    rec_global_firme = []
    rec_global_ab = []
    for p in kb["thumbnail"]["ranking"]["melhores"]:
        if p.get("canais", 0) < 10:
            continue
        niv = classificar_evidencia(p.get("q"), p.get("ic"))
        item_fmt = {"padrao": p["nome"], "efeito": p["efeito"], "ic": p.get("ic"), "q": p.get("q"), "canais": p["canais"]}
        if niv == "firme":
            rec_global_firme.append(item_fmt)
        elif niv == "hipotese_ab":
            rec_global_ab.append(item_fmt)

    # 1.802 combinações mineradas (Item 7): SEMPRE tratadas no máximo como hipóteses A/B e só se q < 0,15
    raros = [
        {"padrao": r["nome"], "efeito": r["efeito"], "ic": r.get("ic"), "canais": r["canais"], "q": r["q"]}
        for r in kb["thumbnail"]["raros"]["linhas"]
        if r.get("tipo") == "combinacao" and r.get("q") is not None and r.get("q") < 0.15
    ][:5]

    # Item 4a + Item 10a: Unificar conclusão Título x Capa (alinhar ganha +4,1%, q=0,034; complementar é nulo)
    # e rotular honestamente a métrica offline como SOBREPOSIÇÃO DE PALAVRAS (não semântica!)
    alinh = None
    if ideia.texto_capa is not None and ideia.texto_capa.strip():
        s = sobreposicao_lexical(ideia.titulo, ideia.texto_capa, idioma=ideia.idioma)
        nivel = "alta" if s >= 0.35 else ("média" if s >= 0.12 else "baixa")
        alinh = {
            "texto_capa": ideia.texto_capa,
            "sobreposicao_lexical": round(s, 3),
            "similaridade_lexical": round(s, 3),  # compatibilidade
            "nivel": nivel,
            "aviso_metrica": "Medido por sobreposição exata de palavras/números (não detecta sinônimos nem paráfrases visuais).",
        }
        if nivel == "baixa":
            # Não pune sinônimos como erro certo: explica que se for assunto desconexo há risco, mas sinônimos não são lidos offline
            hipoteses_ab.append(
                f"Baixa sobreposição de palavras entre título e texto da capa ({fmt_num(s, 2)}): no estudo consolidado (Frente 2C), alinhar a ideia da capa ao título soma +4,1% por DP (q = 0,034) e texto desconexo perde. Se você usou sinônimos diretos da mesma premissa, ignore este aviso lexical."
            )
        else:
            favor.append(
                f"Texto da capa tem sobreposição de palavras {nivel} ({fmt_num(s, 2)}) com o título, reforçando a mesma premissa (alinhamento título-capa: +4,1% por DP, q = 0,034)."
            )

    mitos = []
    for m in MITOS_CAPA:
        p = _padrao(kb, m)
        if p:
            mitos.append({
                "padrao": m,
                "efeito_ingenuo_entre_canais": p["efeito_ingenuo"],
                "efeito_intra_canal": p["efeito"],
                "q": p["q"],
            })

    notas_th = [
        "Conclusão unificada Título × Capa (errata consolidada): alinhar o texto da capa à premissa do título supera texto desconexo (+4,1% por DP, q = 0,034); repetir palavras-chave não é punido e 'complementar com assunto paralelo' teve efeito nulo.",
        "Clusters automáticos de imagem (HDBSCAN/K-Means) foram removidos das recomendações por representarem identidade fixa de canais individuais e vazamento em validação cruzada (Itens 4 e 9).",
    ]
    if GRUPO[ideia.porte] == "pequenos":
        notas_th.append(
            "Hipótese para teste A/B em canais pequenos (rebaixada pelos Itens 3, 11 e 15): breakouts exibiram menos rosto que controles na base bruta, mas sem pareamento por duração e com detector Haar 320x180. Teste capa focada no objeto/cena versus rosto no Testar e Comparar."
        )
    notas_th.append(
        "Consistência visual (hipótese rebaixada pelo Item 2c, centroide com vídeos futuros): manter identidade reconhecível pelo inscrito faz sentido prático, mas a estimativa numérica exata da base tem viés temporal."
    )
    if not ideia.thumb_notes:
        notas_th.append("Sem notas de capa informadas: descreva fundo, cor, rosto, texto e objeto em --thumb-notes para checagem contra os padrões auditados.")

    return {
        "padroes_detectados_nas_notas": detectados_validos,
        "padroes_detectados_nulos_ignorados": detectados_nulos,
        "recomendados_no_nicho": rec_nicho,
        "evitar_no_nicho": evitar_nicho,
        "padroes_firmes_na_base": rec_global_firme,
        "padroes_hipotese_ab_na_base": rec_global_ab,
        "hipoteses_raras_testaveis": raros,
        "alinhamento_titulo_capa": alinh,
        "mitos_a_ignorar": mitos,
        "notas": notas_th,
    }


def secao_cadencia(
    kb: dict,
    ideia: Ideia,
    alertas: list[str],
    favor: list[str],
    hipoteses_ab: list[str],
) -> dict:
    """Item 2 + Item 6 + Item 12 + Item 14:
    Cadência, volume semanal e novidade temática usaram alvo bilateral `y` / centroide futuro / confundimento de escopo (notícias diárias vs vídeos-chefe).
    Confiança máxima cravada em 5/10 e NUNCA apresentadas como recomendação firme (vão para Hipóteses A/B).
    """
    cad = kb["cadencia"]
    grupo = GRUPO[ideia.porte]
    regime = REGIME_ESTRUTURAL[ideia.porte]
    out: dict[str, Any] = {
        "confianca_maxima_alavanca": "5/10 (confundimento de escopo editorial + vazamento temporal residual no alvo bilateral y)",
        "notas": [],
    }

    # Chaves já unificadas em normalizar_kb ("pequenos" e "200k+") e faixa >45d bloqueada por look-ahead bias (Item 2)
    faixas_todas = [f for f in cad["intervalo_faixas_ref_5a9d"] if f["grupo"] == grupo and f.get("faixa") != ">45d"]
    faixas_filtradas = [f for f in faixas_todas if f.get("q") is not None and f.get("q") < 0.15]
    out["intervalo_por_faixa_ref_5a9d"] = faixas_filtradas
    out["faixas_nulas_omitidas"] = [f["faixa"] for f in faixas_todas if f.get("q") is None or f.get("q") >= 0.15]
    out["faixas_bloqueadas_lookahead"] = [">45d"]

    d = ideia.dias_desde_ultimo
    if d is not None:
        out["dias_desde_ultimo"] = d
        if grupo == "200k+":
            curva = cad["intervalo_200k_ref_7d"]["grupos"].get(f"porte={ideia.porte}") or cad["intervalo_200k_ref_7d"]["grupos"]["geral"]
            ef_curva = interp(curva, max(d, 0.1))
            out["efeito_curva_200k_vs_7d"] = None if ef_curva is None else round(ef_curva, 1)
        else:
            out["efeito_curva_200k_vs_7d"] = None
        if d < 2:
            f_curto = next((f for f in faixas_todas if str(f.get("faixa", "")).replace(" ", "") == "<2d"), None)
            if f_curto and f_curto.get("q") is not None and f_curto["q"] < 0.15:
                # Rebaixado de recomendação/risco firme para Hipótese A/B pelos Itens 2a e 6
                hipoteses_ab.append(
                    f"Intervalo menor que 2 dias ({fmt_num(d, 0)}d) em canal {ideia.porte} ({regime}): {fmt_pct(f_curto['efeito'])} na base ({fmt_q(f_curto['q'])}; confiança máx. 5/10; parte da queda vem de lotes efêmeros/partes picadas e do alvo bilateral y). Avalie espaçar ≥ 3 dias se a produção estiver apressada."
                )
            else:
                out["notas"].append(
                    "Intervalo menor que 2 dias neste grupo não tem efeito estatisticamente significativo (q ≥ 0,15); descartado como risco."
                )

    if ideia.ultimo_resultado == "flop":
        l_flop = _linha(cad["pos_extremo_x_intervalo"], modelo="bot_prev", termo="bot_prev")
        if d is not None and d < 3 and l_flop:
            hipoteses_ab.append(
                f"Publicar em menos de 3 dias após um vídeo fraco associa-se a {fmt_pct(l_flop['efeito'])} ({ic_txt(l_flop.get('ic'))}; confiança máx. 5/10, afetado por snapshot bias em y_passado). Se possível, revise embalagem e aguarde 3 a 7 dias."
            )
        else:
            out["notas"].append(
                "Pós-fracasso (confiança máx. 5/10): não há ganho comprovado em correr para compensar; priorize diagnóstico de tema e capa."
            )
    elif ideia.ultimo_resultado == "hit":
        # Item 12: contradição documental sobre momentum pós-hit -> esclarecer explicitamente como inconclusivo/fase
        out["notas"].append(
            "Momentum pós-hit (status revisado, Item 12): o ganho bruto aparente desaparece quando controlado pela fase local do canal (+2,4%, nulo na Frente 2A). Não apresse um vídeo raso tentando 'surfar' o anterior; mantenha o mesmo veio temático com qualidade normal."
        )

    vol = _linha(cad["volume_recente"], grupo="geral", variavel="log_n7", desfecho="yw")
    if vol and vol.get("q") is not None and vol["q"] < 0.15:
        out["notas"].append(
            f"Volume semanal (confiança máx. 5/10, Item 2a): dobrar uploads em 7 dias caiu de {fmt_pct(vol['efeito_por_dobro'])} no alvo bilateral para cerca da metade no alvo estritamente passado, além de confundir vídeos de plantão/notícia com vídeos-chefe."
        )
    out["notas"].append("Dia da semana e horário de publicação têm efeito nulo após correção de múltiplos testes em todos os portes.")

    # Consistência temática (Item 2c: centroide tem look-ahead; Item 10a: tratar ref == 0 sem falha silenciosa e nomear sobreposição lexical)
    out["consistencia_tematica"] = {
        "regra": (
            "Hipótese de consistência temática (rebaixada pelo Item 2c: centroide da base usou vídeos futuros): "
            "mudanças bruscas de assunto costumam reduzir entrega para a base atual, mas a magnitude exata não é causal."
        )
    }
    if ideia.titulos_recentes:
        sims = [sobreposicao_lexical(ideia.titulo, tr, idioma=ideia.idioma) for tr in ideia.titulos_recentes]
        media = sum(sims) / len(sims)
        base_pares = []
        for i_t, tr in enumerate(ideia.titulos_recentes):
            outros = ideia.titulos_recentes[:i_t] + ideia.titulos_recentes[i_t + 1 :]
            if outros:
                base_pares.append(sum(sobreposicao_lexical(tr, o, idioma=ideia.idioma) for o in outros) / len(outros))
        ref = sum(base_pares) / len(base_pares) if base_pares else None
        out["consistencia_tematica"].update({
            "sobreposicao_media_com_recentes": round(media, 3),
            "sobreposicao_entre_recentes": None if ref is None else round(ref, 3),
        })
        if ref is None:
            out["consistencia_tematica"]["avaliacao_recentes"] = (
                "Apenas 1 título recente informado: sem par para estimar a coesão interna habitual do canal."
            )
        elif ref == 0.0:
            # Correção explícita do bug `ref == 0.0` (Item 10a)
            if media == 0.0:
                out["consistencia_tematica"]["avaliacao_recentes"] = (
                    "Os próprios títulos recentes têm sobreposição lexical zero entre si (vocabulário variado); zero sobreposição na nova ideia não configura anomalia lexical."
                )
            else:
                out["consistencia_tematica"]["avaliacao_recentes"] = (
                    f"Sobreposição lexical com recentes ({fmt_num(media, 2)}) acima da média interna dos recentes (0,00)."
                )
        elif media < 0.5 * ref:
            hipoteses_ab.append(
                f"Título com baixa sobreposição de palavras em relação aos vídeos recentes ({fmt_num(media, 2)} vs {fmt_num(ref, 2)} entre recentes): verifique se é um desvio real de assunto ou apenas vocabulário diferente para o mesmo tema (hipótese rebaixada pelo Item 2c)."
            )
        else:
            out["consistencia_tematica"]["avaliacao_recentes"] = (
                f"Sobreposição de palavras compatível com o histórico recente informado ({fmt_num(media, 2)} vs {fmt_num(ref, 2)})."
            )
    return out


def secao_exemplos(kb: dict, ideia: Ideia, caminho_kb: str) -> dict:
    idx = _indice(caminho_kb)
    itens = idx.buscar(ideia.titulo, ideia.nicho, ideia.idioma, ideia.porte, k=5)
    return {
        "tamanho_indice_referencias": idx.n_total,
        "criterio_corte": "sobreposicao_lexical >= 0,05 dentro do mesmo nicho",
        "itens": itens,
    }


def secao_checklist(ideia: Ideia, dur: dict, tit: dict, thumb: dict, cad: dict) -> list[str]:
    c: list[str] = []
    f = dur.get("faixa_recomendada_min")
    if f:
        c.append(
            f"Estruturar roteiro para sustentar genuinamente {f[0]} a {f[1]} min ({dur.get('origem_faixa_recomendada', 'faixa do recorte')}), cortando qualquer enchimento (confiança de duração: máx. 5/10)."
        )
    t = tit["tracos_detectados"]
    if t["abstrato"]:
        c.append("Substituir termos abstratos do título por substantivos concretos, números, objetos ou situações verificáveis.")
    if t["primeira_pessoa"]:
        c.append("Testar versão do título colocando o tema/objeto antes do pronome em 1ª pessoa.")
    if ideia.nicho in ("tech", "games") and not (t["entidade_famosa"] or t["modelo_ou_produto_detectado"]):
        c.append("Se o vídeo tratar de hardware, software ou jogo específico, incluir o nome exato do produto/título na abertura.")
    c.append("Posicionar o termo central do assunto no início do título (+1,3 p.p. na chance de top 5% do canal, q = 0,023).")
    c.append("Alinhar o texto curto da capa à mesma premissa do título (+4,1% por DP, q = 0,034); evitar frase paralela desconexa.")
    c.append("Usar o 'Testar e Comparar' do YouTube Studio para validar 2 variações de capa (ex.: foco em cena/objeto vs expressão), sem copiar clusters de outros canais.")
    if cad.get("dias_desde_ultimo") is not None and cad["dias_desde_ultimo"] < 2:
        c.append("Avaliar se o intervalo menor que 2 dias comprometeu o acabamento da pauta/capa (alavanca de cadência tem confiança máx. 5/10).")
    c.append(
        "Revisar legenda manual como acessibilidade e acabamento (confiança máx. 5/10 como alavanca: os +28,6% brutos na base sofrem confundimento de investimento e edição pós-viralização) e capítulos para navegação."
    )
    c.append("Após 48h da publicação, auditar CTR e retenção no YouTube Studio contra a mediana do próprio canal (variáveis ausentes desta base offline).")
    return c


# ---------------------------------------------------------------- orquestração
def aconselhar(ideia: Ideia, kb_path: str | Path | None = None) -> dict:
    caminho = str(kb_path or KB_PADRAO)
    kb = _carregar_kb_cache(str(Path(caminho).resolve()))
    ideia.normalizar()
    alertas: list[str] = []
    favor: list[str] = []
    hipoteses_ab: list[str] = []

    dur = secao_duracao(kb, ideia, alertas, favor, hipoteses_ab)
    tit = secao_titulo(kb, ideia, alertas, favor, hipoteses_ab)
    thumb = secao_thumb(kb, ideia, alertas, favor, hipoteses_ab)
    cad = secao_cadencia(kb, ideia, alertas, favor, hipoteses_ab)
    ex_bloco = secao_exemplos(kb, ideia, caminho)
    diag = secao_diagnostico(kb, ideia, alertas, favor, hipoteses_ab)

    return {
        "ideia": asdict(ideia),
        "base": {
            "videos": kb["meta"]["videos"],
            "canais": kb["meta"]["canais"],
            "videos_indice_referencias": ex_bloco["tamanho_indice_referencias"],
            "versao_kb": kb["meta"]["versao"],
        },
        "1_diagnostico": diag,
        "2_duracao": dur,
        "3_titulo": tit,
        "4_thumbnail": thumb,
        "5_cadencia": cad,
        "6_exemplos_reais": ex_bloco["itens"],
        "6_exemplos_meta": {
            "tamanho_indice_referencias": ex_bloco["tamanho_indice_referencias"],
            "criterio_corte": ex_bloco["criterio_corte"],
        },
        "7_checklist": secao_checklist(ideia, dur, tit, thumb, cad),
    }


def para_markdown(p: dict) -> str:
    i = p["ideia"]
    d = p["1_diagnostico"]
    cob = d["cobertura_da_celula"]
    mc = d["metricas_de_confianca"]
    q_cel = mc.get("q_medio_regras_da_celula")
    if q_cel is None:
        q_med_str = "sem regras paramétricas no recorte"
    elif q_cel < 0.001:
        q_med_str = "< 0,001"
    else:
        q_med_str = fmt_num(q_cel, 3)

    L = [
        f"# Parecer da ideia: {i['titulo']}",
        "",
        f"Nicho **{i['nicho']}**, idioma **{i['idioma'].upper()}**, porte **{i['porte']}** ({d['contexto_do_porte']['faixa']}; {d['contexto_do_porte']['regime_estrutural']}). "
        f"Base estatística: {fmt_num(p['base']['videos'], 0)} vídeos longos de {p['base']['canais']} canais (índice lexical de exemplos: {fmt_num(p['base']['videos_indice_referencias'], 0)} vídeos).",
        "",
        "## 1. Diagnóstico geral",
        "",
        f"**Grau de confiança epistêmica da base para este recorte: {d['grau_de_confianca']}.** "
        f"(Calculado apenas pela cobertura da célula e pelo q médio das {mc['n_regras_da_celula_com_q']} regras da célula [{q_med_str}]; independe dos alertas da ideia.)",
    ]
    if cob.get("usou_vizinha"):
        L.append(
            f"Cobertura da célula {i['nicho']} × {i['idioma'].upper()} × {cob['grupo']}: sem dados para esta célula exata; "
            f"apoiando contexto na célula vizinha documentada {cob['vizinha_descricao']} ({cob['vizinha_canais']} canais e {fmt_num(cob['vizinha_videos'], 0)} vídeos)."
        )
    else:
        L.append(
            f"Cobertura da célula {i['nicho']} × {i['idioma'].upper()} × {cob['grupo']}: "
            f"{cob['canais']} canais e {fmt_num(cob['videos'], 0)} vídeos ({cob['avaliacao']})."
        )
    L += [
        "",
        f"> {d['teto_preditivo']}",
        "> " + " ".join(d["limites"]),
        "",
    ]

    cp = d["contexto_do_porte"]
    L.append(
        f"Contexto do porte {cp['porte']}: views medianas por vídeo {fmt_num(cp['views_mediana_video'], 0)}; "
        f"top 10% dos vídeos somam {fmt_num(cp['top10_share_pct'])}% das views; "
        f"{fmt_num(cp['anomalias_10x_por_mil'])} vídeos de 10x ou mais por mil; "
        f"intervalo mediano de {fmt_num(cp['intervalo_mediano_dias'])} dias."
    )
    L.append("")

    if d["pontos_a_favor"]:
        L += ["**Recomendações e sinais firmes a favor (q < 0,05 e IC 95% sem cruzar zero)**", ""] + [f"- {x}" for x in d["pontos_a_favor"]] + [""]
    if d["riscos"]:
        L += ["**Riscos firmes identificados (q < 0,05 e IC 95% sem cruzar zero)**", ""] + [f"- {x}" for x in d["riscos"]] + [""]
    if d.get("hipoteses_ab"):
        L += ["### Hipóteses para teste A/B (0,05 ≤ q < 0,15 ou regras sujeitas a confundimento/limites da base)", ""] + [f"- {x}" for x in d["hipoteses_ab"]] + [""]

    L += ["### Limites conhecidos desta base", ""] + [f"- {lim}" for lim in d["limites_conhecidos_desta_base"]] + [""]

    # Seção 2: Duração
    du = p["2_duracao"]
    L += [
        "## 2. Duração",
        "",
        f"Confiança máxima desta alavanca: **{du['confianca_maxima_alavanca']}**.",
    ]
    if du.get("faixa_recomendada_min"):
        f = du["faixa_recomendada_min"]
        L.append(f"Faixa de referência ({du['origem_faixa_recomendada']}): **{f[0]} a {f[1]} min**.")
    o = du["otimo_nicho_200k"]
    if o.get("otimo_min") is not None and GRUPO[i["porte"]] == "200k+":
        borda = " (ótimo na borda superior dos dados)" if o.get("na_borda") else ""
        ic_o = o.get("ic") or [None, None]
        L.append(
            f"Referência da spline 200k+ no nicho ({o.get('canais', 0)} canais): pico em {fmt_num(o['otimo_min'], 0)} min "
            f"(IC {fmt_num(ic_o[0], 0)} a {fmt_num(ic_o[1], 0)}){borda}; retorno decrescente após ~{fmt_num(o['retorno_decrescente_min'], 0)} min ({fmt_q(o['q'])})."
        )
    if du.get("otimo_porte_200k"):
        op = du["otimo_porte_200k"]
        L.append(f"Referência do porte {i['porte']} (200k+): {fmt_num(op['otimo_min'], 0)} min (IC {fmt_num(op['otimo_ic'][0], 0)} a {fmt_num(op['otimo_ic'][1], 0)}).")
    if du.get("proposta"):
        pr = du["proposta"]
        partes_prop = []
        if pr.get("efeito_curva_porte_vs_12min") is not None:
            partes_prop.append(
                f"curva do grupo ({'5k a 200k' if GRUPO[i['porte']] == 'pequenos' else '200k+'}) {fmt_pct(pr['efeito_curva_porte_vs_12min'])} contra ~12 min"
            )
        if GRUPO[i["porte"]] == "200k+" and pr.get("efeito_curva_nicho_200k_vs_12min") is not None:
            partes_prop.append(f"curva do nicho 200k+ {fmt_pct(pr['efeito_curva_nicho_200k_vs_12min'])} contra 12 min")
        if partes_prop:
            L.append(f"Proposta de {fmt_num(pr['duracao_min'], 0)} min: " + "; ".join(partes_prop) + ".")
        fe = pr.get("faixa_empirica")
        if fe:
            L.append(
                f"Na célula empírica ({i['nicho']}, {du['celula_empirica']['porte_referencia']}), a faixa {fe['faixa']} min tem {fe['n']} vídeos de {fe['canais']} canais, "
                f"múltiplo mediano {fmt_num(fe['mult_mediana'], 2)}x e {fmt_num(fe['pct_3x'])}% com 3x ou mais."
            )
    ce = du["celula_empirica"]
    if ce.get("nota_vizinha"):
        L.append(f"Nota de cobertura empírica: {ce['nota_vizinha']}")
    if ce.get("videos"):
        L.append(
            f"Duração mediana na célula ({i['nicho']} × {ce['porte_referencia']}): {fmt_num(ce['duracao_mediana'])} min; "
            f"no top 10% de cada canal: {fmt_num(ce['duracao_mediana_top10_canal'])} min."
        )
        mb = ce.get("melhor_faixa_por_pct_3x")
        if mb:
            L.append(f"Faixa com maior taxa descritiva de vídeos 3x na célula (3+ canais, 20+ vídeos): {mb['faixa']} min ({fmt_num(mb['pct_3x'])}%).")
    L += [f"- {x}" for x in du["notas"]] + [""]

    # Seção 3: Título
    t = p["3_titulo"]
    td = t["tracos_detectados"]
    L += [
        "## 3. Título",
        "",
        f"{td['caracteres']} caracteres, {td['palavras']} palavras (análise léxica em {td['idioma_analise'].upper()}). {t['nota']}",
        "",
    ]
    if t["achados"]:
        L += [
            "| Traço | Presente | Efeito no múltiplo do canal | IC 95% | q | Classificação |",
            "|---|---|---:|---|---:|---|",
        ]
        for a in t["achados"]:
            pres = "não aplicável" if a["presente"] is None else ("sim" if a["presente"] else "não")
            ic_s = f"{fmt_pct(a['ic'][0])} a {fmt_pct(a['ic'][1])}" if a.get("ic") and a["ic"][0] is not None else "sem IC parametrizado"
            L.append(
                f"| {a['traco']} | {pres} | {fmt_pct(a['efeito'])} | {ic_s} | {fmt_q(a['q']).replace('q = ', '').replace('q ', '')} | {a['confianca']} |"
            )
        L.append("")
    if t.get("lembretes_neutros"):
        L += ["**Lembretes neutros**", ""] + [f"- {x}" for x in t["lembretes_neutros"]] + [""]
    L += ["**O que não importa (ruído descartado, q ≥ 0,15 ou IC cruzando zero)**", ""] + [f"- {x}" for x in t["o_que_nao_importa"]] + [""]

    # Seção 4: Thumbnail
    th = p["4_thumbnail"]
    L += ["## 4. Thumbnail e alinhamento título + capa", ""]
    if th["padroes_detectados_nas_notas"]:
        L.append("Padrões com evidência (q < 0,15) lidos nas notas da capa:")
        for x in th["padroes_detectados_nas_notas"]:
            rot_ev = "recomendação/risco firme" if x["nivel_evidencia"] == "firme" else "hipótese para teste A/B"
            L.append(
                f"- {x['padrao']}: {fmt_pct(x['efeito_intra_canal'])} dentro do canal ({fmt_q(x['q'])}, {rot_ev}; comparação ingênua entre canais {fmt_pct(x['efeito_ingenuo'])})"
            )
        L.append("")
    if th.get("padroes_detectados_nulos_ignorados"):
        nomes_nulos = ", ".join(f"{x['padrao']} ({fmt_q(x['q'])})" for x in th["padroes_detectados_nulos_ignorados"])
        L.append(f"Elementos descritos nas notas sem efeito estatístico intra-canal (q ≥ 0,15, ignorados como recomendação/risco): {nomes_nulos}.")
        L.append("")
    if th["recomendados_no_nicho"]:
        L.append(f"Sinais com q < 0,15 no nicho {i['nicho']} (usar como hipótese de teste A/B):")
        L += [f"- {x['nome']}: {fmt_pct(x['efeito'])} ({fmt_q(x['q'])}, {x['n']} vídeos)" for x in th["recomendados_no_nicho"]]
    else:
        L.append(f"No nicho {i['nicho']}, nenhum padrão isolado de capa teve q < 0,15 após correção de múltiplos testes (sem dados com significância para esta célula).")
    if th["evitar_no_nicho"]:
        L.append("Sinais negativos com q < 0,15 no nicho: " + "; ".join(f"{x['nome']} {fmt_pct(x['efeito'])} ({fmt_q(x['q'])})" for x in th["evitar_no_nicho"]) + ".")
    if th.get("padroes_firmes_na_base"):
        L.append(
            "Padrões visuais com q < 0,05 na base agregada (10+ canais): "
            + "; ".join(f"{x['padrao']} {fmt_pct(x['efeito'])} ({fmt_q(x['q'])})" for x in th["padroes_firmes_na_base"])
            + "."
        )
    if th.get("padroes_hipotese_ab_na_base"):
        L.append(
            "Padrões visuais em zona de hipótese A/B (0,05 ≤ q < 0,15 na base agregada): "
            + "; ".join(f"{x['padrao']} {fmt_pct(x['efeito'])} ({fmt_q(x['q'])})" for x in th["padroes_hipotese_ab_na_base"])
            + "."
        )
    if th["hipoteses_raras_testaveis"]:
        L.append(
            "Combinações raras mineradas (1.802 candidatos; tratar estritamente como hipótese A/B): "
            + "; ".join(f"{x['padrao']} {fmt_pct(x['efeito'])} ({fmt_q(x['q'])}, {x['canais']} canais)" for x in th["hipoteses_raras_testaveis"])
            + "."
        )
    al = th["alinhamento_titulo_capa"]
    if al:
        L.append(
            f"Alinhamento título ↔ texto da capa (\"{al['texto_capa']}\"): sobreposição de palavras {fmt_num(al['sobreposicao_lexical'], 2)} (nível {al['nivel']}). {al['aviso_metrica']}"
        )
    L.append(
        "Mitos populares sem efeito dentro do mesmo canal: "
        + "; ".join(
            f"{m['padrao']} (entre canais {fmt_pct(m['efeito_ingenuo_entre_canais'])}, dentro do canal {fmt_pct(m['efeito_intra_canal'])})"
            for m in th["mitos_a_ignorar"]
        )
        + "."
    )
    L += [f"- {x}" for x in th["notas"]] + [""]

    # Seção 5: Cadência
    c = p["5_cadencia"]
    L += [
        "## 5. Cadência e consistência",
        "",
        f"Confiança máxima desta seção: **{c['confianca_maxima_alavanca']}**.",
    ]
    if "dias_desde_ultimo" in c:
        if GRUPO[i["porte"]] == "200k+" and c.get("efeito_curva_200k_vs_7d") is not None:
            L.append(
                f"{fmt_num(c['dias_desde_ultimo'], 0)} {'dia' if c['dias_desde_ultimo'] == 1 else 'dias'} desde o vídeo anterior "
                f"(referência descritiva na curva 200k+ vs 7 dias: {fmt_pct(c['efeito_curva_200k_vs_7d'])}; sujeita a confundimento de escopo)."
            )
        else:
            L.append(
                f"{fmt_num(c['dias_desde_ultimo'], 0)} {'dia' if c['dias_desde_ultimo'] == 1 else 'dias'} desde o vídeo anterior "
                "(curva contínua de intervalo restrita aos canais 200k+; não extrapolada para 5k a 200k)."
            )
    if c["intervalo_por_faixa_ref_5a9d"]:
        L.append(
            "Faixas de intervalo com q < 0,15 no grupo (referência 5 a 9 dias, tratadas como hipótese): "
            + "; ".join(f"{f['faixa']} {fmt_pct(f['efeito'])} ({fmt_q(f['q'])})" for f in c["intervalo_por_faixa_ref_5a9d"])
            + "."
        )
    else:
        L.append("Nenhuma faixa de intervalo teve q < 0,15 neste grupo de porte (intervalo de dias é inconclusivo isoladamente).")
    L.append(c["consistencia_tematica"]["regra"])
    ct = c["consistencia_tematica"]
    if "sobreposicao_media_com_recentes" in ct:
        ref_str = (
            fmt_num(ct["sobreposicao_entre_recentes"], 2)
            if ct.get("sobreposicao_entre_recentes") is not None
            else "sem par de referência (apenas 1 título informado)"
        )
        L.append(
            f"Sobreposição lexical de palavras com os títulos recentes: {fmt_num(ct['sobreposicao_media_com_recentes'], 2)} "
            f"(sobreposição média entre os próprios recentes: {ref_str}). {ct.get('avaliacao_recentes', '')}"
        )
    L += [f"- {x}" for x in c["notas"]] + [""]

    # Seção 6: Exemplos reais
    ex_meta = p.get("6_exemplos_meta", {})
    n_idx = ex_meta.get("tamanho_indice_referencias", p["base"].get("videos_indice_referencias", 4639))
    L += [
        f"## 6. Exemplos reais de alto desempenho no nicho (índice de {fmt_num(n_idx, 0)} vídeos)",
        "",
    ]
    if p["6_exemplos_reais"]:
        L += [
            "| Título | Canal | Porte | Idioma | Múltiplo vs mediana do canal | Views | Duração | Sobreposição de palavras |",
            "|---|---|---|---|---:|---:|---:|---:|",
        ]
        for e in p["6_exemplos_reais"]:
            tit_e = e["titulo"].replace("|", "/")
            sim_val = e.get("sobreposicao_lexical", e.get("similaridade", 0.0))
            L.append(
                f"| {tit_e} | {e['canal']} | {e['porte']} | {e['idioma'].upper()} | {fmt_num(e['mult'])}x | {fmt_num(e['views'], 0)} | {fmt_num(e['dur_min'])} min | {fmt_num(sim_val, 2)} |"
            )
        L.append("")
        L.append("Exemplos filtrados por sobreposição lexical ≥ 0,05 no mesmo nicho; servem como referência de embalagem, nunca garantia de resultado.")
    else:
        L.append(
            "Nenhum vídeo no índice de referências do nicho atingiu a sobreposição mínima de palavras (≥ 0,05) com este título; omitimos exemplos aleatórios para evitar falsas analogias."
        )

    L += ["", "## 7. Checklist pré-publicação", ""] + [f"- [ ] {x}" for x in p["7_checklist"]]
    return "\n".join(L) + "\n"


def popular_parser(ap: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Adiciona apenas os argumentos reais usados pelo advisor offline (sem flags mortas de rede/cache/-o)."""
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
    ap.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Formato de saída no stdout")
    return ap


def construir_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="idea_advisor",
        description="Parecer acionável para uma nova ideia de vídeo longo (offline, sem API, sem rede).",
    )
    return popular_parser(ap)


def main(argv: list[str] | None = None) -> int:
    a = construir_parser().parse_args(argv)
    porte = a.tier or (porte_por_inscritos(a.subscribers) if a.subscribers else "pequeno")
    ideia = Ideia(
        titulo=a.title,
        nicho=a.niche,
        idioma=a.lang,
        porte=porte,
        duracao_min=a.duration_min,
        thumb_notes=a.thumb_notes,
        texto_capa=a.thumb_text,
        dias_desde_ultimo=a.days_since_last,
        ultimo_resultado=a.last_result,
        titulos_recentes=[t.strip() for t in (a.recent_titles or "").split("||") if t.strip()],
    )
    try:
        p = aconselhar(ideia, a.kb)
    except ValueError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(p, ensure_ascii=False, indent=2) + "\n" if a.format == "json" else para_markdown(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
