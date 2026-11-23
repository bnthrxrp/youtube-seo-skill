from youtube_seo.cliente import YouTubeClient
from youtube_seo.modulos.palavras import pesquisar_palavras


def _chamar(servicos, **extra):
    return pesquisar_palavras(
        "pao caseiro",
        hl="pt",
        gl="BR",
        client=servicos["client"],
        transport=servicos["transport"],
        cache=servicos["cache"],
        quota=servicos["quota"],
        now=servicos["now"],
        letras="",
        usar_prefixos=extra.pop("usar_prefixos", False),
        **extra,
    )


def test_com_chave_junta_sugestao_tags_e_canais(servicos):
    payload = _chamar(servicos)
    assert payload["ok"] is True
    assert payload["api"]["usada"] is True
    termos = [s["termo"] for s in payload["sugestoes"]]
    assert termos[:2] == ["pao caseiro facil", "pao caseiro integral"]
    assert payload["sugestoes"][0]["fonte"] == "autocomplete"
    assert payload["sugestoes"][0]["intencao"] == "indefinida"
    assert {t["tag"] for t in payload["tags"]} >= {"pao", "caseiro"}
    assert payload["metricas"]["n_videos"] == 3
    assert payload["metricas"]["mediana_views"] == 2000
    assert payload["canais"][0]["porte"] == "pequeno"
    assert payload["videos"][1]["capitulos"] is True
    assert payload["videos"][1]["duracao_segundos"] == 1200
    assert "test-key" not in str(payload)


def test_sem_chave_fica_so_no_autocomplete(servicos):
    servicos["client"] = YouTubeClient("", servicos["transport"], servicos["cache"], servicos["quota"])
    antes = len(servicos["transport"].calls)
    payload = _chamar(servicos)
    assert payload["ok"] is True
    assert payload["api"]["usada"] is False
    assert payload["videos"] == []
    assert payload["sugestoes"]
    novas = servicos["transport"].urls()[antes:]
    assert novas
    assert all("youtube/v3" not in url for url in novas)
    assert servicos["quota"].session_used == 0


def test_prefixo_entra_como_expansao(servicos):
    servicos["transport"].sugestoes["como pao caseiro"] = ["como fazer pao caseiro"]
    payload = _chamar(servicos, usar_prefixos=True)
    achado = next(s for s in payload["sugestoes"] if s["termo"] == "como fazer pao caseiro")
    assert achado["fonte"] == "prefixo"
    assert achado["intencao"] == "aprender"


def test_cota_bloqueia_antes_da_rede(tmp_path, servicos):
    import json
    from datetime import datetime, timezone

    from tests.roteador import NOW

    dia = datetime.fromtimestamp(NOW, tz=timezone.utc).date().isoformat()
    path = tmp_path / "cheia.json"
    path.write_text(json.dumps({"date": dia, "used": 9950, "events": []}), encoding="utf-8")
    from youtube_seo.quota import QuotaLedger

    servicos["quota"] = QuotaLedger(path, now=servicos["now"])
    servicos["client"] = YouTubeClient("test-key", servicos["transport"], servicos["cache"], servicos["quota"])
    payload = _chamar(servicos)
    assert payload["api"]["bloqueada_por_cota"] is True
    assert payload["videos"] == []
    assert servicos["quota"].used == 9950
    assert all("youtube/v3" not in url for url in servicos["transport"].urls())
    assert any("100" in aviso for aviso in payload["cota"]["avisos"])
