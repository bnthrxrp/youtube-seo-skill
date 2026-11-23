"""Etapa 2b: reforço dos estratos que ficaram com menos de 3 canais válidos depois do filtro de idioma.
Pega os próximos candidatos da busca (mesma regra de porte) e acrescenta em canais_selecionados.csv com origem 'reforco:'."""
import pandas as pd
d = pd.read_parquet("dados/dataset.parquet"); sel = pd.read_csv("dados/canais_selecionados.csv"); c = pd.read_csv("dados/candidatos.csv")
c = c[c.inscritos.fillna(0) >= 2e5]; c = c[~c.nome.fillna("").str.contains(r"- Topic|VEVO")]
c["porte"] = pd.cut(c.inscritos, [2e5,2e6,2e7,1e12], labels=["medio","grande","gigante"], right=False).astype(str)
ok = d.groupby(["nicho","idioma","porte"]).channel_id.nunique()
extra = []
for (n,l,p), g in c[~c.channel_id.isin(sel.channel_id)].groupby(["nicho","idioma","porte"]):
    falta = 3 - ok.get((n,l,p), 0)
    if falta > 0: extra.append(g.head(falta*2 + 2).assign(origem=lambda x: "reforco:" + x.origem))
e = pd.concat(extra); print(len(e)); print(e.groupby(["nicho","idioma","porte"]).size())
pd.concat([sel, e[sel.columns]]).to_csv("dados/canais_selecionados.csv", index=False)
