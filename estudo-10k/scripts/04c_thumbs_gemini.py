"""Etapa 4c: leitura das miniaturas com Gemini (gemini-3.5-flash-lite; o 2.5 deixou de aceitar contas novas), saída JSON estruturada.
Uso: python3 04c_thumbs_gemini.py PILOTO_N|all. Chave em GEMINI_API_KEY (nunca impressa).
Custo medido por usageMetadata e gravado em dados/gemini_uso.csv."""
import os, sys, json, glob, base64, time, csv, urllib.request, urllib.error, concurrent.futures as cf, threading
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite"); KEY = os.environ["GEMINI_API_KEY"]
PRICE_IN, PRICE_OUT = 0.30/1e6, 2.50/1e6   # USD por token, gemini-3.5-flash-lite padrão (ai.google.dev/gemini-api/docs/pricing, 23/11/2026)
BRL = 5.93; TETO_BRL = float(os.environ.get("TETO_BRL", "40"))
gasto_ant = 0.0   # gasto já medido em rodadas anteriores (dados/gemini_uso.csv)
if os.path.exists("dados/gemini_uso.csv"):
    for r_ in csv.DictReader(open("dados/gemini_uso.csv")): gasto_ant += float(r_["usd"] or 0)
os.makedirs("dados/thumbs", exist_ok=True); OUT = "dados/thumbs_gemini.jsonl"
vids = [json.loads(l) for p in sorted(glob.glob("dados/api/*.jsonl")) for l in open(p)]
vids = [v for v in vids if (v.get("duration") or 0) > 180]
if os.environ.get("SO_DATASET"):
    import pandas as pd; keep = set(pd.read_parquet("dados/dataset.parquet", columns=["video_id"]).video_id); vids = [v for v in vids if v["video_id"] in keep]
done = {json.loads(l)["video_id"] for l in open(OUT)} if os.path.exists(OUT) else set()
arg = sys.argv[1]
if arg != "all":
    import random; random.seed(7); vids = random.sample(vids, int(arg))
todo = [v for v in vids if v["video_id"] not in done]
# Esquema enxuto (v2): sem transcrição do texto (o OCR local já tem), sem cores/contraste/saturação (medidos por pixel), para caber no teto.
S = {"type":"OBJECT","properties":{
 "n_rostos":{"type":"INTEGER"},"expressao":{"type":"STRING","enum":["nenhum_rosto","neutra","feliz","surpresa_choque","medo_tensao","raiva","triste","seria_concentrada"]},
 "olhar_camera":{"type":"BOOLEAN"},"rosto_ocupa_grande_area":{"type":"BOOLEAN"},"n_palavras_texto":{"type":"INTEGER"},
 "texto_repete_titulo":{"type":"STRING","enum":["sem_texto","repete","complementa","outro"]},
 "tem_objeto_destaque":{"type":"BOOLEAN"},"tem_seta_ou_circulo":{"type":"BOOLEAN"},"n_elementos_principais":{"type":"INTEGER"},
 "fundo":{"type":"STRING","enum":["liso_ou_desfocado","cenario_real","cenario_ilustrado","tela_ou_interface","colagem"]},
 "estilo":{"type":"STRING","enum":["foto","foto_editada_montagem","ilustracao","animacao_3d","captura_de_jogo","texto_grafico"]},
 "antes_depois_ou_comparacao":{"type":"BOOLEAN"},"numero_ou_dinheiro_visivel":{"type":"BOOLEAN"}},
 "propertyOrdering":["n_rostos","expressao","olhar_camera","rosto_ocupa_grande_area","n_palavras_texto","texto_repete_titulo","tem_objeto_destaque","tem_seta_ou_circulo","n_elementos_principais","fundo","estilo","antes_depois_ou_comparacao","numero_ou_dinheiro_visivel"]}
S["required"] = S["propertyOrdering"]
PROMPT = ("Miniatura (thumbnail) de vídeo do YouTube. Título: \"{t}\". Descreva só o que está visível. "
 "n_rostos: rostos humanos ou de personagens claramente visíveis. n_palavras_texto: palavras escritas na imagem (0 se nenhuma). "
 "texto_repete_titulo: 'repete' se o texto diz basicamente o mesmo que o título, 'complementa' se acrescenta algo diferente. "
 "tem_objeto_destaque: há um objeto/produto (não pessoa) em destaque.")
lock = threading.Lock(); tot = {"in":0,"out":0,"n":0,"err":0}; stop = threading.Event()
def thumb(v):
    p = f"dados/thumbs/{v['video_id']}.jpg"
    if not os.path.exists(p): urllib.request.urlretrieve(f"https://i.ytimg.com/vi/{v['video_id']}/mqdefault.jpg", p)
    return base64.b64encode(open(p,"rb").read()).decode()
def call(v):
    if stop.is_set(): return None
    try: b64 = thumb(v)
    except Exception: return None
    body = {"contents":[{"parts":[{"inline_data":{"mime_type":"image/jpeg","data":b64}},{"text":PROMPT.format(t=v["title"])}]}],
            "generationConfig":{"responseMimeType":"application/json","responseSchema":S,"temperature":0,"mediaResolution":"MEDIA_RESOLUTION_LOW","thinkingConfig":{"thinkingLevel":"minimal"}}}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent", data=json.dumps(body).encode(),
                                 headers={"Content-Type":"application/json","x-goog-api-key":KEY})
    for t in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r: d = json.load(r)
            u = d.get("usageMetadata", {}); res = json.loads(d["candidates"][0]["content"]["parts"][0]["text"])
            res.update(video_id=v["video_id"], tok_in=u.get("promptTokenCount",0), tok_out=u.get("candidatesTokenCount",0)+u.get("thoughtsTokenCount",0))
            return res
        except urllib.error.HTTPError as e:
            msg = e.read().decode()
            if e.code in (401, 402, 403, 404): 
                with lock: tot["fatal"] = f"HTTP {e.code}"
                return None
            if e.code == 400 and "mediaResolution" in msg:
                body["generationConfig"].pop("mediaResolution"); req.data = json.dumps(body).encode(); continue
            time.sleep(2**t*2)
        except Exception: time.sleep(2**t*2)
    with lock: tot["err"] += 1
    return None
t0 = time.time()
with open(OUT, "a") as f, cf.ThreadPoolExecutor(8) as ex:
    for r in ex.map(call, todo):
        if not r: continue
        f.write(json.dumps(r, ensure_ascii=False)+"\n")
        with lock:
            tot["in"] += r["tok_in"]; tot["out"] += r["tok_out"]; tot["n"] += 1
            usd_now = tot['in']*PRICE_IN+tot['out']*PRICE_OUT
            if tot["n"] % 500 == 0: print(tot, f"US$ {usd_now:.4f}", f"acumulado R$ {(gasto_ant+usd_now)*BRL:.2f}", flush=True); f.flush()
            if (gasto_ant+usd_now)*BRL > TETO_BRL: stop.set(); print("TETO ATINGIDO, parando", flush=True)
        if "fatal" in tot: stop.set()
usd = tot["in"]*PRICE_IN + tot["out"]*PRICE_OUT
new = not os.path.exists("dados/gemini_uso.csv")
with open("dados/gemini_uso.csv","a") as f:
    w = csv.writer(f)
    if new: w.writerow(["quando","modo","imagens","tokens_entrada","tokens_saida","usd","erros","segundos"])
    w.writerow([time.strftime("%Y-%m-%d %H:%M"), f"{arg} {MODEL}", tot["n"], tot["in"], tot["out"], round(usd,5), tot["err"], int(time.time()-t0)])
print("FIM", tot, "acumulado R$", round((gasto_ant+usd)*BRL, 2), f"US$ {usd:.5f}", "por imagem", usd/max(tot["n"],1), "total elegíveis", len(vids))
