import json
from datetime import datetime, timezone

from tests.roteador import NOW
from youtube_seo.cache import FileCache
from youtube_seo.quota import COSTS, DAILY_LIMIT, QuotaLedger


def test_cache_ignora_chave_e_expira(tmp_path):
    relogio = {"t": 0.0}
    cache = FileCache(tmp_path, now=lambda: relogio["t"])
    assert cache.make_key("search", {"q": "pao", "key": "test-key"}) == cache.make_key("search", {"q": "pao"})
    cache.put("abc", {"ok": 1}, ttl=10, meta={"endpoint": "search"})
    assert cache.get("abc") == {"ok": 1}
    relogio["t"] = 10
    assert cache.get("abc") is None
    texto = (tmp_path / "abc.json").read_text()
    assert "test-key" not in texto


def test_search_custa_100_e_o_dia_zera(tmp_path):
    assert COSTS["search.list"] == 100
    assert COSTS["videos.list"] == 1
    assert DAILY_LIMIT == 10_000
    dia = datetime.fromtimestamp(NOW, tz=timezone.utc).date().isoformat()
    path = tmp_path / "quota.json"
    path.write_text(json.dumps({"date": dia, "used": 8000, "events": []}), encoding="utf-8")
    ledger = QuotaLedger(path, now=lambda: NOW)
    assert ledger.used == 8000
    assert any("80%" in aviso for aviso in ledger.resumo()["avisos"])
    ledger.charge("videos.list")
    assert ledger.used == 8001
    seguinte = QuotaLedger(path, now=lambda: NOW + 86400)
    assert seguinte.used == 0


def test_cache_nao_debita_e_arquivo_nao_guarda_chave(servicos):
    from youtube_seo.modulos.palavras import pesquisar_palavras

    comum = dict(
        termo="pao caseiro",
        hl="pt",
        gl="BR",
        letras="",
        usar_prefixos=False,
        max_results=25,
        client=servicos["client"],
        transport=servicos["transport"],
        cache=servicos["cache"],
        quota=servicos["quota"],
        now=servicos["now"],
    )
    primeiro = pesquisar_palavras(**comum)
    segundo = pesquisar_palavras(**comum)
    eventos = servicos["quota"].session_events
    buscas = [e for e in eventos if e["method"] == "search.list" and not e["cached"]]
    assert len(buscas) == 1
    assert buscas[0]["units"] == 100
    assert primeiro["cota"]["gastas_nesta_execucao"] == 102
    assert segundo["cota"]["evitadas_por_cache"] == 102
    assert segundo["cota"]["usadas_no_dia"] == 102
    bruto = "".join(p.read_text() for p in (servicos["tmp"]).rglob("*.json"))
    assert "test-key" not in bruto
    assert "search.list custa 100" in segundo["cota"]["regra"]
