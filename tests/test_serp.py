from youtube_seo.cliente import YouTubeClient
from youtube_seo.modulos.serp import analisar_serp


def test_padroes_de_titulo_duracao_idade_legenda_e_concentracao(servicos):
    payload = analisar_serp(
        ["pao caseiro"],
        hl="pt",
        gl="BR",
        client=servicos["client"],
        now=servicos["now"],
    )
    assert payload["ok"] is True
    bloco = payload["termos"][0]
    padrao = bloco["padroes"]
    assert padrao["titulos"]["pct_pergunta"] == 33.3
    assert padrao["titulos"]["pct_palavra_caps"] == 33.3
    assert padrao["titulos"]["pct_termo_no_inicio"] == 100.0
    assert padrao["duracao"]["mediana_segundos"] == 480
    assert padrao["duracao"]["faixas"]["ate_5min"] == 1
    assert padrao["duracao"]["faixas"]["de_15_a_60"] == 1
    assert padrao["idade"]["mediana_dias"] == 100
    assert padrao["pct_legendas"] == 66.7
    assert padrao["pct_capitulos"] == 33.3
    assert padrao["mediana_inscritos"] == 50_000
    assert padrao["pct_canais_pequenos"] == 100.0
    assert padrao["concentracao"]["n_canais"] == 2
    assert padrao["concentracao"]["participacao_top1"] == 0.667
    assert padrao["concentracao"]["hhi"] == 0.556
    forcas = {n["traco"]: n["forca"] for n in bloco["leitura_estudo"]}
    assert "forte" in forcas.values()
    assert forcas["Tamanho do título"] == "sem_efeito"
    assert payload["cota_estimada_sem_cache"]["search.list"] == 100
    assert payload["cota"]["gastas_nesta_execucao"] == 102


def test_segunda_serp_nao_gasta_de_novo(servicos):
    analisar_serp(["pao caseiro"], hl="pt", gl="BR", client=servicos["client"], now=servicos["now"])
    analisar_serp(["pao caseiro"], hl="pt", gl="BR", client=servicos["client"], now=servicos["now"])
    cobradas = [e for e in servicos["quota"].session_events if e["method"] == "search.list" and not e["cached"]]
    assert len(cobradas) == 1
    assert servicos["quota"].session_avoided >= 100


def test_termo_seguinte_e_pulado_quando_a_cota_nao_cabe(servicos):
    analisar_serp(["pao caseiro"], hl="pt", gl="BR", client=servicos["client"], now=servicos["now"])
    servicos["quota"].used = 9950
    servicos["quota"].save()
    # o ledger em memória é a fonte da próxima decisão; o arquivo só persiste a carga
    payload = analisar_serp(
        ["outro termo"],
        hl="pt",
        gl="BR",
        client=servicos["client"],
        now=servicos["now"],
    )
    assert payload["ok"] is False
    assert payload["pulados"][0]["termo"] == "outro termo"
    assert "100" in payload["pulados"][0]["motivo"]
    assert not any(c["params"].get("q") == "outro termo" for c in servicos["transport"].calls)


def test_sem_chave_nao_chama_a_api(servicos):
    servicos["client"] = YouTubeClient("", servicos["transport"], servicos["cache"], servicos["quota"])
    payload = analisar_serp(["pao caseiro"], hl="pt", gl="BR", client=servicos["client"], now=servicos["now"])
    assert payload["ok"] is False
    assert payload["termos"] == []
    assert servicos["quota"].session_used == 0
