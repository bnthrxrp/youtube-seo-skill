"""Etapa 3 (versão final): coleta via YouTube Data API v3 (chave em YOUTUBE_API_KEY; nunca impressa).
Sem search.list. Custo: channels.list + playlistItems.list + videos.list = 1 unidade por chamada.
Long-form: playlist 'UULF' (só vídeos longos do canal); se não existir, playlist de uploads 'UU' filtrando duração > 180 s.
Exclui vídeos com menos de 35 dias e transmissões ao vivo. Resumível: dados/api/<channel_id>.jsonl"""
import os, json, time, re, csv, urllib.request, urllib.parse, urllib.error
KEY = os.environ["YOUTUBE_API_KEY"]; N = 100; os.makedirs("dados/api", exist_ok=True)
CUT = time.time() - 35*86400; units = [0]
def api(ep, **p):
    p["key"] = KEY; url = f"https://www.googleapis.com/youtube/v3/{ep}?" + urllib.parse.urlencode(p)
    for t in range(4):
        try:
            units[0] += 1
            with urllib.request.urlopen(url, timeout=30) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            if e.code == 403: raise SystemExit("403 (cota ou chave): " + e.read().decode()[:300].replace(KEY, "***"))
            time.sleep(3*(t+1))
        except Exception: time.sleep(3*(t+1))
    return None
def iso(d):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    return sum(int(x or 0)*k for x,k in zip(m.groups(), (86400,3600,60,1))) if m else None
def ts(s): return int(time.mktime(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone)
rows = list(csv.DictReader(open("dados/canais_selecionados.csv")))
info = {}
for i in range(0, len(rows), 50):
    r = api("channels", part="statistics,snippet,contentDetails", id=",".join(x["channel_id"] for x in rows[i:i+50]), maxResults=50)
    for it in r.get("items", []): info[it["id"]] = it
def plist(pid, pages=3):
    ids, tok = [], None
    for _ in range(pages):
        kw = dict(part="contentDetails", playlistId=pid, maxResults=50); 
        if tok: kw["pageToken"] = tok
        r = api("playlistItems", **kw)
        if not r: return None if not ids else ids
        ids += [(x["contentDetails"]["videoId"], x["contentDetails"].get("videoPublishedAt")) for x in r.get("items", [])]
        tok = r.get("nextPageToken")
        if not tok: break
    return ids
for n, row in enumerate(rows):
    cid = row["channel_id"]; path = f"dados/api/{cid}.jsonl"
    if os.path.exists(path): continue
    ch = info.get(cid)
    if not ch: print(n, row["nome"], "canal não encontrado", flush=True); open(path,"w").close(); continue
    src = "UULF"; ids = plist("UULF" + cid[2:], pages=4)
    if not ids: src = "UU"; ids = plist("UU" + cid[2:], pages=8) or []
    ids = [v for v,p in ids if p and ts(p) < CUT]
    out = []
    for i in range(0, len(ids), 50):
        if len(out) >= N: break
        r = api("videos", part="snippet,contentDetails,statistics,topicDetails,status,liveStreamingDetails", id=",".join(ids[i:i+50]), maxResults=50) or {}
        for v in r.get("items", []):
            sn, cd, st = v["snippet"], v["contentDetails"], v.get("statistics", {})
            dur = iso(cd.get("duration"))
            if src == "UU" and (dur or 0) <= 180: continue
            if "liveStreamingDetails" in v or sn.get("liveBroadcastContent","none") != "none": continue
            out.append(dict(video_id=v["id"], channel_id=cid, title=sn.get("title"), description=sn.get("description"), tags=sn.get("tags"),
                category_id=sn.get("categoryId"), duration=dur, view_count=int(st["viewCount"]) if "viewCount" in st else None,
                like_count=int(st["likeCount"]) if "likeCount" in st else None, comment_count=int(st["commentCount"]) if "commentCount" in st else None,
                timestamp=ts(sn["publishedAt"]), language=sn.get("defaultAudioLanguage") or sn.get("defaultLanguage"),
                caption=cd.get("caption")=="true", definition=cd.get("definition"), licensed=cd.get("licensedContent"),
                made_for_kids=v.get("status",{}).get("madeForKids"), topics="|".join(u.rsplit("/",1)[-1] for u in v.get("topicDetails",{}).get("topicCategories",[])),
                thumbnail=(sn.get("thumbnails",{}).get("medium") or {}).get("url"), fonte_lista=src,
                channel_follower_count=int(ch["statistics"].get("subscriberCount",0)), canal_videos_total=int(ch["statistics"].get("videoCount",0)),
                collected_at=int(time.time())))
            if len(out) >= N: break
    with open(path, "w") as f:
        for x in out: f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print(n, row["nicho"], row["idioma"], row["porte"], row["nome"], len(out), src, f"unid={units[0]}", flush=True)
print("TOTAL unidades", units[0])
