"""Etapa 4b: baixa a miniatura pública (mqdefault 320x180, i.ytimg.com) e mede cor/brilho/contraste/rostos.
Rostos: detector Haar do OpenCV (aproximado, erra em rostos de perfil e desenhos)."""
import json, glob, os, urllib.request, concurrent.futures as cf, numpy as np, cv2, pandas as pd, time
os.makedirs("dados/thumbs", exist_ok=True)
ids = [json.loads(l)["video_id"] for p in glob.glob("dados/api/*.jsonl") for l in open(p)]
face = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
def get(v):
    p = f"dados/thumbs/{v}.jpg"
    if not os.path.exists(p):
        try:
            urllib.request.urlretrieve(f"https://i.ytimg.com/vi/{v}/mqdefault.jpg", p)
        except Exception: return None
    img = cv2.imread(p)
    if img is None: return None
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    b,gc,r = [img[:,:,i].astype(float) for i in range(3)]
    rg, yb = r-gc, 0.5*(r+gc)-b
    colorf = np.sqrt(rg.std()**2+yb.std()**2)+0.3*np.sqrt(rg.mean()**2+yb.mean()**2)
    faces = face.detectMultiScale(g, 1.1, 5, minSize=(24,24))
    areas = [w*h for (x,y,w,h) in faces]
    return dict(video_id=v, thumb_brilho=g.mean()/255, thumb_contraste=g.std()/255, thumb_saturacao=hsv[:,:,1].mean()/255,
                thumb_colorido=colorf/100, thumb_bordas=(cv2.Canny(g,100,200)>0).mean(), thumb_n_rostos=len(faces),
                thumb_rosto_grande=int(bool(areas) and max(areas) > 0.08*g.size))
old = pd.read_csv("dados/thumb_features.csv") if os.path.exists("dados/thumb_features.csv") else pd.DataFrame(columns=["video_id"])
done = set(old.video_id); ids = [v for v in dict.fromkeys(ids) if v not in done]; print("faltam", len(ids), flush=True)
with cf.ThreadPoolExecutor(16) as ex: res = [r for r in ex.map(get, ids) if r]
out = pd.concat([old, pd.DataFrame(res)]).drop_duplicates("video_id")
out.to_csv("dados/thumb_features.csv", index=False); print("novas", len(res), "total", len(out))
