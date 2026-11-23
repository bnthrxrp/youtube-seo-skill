from youtube_seo.modulos.titulos import analisar_titulos


class VisaoFixa:
    def __init__(self):
        self.chamadas = 0

    def analyze(self, image_bytes: bytes, titulo: str = "") -> dict:
        self.chamadas += 1
        return {
            "disponivel": True,
            "ocr_texto": "PAO CASEIRO",
            "thumb_n_rostos": 1,
            "thumb_rosto_grande": 1,
            "thumb_contraste": 0.42,
        }


class PostProibido:
    def post_json(self, *args, **kwargs):
        raise AssertionError("Gemini não pode ser chamado com a opção desligada")

    def get_json(self, *args, **kwargs):
        raise AssertionError("rede")

    def get_bytes(self, *args, **kwargs):
        raise AssertionError("rede")


def test_titulos_cruzam_forca_do_estudo_e_nao_chamam_gemini():
    visao = VisaoFixa()
    payload = analisar_titulos(
        videos=[
            {"video_id": "1", "titulo": "COMO fazer pao caseiro?", "imagem_bytes": b"\xff\xd8\xff"},
            {"video_id": "2", "titulo": "pão de todo dia", "imagem_bytes": b"\xff\xd8\xff"},
        ],
        vision=visao,
        gemini_enabled=False,
        gemini_key="nao-usar",
        transport=PostProibido(),
    )
    assert visao.chamadas == 2
    assert payload["gemini"]["habilitado"] is False
    assert payload["gemini"]["chamadas_ok"] == 0
    assert all(item["gemini"]["status"] == "desligado" for item in payload["itens"])
    cruz = {c["chave"]: c for c in payload["cruzamento_estudo"]}
    assert cruz["palavra_caps"]["forca"] == "provavel"
    assert cruz["tamanho_titulo"]["forca"] == "sem_efeito"
    assert cruz["emoji_titulo"]["forca"] == "provavel"
    assert cruz["pergunta_titulo"]["nesta_amostra"] == 50.0
    assert payload["visao_agregada"]["pct_rosto_grande"] == 100.0
    assert payload["visao_agregada"]["pct_repete_titulo"] == 50.0
    assert payload["visao_agregada"]["estudo"]["rosto_grande"]["forca"] == "fraco"
    assert "1,5%" in payload["estudo"]


def test_arquivo_local_e_gemini_opt_in(tmp_path):
    imagem = tmp_path / "COMO assar pao.jpg"
    imagem.write_bytes(b"\xff\xd8\xff\xd9")
    visao = VisaoFixa()

    class GeminiOk(PostProibido):
        def post_json(self, url, payload, params=None):
            self.posts = [{"url": url, "params": params or {}}]
            assert "test-gemini" in (params or {}).get("key", "")
            return {"candidates": [{"content": {"parts": [{"text": "{\"rosto\": true, \"expressao\": \"seria\"}"}]}}]}

    transporte = GeminiOk()
    payload = analisar_titulos(
        imagens=[imagem],
        vision=visao,
        gemini_enabled=True,
        gemini_key="test-gemini",
        transport=transporte,
    )
    assert payload["itens"][0]["titulo_tracos"]["tem_palavra_caps"] == 1
    assert payload["itens"][0]["gemini"]["status"] == "ok"
    assert payload["itens"][0]["gemini"]["forca"] == "fraco"
    assert payload["itens"][0]["gemini"]["leitura"]["expressao"] == "seria"
    assert "test-gemini" not in payload["itens"][0]["gemini"].get("motivo", "")


def test_visao_local_sem_opencv(monkeypatch):
    import builtins

    real = builtins.__import__

    def falha(name, *args, **kwargs):
        if name in {"cv2", "numpy"}:
            raise ImportError(name)
        return real(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", falha)
    from youtube_seo.visao import analisar_bytes

    resultado = analisar_bytes(b"nao-e-imagem", "titulo")
    assert resultado["disponivel"] is False
