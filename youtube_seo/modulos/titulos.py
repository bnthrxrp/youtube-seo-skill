"""Title & Thumbnail Intelligence, cruzado com o estudo próprio.

Visão/OCR local é o caminho gratuito. Gemini só roda com enabled=True e chave,
e o relatório deixa claro que esses traços não têm sinal forte no estudo.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from youtube_seo.cliente import YouTubeClient
from youtube_seo.findings import NOTA_GERAL, achar
from youtube_seo.gemini import MODELO_PADRAO, analisar as analisar_gemini
from youtube_seo.http import HttpError, Transport
from youtube_seo.modulos.serp import analisar_serp
from youtube_seo.texto import extrair_titulo, metricas_ocr
from youtube_seo.visao import LocalVision

_MAPA = {
    "chars": "tamanho_titulo",
    "tem_emoji": "emoji_titulo",
    "tem_palavra_caps": "palavra_caps",
    "titulo_todo_caps": "titulo_todo_caps",
    "tem_numero": "numero_titulo",
    "tem_pergunta": "pergunta_titulo",
    "tem_separador": "separador_titulo",
    "tem_parenteses": "parenteses_titulo",
    "tem_eu": "primeira_pessoa",
    "tem_voce": "voce_titulo",
}


def _media_flag(linhas: list[dict], chave: str) -> float | None:
    valores = [linha["titulo_tracos"][chave] for linha in linhas if chave in linha.get("titulo_tracos", {})]
    if not valores:
        return None
    if chave == "chars":
        valores_ord = sorted(valores)
        meio = len(valores_ord) // 2
        if len(valores_ord) % 2:
            return float(valores_ord[meio])
        return (valores_ord[meio - 1] + valores_ord[meio]) / 2
    return round(100 * sum(valores) / len(valores), 1)


def _cruzar(linhas: list[dict]) -> list[dict[str, Any]]:
    saida = []
    for chave, achado in _MAPA.items():
        info = achar(achado)
        saida.append(
            {
                "chave": achado,
                "traco": info["traco"],
                "forca": info["forca"],
                "rotulo": info["rotulo"],
                "efeito": info["efeito"],
                "margem": info["margem"],
                "leitura": info["leitura"],
                "nesta_amostra": _media_flag(linhas, chave),
                "unidade": "caracteres (mediana)" if chave == "chars" else "% dos títulos",
            }
        )
    return saida


def _baixar(url: str, transport: Transport | None) -> tuple[bytes | None, str | None]:
    if not url or transport is None:
        return None, None
    try:
        return transport.get_bytes(url), None
    except HttpError as exc:
        return None, str(exc)


def _linha(
    video: dict,
    *,
    vision,
    transport: Transport | None,
    baixar: bool,
    gemini_enabled: bool,
    gemini_key: str | None,
    gemini_model: str,
) -> dict[str, Any]:
    titulo = video.get("titulo") or ""
    imagem = video.get("imagem_bytes")
    aviso_imagem = None
    if imagem is None and baixar:
        imagem, aviso_imagem = _baixar(video.get("thumbnail_url") or "", transport)
    visao = None
    if imagem is not None and vision is not None:
        visao = vision.analyze(imagem, titulo)
        if isinstance(visao, dict) and visao.get("ocr_texto") and "ocr_repete_titulo" not in visao:
            visao.update(metricas_ocr(visao["ocr_texto"], titulo))
    gemini = analisar_gemini(
        imagem,
        titulo,
        enabled=gemini_enabled,
        api_key=gemini_key,
        transport=transport,
        model=gemini_model,
    )
    return {
        "video_id": video.get("video_id"),
        "titulo": titulo,
        "canal_nome": video.get("canal_nome"),
        "origem": video.get("origem") or "video",
        "titulo_tracos": extrair_titulo(titulo),
        "visao_local": visao,
        "gemini": gemini,
        "aviso_imagem": aviso_imagem,
    }


def _resumo_visao(linhas: list[dict]) -> dict[str, Any] | None:
    locais = [l["visao_local"] for l in linhas if isinstance(l.get("visao_local"), dict) and l["visao_local"].get("disponivel")]
    if not locais:
        return None
    n = len(locais)

    def taxa(chave: str) -> float | None:
        valores = [item[chave] for item in locais if chave in item]
        if not valores:
            return None
        return round(100 * sum(int(bool(v)) for v in valores) / len(valores), 1)

    return {
        "n": n,
        "pct_rosto": taxa("thumb_n_rostos"),
        "pct_rosto_grande": taxa("thumb_rosto_grande"),
        "mediana_contraste": round(sum(item.get("thumb_contraste") or 0 for item in locais) / n, 4),
        "pct_texto": taxa("ocr_tem_texto"),
        "pct_repete_titulo": taxa("ocr_repete_titulo"),
        "pct_5_palavras_ou_mais": round(
            100 * sum(1 for item in locais if (item.get("ocr_n_palavras") or 0) >= 5) / n, 1
        ),
        "estudo": {
            "rosto_grande": achar("rosto_grande"),
            "ocr_repete_titulo": achar("ocr_repete_titulo"),
            "contraste": achar("contraste"),
            "ocr_muitas_palavras": achar("ocr_muitas_palavras"),
        },
    }


def analisar_titulos(
    *,
    videos: list[dict] | None = None,
    termo: str | None = None,
    hl: str | None = None,
    gl: str | None = None,
    client: YouTubeClient | None = None,
    transport: Transport | None = None,
    now: Callable[[], float] | None = None,
    max_results: int = 25,
    pages: int = 1,
    imagens: list[Path] | None = None,
    baixar_miniaturas: bool = False,
    vision=None,
    gemini_enabled: bool = False,
    gemini_key: str | None = None,
    gemini_model: str = MODELO_PADRAO,
) -> dict[str, Any]:
    avisos: list[str] = []
    base: list[dict] = [dict(v) for v in (videos or [])]
    if termo:
        if client is None or now is None:
            avisos.append("Termo informado sem cliente da API; a busca de títulos não rodou.")
        else:
            serp = analisar_serp(
                [termo], hl=hl, gl=gl, client=client, now=now, max_results=max_results, pages=pages
            )
            avisos.extend(serp.get("avisos") or [])
            if serp.get("termos"):
                base.extend(serp["termos"][0].get("videos") or [])
            elif not client.enabled:
                avisos.append("Sem YOUTUBE_API_KEY não há títulos da busca. Use --imagens para arquivos locais.")
    for caminho in imagens or []:
        path = Path(caminho)
        if not path.is_file():
            avisos.append(f"Arquivo ignorado: {path}")
            continue
        base.append(
            {
                "video_id": path.stem,
                "titulo": path.stem.replace("_", " ").replace("-", " "),
                "origem": "arquivo",
                "imagem_bytes": path.read_bytes(),
            }
        )
    analisador = vision if vision is not None else LocalVision()
    # Sem imagem, não chama visão. O stub de teste pode falhar se for chamado à toa.
    class _SomenteComImagem:
        def analyze(self, image_bytes: bytes, titulo: str = "") -> dict:
            return analisador.analyze(image_bytes, titulo)

    linhas = [
        _linha(
            video,
            vision=_SomenteComImagem(),
            transport=transport,
            baixar=baixar_miniaturas,
            gemini_enabled=gemini_enabled,
            gemini_key=gemini_key,
            gemini_model=gemini_model,
        )
        for video in base
    ]
    gemini_feitos = sum(1 for linha in linhas if (linha.get("gemini") or {}).get("status") == "ok")
    return {
        "modulo": "titles",
        "ok": bool(linhas) or not termo,
        "n": len(linhas),
        "itens": linhas,
        "cruzamento_estudo": _cruzar(linhas),
        "visao_agregada": _resumo_visao(linhas),
        "gemini": {
            "habilitado": gemini_enabled,
            "chamadas_ok": gemini_feitos,
            "nota": (
                "Desligado por padrão. Mesmo ligado, os traços de IA do estudo são correlação fraca "
                "ou sem efeito confirmado. Sinal forte do estudo não está na miniatura."
            ),
        },
        "estudo": NOTA_GERAL,
        "avisos": avisos,
        "cota": client.quota.resumo() if client is not None else None,
    }
