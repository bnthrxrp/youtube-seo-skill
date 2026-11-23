"""Etapa 7: traços de miniatura lidos pelo Gemini (04d) no modelo cauteloso: comparação dentro do canal, erro agrupado por canal,
controles de título/descrição/tags/duração/idade/hora, Benjamini-Hochberg só entre os traços de miniatura, estabilidade por idioma e nicho,
e modelo de efeitos mistos como checagem. Saídas: resultados/gemini_*.csv, graficos/09-11*.png"""
import numpy as np, pandas as pd, statsmodels.api as sm, statsmodels.formula.api as smf, warnings, json
from statsmodels.stats.multitest import multipletests
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; plt.rcParams["text.parse_math"] = False
warnings.filterwarnings("ignore")
df = pd.read_parquet("dados/dataset.parquet")
g = pd.read_json("dados/thumbs_gemini.jsonl", lines=True).drop_duplicates("video_id")
d = df.merge(g, on="video_id", how="inner")
B = lambda s: s.astype(str).str.lower().isin(["true","1"]).astype(float)
d["gm_rosto"] = (d.n_rostos>0).astype(float)
d["gm_rosto_grande"] = B(d.rosto_ocupa_grande_area) * d.gm_rosto
d["gm_olhar"] = B(d.olhar_camera) * d.gm_rosto
for e in ["surpresa","feliz","seria","medo","raiva","triste","neutra"]: d[f"gm_exp_{e}"] = (d.expressao==e).astype(float)
d["gm_seta"] = B(d.tem_seta_ou_circulo); d["gm_objeto"] = B(d.tem_objeto_destaque)
d["gm_antes_depois"] = B(d.antes_depois_ou_comparacao); d["gm_num_dinheiro"] = B(d.numero_ou_dinheiro_visivel)
d["gm_texto"] = (d.n_palavras_texto>0).astype(float); d["gm_5palavras"] = (d.n_palavras_texto>=5).astype(float)
d["gm_texto_repete"] = (d.texto_repete_titulo=="repete").astype(float); d["gm_texto_complementa"] = (d.texto_repete_titulo=="complementa").astype(float)
d["gm_4elementos"] = (d.n_elementos_principais>=4).astype(float)
for y in ["montagem","ilustracao","3d","jogo","grafico"]: d[f"gm_estilo_{y}"] = (d.estilo==y).astype(float)
for f in ["liso","ilustrado","tela","colagem"]: d[f"gm_fundo_{f}"] = (d.fundo==f).astype(float)
ROT = {"gm_rosto":"Tem rosto","gm_rosto_grande":"Rosto grande","gm_olhar":"Rosto olhando para a câmera",
 "gm_exp_surpresa":"Expressão de surpresa/choque","gm_exp_feliz":"Expressão feliz","gm_exp_seria":"Expressão séria/concentrada","gm_exp_medo":"Expressão de medo/tensão",
 "gm_exp_raiva":"Expressão de raiva","gm_exp_triste":"Expressão triste","gm_seta":"Seta ou círculo de destaque","gm_objeto":"Objeto/produto em destaque",
 "gm_antes_depois":"Antes/depois ou comparação","gm_num_dinheiro":"Número ou dinheiro visível","gm_texto":"Tem texto escrito","gm_5palavras":"5+ palavras escritas",
 "gm_texto_repete":"Texto repete o título","gm_texto_complementa":"Texto complementa o título","gm_4elementos":"4+ elementos principais",
 "gm_estilo_montagem":"Estilo: montagem/foto editada","gm_estilo_ilustracao":"Estilo: ilustração","gm_estilo_3d":"Estilo: animação 3D","gm_estilo_jogo":"Estilo: captura de jogo",
 "gm_estilo_grafico":"Estilo: gráfico/só texto","gm_fundo_liso":"Fundo liso/desfocado","gm_fundo_ilustrado":"Fundo ilustrado","gm_fundo_tela":"Fundo de tela/interface","gm_fundo_colagem":"Fundo em colagem"}
F = [f for f in ROT if d[f].mean() > 0.01]   # traços presentes em pelo menos 1% das miniaturas
d["titulo_10chars"] = d.titulo_chars/10; d["desc_dobro"] = d.log_desc/np.log(2); d["duracao_dobro"] = d.log_duracao/np.log(2)
d["tags_dobro"] = d.log_n_tags/np.log(2); d["links_dobro"] = np.log1p(d.desc_links)/np.log(2); d["hashtags_dobro"] = np.log1p(d.desc_hashtags)/np.log(2)
CTRL = ["titulo_10chars","tem_numero","tem_pergunta","tem_palavra_caps","tem_emoji","tem_eu","desc_dobro","links_dobro","hashtags_dobro",
        "tem_capitulos","tags_dobro","duracao_dobro","legenda_manual","fim_de_semana","log_idade"]
d = d.dropna(subset=F+CTRL+["y"]).copy()
def within(sub, feats):
    X = sub[feats+CTRL].astype(float); X = pd.concat([X, pd.get_dummies(sub.faixa_hora, drop_first=True, dtype=float)], axis=1)
    Xd = X - X.groupby(sub.channel_id.values).transform("mean"); yd = sub.y - sub.y.groupby(sub.channel_id).transform("mean")
    keep = Xd.columns[Xd.std() > 0]
    return sm.OLS(yd, Xd[keep]).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(sub.channel_id)[0]})
m = within(d, F)
p, se, pv = m.params.reindex(F), m.bse.reindex(F), m.pvalues.reindex(F)
q = multipletests(pv, method="fdr_bh")[1]
T = pd.DataFrame(dict(variavel=F, rotulo=[ROT[f] for f in F], pct_miniaturas=[d[f].mean()*100 for f in F], efeito_pct=(np.exp(p)-1).values*100,
    ic_baixo_pct=(np.exp(p-1.96*se)-1).values*100, ic_alto_pct=(np.exp(p+1.96*se)-1).values*100, p=pv.values, q_bh=q))
S = {}
for col in ["idioma","nicho"]:
    for v, sub in d.groupby(col):
        if sub.channel_id.nunique() >= 6: S[f"{col}={v}"] = within(sub, F).params.reindex(F)
S = pd.DataFrame(S); S.to_csv("resultados/gemini_estabilidade.csv")
nc = [c for c in S if c.startswith("nicho=")]
T["nichos_mesmo_sinal"] = [f"{int((np.sign(S.loc[f,nc])==np.sign(p[f])).sum())}/{int(S.loc[f,nc].notna().sum())}" for f in F]
T["pt_pct"] = (np.exp(S["idioma=pt"].reindex(F).values)-1)*100; T["en_pct"] = (np.exp(S["idioma=en"].reindex(F).values)-1)*100
# checagem: modelo de efeitos mistos (intercepto por canal; nicho/idioma/porte/categoria fixos)
form = "y ~ " + " + ".join(F+CTRL) + " + C(faixa_hora) + C(nicho) + C(idioma) + C(porte) + C(categoria)"
try:
    mm = smf.mixedlm(form, d, groups=d.channel_id).fit(method=["lbfgs","powell"])
    T["misto_efeito_pct"] = (np.exp(mm.params.reindex(F))-1).values*100
    T["misto_q_bh"] = multipletests(mm.pvalues.reindex(F), method="fdr_bh")[1]
except Exception as e: print("misto falhou", e)
T = T.sort_values("efeito_pct"); T.to_csv("resultados/gemini_efeitos_miniatura.csv", index=False)
# prevalência por nicho e melhores vs piores do canal
P = (d.groupby("nicho")[F].mean()*100).rename(columns=ROT).round(1); P.loc["TODOS"] = (d[F].mean()*100).rename(ROT).round(1); P.to_csv("resultados/gemini_prevalencia_por_nicho.csv")
d["q_canal"] = d.groupby("channel_id").y.rank(pct=True)
C = pd.DataFrame({"20% melhores do canal": d[d.q_canal>=.8][F].mean()*100, "20% piores do canal": d[d.q_canal<=.2][F].mean()*100}).rename(index=ROT).round(1)
C["diferença (pontos)"] = (C.iloc[:,0]-C.iloc[:,1]).round(1); C.to_csv("resultados/gemini_melhores_vs_piores.csv")
r = dict(n_videos=len(d), n_canais=int(d.channel_id.nunique()), por_idioma=d.groupby("idioma").video_id.count().to_dict())
json.dump(r, open("resultados/gemini_resumo.json","w"), indent=1)
# gráficos
G = T.sort_values("efeito_pct"); cor = ["#1a7f37" if (qq<.05 and e>0) else "#cf222e" if (qq<.05 and e<0) else "#8c959f" for qq,e in zip(G.q_bh, G.efeito_pct)]
fig, ax = plt.subplots(figsize=(9, 0.33*len(G)+1.6))
ax.errorbar(G.efeito_pct, range(len(G)), xerr=[G.efeito_pct-G.ic_baixo_pct, G.ic_alto_pct-G.efeito_pct], fmt="none", ecolor=cor, elinewidth=2)
ax.scatter(G.efeito_pct, range(len(G)), c=cor, zorder=3); ax.axvline(0, color="k", lw=.8)
ax.set_yticks(range(len(G))); ax.set_yticklabels([f"{a} ({b:.0f}%)" for a,b in zip(G.rotulo, G.pct_miniaturas)], fontsize=8)
ax.set_xlabel("% de views a mais (ou a menos) que o normal do próprio canal\n(entre parênteses: % das miniaturas com o traço)\nverde/vermelho = passa na correção de Benjamini-Hochberg a 5%; cinza = incerto", fontsize=8)
ax.set_title(f"Miniaturas lidas por IA vs normal do canal\n({len(d):,} vídeos, {d.channel_id.nunique()} canais)".replace(",", "."), fontsize=10)
plt.tight_layout(); plt.savefig("graficos/09_miniatura_ia_efeitos.png", dpi=150); plt.close()
H = P.drop(index="TODOS")
fig, ax = plt.subplots(figsize=(13, 5.5)); im = ax.imshow(H.values, cmap="Blues", aspect="auto")
ax.set_xticks(range(H.shape[1])); ax.set_xticklabels(H.columns, rotation=40, ha="right", fontsize=7); ax.set_yticks(range(H.shape[0])); ax.set_yticklabels(H.index, fontsize=8)
for i in range(H.shape[0]):
    for j in range(H.shape[1]): ax.text(j, i, f"{H.values[i,j]:.0f}", ha="center", va="center", fontsize=6, color="white" if H.values[i,j]>60 else "black")
ax.set_title("Miniaturas lidas por IA: % dos vídeos com cada traço, por nicho", fontsize=10); plt.tight_layout(); plt.savefig("graficos/10_miniatura_ia_por_nicho.png", dpi=150); plt.close()
H2 = (np.exp(S.loc[G.variavel, nc])-1)*100
fig, ax = plt.subplots(figsize=(10, 0.33*len(G)+2)); im = ax.imshow(H2.clip(-40,40).values, cmap="RdYlGn", vmin=-40, vmax=40, aspect="auto")
ax.set_yticks(range(len(H2))); ax.set_yticklabels([ROT[v] for v in H2.index], fontsize=8); ax.set_xticks(range(len(nc))); ax.set_xticklabels([c.split("=")[1] for c in nc], rotation=45, ha="right", fontsize=8)
plt.colorbar(im, label="% vs normal do canal (cortado em ±40%)"); ax.set_title("Miniaturas lidas por IA: o efeito se repete em cada nicho?", fontsize=10)
plt.tight_layout(); plt.savefig("graficos/11_miniatura_ia_por_nicho_efeito.png", dpi=150); plt.close()
print(json.dumps(r)); print(T.round(2).to_string()); print(C)
