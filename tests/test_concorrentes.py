from tests.roteador import CANAL_C
from youtube_seo.modulos.concorrentes import monitorar_concorrentes


def test_frequencia_temas_legenda_e_desempenho_contra_a_mediana(servicos):
    payload = monitorar_concorrentes([CANAL_C], client=servicos["client"], now=servicos["now"], max_videos=50)
    assert payload["ok"] is True
    canal = payload["canais"][0]
    assert canal["fonte_lista"] == "UULF"
    assert canal["porte"] == "medio"
    assert canal["frequencia"]["por_semana"] == 1.0
    assert canal["frequencia"]["intervalo_mediano_dias"] == 7
    assert canal["pct_legendas"] == 60.0
    assert canal["duracao_mediana_segundos"] == 600
    termos = [t["termo"] for t in canal["temas"]["termos"]]
    assert "pao" in termos and "caseiro" in termos and "de" not in termos
    desempenho = {v["titulo"]: v for v in canal["desempenho"]["videos"]}
    assert canal["desempenho"]["fragil"] is False
    assert canal["desempenho"]["mediana_views"] == 100
    assert desempenho["receita de pao caseiro 5"]["faixa"] == "acima"
    assert desempenho["receita de pao caseiro 1"]["faixa"] == "perto_da_mediana"
    metodos = [e["method"] for e in servicos["quota"].session_events if not e["cached"]]
    assert "search.list" not in metodos
    assert metodos.count("channels.list") == 1
    assert metodos.count("playlistItems.list") == 1
    assert metodos.count("videos.list") == 1
    assert servicos["quota"].session_used == 3


def test_canal_inexistente(servicos):
    payload = monitorar_concorrentes(["UC" + "z" * 22], client=servicos["client"], now=servicos["now"])
    assert payload["canais"][0]["ok"] is False
