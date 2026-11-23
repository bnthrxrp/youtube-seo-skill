"""Etapa 2: seleciona até K canais por estrato (nicho x idioma x porte). Sementes primeiro, depois resultados de busca na ordem.
Porte pelo nº de inscritos: gigante >20M, grande 2M-20M, medio 200k-2M. Exclui <200k, canais 'Topic'/VEVO."""
import pandas as pd, sys
K = int(sys.argv[1]) if len(sys.argv)>1 else 4
c = pd.read_csv("dados/candidatos.csv")
c = c[c.inscritos.fillna(0) >= 200_000]
c = c[~c.nome.fillna("").str.contains(r"- Topic|VEVO", regex=True)]
c["porte"] = pd.cut(c.inscritos, [2e5, 2e6, 2e7, 1e12], labels=["medio","grande","gigante"], right=False).astype(str)
c["ordem"] = (c.origem!="semente").astype(int)
c = c.reset_index().sort_values(["ordem","index"])
sel = c.groupby(["nicho","idioma","porte"], group_keys=False).head(K).drop(columns=["index","ordem"])
sel.sort_values(["nicho","idioma","porte"]).to_csv("dados/canais_selecionados.csv", index=False)
print(len(sel)); print(sel.groupby(["nicho","idioma","porte"]).size().unstack())
