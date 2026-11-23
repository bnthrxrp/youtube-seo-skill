"""Etapa 3: para cada canal selecionado, lista a aba /videos (long-form, sem Shorts) com data aproximada,
descarta vídeos com menos de 35 dias, e extrai metadados completos (sem baixar vídeo) de até N vídeos.
Resumível: grava dados/raw/<channel_id>.jsonl. Uso: python3 03_coleta.py [N=55] [workers=4]"""
import json, subprocess, sys, time, os, csv, random, threading, concurrent.futures as cf
N = int(sys.argv[1]) if len(sys.argv)>1 else 55
W = int(sys.argv[2]) if len(sys.argv)>2 else 4
os.makedirs("dados/raw", exist_ok=True)
CUT = time.time() - 35*86400
lock = threading.Lock(); bot_hits = [0]
class _R: returncode=1; stdout=""; stderr="timeout"
def run(args, timeout=120):
    try: r = subprocess.run(["yt-dlp","--no-warnings","--socket-timeout","30"]+args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired: return _R()
    if "not a bot" in r.stderr or "HTTP Error 429" in r.stderr:
        with lock: bot_hits[0]+=1
    return r
def keep(d):
    afmt = {f.get("language") for f in d.get("formats") or [] if f.get("vcodec")=="none" and f.get("language")}
    return dict(video_id=d.get("id"), channel_id=d.get("channel_id"), title=d.get("title"), description=d.get("description"),
        tags=d.get("tags"), categories=d.get("categories"), duration=d.get("duration"), view_count=d.get("view_count"),
        like_count=d.get("like_count"), comment_count=d.get("comment_count"), timestamp=d.get("timestamp"),
        upload_date=d.get("upload_date"), language=d.get("language"), n_chapters=len(d.get("chapters") or []),
        sub_langs=sorted((d.get("subtitles") or {}).keys()), n_auto_caps=len(d.get("automatic_captions") or {}),
        n_audio_langs=len(afmt), live_status=d.get("live_status"), age_limit=d.get("age_limit"),
        thumbnail=d.get("thumbnail"), channel_follower_count=d.get("channel_follower_count"),
        availability=d.get("availability"), collected_at=int(time.time()))
def video(vid):
    for tent in range(4):
        r = run(["--skip-download","-j",f"https://www.youtube.com/watch?v={vid}"])
        if r.returncode==0 and r.stdout.strip():
            time.sleep(0.4); return keep(json.loads(r.stdout))
        if any(k in r.stderr for k in ("members","Private video","unavailable","confirm your age","Premieres in","removed")): return None
        bot = "not a bot" in r.stderr or "429" in r.stderr
        time.sleep((30 if bot else 5)*(tent+1))
    return None
def canal(row):
    cid = row["channel_id"]; path = f"dados/raw/{cid}.jsonl"
    if os.path.exists(path) and os.path.getsize(path)>0: return cid, "ja"
    r = run(["--flat-playlist","-J","--playlist-end","250","--extractor-args","youtubetab:approximate_date",
             f"https://www.youtube.com/channel/{cid}/videos"])
    if r.returncode!=0: return cid, "falha_lista"
    ents = json.loads(r.stdout).get("entries") or []
    elig = [e["id"] for e in ents if e.get("timestamp") and e["timestamp"] < CUT][:N]
    out = []
    with cf.ThreadPoolExecutor(W) as ex:
        for v in ex.map(video, elig):
            if v: out.append(v)
    with open(path,"w") as f:
        for v in out: f.write(json.dumps(v, ensure_ascii=False)+"\n")
    return cid, f"{len(out)}/{len(elig)} de {len(ents)}"
rows = list(csv.DictReader(open("dados/canais_selecionados.csv")))
if os.environ.get("REVERSO"): rows = rows[::-1]
for i,row in enumerate(rows):
    t=time.time(); b0=bot_hits[0]; cid,st = canal(row)
    print(i, row["nicho"], row["idioma"], row["porte"], row["nome"], st, f"{time.time()-t:.0f}s bot={bot_hits[0]}", flush=True)
    if bot_hits[0]-b0 >= 8: print("Muitos avisos anti-bot neste canal; pausando 5 min", flush=True); time.sleep(300)
