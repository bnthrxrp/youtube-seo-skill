"""Etapa 6: tabelas descritivas (amostra por estrato) e padrões de miniatura. Saídas: resultados/*.csv e graficos/07-08*.png"""
import pandas as pd, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d = pd.read_parquet("dados/dataset.parquet")
est = d.groupby(["nicho","idioma","porte"]).agg(canais=("channel_id","nunique"), videos=("video_id","count")).reset_index()
est.to_csv("resultados/amostra_por_estrato.csv", index=False)
for c in ["nicho","idioma","porte"]:
    d.groupby(c).agg(canais=("channel_id","nunique"), videos=("video_id","count")).to_csv(f"resultados/amostra_por_{c}.csv")
# padrões de miniatura: quanto cada traço aparece, por nicho, e nos 20% de vídeos mais acima do normal do canal vs 20% mais abaixo
d["ocr_5mais_palavras"] = (d.ocr_n_palavras>=5).astype(float).where(d.ocr_n_palavras.notna())
tr = {"thumb_tem_rosto":"Rosto (detector simples)","thumb_rosto_grande":"Rosto grande","ocr_tem_texto":"Tem texto","ocr_5mais_palavras":"5+ palavras",
      "ocr_repete_titulo":"Texto repete o título","ocr_numero":"Número na imagem","ocr_dinheiro":"Símbolo de dinheiro","ocr_caps":"Texto em CAIXA ALTA"}
tr = {k:v for k,v in tr.items() if k in d}
P = (d.groupby("nicho")[list(tr)].mean()*100).rename(columns=tr).round(1); P.loc["TODOS"] = (d[list(tr)].mean()*100).rename(tr).round(1)
P.to_csv("resultados/miniatura_prevalencia_por_nicho.csv")
d["q_canal"] = d.groupby("channel_id").y.rank(pct=True)
top, bot = d[d.q_canal>=0.8], d[d.q_canal<=0.2]
C = pd.DataFrame({"20% melhores do canal": top[list(tr)].mean()*100, "20% piores do canal": bot[list(tr)].mean()*100}).rename(index=tr).round(1)
C["diferença (pontos)"] = (C.iloc[:,0]-C.iloc[:,1]).round(1); C.to_csv("resultados/miniatura_melhores_vs_piores.csv")
num = ["thumb_brilho","thumb_contraste","thumb_saturacao","thumb_bordas","ocr_n_palavras"]
pd.DataFrame({"20% melhores": top[num].median(), "20% piores": bot[num].median(), "todos": d[num].median()}).round(3).to_csv("resultados/miniatura_medianas_melhores_vs_piores.csv")
fig, ax = plt.subplots(figsize=(8,4)); x = np.arange(len(C))
ax.bar(x-0.2, C.iloc[:,0], 0.4, label="20% de vídeos mais acima do normal do canal", color="#1a7f37")
ax.bar(x+0.2, C.iloc[:,1], 0.4, label="20% mais abaixo", color="#cf222e")
ax.set_xticks(x); ax.set_xticklabels(C.index, rotation=30, ha="right", fontsize=8); ax.set_ylabel("% das miniaturas"); ax.legend(fontsize=8)
ax.set_title("Miniaturas: o que aparece nos melhores e nos piores vídeos de cada canal", fontsize=10); plt.tight_layout(); plt.savefig("graficos/07_miniatura_melhores_vs_piores.png", dpi=150); plt.close()
fig, ax = plt.subplots(figsize=(9,5)); im = ax.imshow(P.values, cmap="Blues", aspect="auto")
ax.set_xticks(range(P.shape[1])); ax.set_xticklabels(P.columns, rotation=30, ha="right", fontsize=8); ax.set_yticks(range(P.shape[0])); ax.set_yticklabels(P.index, fontsize=8)
for i in range(P.shape[0]):
    for j in range(P.shape[1]): ax.text(j, i, f"{P.values[i,j]:.0f}", ha="center", va="center", fontsize=7, color="white" if P.values[i,j]>60 else "black")
ax.set_title("Quanto cada traço aparece nas miniaturas, por nicho (% dos vídeos)", fontsize=10); plt.tight_layout(); plt.savefig("graficos/08_miniatura_por_nicho.png", dpi=150); plt.close()
print(est.groupby(["idioma","porte"])[["canais","videos"]].sum()); print(P); print(C)
