"""Leitura opcional de miniatura por Gemini. Desligada por padrão.

Não roda sem as duas condições: o usuário passa ``enabled=True`` (CLI ``--gemini``)
e existe ``GEMINI_API_KEY``. Sem isso nenhuma requisição é feita.
"""

from __future__ import annotations

import base64
import json
from typing import Any

from youtube_seo.http import HttpError, Transport, redact_text

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODELO_PADRAO = "gemini-2.5-flash-lite"

PROMPT = """Leia esta miniatura de YouTube e responda só com JSON, sem markdown, nestas chaves:
rosto (bool), rosto_grande (bool), olhar_camera (bool), expressao (feliz|surpresa|seria|medo|raiva|triste|nenhuma),
seta (bool), palavras (int), complementa_titulo (bool), objeto (bool), estilo (montagem|ilustracao|3d|outro),
fundo (real|ilustrado|colagem|liso|outro).
Título do vídeo, só como contexto: {titulo}
"""


def _mime(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG"):
        return "image/png"
    if image_bytes.startswith(b"RIFF"):
        return "image/webp"
    return "image/jpeg"


def _texto_resposta(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""
    parts = ((candidates[0] or {}).get("content") or {}).get("parts") or []
    return "\n".join(p.get("text", "") for p in parts if isinstance(p, dict)).strip()


def _json_solto(texto: str) -> dict | None:
    limpo = texto.strip()
    if limpo.startswith("```"):
        limpo = limpo.strip("`")
        limpo = limpo.removeprefix("json").strip()
    try:
        parsed = json.loads(limpo)
    except json.JSONDecodeError:
        inicio, fim = limpo.find("{"), limpo.rfind("}")
        if inicio < 0 or fim <= inicio:
            return None
        try:
            parsed = json.loads(limpo[inicio : fim + 1])
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


def analisar(
    image_bytes: bytes | None,
    titulo: str,
    *,
    enabled: bool,
    api_key: str | None,
    transport: Transport | None,
    model: str = MODELO_PADRAO,
) -> dict[str, Any]:
    if not enabled:
        return {
            "status": "desligado",
            "custo": "R$ 0 (chamada não feita)",
            "motivo": "Gemini fica desligado por padrão. Só roda com --gemini e GEMINI_API_KEY.",
        }
    if not api_key:
        return {
            "status": "sem_chave",
            "custo": "R$ 0 (chamada não feita)",
            "motivo": "GEMINI_API_KEY ausente. A leitura local segue; nenhuma chamada paga foi feita.",
        }
    if not image_bytes:
        return {
            "status": "sem_imagem",
            "custo": "R$ 0 (chamada não feita)",
            "motivo": "Não há bytes de miniatura para enviar.",
        }
    if transport is None:
        return {
            "status": "sem_transporte",
            "custo": "R$ 0 (chamada não feita)",
            "motivo": "Transporte HTTP indisponível.",
        }
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": PROMPT.format(titulo=titulo or "")},
                    {"inline_data": {"mime_type": _mime(image_bytes), "data": base64.b64encode(image_bytes).decode("ascii")}},
                ]
            }
        ],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    url = ENDPOINT.format(model=model)
    try:
        data = transport.post_json(url, payload, params={"key": api_key})
    except HttpError as exc:
        return {
            "status": "erro",
            "custo": "a tentativa foi feita na conta de quem forneceu a chave",
            "motivo": redact_text(str(exc), [api_key]),
            "modelo": model,
        }
    parsed = _json_solto(_texto_resposta(data if isinstance(data, dict) else {}))
    if not parsed:
        return {
            "status": "resposta_invalida",
            "custo": "a chamada foi feita na conta de quem forneceu a chave",
            "motivo": "A resposta não veio em JSON utilizável.",
            "modelo": model,
        }
    return {
        "status": "ok",
        "custo": "chamada paga na conta Google AI de quem forneceu GEMINI_API_KEY; opt-in",
        "modelo": model,
        "leitura": parsed,
        "forca": "fraco",
        "nota": (
            "Traços lidos por IA no estudo não passaram na correção para múltiplos testes. "
            "Trate como hipótese fraca, não como sinal forte."
        ),
    }
