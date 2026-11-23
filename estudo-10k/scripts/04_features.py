"""Etapa 4: junta os brutos, filtra, calcula a variável alvo e as variáveis de SEO. Saída: dados/dataset.parquet e .csv"""
import json, glob, re, math, os, numpy as np, pandas as pd
from zoneinfo import ZoneInfo
can = pd.read_csv("dados/canais_selecionados.csv")
rows = [json.loads(l) for p in glob.glob("dados/api/*.jsonl") for l in open(p)]   # fonte principal: YouTube Data API v3
# extras que só o yt-dlp traz (faixas de áudio, capítulos oficiais) para o subconjunto coletado antes da troca para a API
xt = [json.loads(l) for p in glob.glob("dados/raw/*.jsonl") for l in open(p)]
xt = pd.DataFrame(xt)[["video_id","n_audio_langs","n_chapters","sub_langs"]].drop_duplicates("video_id").rename(columns={"n_chapters":"n_chapters_ytdlp"}) if xt else pd.DataFrame(columns=["video_id"])
df = pd.DataFrame(rows).drop_duplicates("video_id").merge(can[["channel_id","nome","nicho","idioma","porte","inscritos"]], on="channel_id", how="inner")
n0 = len(df)
# filtros: long-form publicado normalmente, com views, >= 35 dias, sem transmissões ao vivo, duração >= 61s
df = df[df.view_count.notna() & (df.view_count>0) & (df.duration.fillna(0)>180)]
eh_short_tag = df.title.fillna("").str.contains(r"#shorts?\b", case=False) | df.description.fillna("").str[:500].str.contains(r"#shorts?\b", case=False)
n_shorts_tag = int(eh_short_tag.sum()); df = df[~eh_short_tag]
df = df[(df.collected_at - df.timestamp)/86400 >= 30]
df = df.merge(xt, on="video_id", how="left")
# idioma do canal: maioria do campo 'language' dos vídeos; descarta canal cujo idioma diverge do estrato
SW = {"pt": set("de que não para com uma os no na do da você eu meu como mais por isso".split()),
      "en": set("the and you to of is in my this with how what for i it".split()),
      "es": set("el la los las que y en un una por con para es mi como del".split())}
def lang_txt(txts):
    w = re.findall(r"[a-záéíóúãõâêôçñ']+", " ".join(txts).lower()); c = {k: sum(x in v for x in w) for k,v in SW.items()}
    return max(c, key=c.get) if sum(c.values()) else None
def lang_canal(g):
    api = g.language.dropna().str[:2]
    if api.size >= len(g)*0.5: return api.mode().iloc[0]
    return lang_txt(list(g.title.fillna("")) + list(g.description.fillna("").str[:300]))
lang = df.groupby("channel_id").apply(lang_canal)
df["lang_canal"] = df.channel_id.map(lang)
bad = df[(df.lang_canal.notna()) & (df.lang_canal!=df.idioma)].channel_id.unique()
df = df[~df.channel_id.isin(bad)]
# canais com pelo menos 15 vídeos válidos
cnt = df.channel_id.value_counts(); df = df[df.channel_id.isin(cnt[cnt>=15].index)].copy()
ref = df.collected_at.max()
df["idade_dias"] = (df.collected_at - df.timestamp)/86400
df["log_views"] = np.log(df.view_count)
# ALVO: log(views) menos a mediana de log(views) dos 10 vídeos do mesmo canal mais próximos em data (sem o próprio)
def baseline(g):
    g = g.sort_values("timestamp"); lv = g.log_views.values; ts = g.timestamp.values; out=[]
    for i in range(len(g)):
        d = np.abs(ts-ts[i]).astype(float); d[i]=np.inf
        out.append(np.median(lv[np.argsort(d)[:10]]))
    return pd.Series(out, index=g.index)
df["base_canal"] = df.groupby("channel_id", group_keys=False).apply(baseline)
df["y"] = df.log_views - df.base_canal
# ---------- variáveis de SEO ----------
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\U0001F1E6-\U0001F1FF]")
STOP = set("a o os as de do da dos das e em no na um uma para por com que the a an of to in on and for with is my i you how what this".split())
def tokens(s): return re.findall(r"[\wÀ-ÿ']+", s.lower())
t = df.title.fillna(""); dsc = df.description.fillna("")
df["titulo_chars"] = t.str.len()
df["titulo_palavras"] = t.apply(lambda s: len(s.split()))
df["tem_numero"] = t.str.contains(r"\d").astype(int)
df["tem_dinheiro"] = t.str.contains(r"\$|R\$|€|£|\b\d+\s?(mil|k|million|milhão|milhões|thousand)\b", case=False).astype(int)
df["tem_pergunta"] = t.str.contains(r"\?").astype(int)
df["tem_exclamacao"] = t.str.contains("!").astype(int)
df["tem_palavra_caps"] = t.apply(lambda s: int(any(len(w)>=3 and w.isupper() and w.isalpha() for w in re.findall(r"[A-Za-zÀ-ÿ]+", s)))).astype(int)
df["titulo_todo_caps"] = t.apply(lambda s: int(sum(c.isalpha() for c in s)>5 and all(not c.islower() for c in s if c.isalpha())))
df["tem_emoji"] = t.apply(lambda s: int(bool(EMOJI.search(s))))
df["tem_separador"] = t.str.contains(r"\||:| - | – | — ").astype(int)
df["tem_parenteses"] = t.str.contains(r"[\(\[]").astype(int)
df["tem_eu"] = t.apply(lambda s: int(bool(set(tokens(s)) & {"eu","meu","minha","me","comprei","i","my","me","i'm","im","we","our","nós","nosso"}))) 
df["tem_voce"] = t.apply(lambda s: int(bool(set(tokens(s)) & {"você","voce","vc","seu","sua","vocês","you","your","you're"})))
df["tem_colab"] = t.str.contains(r"\bft\.?\b|\bfeat\.?\b|\bvs\.?\b|\bx\b|@", case=False).astype(int)
def nome_proprio(s):
    w = re.findall(r"[A-Za-zÀ-ÿ']+", s)
    if len(w)<3: return 0
    cap = [x[0].isupper() for x in w]
    if sum(cap)/len(w) > 0.5: return np.nan   # título em Title Case: heurística não se aplica
    return int(any(c and not x.isupper() for c,x in zip(cap[1:], w[1:])))
df["tem_nome_proprio"] = t.apply(nome_proprio)
def kw_inicio(row):
    tk = [x for x in tokens(row.title or "") if x not in STOP and len(x)>2][:2]
    alvo = " ".join((row.tags or [])).lower() + " " + (row.description or "")[:200].lower()
    return int(bool(tk) and any(x in alvo for x in tk))
df["palavra_chave_inicio"] = df.apply(kw_inicio, axis=1)
df["desc_chars"] = dsc.str.len()
df["log_desc"] = np.log1p(df.desc_chars)
df["desc_links"] = dsc.str.count(r"https?://")
df["desc_hashtags"] = dsc.str.count(r"(?<!\w)#\w+")
df["desc_timestamps"] = dsc.str.count(r"(?m)^\s*\(?\d{1,2}:\d{2}(:\d{2})?")
df["tem_capitulos"] = ((df.desc_timestamps>=3) & dsc.str.contains(r"(?m)^\s*\(?0?0:00")).astype(int)   # regra do YouTube: começa em 0:00 e tem 3+ marcas
df["titulo_na_desc"] = [int(bool(set(tokens(a))&set(tokens(b[:300])) - STOP)) for a,b in zip(t,dsc)]
df["n_tags"] = df.tags.apply(lambda x: len(x) if isinstance(x,list) else 0)
df["sem_tags"] = (df.n_tags==0).astype(int)
df["log_n_tags"] = np.log1p(df.n_tags)
df["duracao_min"] = df.duration/60
df["log_duracao"] = np.log(df.duracao_min)
df["log_idade"] = np.log(df.idade_dias)
tz = {"pt":ZoneInfo("America/Sao_Paulo"),"en":ZoneInfo("America/New_York")}
lt = [pd.Timestamp(ts, unit="s", tz="UTC").tz_convert(tz[l]) for ts,l in zip(df.timestamp, df.idioma)]
df["dia_semana"] = [x.day_of_week for x in lt]; df["hora_local"] = [x.hour for x in lt]
df["fim_de_semana"] = (df.dia_semana>=5).astype(int)
df["faixa_hora"] = pd.cut(df.hora_local, [-1,5,11,17,23], labels=["madrugada","manha","tarde","noite"]).astype(str)
df["legenda_manual"] = df.caption.astype(int)   # contentDetails.caption: legenda enviada pelo canal
df["multi_audio"] = np.where(df.n_audio_langs.notna(), (df.n_audio_langs>=2).astype(float), np.nan)   # só no subconjunto yt-dlp
CAT = {"1":"Filmes/Animação","2":"Autos","10":"Música","15":"Animais","17":"Esportes","19":"Viagem","20":"Games","22":"Pessoas/Blogs","23":"Comédia","24":"Entretenimento","25":"Notícias","26":"Estilo/Como fazer","27":"Educação","28":"Ciência/Tecnologia","29":"ONGs"}
df["categoria"] = df.category_id.map(CAT).fillna("Outra")
df["tags_txt"] = df.tags.apply(lambda x: "|".join(x) if isinstance(x,list) else "")
df["sub_langs_txt"] = df.sub_langs.apply(lambda x: "|".join(x) if isinstance(x,list) else "")
# miniatura (se baixada pela etapa 4b)
if os.path.exists("dados/thumb_features.csv"):
    df = df.merge(pd.read_csv("dados/thumb_features.csv").drop_duplicates("video_id"), on="video_id", how="left")
if os.path.exists("dados/thumb_ocr.jsonl"):
    o = pd.read_json("dados/thumb_ocr.jsonl", lines=True).drop_duplicates("video_id")
    df = df.merge(o, on="video_id", how="left")
df["thumb_tem_rosto"] = np.where(df.thumb_n_rostos.notna(), (df.thumb_n_rostos>0).astype(float), np.nan)
# idioma do áudio declarado pelo canal (defaultAudioLanguage/defaultLanguage na API)
df["idioma_declarado"] = df.language.notna().astype(int)
df["idioma_declarado_bate"] = np.where(df.language.notna(), (df.language.fillna("").str[:2]==df.idioma).astype(float), np.nan)
out = df.drop(columns=["tags","sub_langs"])
out.to_parquet("dados/dataset.parquet", index=False); out.to_csv("dados/dataset.csv", index=False)
print("shorts_por_hashtag", n_shorts_tag); print("brutos", n0, "final", len(out), "canais", out.channel_id.nunique(), "descartados_idioma", len(bad))
print(out.groupby(["nicho","idioma","porte"]).channel_id.nunique().unstack(["idioma","porte"]).fillna(0).astype(int))
