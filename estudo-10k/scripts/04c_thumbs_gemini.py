"""Etapa 4c: leitura das miniaturas com Gemini (gemini-2.5-flash-lite), saída JSON estruturada.
Uso: python3 04c_thumbs_gemini.py PILOTO_N|all. Chave em GEMINI_API_KEY (nunca impressa).
Custo medido por usageMetadata e gravado em dados/gemini_uso.csv."""
import os, sys, json, glob, base64, time, csv, urllib.request, urllib.error, concurrent.futures as cf, threading
MODEL = "gemini-2.5-flash-lite"; KEY = os.environ["GEMINI_API_KEY"]
PRICE_IN, PRICE_OUT = 0.10/1e6, 0.40/1e6   # USD por token (ai.google.dev/pricing, padrão)
os.makedirs("dados/thumbs", exist_ok=True); OUT = "dados/thumbs_gemini.jsonl"
vids = [json.loads(l) for p in sorted(glob.glob("dados/api/*.jsonl")) for l in open(p)]
vids = [v for v in vids if (v.get("duration") or 0) > 180]
done = {json.loads(l)["video_id"] for l in open(OUT)} if os.path.exists(OUT) else set()
arg = sys.argv[1]
if arg != "all":
    import random; random.seed(7); vids = random.sample(vids, int(arg))
todo = [v for v in vids if v["video_id"] not in done]
S = {"type":"OBJECT","properties":{
 "n_rostos":{"type":"INTEGER"},"expressao":{"type":"STRING","enum":["nenhum_rosto","neutra","feliz","surpresa_choque","medo_tensao","raiva","triste","seria_concentrada"]},
 "olhar_camera":{"type":"BOOLEAN"},"rosto_ocupa_grande_area":{"type":"BOOLEAN"},
 "tem_texto":{"type":"BOOLEAN"},"n_palavras_texto":{"type":"INTEGER"},"texto_lido":{"type":"STRING"},
 "texto_repete_titulo":{"type":"STRING","enum":["sem_texto","repete","complementa","outro"]},
 "objeto_destaque":{"type":"STRING"},"tem_seta_ou_circulo":{"type":"BOOLEAN"},"n_elementos_principais":{"type":"INTEGER"},
 "fundo":{"type":"STRING","enum":["liso_ou_desfocado","cenario_real","cenario_ilustrado","tela_ou_interface","colagem"]},
 "cores_dominantes":{"type":"ARRAY","items":{"type":"STRING"}},"contraste":{"type":"STRING","enum":["baixo","medio","alto"]},
 "saturacao":{"type":"STRING","enum":["baixa","media","alta"]},"estilo":{"type":"STRING","enum":["foto","foto_editada_montagem","ilustracao","animacao_3d","captura_de_jogo","texto_grafico"]},
 "antes_depois_ou_comparacao":{"type":"BOOLEAN"},"numero_ou_dinheiro_visivel":{"type":"BOOLEAN"}},
 "required":["n_rostos","expressao","olhar_camera","rosto_ocupa_grande_area","tem_texto","n_palavras_texto","texto_lido","texto_repete_titulo","objeto_destaque","tem_seta_ou_circulo","n_elementos_principais","fundo","cores_dominantes","contraste","saturacao","estilo","antes_depois_ou_comparacao","numero_ou_dinheiro_visivel"]}
PROMPT = ("Você analisa a miniatura (thumbnail) de um vídeo do YouTube. Título do vídeo: \"{t}\". Descreva só o que está visível. "
 "n_rostos: rostos humanos ou de personagens claramente visíveis. texto_lido: transcreva o texto da imagem (vazio se não houver). "
 "texto_repete_titulo: 'repete' se o texto diz basicamente o mesmo que o título, 'complementa' se acrescenta algo diferente. "
 "objeto_destaque: o objeto/produto principal em até 4 palavras, ou 'nenhum'. cores_dominantes: até 3 cores em português.")
lock = threading.Lock(); tot = {"in":0,"out":0,"n":0,"err":0}
def thumb(v):
    p = f"dados/thumbs/{v['video_id']}.jpg"
    if not os.path.exists(p): urllib.request.urlretrieve(f"https://i.ytimg.com/vi/{v['video_id']}/mqdefault.jpg", p)
    return base64.b64encode(open(p,"rb").read()).decode()
def call(v):
    try: b64 = thumb(v)
    except Exception: return None
    body = {"contents":[{"parts":[{"inline_data":{"mime_type":"image/jpeg","data":b64}},{"text":PROMPT.format(t=v["title"])}]}],
            "generationConfig":{"responseMimeType":"application/json","responseSchema":S,"temperature":0,"mediaResolution":"MEDIA_RESOLUTION_LOW"}}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent", data=json.dumps(body).encode(),
                                 headers={"Content-Type":"application/json","x-goog-api-key":KEY})
    for t in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r: d = json.load(r)
            u = d.get("usageMetadata", {}); res = json.loads(d["candidates"][0]["content"]["parts"][0]["text"])
            res.update(video_id=v["video_id"], tok_in=u.get("promptTokenCount",0), tok_out=u.get("candidatesTokenCount",0)+u.get("thoughtsTokenCount",0))
            return res
        except urllib.error.HTTPError as e:
            if e.code == 400 and "mediaResolution" in e.read().decode():
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
            if tot["n"] % 500 == 0: print(tot, f"US$ {tot['in']*PRICE_IN+tot['out']*PRICE_OUT:.4f}", flush=True)
usd = tot["in"]*PRICE_IN + tot["out"]*PRICE_OUT
new = not os.path.exists("dados/gemini_uso.csv")
with open("dados/gemini_uso.csv","a") as f:
    w = csv.writer(f)
    if new: w.writerow(["quando","modo","imagens","tokens_entrada","tokens_saida","usd","erros","segundos"])
    w.writerow([time.strftime("%Y-%m-%d %H:%M"), arg, tot["n"], tot["in"], tot["out"], round(usd,5), tot["err"], int(time.time()-t0)])
print("FIM", tot, f"US$ {usd:.5f}", "por imagem", usd/max(tot["n"],1), "total elegíveis", len(vids))
