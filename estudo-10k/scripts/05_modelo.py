"""Etapa 5: modelo de efeitos mistos + robustez. Saídas: resultados/*.csv e graficos/*.png"""
import numpy as np, pandas as pd, statsmodels.formula.api as smf, statsmodels.api as sm, warnings, os, json
from statsmodels.stats.multitest import multipletests
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; plt.rcParams["text.parse_math"] = False
warnings.filterwarnings("ignore"); os.makedirs("resultados", exist_ok=True)
df = pd.read_parquet("dados/dataset.parquet")
# unidades naturais para leitura simples
df["titulo_10chars"] = df.titulo_chars/10
df["desc_dobro"] = df.log_desc/np.log(2)
df["duracao_dobro"] = df.log_duracao/np.log(2)
df["tags_dobro"] = df.log_n_tags/np.log(2)
df["links_dobro"] = np.log1p(df.desc_links)/np.log(2)
df["hashtags_dobro"] = np.log1p(df.desc_hashtags)/np.log(2)
if "ocr_n_palavras" in df: df["ocr_5mais_palavras"] = np.where(df.ocr_n_palavras.notna(), (df.ocr_n_palavras>=5).astype(float), np.nan)
for c in ["thumb_brilho","thumb_contraste","thumb_saturacao","thumb_colorido","thumb_bordas"]:
    df[c+"_dp"] = (df[c]-df[c].mean())/df[c].std()
ROT = {"titulo_10chars":"Título: +10 caracteres","tem_numero":"Título com número","tem_dinheiro":"Título com dinheiro ($, R$, mil, milhão)",
 "tem_pergunta":"Título com pergunta (?)","tem_exclamacao":"Título com exclamação (!)","tem_palavra_caps":"Título com palavra em CAIXA ALTA",
 "titulo_todo_caps":"Título inteiro em CAIXA ALTA","tem_emoji":"Título com emoji","tem_separador":"Título com separador (| : -)",
 "tem_parenteses":"Título com parênteses/colchetes","tem_eu":"Título em 1ª pessoa (eu/meu/I/my)","tem_voce":"Título fala com você (você/you)",
 "tem_colab":"Título com colab/versus (ft., vs, x, @)","palavra_chave_inicio":"Início do título repetido em tags/descrição",
 "desc_dobro":"Descrição: dobro do tamanho","links_dobro":"Descrição: dobro de links","hashtags_dobro":"Descrição: dobro de hashtags",
 "tem_capitulos":"Tem capítulos (3+)","sem_tags":"Sem nenhuma tag","tags_dobro":"Tags: dobro da quantidade","duracao_dobro":"Duração: dobro",
 "legenda_manual":"Legenda enviada pelo canal","multi_audio":"Áudio em 2+ idiomas (dublagem)","fim_de_semana":"Publicado no fim de semana",
 "thumb_rosto_grande":"Miniatura com rosto grande","thumb_brilho_dp":"Miniatura mais clara (+1 desvio)","thumb_contraste_dp":"Miniatura com mais contraste (+1 desvio)",
 "thumb_saturacao_dp":"Miniatura mais saturada (+1 desvio)","thumb_bordas_dp":"Miniatura mais 'carregada' (+1 desvio)",
 "thumb_tem_rosto":"Miniatura com rosto (detector simples)","ocr_tem_texto":"Miniatura com texto escrito","ocr_5mais_palavras":"Miniatura com 5+ palavras",
 "ocr_repete_titulo":"Texto da miniatura repete o título","ocr_numero":"Miniatura com número","ocr_dinheiro":"Miniatura com símbolo de dinheiro",
 "ocr_caps":"Texto da miniatura em CAIXA ALTA","idioma_declarado":"Idioma do áudio declarado no envio"}
FEATS = list(ROT)
FEATS = [f for f in FEATS if f in df and df[f].notna().mean()>0.9 and df[f].nunique()>1 and df[f].value_counts(normalize=True).iloc[0] < 0.995]
d = df.dropna(subset=FEATS+["y","log_idade"]).copy()
ctrl = "log_idade + C(faixa_hora) + C(nicho) + C(idioma) + C(porte) + C(categoria)"
form = "y ~ " + " + ".join(FEATS) + " + " + ctrl
m = smf.mixedlm(form, d, groups=d.channel_id).fit(method="lbfgs", reml=True)
def tab(model, names, tag):
    p = model.params.reindex(names); se = model.bse.reindex(names); pv = model.pvalues.reindex(names)
    q = pd.Series(np.nan, index=names); ok = pv.notna(); q[ok] = multipletests(pv[ok], method="fdr_bh")[1]
    t = pd.DataFrame(dict(variavel=names, rotulo=[ROT[n] for n in names], coef=p.values, ep=se.values, p=pv.values, q_bh=q.values,
        efeito_pct=(np.exp(p)-1).values*100, ic_baixo_pct=(np.exp(p-1.96*se)-1).values*100, ic_alto_pct=(np.exp(p+1.96*se)-1).values*100,
        pct_videos_com=[(d[n]>0).mean()*100 if set(d[n].dropna().unique())<= {0,1} else np.nan for n in names]))
    t.to_csv(f"resultados/{tag}.csv", index=False); return t
T = tab(m, FEATS, "efeitos_modelo_misto")
# robustez 1: dentro do canal (tira a média do canal de tudo), erro-padrão agrupado por canal
def within(sub):
    X = sub[FEATS+["log_idade"]].astype(float); X = pd.concat([X, pd.get_dummies(sub.faixa_hora, drop_first=True, dtype=float)], axis=1)
    Xd = X - X.groupby(sub.channel_id.values).transform("mean"); yd = sub.y - sub.y.groupby(sub.channel_id).transform("mean")
    keep = Xd.columns[Xd.std()>0]
    return sm.OLS(yd, Xd[keep]).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(sub.channel_id)[0]}), keep
w, _ = within(d); W = tab(w, FEATS, "efeitos_dentro_do_canal")
# robustez 2: estabilidade por idioma e nicho (sinal do coeficiente)
stab = {}
for col in ["idioma","nicho"]:
    for v, sub in d.groupby(col):
        if sub.channel_id.nunique() < 6: continue
        r, keep = within(sub); stab[f"{col}={v}"] = r.params.reindex(FEATS)
S = pd.DataFrame(stab); S.to_csv("resultados/estabilidade_coef.csv")
sinal = np.sign(T.set_index("variavel").coef)
niche_cols = [c for c in S if c.startswith("nicho=")]
T["nichos_mesmo_sinal"] = [f"{int((np.sign(S.loc[f,niche_cols])==sinal[f]).sum())}/{S.loc[f,niche_cols].notna().sum()}" for f in FEATS]
T["pt"] = [S.loc[f,"idioma=pt"] for f in FEATS]; T["en"] = [S.loc[f,"idioma=en"] for f in FEATS]
T["pt_pct"] = (np.exp(T.pt)-1)*100; T["en_pct"] = (np.exp(T.en)-1)*100
# robustez 3: validação fora da amostra (5 grupos de canais)
from sklearn.model_selection import GroupKFold
X = d[FEATS+["log_idade"]].astype(float); Xd = X - X.groupby(d.channel_id.values).transform("mean")
yd = d.y - d.y.groupby(d.channel_id).transform("mean")
r2 = []
for tr, te in GroupKFold(5).split(Xd, yd, d.channel_id):
    b = np.linalg.lstsq(Xd.iloc[tr].values, yd.iloc[tr].values, rcond=None)[0]
    pred = Xd.iloc[te].values @ b; r2.append(1 - ((yd.iloc[te]-pred)**2).sum()/((yd.iloc[te])**2).sum())
# proporção da variação das variáveis que acontece dentro do canal (só ela pode ser medida aqui)
dentro = {f: float((Xd[f].var()/X[f].var()) if X[f].var()>0 else np.nan) for f in FEATS}
T["variacao_dentro_canal"] = [dentro[f] for f in FEATS]
T = T.merge(W[["variavel","efeito_pct","ic_baixo_pct","ic_alto_pct","q_bh"]].rename(columns=lambda c: c if c=="variavel" else "dentro_"+c), on="variavel")
T.sort_values("efeito_pct").to_csv("resultados/tabela_final.csv", index=False)
resumo = dict(n_videos=len(d), n_canais=int(d.channel_id.nunique()), r2_fora_amostra=[round(x,4) for x in r2], r2_medio=float(np.mean(r2)),
   dp_y=float(d.y.std()), var_canal=float(m.cov_re.iloc[0,0]), var_resid=float(m.scale),
   pct_y_acima_2x=float((d.y>np.log(2)).mean()), pct_y_abaixo_metade=float((d.y<np.log(.5)).mean()))
json.dump(resumo, open("resultados/resumo.json","w"), indent=1); print(json.dumps(resumo, indent=1))
print(T[["rotulo","efeito_pct","ic_baixo_pct","ic_alto_pct","q_bh","dentro_efeito_pct","dentro_q_bh","nichos_mesmo_sinal","pt_pct","en_pct","pct_videos_com"]].round(3).to_string())
# nome próprio (só títulos que não estão em Title Case)
sub = d[d.tem_nome_proprio.notna()]
try:
    mp = smf.mixedlm("y ~ tem_nome_proprio + titulo_10chars + duracao_dobro + " + ctrl.replace(" + C(categoria)", ""), sub, groups=sub.channel_id).fit(method=["lbfgs","powell"])
    b, e, pvn, metodo = mp.params.tem_nome_proprio, mp.bse.tem_nome_proprio, mp.pvalues.tem_nome_proprio, "misto"
except Exception:
    yy = sub.y - sub.y.groupby(sub.channel_id).transform("mean"); XX = sub[["tem_nome_proprio","titulo_10chars","duracao_dobro","log_idade"]].astype(float)
    XX = XX - XX.groupby(sub.channel_id.values).transform("mean")
    mp = sm.OLS(yy, XX).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(sub.channel_id)[0]})
    b, e, pvn, metodo = mp.params.tem_nome_proprio, mp.bse.tem_nome_proprio, mp.pvalues.tem_nome_proprio, "dentro_do_canal"
np_ = dict(n=len(sub), metodo=metodo, efeito_pct=(np.exp(b)-1)*100, ic=[(np.exp(b+s_*1.96*e)-1)*100 for s_ in (-1,1)], p=pvn)
json.dump(np_, open("resultados/nome_proprio.json","w"), indent=1); print("nome proprio", np_)
# ---------- gráficos ----------
G = T.sort_values("dentro_efeito_pct").copy()
G["efeito_pct"], G["ic_baixo_pct"], G["ic_alto_pct"], G["q_bh"] = G.dentro_efeito_pct, G.dentro_ic_baixo_pct, G.dentro_ic_alto_pct, G.dentro_q_bh   # versão conservadora (erro agrupado por canal)
fig, ax = plt.subplots(figsize=(9, 0.33*len(G)+1.5))
cor = ["#1a7f37" if (q<0.05 and e>0) else "#cf222e" if (q<0.05 and e<0) else "#8c959f" for q,e in zip(G.q_bh, G.efeito_pct)]
ax.errorbar(G.efeito_pct, range(len(G)), xerr=[G.efeito_pct-G.ic_baixo_pct, G.ic_alto_pct-G.efeito_pct], fmt="none", ecolor=cor, elinewidth=2)
ax.scatter(G.efeito_pct, range(len(G)), c=cor, zorder=3); ax.axvline(0, color="k", lw=.8)
ax.set_yticks(range(len(G))); ax.set_yticklabels(G.rotulo, fontsize=8)
ax.set_xlabel("% de views a mais (ou a menos) que o normal do próprio canal\n(comparação dentro do canal, margem de erro agrupada por canal;\nverde/vermelho = passa na correção de Benjamini-Hochberg a 5%, cinza = incerto)")
ax.set_title(f"O que acompanha vídeos acima do padrão do canal ({len(d):,} vídeos, {d.channel_id.nunique()} canais)".replace(",", "."), fontsize=10)
plt.tight_layout(); plt.savefig("graficos/01_efeitos_principais.png", dpi=150); plt.close()
# heatmap de estabilidade por nicho
H = (np.exp(S[niche_cols])-1)*100; H = H.loc[G.variavel]
fig, ax = plt.subplots(figsize=(10, 0.33*len(G)+2)); lim = 40
im = ax.imshow(H.clip(-lim,lim).values, cmap="RdYlGn", vmin=-lim, vmax=lim, aspect="auto")
ax.set_yticks(range(len(H))); ax.set_yticklabels([ROT[v] for v in H.index], fontsize=8)
ax.set_xticks(range(len(niche_cols))); ax.set_xticklabels([c.split("=")[1] for c in niche_cols], rotation=45, ha="right", fontsize=8)
plt.colorbar(im, label="% vs normal do canal (cortado em ±40%)"); ax.set_title("O efeito se repete em cada nicho?", fontsize=10)
plt.tight_layout(); plt.savefig("graficos/02_estabilidade_por_nicho.png", dpi=150); plt.close()
# curvas simples dentro do canal (mediana do alvo por faixa)
def curva(col, bins, labels, fname, titulo):
    dd = d.copy(); dd["faixa"] = pd.cut(dd[col], bins, labels=labels)
    dd["yc"] = dd.y - dd.y.groupby(dd.channel_id).transform("mean")
    g = dd.groupby("faixa", observed=True).yc.agg(["mean","sem","count"])
    fig, ax = plt.subplots(figsize=(7,4)); x = range(len(g))
    ax.bar(x, (np.exp(g["mean"])-1)*100, yerr=[(np.exp(g["mean"])-np.exp(g["mean"]-1.96*g["sem"]))*100, (np.exp(g["mean"]+1.96*g["sem"])-np.exp(g["mean"]))*100], color="#0969da", capsize=3)
    ax.set_xticks(list(x)); ax.set_xticklabels([f"{i}\n(n={n})" for i,n in zip(g.index, g["count"])], fontsize=8); ax.axhline(0,color="k",lw=.8)
    ax.set_ylabel("% vs média do próprio canal"); ax.set_title(titulo, fontsize=10); plt.tight_layout(); plt.savefig(fname, dpi=150); plt.close()
    g.to_csv(fname.replace("graficos/","resultados/").replace(".png",".csv"))
curva("titulo_chars", [0,30,45,60,75,90,200], ["<30","30-44","45-59","60-74","75-89","90+"], "graficos/03_tamanho_titulo.png", "Tamanho do título (caracteres), comparado dentro do canal")
curva("duracao_min", [0,5,10,15,20,30,60,1e4], ["<5","5-10","10-15","15-20","20-30","30-60","60+"], "graficos/04_duracao.png", "Duração (minutos), comparada dentro do canal")
curva("desc_chars", [-1,200,500,1000,2000,3500,6000], ["<200","200-499","500-999","1000-1999","2000-3499","3500+"], "graficos/05_descricao.png", "Tamanho da descrição (caracteres), comparado dentro do canal")
curva("hora_local", [-1,5,11,17,23], ["0-5h","6-11h","12-17h","18-23h"], "graficos/06_hora.png", "Hora de publicação (fuso do público), comparada dentro do canal")
print("ok")
