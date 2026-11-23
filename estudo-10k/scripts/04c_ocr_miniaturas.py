"""Etapa 4c (substitui o Gemini, cuja conta estava sem crédito): OCR local e gratuito (RapidOCR/ONNX) do texto da miniatura.
Gera: tem texto, nº de palavras, se repete palavras do título, número/dinheiro visível, texto em caixa alta."""
import json, glob, os, re, multiprocessing as mp, pandas as pd
def init():
    global O
    import onnxruntime as ort
    _IS = ort.InferenceSession
    def IS(path, sess_options=None, **kw):
        so = sess_options or ort.SessionOptions(); so.intra_op_num_threads = 1; so.inter_op_num_threads = 1
        return _IS(path, sess_options=so, **kw)
    ort.InferenceSession = IS
    from rapidocr_onnxruntime import RapidOCR; O = RapidOCR()
def tok(s): return set(re.findall(r"[a-záéíóúãõâêôçñ0-9]{3,}", s.lower()))
def work(v):
    p = f"dados/thumbs/{v['video_id']}.jpg"
    if not os.path.exists(p): return None
    try: r, _ = O(p)
    except Exception: return None
    try: txt = " ".join(x[1] for x in (r or []) if float(x[2]) >= 0.6)
    except Exception: return None
    w = re.findall(r"\S+", txt); tt = tok(v["title"] or ""); ot = tok(txt)
    letras = [c for c in txt if c.isalpha()]
    return dict(video_id=v["video_id"], ocr_texto=txt[:200], ocr_tem_texto=int(len(w)>0), ocr_n_palavras=len(w),
        ocr_repete_titulo=int(bool(ot) and len(ot & tt)/len(ot) >= 0.5), ocr_numero=int(bool(re.search(r"\d", txt))),
        ocr_dinheiro=int(bool(re.search(r"\$|R\$|€|£", txt))), ocr_caps=int(len(letras)>=4 and sum(c.isupper() for c in letras)/len(letras) > 0.8))
if __name__ == "__main__":
    vids = [json.loads(l) for p in glob.glob("dados/api/*.jsonl") for l in open(p)]
    OUT = "dados/thumb_ocr.jsonl"
    done = {json.loads(l)["video_id"] for l in open(OUT)} if os.path.exists(OUT) else set()
    vids = [v for v in {v["video_id"]: v for v in vids}.values() if v["video_id"] not in done]; print("faltam", len(vids), flush=True)
    with open(OUT, "a") as f, mp.Pool(7, initializer=init) as pool:
        for i, r in enumerate(pool.imap(work, vids, chunksize=20)):
            if r: f.write(json.dumps(r, ensure_ascii=False) + "\n")
            if i % 1000 == 0: f.flush(); print(i, flush=True)
    pd.read_json(OUT, lines=True).drop_duplicates("video_id").to_csv("dados/thumb_ocr.csv", index=False); print("FIM")
