"""Etapa 1: monta candidatos (sementes + busca de canais por nicho/idioma) com inscritos."""
import json, subprocess, sys, time, csv, urllib.parse, concurrent.futures as cf
sys.path.insert(0, __file__.rsplit('/',1)[0]); from seeds import SEEDS, QUERIES
OUT = "dados/candidatos.csv"
def ytdlp(url, n):
    r = subprocess.run(["yt-dlp","--flat-playlist","-J","--no-warnings","--playlist-end",str(n),url],capture_output=True,text=True,timeout=120)
    return json.loads(r.stdout) if r.returncode==0 and r.stdout else None
rows = {}
def add(cid, handle, title, subs, niche, lang, origem):
    if not cid or cid in rows: return
    rows[cid] = dict(channel_id=cid, handle=handle, nome=title, inscritos=subs, nicho=niche, idioma=lang, origem=origem)
def seed_job(args):
    (niche,lang),h = args
    d = ytdlp(f"https://www.youtube.com/@{h}/videos", 1)
    time.sleep(0.5)
    return niche,lang,h,d
jobs = [((k),h) for k,v in SEEDS.items() for h in v.split()]
with cf.ThreadPoolExecutor(4) as ex:
    for niche,lang,h,d in ex.map(seed_job, jobs):
        if d: add(d.get("channel_id"), d.get("uploader_id") or "@"+h, d.get("channel"), d.get("channel_follower_count"), niche, lang, "semente")
        else: print("falhou semente", h, file=sys.stderr)
for (niche,lang),qs in QUERIES.items():
    for q in qs:
        hl = "&hl=pt&gl=BR" if lang=="pt" else "&hl=en&gl=US"
        url = "https://www.youtube.com/results?search_query="+urllib.parse.quote(q)+"&sp=EgIQAg%253D%253D"+hl
        d = ytdlp(url, 40); time.sleep(1)
        for e in (d or {}).get("entries",[]):
            add(e.get("id"), e.get("uploader_id"), e.get("title"), e.get("channel_follower_count"), niche, lang, "busca:"+q)
with open(OUT,"w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(next(iter(rows.values())).keys())); w.writeheader(); w.writerows(rows.values())
print(len(rows), "candidatos")
