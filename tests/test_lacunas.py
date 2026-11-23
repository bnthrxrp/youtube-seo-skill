from youtube_seo.modulos.lacunas import DISCLAIMER, analisar_lacunas
from youtube_seo.padroes import classificar_concorrencia


def test_oportunidade_quando_a_oferta_e_pequena(servicos):
    payload = analisar_lacunas(
        "pao caseiro",
        hl="pt",
        gl="BR",
        client=servicos["client"],
        transport=servicos["transport"],
        cache=servicos["cache"],
        quota=servicos["quota"],
        now=servicos["now"],
        max_serp=1,
        letras="",
        usar_prefixos=False,
    )
    assert payload["disclaimer"] == DISCLAIMER
    assert "não publica volume oficial" in payload["disclaimer"]
    semente = payload["oportunidades"][0]
    assert semente["termo"] == "pao caseiro"
    assert semente["demanda"] == "semente"
    assert semente["concorrencia"] == "baixa"
    assert semente["classe"] == "oportunidade"
    assert semente["pontos"] == 85
    assert payload["completo"] is False
    assert payload["cobertura_serp"]["medidas"] == 1
    outras = [o for o in payload["oportunidades"] if o["termo"] != "pao caseiro"]
    assert outras
    assert all(o["concorrencia"] == "nao_medida" for o in outras)
    assert all(o["classe"] == "incompleta" for o in outras)
    assert all(o["pontos"] is None for o in outras)
    buscas = [c for c in servicos["transport"].calls if c["url"].endswith("/search") and "complete" not in c["url"]]
    assert len(buscas) == 1


def test_concorrencia_alta_com_gigante_recente():
    classe, _nota = classificar_concorrencia(
        {"n": 5, "mediana_inscritos": 5_000_000, "idade": {"mediana_dias": 30}, "pct_canais_pequenos": 0}
    )
    assert classe == "alta"
    antiga, _nota = classificar_concorrencia(
        {"n": 5, "mediana_inscritos": 500_000, "idade": {"mediana_dias": 400}, "pct_canais_pequenos": 0}
    )
    assert antiga == "baixa"


def test_sem_serp_o_relatorio_ainda_diz_que_a_demanda_e_estimada(servicos):
    from youtube_seo.cliente import YouTubeClient

    servicos["client"] = YouTubeClient("", servicos["transport"], servicos["cache"], servicos["quota"])
    payload = analisar_lacunas(
        "pao caseiro",
        hl="pt",
        gl="BR",
        client=servicos["client"],
        transport=servicos["transport"],
        cache=servicos["cache"],
        quota=servicos["quota"],
        now=servicos["now"],
        letras="",
        usar_prefixos=False,
    )
    assert payload["ok"] is True
    assert payload["completo"] is False
    assert payload["oportunidades"][0]["classe"] == "incompleta"
    assert servicos["quota"].session_used == 0
