"""Gera knowledge_base.json (compacto e autossuficiente) a partir dos arquivos reais do laboratório.

Uso:
    python build_knowledge_base.py [--lab PASTA_DO_LABORATORIO] [--saida knowledge_base.json]

Lê só arquivos locais (parquet e CSV das 5 frentes). Não usa rede nem API.
Todo número do JSON vem de um arquivo de resultado ou é calculado aqui a partir das duas bases
(base_mestra.parquet, 17.882 vídeos de 203 canais 200k+; base_pequenos.parquet, 8.312 vídeos
de 107 canais de 5k a 200k).
"""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
LAB_PADRAO = Path("laboratorio")  # pasta do laboratório com dados/ e frente_*/ (não versionada)

PORTES = ["pequeno", "emergente", "medio", "grande", "gigante"]
GRUPO_PORTE = {"pequeno": "pequenos", "emergente": "pequenos", "medio": "200k+", "grande": "200k+", "gigante": "200k+"}
FAIXAS_DUR = [(3, 6), (6, 10), (10, 15), (15, 20), (20, 30), (30, 45), (45, 60), (60, 10_000)]

# Lista opcional de termos a excluir das referências (títulos e nomes de canal), lida de um JSON
# {"sensivel_a_caixa": [...], "insensivel_a_caixa": [...]}. Sem o arquivo, nada é filtrado.
DENYLIST_PADRAO = LAB_PADRAO / "consolidacao" / "termos_proibidos.json"
PROIBIDOS_CS: list[str] = []
PROIBIDOS_CI: list[str] = []


def carregar_denylist(caminho: Path | None) -> None:
    global PROIBIDOS_CS, PROIBIDOS_CI
    if caminho and Path(caminho).exists():
        d = json.loads(Path(caminho).read_text(encoding="utf-8"))
        PROIBIDOS_CS = list(d.get("sensivel_a_caixa", []))
        PROIBIDOS_CI = [t.lower() for t in d.get("insensivel_a_caixa", [])]


def proibido(txt: str) -> bool:
    if not isinstance(txt, str):
        return False
    low = txt.lower()
    return any(p in txt for p in PROIBIDOS_CS) or any(p in low for p in PROIBIDOS_CI)


def r(x, nd=1):
    if x is None:
        return None
    try:
        if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
            return None
        return round(float(x), nd)
    except (TypeError, ValueError):
        return None


def pct_log(v):
    return (math.exp(v) - 1) * 100


def downsample(df: pd.DataFrame, n: int = 28) -> pd.DataFrame:
    if len(df) <= n:
        return df
    idx = np.unique(np.linspace(0, len(df) - 1, n).round().astype(int))
    return df.iloc[idx]


def carregar_bases(lab: Path) -> pd.DataFrame:
    cols = ["video_id", "channel_id", "title", "nome", "nicho", "idioma", "porte", "view_count",
            "duracao_min", "y", "y_pct_canal", "gap_ant_dias", "inscritos"]
    a = pd.read_parquet(lab / "dados/base_mestra.parquet", columns=cols)
    b = pd.read_parquet(lab / "frente_pequenos/dados/base_pequenos.parquet", columns=cols + ["subfaixa"])
    b["porte"] = b["subfaixa"]
    b = b.drop(columns=["subfaixa"])
    df = pd.concat([a, b], ignore_index=True)
    df["grupo"] = df["porte"].map(GRUPO_PORTE)
    df["mult"] = np.exp(df["y"])
    return df


def bloco_duracao(lab: Path, df: pd.DataFrame) -> dict:
    out: dict = {}
    pts = pd.read_csv(lab / "frente_ml/resultados/E_curvas_duracao_pontos.csv")
    pts = pts[pts.desfecho == "yw"]
    curvas = {}
    for g, d in pts.groupby("grupo"):
        d = downsample(d.sort_values("duracao_min"))
        curvas[g] = [[r(m, 1), r(pct_log(e)), r(pct_log(lo)), r(pct_log(hi))]
                     for m, e, lo, hi in zip(d.duracao_min, d.efeito, d.ic_lo, d.ic_hi)]
    out["curvas_200k_ref_12min"] = {"descricao": "Efeito % em views relativas ao canal contra um vídeo de 12 min do mesmo canal (spline com efeito fixo de canal, canais 200k+). Colunas: minutos, efeito, IC95 inferior, IC95 superior.", "grupos": curvas}
    res = pd.read_csv(lab / "frente_ml/resultados/E_curvas_duracao_resumo.csv")
    res = res[res.desfecho.isin(["yw", "top5_c"])]
    out["resumo_200k"] = {f"{row.grupo}|{row.desfecho}": {"otimo_min": r(row.otimo_min), "otimo_ic": [r(row.otimo_ic_lo), r(row.otimo_ic_hi)],
                                                           "retorno_decrescente_min": r(row.retorno_decrescente_min), "otimo_na_borda": bool(row.otimo_na_borda),
                                                           "q_bh": r(row.q_bh_wald, 5), "canais": int(row.canais)} for row in res.itertuples()}
    sp = pd.read_csv(lab / "frente_pequenos/resultados/peq_04d_duracao_spline.csv")
    out["curvas_pequenos_vs_200k"] = {"descricao": "Spline de duração dentro do canal (Frente 2D), efeito % contra um vídeo de cerca de 12 min do mesmo canal (arquivo peq_04d). Colunas: minutos, efeito, IC95 inferior, IC95 superior.",
                                      "grupos": {g: [[r(m), r(e), r(lo), r(hi)] for m, e, lo, hi in zip(d.duracao_min, d.efeito_pct, d.lo, d.hi)]
                                                 for g, d in ((g, downsample(d.sort_values("duracao_min"))) for g, d in sp.groupby("grupo"))}}
    fx = pd.read_csv(lab / "frente_pequenos/resultados/peq_04c_duracao_faixas.csv")
    out["faixas_ref_10a15"] = {"descricao": "Efeito % por faixa de duração contra 10 a 15 min, dentro do canal (Frente 2D).",
                               "linhas": [{"grupo": x.grupo, "faixa": x.faixa, "efeito": r(x.efeito_pct), "ic": [r(x.ic_lo_pct), r(x.ic_hi_pct)], "p": r(x.p, 4), "n": int(x.n_faixa)} for x in fx.itertuples()]}
    # Curva empírica por nicho x porte, direto das bases (múltiplo vs mediana do canal)
    emp = {}
    for (nicho, porte), d in df.groupby(["nicho", "porte"]):
        linhas = []
        for lo, hi in FAIXAS_DUR:
            s = d[(d.duracao_min >= lo) & (d.duracao_min < hi)]
            if len(s) < 15:
                continue
            linhas.append({"faixa": f"{lo}-{hi if hi < 10_000 else ''}".rstrip("-") + ("+" if hi >= 10_000 else ""),
                           "lo": lo, "hi": hi if hi < 10_000 else None, "n": int(len(s)), "canais": int(s.channel_id.nunique()),
                           "mult_mediana": r(s.mult.median(), 2), "pct_3x": r((s.mult >= 3).mean() * 100), "pct_top10_canal": r((s.y_pct_canal >= 0.9).mean() * 100)})
        top = d[d.y_pct_canal >= 0.9]
        emp[f"{nicho}|{porte}"] = {"n": int(len(d)), "canais": int(d.channel_id.nunique()), "duracao_mediana": r(d.duracao_min.median()),
                                   "duracao_mediana_top10_canal": r(top.duracao_min.median()) if len(top) else None, "faixas": linhas}
    out["empirico_nicho_porte"] = {"descricao": "Calculado das duas bases: por nicho x porte e faixa de duração, múltiplo mediano de views contra a mediana do próprio canal (exp(y)), % de vídeos com 3x ou mais e % no top 10% do próprio canal. Descritivo, sem controle de idade.", "celulas": emp}
    return out


def bloco_titulo(lab: Path) -> dict:
    b1 = pd.read_csv(lab / "frente_arquetipos/resultados/b1_tracos_titulo_efeitos.csv")
    b1 = b1[b1.desfecho == "y_li_w"]
    linhas = []
    for x in b1.itertuples():
        linhas.append({"variavel": x.variavel, "rotulo": x.rotulo, "amostra": x.amostra, "efeito": r(x.efeito_pct), "ic": [r(x.lo_pct), r(x.hi_pct)],
                       "q": r(x.q_bh, 5), "n_pos": int(x.n_pos), "canais_pos": int(x.canais_pos), "unidade": x.unidade})
    peq = pd.read_csv(lab / "frente_pequenos/resultados/peq_06_universal_vs_especifico.csv")
    pv = [{"variavel": x.variavel, "rotulo": x.rotulo, "pequenos": r(x.pequenos_pct), "pequenos_ic": [r(x.pequenos_lo), r(x.pequenos_hi)], "pequenos_q": r(x.pequenos_q, 4),
           "grandes": r(x.grandes_pct), "grandes_ic": [r(x.grandes_lo), r(x.grandes_hi)], "grandes_q": r(x.grandes_q, 4), "dif_q": r(x.dif_q, 4), "classe": x.classe}
          for x in peq.itertuples()]
    b2 = pd.read_csv(lab / "frente_arquetipos/resultados/b2_redundancia_vs_complementaridade.csv")
    b2 = b2[(b2.desfecho == "y_li_w") & (b2.amostra.isin(["todos", "pt", "en"]))]
    sim = [{"teste": x.teste, "amostra": x.amostra, "variavel": x.variavel, "efeito": r(x.efeito_pct), "ic": [r(x.lo_pct), r(x.hi_pct)], "q": r(x.q_bh, 5)} for x in b2.itertuples()]
    oos = pd.read_csv(lab / "frente_arquetipos/resultados/b5_poder_preditivo_titulos_oos.csv")
    gp = pd.read_csv(lab / "frente_arquetipos/resultados/b1_gancho_principal_vs_descritivo.csv")
    gp = gp[gp.desfecho == "y_li_w"]
    ganchos = [{"gancho": x.gancho, "amostra": x.amostra, "efeito": r(x.efeito_pct), "ic": [r(x.lo_pct), r(x.hi_pct)], "q": r(x.q_bh, 5), "n_pos": int(x.n_pos)} for x in gp.itertuples()]
    return {"ganchos_principais_vs_descritivo": {"descricao": "Frente 2C: gancho principal do título contra título descritivo, efeito fixo de canal.", "linhas": ganchos},
            "tracos_200k": {"descricao": "Frente 2C: efeito % no múltiplo relativo ao canal (efeito fixo de canal, controle de duração, IC bootstrap por canal, q BH por recorte).", "linhas": linhas},
            "pequenos_vs_200k": {"descricao": "Frente 2D: efeito % dentro do canal nos pequenos (5k a 200k) e nos 200k+, com q BH e q da diferença.", "linhas": pv},
            "titulo_capa": {"descricao": "Frente 2C: repetir x complementar e similaridade semântica título x texto da capa.", "linhas": sim},
            "poder_preditivo_oos": oos.round(4).to_dict(orient="records")}


def bloco_thumb(lab: Path) -> dict:
    ps = pd.read_csv(lab / "frente_thumbs/resultados/padroes_stats.csv")
    fichas = json.loads((lab / "frente_thumbs/dados/fichas_clusters.json").read_text())
    nomes = {k: v.get("nome", "") for k, v in fichas.items()}
    cols = ["padrao", "grupo", "descricao", "n", "n_canais", "share_top_canal", "efeito_pct", "efeito_lo_pct", "efeito_hi_pct", "q_bh", "naive_views_pct", "confianca"]
    elig = ps[(ps.n_canais >= 10) & (ps.share_top_canal < 0.5)].copy()

    def lin(x):
        nome = nomes.get(x.padrao, "")
        return {"padrao": x.padrao, "nome": (f"{x.padrao} {nome}" if nome and not proibido(nome) else x.padrao), "grupo": x.grupo, "n": int(x.n), "canais": int(x.n_canais), "efeito": r(x.efeito_pct), "ic": [r(x.efeito_lo_pct), r(x.efeito_hi_pct)],
                "q": r(x.q_bh, 5), "efeito_ingenuo": r(x.naive_views_pct), "confianca": x.confianca}
    elig = elig.sort_values("efeito_pct", ascending=False)
    todos = {x.padrao: lin(x) for x in ps[cols].itertuples() if x.n_canais >= 10}
    por_nicho = pd.read_csv(lab / "frente_thumbs/resultados/padroes_por_nicho.csv")
    pn = {}
    for nicho, d in por_nicho.groupby("nicho"):
        d = d[d.padrao.isin(elig.padrao)]
        pos = d[(d.efeito_pct > 0) & (d.n >= 30)].sort_values(["q_bh", "efeito_pct"], ascending=[True, False]).head(6)
        neg = d[(d.efeito_pct < 0) & (d.n >= 30)].sort_values(["q_bh", "efeito_pct"]).head(4)
        pn[nicho] = {"melhores": [{"padrao": x.padrao, "nome": todos.get(x.padrao, {}).get("nome", x.padrao), "n": int(x.n), "efeito": r(x.efeito_pct), "q": r(x.q_bh, 3)} for x in pos.itertuples()],
                     "piores": [{"padrao": x.padrao, "nome": todos.get(x.padrao, {}).get("nome", x.padrao), "n": int(x.n), "efeito": r(x.efeito_pct), "q": r(x.q_bh, 3)} for x in neg.itertuples()]}
    raros = pd.read_csv(lab / "frente_thumbs/resultados/padroes_raros.csv").sort_values("efeito_pct", ascending=False).head(15)
    rr = [{"padrao": x.padrao, "nome": (f"{x.padrao} {nomes.get(x.padrao.upper().replace('HDB100-', 'HDB-'), '')}".strip() if x.tipo.startswith("cluster") else x.padrao), "tipo": x.tipo, "n": int(x.n), "canais": int(x.n_canais), "efeito": r(x.efeito_pct), "ic": [r(pct_log(x.ic_lo)), r(pct_log(x.ic_hi))],
           "boot": [r(pct_log(x.boot_lo)), r(pct_log(x.boot_hi))], "q": r(x.q_bh, 3)} for x in raros.itertuples()]
    oos = json.loads((lab / "frente_thumbs/resultados/poder_preditivo_oos.json").read_text())
    pv = pd.read_csv(lab / "frente_pequenos/resultados/peq_05b_visual_embeddings.csv")
    an = pd.read_csv(lab / "frente_pequenos/resultados/peq_02_anomalias_vs_controles_gemini.csv")
    return {"ranking": {"descricao": "Frente 2B: efeito % intra-canal (efeito fixo de canal + log idade + log duração), IC 95% com erro agrupado por canal, q BH sobre os 191 padrões. Filtro: 10+ canais e canal dominante abaixo de 50%.",
                        "melhores": [lin(x) for x in elig.head(15).itertuples()],
                        "piores": [lin(x) for x in elig.sort_values("efeito_pct").head(10).itertuples()]},
            "padroes": todos,
            "por_nicho": pn,
            "raros": {"descricao": "1.802 candidatos testados; tratar como hipóteses para teste A/B, não regras.", "linhas": rr},
            "poder_preditivo_oos": oos,
            "pequenos_visual_embeddings": pv.round(4).to_dict(orient="records"),
            "pequenos_breakouts_vs_controles": an.round(3).to_dict(orient="records")}


def bloco_cadencia(lab: Path) -> dict:
    f = pd.read_csv(lab / "frente_ml/resultados/F_intervalo_spline_pontos.csv")
    f = f[f.desfecho == "yw"]
    curvas = {g: [[r(dd, 2), r(pct_log(e)), r(pct_log(lo)), r(pct_log(hi))] for dd, e, lo, hi in zip(d.dias, d.efeito, d.ic_lo, d.ic_hi)]
              for g, d in ((g, downsample(d.sort_values("dias"), 30)) for g, d in f.groupby("grupo") if g in ("geral", "porte=medio", "porte=grande", "porte=gigante"))}
    peq = pd.read_csv(lab / "frente_pequenos/resultados/peq_04e_intervalo_entre_videos.csv")
    mom = pd.read_csv(lab / "frente_pequenos/resultados/peq_04f_momentum.csv")
    pvi = pd.read_csv(lab / "frente_ml/resultados/F_pos_viral_x_intervalo.csv")
    vol = pd.read_csv(lab / "frente_ml/resultados/F_volume_recente.csv")
    nov = pd.read_csv(lab / "frente_pequenos/resultados/peq_05_novidade_tematica.csv")
    return {"intervalo_200k_ref_7d": {"descricao": "Efeito % contra intervalo de 7 dias desde o vídeo anterior (spline, efeito fixo de canal). Colunas: dias, efeito, IC95 inf, IC95 sup.", "grupos": curvas},
            "intervalo_faixas_ref_5a9d": [{"grupo": x.grupo, "faixa": x.faixa, "efeito": r(x.efeito_pct), "ic": [r(x.ic_lo_pct), r(x.ic_hi_pct)], "q": r(x.q_bh, 5), "n": int(x.n)} for x in peq.itertuples()],
            "momentum": [{"grupo": x.grupo, "condicao": x.condicao, "efeito": r(x.efeito_pct), "ic": [r(x.ic_lo_pct), r(x.ic_hi_pct)], "n": int(x.n)} for x in mom.itertuples()],
            "pos_extremo_x_intervalo": [{"modelo": x.modelo, "termo": x.termo, "efeito": r(x.efeito_pct), "ic": [r(x.ic_lo_pct), r(x.ic_hi_pct)], "p": r(x.p, 4)} for x in pvi.itertuples()],
            "volume_recente": [{"grupo": x.grupo, "variavel": x.variavel, "desfecho": x.desfecho, "efeito_por_dobro": r(x.efeito_pct_por_dobro), "q": r(x.q_bh, 5)} for x in vol.itertuples()],
            "novidade_tematica": nov.round(4).to_dict(orient="records")}


def bloco_portes(lab: Path, df: pd.DataFrame) -> dict:
    p1 = pd.read_csv(lab / "frente_pequenos/resultados/peq_01_concentracao_volatilidade_anomalias_5portes.csv")
    out = {}
    for x in p1.itertuples():
        d = df[df.porte == x.porte]
        out[x.porte] = {"canais": int(x.canais), "videos": int(x.videos), "views_mediana_video": r(x.views_mediana_video, 0),
                        "top10_share": r(x.top10 * 100), "top10_ic": [r(x.top10_lo * 100), r(x.top10_hi * 100)], "gini": r(x.gini, 3),
                        "dp_y": r(x.sd_y, 3), "anomalias_10x_por_mil": r(x.anomalia10x_por_mil), "anomalias_10x_ic": [r(x.anomalia10x_lo), r(x.anomalia10x_hi)],
                        "anomalias_robustas_por_mil": r(x.anomalia_robusta_por_mil), "intervalo_mediano_dias": r(d.gap_ant_dias.median()),
                        "duracao_mediana_min": r(d.duracao_min.median()), "inscritos_mediana": r(d.drop_duplicates("channel_id").inscritos.median(), 0)}
    return out


def bloco_nicho_idioma(lab: Path, df: pd.DataFrame) -> dict:
    out = {}
    for (nicho, idioma, grupo), d in df.groupby(["nicho", "idioma", "grupo"]):
        out[f"{nicho}|{idioma}|{grupo}"] = {"videos": int(len(d)), "canais": int(d.channel_id.nunique()), "views_mediana": r(d.view_count.median(), 0),
                                             "duracao_mediana": r(d.duracao_min.median()), "intervalo_mediano_dias": r(d.gap_ant_dias.median()),
                                             "pct_3x": r((d.mult >= 3).mean() * 100, 2), "pct_10x": r((d.mult >= 10).mean() * 100, 2)}
    g = pd.read_csv(lab / "frente_ml/resultados/G_mapa_nicho_x_idioma.csv")
    g = g[g.limiar == ">=3x"]
    eb = {f"{x.nicho}|{x.idioma}": {"taxa_eb_3x_pct": r(x.taxa_eb * 100, 2), "lift_vs_global": r(x.lift_vs_global, 2), "confiavel": bool(x.confiavel)} for x in g.itertuples()}
    return {"celulas": out, "breakout_eb_200k": eb}


def bloco_referencias(df: pd.DataFrame, por_celula: int = 70) -> dict:
    d = df[(df.mult >= 2) & df.title.notna()].copy()
    d = d[~d.title.map(proibido) & ~d.nome.map(proibido)]
    d = d.sort_values("y", ascending=False)
    d = d.groupby(["nicho", "idioma", "porte"], group_keys=False).head(por_celula)
    campos = ["titulo", "canal", "nicho", "idioma", "porte", "mult", "views", "dur_min", "video_id"]
    linhas = [[t, c, n, i, p, r(m, 1), int(v), r(du, 1), vid] for t, c, n, i, p, m, v, du, vid in
              zip(d.title, d.nome, d.nicho, d.idioma, d.porte, d.mult, d.view_count, d.duracao_min, d.video_id)]
    return {"descricao": f"Até {por_celula} vídeos de maior múltiplo (2x ou mais a mediana do próprio canal) por nicho x idioma x porte, das duas bases reais. Usado para busca lexical TF-IDF no motor.",
            "campos": campos, "linhas": linhas}


def limpar(o):
    """Troca NaN/inf por None e tipos numpy por tipos nativos, recursivamente."""
    if isinstance(o, dict):
        return {str(k): limpar(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [limpar(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        f = float(o)
        return None if (math.isnan(f) or math.isinf(f)) else round(f, 5)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def construir(lab: Path) -> dict:
    df = carregar_bases(lab)
    kb = {
        "meta": {
            "versao": "1.0.0",
            "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "videos": int(len(df)), "canais": int(df.channel_id.nunique()),
            "videos_200k": int((df.grupo == "200k+").sum()), "canais_200k": int(df[df.grupo == "200k+"].channel_id.nunique()),
            "videos_pequenos": int((df.grupo == "pequenos").sum()), "canais_pequenos": int(df[df.grupo == "pequenos"].channel_id.nunique()),
            "nichos": sorted(df.nicho.unique().tolist()), "idiomas": sorted(df.idioma.unique().tolist()), "portes": PORTES,
            "faixas_porte": {"pequeno": "5k a 49.999 inscritos", "emergente": "50k a 199.999", "medio": "200k a 2M", "grande": "2M a 10M", "gigante": "10M ou mais"},
            "alvo": "y = log(views do vídeo) menos log da mediana de views do próprio canal; múltiplo = exp(y).",
            "teto_preditivo": {
                "titulo_r2_oos_melhor": 0.018, "titulo_auc_top5_dentro_canal": "0,53 a 0,54",
                "thumb_r2_oos_intra_canal_embeddings": 0.025, "ml_r2_oos_canais_novos": "0,016 (LightGBM, yw)",
                "ml_auc_top5_canal_canais_novos": 0.583, "melhor_preditor_top5_global": "volatilidade histórica do canal (AUC 0,744)"},
            "limites": ["A base não tem CTR, impressões, retenção, tempo de exibição, origem de tráfego, inscritos por vídeo nem transcrições.",
                        "Associação, não causa. Título, capa, legenda e capítulos foram lidos no dia da coleta (podem ter sido editados depois do resultado).",
                        "Canais pequenos vêm da busca de vídeos recentes: representam pequenos ativos e visíveis, não o pequeno típico."],
        },
        "portes": bloco_portes(lab, df),
        "duracao": bloco_duracao(lab, df),
        "titulo": bloco_titulo(lab),
        "thumbnail": bloco_thumb(lab),
        "cadencia": bloco_cadencia(lab),
        "nicho_idioma": bloco_nicho_idioma(lab, df),
        "referencias": bloco_referencias(df),
    }
    return kb


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lab", default=str(LAB_PADRAO))
    ap.add_argument("--saida", default="youtube_seo/advisor/knowledge_base.json")
    ap.add_argument("--denylist", default=str(DENYLIST_PADRAO), help="JSON opcional com termos a excluir das referências")
    a = ap.parse_args()
    carregar_denylist(Path(a.denylist))
    kb = limpar(construir(Path(a.lab)))
    txt = json.dumps(kb, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    Path(a.saida).write_text(txt, encoding="utf-8")
    print(f"knowledge_base.json: {len(txt.encode('utf-8')) / 1e6:.2f} MB, {kb['meta']['videos']} vídeos, {kb['meta']['canais']} canais, {len(kb['referencias']['linhas'])} referências")


if __name__ == "__main__":
    main()
