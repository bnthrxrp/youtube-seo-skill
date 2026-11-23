"""Etapa 4d: leitura das miniaturas com gemini-3.5-flash-lite pela Batch API (50% mais barata que a chamada normal).
Esquema JSON com chaves curtas (a saída é cobrada por token; chaves curtas cortam ~2/3 do custo). Chave em GEMINI_API_KEY (nunca impressa).
Uso:  python3 04d_gemini_batch.py piloto 50     -> chamadas normais, mede tokens reais
      python3 04d_gemini_batch.py lote [tam]    -> envia em lotes (Batch API), retomável; estado em dados/gemini_batch_estado.json
Saída: dados/thumbs_gemini.jsonl (uma linha por miniatura, nomes de campo longos). Custo em dados/gemini_uso.csv."""
import os, sys, json, base64, time, csv, random, urllib.request, urllib.error
import pandas as pd
MODEL = "gemini-3.5-flash-lite"; KEY = os.environ["GEMINI_API_KEY"]; BASE = "https://generativelanguage.googleapis.com"
P_IN, P_OUT = 0.30/1e6, 2.50/1e6      # USD por token, preço padrão (ai.google.dev/gemini-api/docs/pricing, 23/11/2026)
BATCH_DESC = 0.5                      # Batch API: 50% do preço padrão
BRL = 5.93; TETO_BRL = 40.0
OUT = "dados/thumbs_gemini.jsonl"; EST = "dados/gemini_batch_estado.json"; USO = "dados/gemini_uso.csv"
CAMPOS = {"r":"n_rostos","e":"expressao","o":"olhar_camera","g":"rosto_ocupa_grande_area","p":"n_palavras_texto","t":"texto_repete_titulo",
          "b":"tem_objeto_destaque","s":"tem_seta_ou_circulo","n":"n_elementos_principais","f":"fundo","y":"estilo","a":"antes_depois_ou_comparacao","d":"numero_ou_dinheiro_visivel"}
ENUM = {"e":["nenhum","neutra","feliz","surpresa","medo","raiva","triste","seria"], "t":["sem","repete","complementa","outro"],
        "f":["liso","real","ilustrado","tela","colagem"], "y":["foto","montagem","ilustracao","3d","jogo","grafico"]}
TIPO = {"r":"INTEGER","p":"INTEGER","n":"INTEGER"}
S = {"type":"OBJECT","properties":{k: ({"type":"STRING","enum":ENUM[k]} if k in ENUM else {"type":TIPO.get(k,"BOOLEAN")}) for k in CAMPOS},
     "required":list(CAMPOS), "propertyOrdering":list(CAMPOS)}
PROMPT = ('Miniatura de vídeo do YouTube. Título: "{t}". Descreva só o que está visível. Chaves: r=nº de rostos (humanos ou personagens); '
 'e=expressão do rosto principal (nenhum se não há rosto; surpresa=surpresa/choque; medo=medo/tensão; seria=séria/concentrada); o=olha para a câmera; '
 'g=rosto ocupa grande área; p=nº de palavras escritas na imagem; t=o texto da imagem repete o título, complementa, outro, ou sem texto; '
 'b=objeto/produto (não pessoa) em destaque; s=seta ou círculo de destaque; n=nº de elementos principais; '
 'f=fundo (liso/desfocado, cenário real, ilustrado, tela/interface, colagem); y=estilo (foto, montagem/foto editada, ilustração, animação 3D, captura de jogo, gráfico/texto); '
 'a=antes/depois ou comparação; d=número ou dinheiro visível.')
def req_body(v):
    b64 = base64.b64encode(open(f"dados/thumbs/{v['video_id']}.jpg","rb").read()).decode()
    return {"contents":[{"parts":[{"inline_data":{"mime_type":"image/jpeg","data":b64}},{"text":PROMPT.format(t=(v["title"] or "").replace('"',"'"))}]}],
            "generationConfig":{"responseMimeType":"application/json","responseSchema":S,"temperature":0,
                                "mediaResolution":"MEDIA_RESOLUTION_LOW","thinkingConfig":{"thinkingLevel":"minimal"}}}
def http(method, url, data=None, headers=None, raw=False, timeout=120):
    h = {"x-goog-api-key": KEY}; h.update(headers or {})
    for t in range(6):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h, method=method), timeout=timeout)
            return r if raw else json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:400].replace(KEY, "***")
            if e.code in (400, 401, 402, 403, 404): raise SystemExit(f"HTTP {e.code}: {msg}")
            time.sleep(5*(t+1))
        except Exception: time.sleep(5*(t+1))
    raise SystemExit("falha de rede repetida")
def parse(vid, resp):
    u = resp.get("usageMetadata", {})
    try: j = json.loads(resp["candidates"][0]["content"]["parts"][0]["text"])
    except Exception: return None, u
    row = {CAMPOS[k]: j.get(k) for k in CAMPOS}; row.update(video_id=vid, tok_in=u.get("promptTokenCount",0), tok_out=u.get("candidatesTokenCount",0)+u.get("thoughtsTokenCount",0))
    return row, u
def gasto_usd():
    if not os.path.exists(USO): return 0.0
    return sum(float(r["usd"] or 0) for r in csv.DictReader(open(USO)))
def log_uso(modo, n, ti, to, usd, err, seg):
    new = not os.path.exists(USO)
    with open(USO, "a") as f:
        w = csv.writer(f)
        if new: w.writerow(["quando","modo","imagens","tokens_entrada","tokens_saida","usd","erros","segundos"])
        w.writerow([time.strftime("%Y-%m-%d %H:%M"), modo, n, ti, to, round(usd,5), err, seg])
d = pd.read_parquet("dados/dataset.parquet", columns=["video_id","title"])   # só os vídeos do dataset final
d = d[[os.path.exists(f"dados/thumbs/{v}.jpg") for v in d.video_id]]
done = {json.loads(l)["video_id"] for l in open(OUT)} if os.path.exists(OUT) else set()
modo = sys.argv[1]
if modo == "piloto":
    n = int(sys.argv[2]); amostra = d.sample(n, random_state=11).to_dict("records"); t0 = time.time(); ti = to = ok = 0
    with open("dados/thumbs_gemini_piloto_v3.jsonl", "w") as f:
        for v in amostra:
            r = http("POST", f"{BASE}/v1beta/models/{MODEL}:generateContent", json.dumps(req_body(v)).encode(), {"Content-Type":"application/json"})
            row, u = parse(v["video_id"], r); ti += u.get("promptTokenCount",0); to += u.get("candidatesTokenCount",0)+u.get("thoughtsTokenCount",0)
            if row: ok += 1; f.write(json.dumps(row, ensure_ascii=False)+"\n")
    usd = ti*P_IN + to*P_OUT; log_uso(f"piloto{n} {MODEL} chaves-curtas", ok, ti, to, usd, n-ok, int(time.time()-t0))
    por = usd/max(ok,1); falta = len(d)
    print(f"piloto: {ok}/{n} ok, tokens entrada {ti} saída {to}, US$ {usd:.5f}, por imagem US$ {por:.7f}")
    print(f"projeção {falta} imagens: padrão US$ {por*falta:.2f} = R$ {por*falta*BRL:.2f}; Batch US$ {por*falta*BATCH_DESC:.2f} = R$ {por*falta*BATCH_DESC*BRL:.2f}")
    print(f"gasto acumulado medido: R$ {gasto_usd()*BRL:.2f}")
    sys.exit()
# ---------- modo lote (Batch API) ----------
TAM = int(sys.argv[2]) if len(sys.argv) > 2 else 2500
est = json.load(open(EST)) if os.path.exists(EST) else {"lotes": []}
def salvar(): json.dump(est, open(EST,"w"), indent=1)
pend_ids = {i for L in est["lotes"] if L["estado"] != "baixado" for i in L["ids"]}
todo = [v for v in d.to_dict("records") if v["video_id"] not in done and v["video_id"] not in pend_ids]
def upload(path, nome):
    size = os.path.getsize(path)
    r = http("POST", f"{BASE}/upload/v1beta/files", json.dumps({"file":{"display_name":nome}}).encode(),
             {"X-Goog-Upload-Protocol":"resumable","X-Goog-Upload-Command":"start","X-Goog-Upload-Header-Content-Length":str(size),
              "X-Goog-Upload-Header-Content-Type":"application/jsonl","Content-Type":"application/json"}, raw=True)
    url = r.headers["X-Goog-Upload-URL"]
    r = http("POST", url, open(path,"rb").read(), {"Content-Length":str(size),"X-Goog-Upload-Offset":"0","X-Goog-Upload-Command":"upload, finalize"}, timeout=600)
    return r["file"]["name"]
def custo_por_img():
    rows = [json.loads(l) for l in open("dados/thumbs_gemini_piloto_v3.jsonl")]
    return sum(r["tok_in"]*P_IN + r["tok_out"]*P_OUT for r in rows)/len(rows)*BATCH_DESC
cpi = custo_por_img()
# 1) enviar lotes novos enquanto a projeção (gasto medido + lotes em andamento + este lote) couber no teto
for i in range(0, len(todo), TAM):
    chunk = todo[i:i+TAM]
    em_andamento = sum(len(L["ids"]) for L in est["lotes"] if L["estado"] != "baixado") * cpi
    if (gasto_usd() + em_andamento + len(chunk)*cpi)*BRL > TETO_BRL: print("projeção passaria do teto; não envio mais lotes"); break
    path = f"/tmp/gemini_lote_{len(est['lotes'])}.jsonl"
    with open(path, "w") as f:
        for v in chunk: f.write(json.dumps({"key": v["video_id"], "request": req_body(v)})+"\n")
    fn = upload(path, os.path.basename(path)); os.remove(path)
    b = http("POST", f"{BASE}/v1beta/models/{MODEL}:batchGenerateContent", json.dumps({"batch":{"display_name":f"thumbs-{len(est['lotes'])}","input_config":{"file_name":fn}}}).encode(), {"Content-Type":"application/json"})
    est["lotes"].append({"nome": b["name"], "arquivo": fn, "ids": [v["video_id"] for v in chunk], "estado": "enviado", "enviado_em": time.strftime("%H:%M")}); salvar()
    print("lote enviado", b["name"], len(chunk), flush=True)
# 2) acompanhar e baixar
while any(L["estado"] != "baixado" for L in est["lotes"]):
    for L in est["lotes"]:
        if L["estado"] == "baixado": continue
        b = http("GET", f"{BASE}/v1beta/{L['nome']}")
        st = (b.get("metadata") or {}).get("state") or b.get("state"); L["estado_api"] = st
        if b.get("done") or st in ("BATCH_STATE_SUCCEEDED","JOB_STATE_SUCCEEDED","BATCH_STATE_FAILED","BATCH_STATE_CANCELLED","BATCH_STATE_EXPIRED"):
            resp = (b.get("response") or {}); rf = resp.get("responsesFile") or ((b.get("metadata") or {}).get("output") or {}).get("responsesFile")
            ti = to = ok = 0
            if rf:
                r = http("GET", f"{BASE}/download/v1beta/{rf}:download?alt=media", raw=True, timeout=600)
                with open(OUT, "a") as f:
                    for line in r.read().decode().splitlines():
                        x = json.loads(line); rr = x.get("response") or {}
                        row, u = parse(x.get("key"), rr); ti += u.get("promptTokenCount",0); to += u.get("candidatesTokenCount",0)+u.get("thoughtsTokenCount",0)
                        if row: ok += 1; f.write(json.dumps(row, ensure_ascii=False)+"\n")
            usd = (ti*P_IN + to*P_OUT)*BATCH_DESC
            log_uso(f"batch {L['nome']} {st}", ok, ti, to, usd, len(L["ids"])-ok, 0)
            L["estado"] = "baixado"; L["ok"] = ok; L["usd"] = usd; salvar()
            print("lote baixado", L["nome"], st, ok, f"US$ {usd:.4f}", f"acumulado R$ {gasto_usd()*BRL:.2f}", flush=True)
    salvar()
    if any(L["estado"] != "baixado" for L in est["lotes"]):
        print(time.strftime("%H:%M"), {L["nome"][-8:]: L.get("estado_api") for L in est["lotes"] if L["estado"]!="baixado"}, flush=True); time.sleep(60)
print("FIM. gasto acumulado R$", round(gasto_usd()*BRL, 2))
