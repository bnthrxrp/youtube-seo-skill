"""Visão local e gratuita da miniatura.

Reaproveita estudo-10k/scripts/04b_miniaturas.py (OpenCV: brilho, contraste,
saturação, rostos Haar) e 04c_ocr_miniaturas.py (RapidOCR). As duas bibliotecas
são opcionais: sem elas o módulo de títulos segue só com o texto.
"""

from __future__ import annotations

from youtube_seo.texto import metricas_ocr

_OCR = None


def analisar_bytes(image_bytes: bytes, titulo: str = "") -> dict:
    try:
        import cv2
        import numpy as np
    except ImportError:
        return {
            "disponivel": False,
            "motivo": "OpenCV não instalado. A análise de título segue. Visão local: pip install -e '.[vision]'.",
        }
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return {"disponivel": False, "motivo": "Não foi possível ler a imagem."}
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    b, g, r = [img[:, :, i].astype(float) for i in range(3)]
    rg, yb = r - g, 0.5 * (r + g) - b
    colorido = float((rg.std() ** 2 + yb.std() ** 2) ** 0.5 + 0.3 * (rg.mean() ** 2 + yb.mean() ** 2) ** 0.5)
    face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face.detectMultiScale(gray, 1.1, 5, minSize=(24, 24))
    areas = [int(w * h) for (_x, _y, w, h) in faces]
    resultado = {
        "disponivel": True,
        "thumb_brilho": round(float(gray.mean() / 255), 4),
        "thumb_contraste": round(float(gray.std() / 255), 4),
        "thumb_saturacao": round(float(hsv[:, :, 1].mean() / 255), 4),
        "thumb_colorido": round(colorido / 100, 4),
        "thumb_bordas": round(float((cv2.Canny(gray, 100, 200) > 0).mean()), 4),
        "thumb_n_rostos": int(len(faces)),
        "thumb_rosto_grande": int(bool(areas) and max(areas) > 0.08 * gray.size),
    }
    resultado.update(_ocr(img, titulo))
    return resultado


def _ocr(img, titulo: str) -> dict:
    global _OCR
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        return {
            "ocr_disponivel": False,
            "motivo_ocr": "RapidOCR não instalado. Medidas de cor e rosto seguem; o texto da miniatura não.",
        }
    if _OCR is None:
        _OCR = RapidOCR()
    try:
        leitura, _elapsed = _OCR(img)
        texto = " ".join(x[1] for x in (leitura or []) if float(x[2]) >= 0.6)
    except Exception as exc:  # biblioteca externa: falha de uma imagem não derruba o relatório
        return {"ocr_disponivel": False, "motivo_ocr": f"OCR falhou: {exc.__class__.__name__}"}
    saida = {"ocr_disponivel": True}
    saida.update(metricas_ocr(texto, titulo))
    return saida


class LocalVision:
    def analyze(self, image_bytes: bytes, titulo: str = "") -> dict:
        return analisar_bytes(image_bytes, titulo)
