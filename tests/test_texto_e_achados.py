from youtube_seo.findings import FINDINGS, NOTA_GERAL, achar
from youtube_seo.modelos import iso_duracao, porte_de
from youtube_seo.texto import extrair_titulo, metricas_ocr, tem_capitulos


def test_tracos_de_titulo():
    titulo = extrair_titulo("COMO fazer PÃO em 10 minutos?")
    assert titulo["tem_pergunta"] == 1
    assert titulo["tem_numero"] == 1
    assert titulo["tem_palavra_caps"] == 1
    assert titulo["tem_emoji"] == 0
    assert titulo["titulo_todo_caps"] == 0
    assert extrair_titulo("EU COMPREI UM FORNO NOVO")["titulo_todo_caps"] == 1
    assert extrair_titulo("eu comprei um forno")["tem_eu"] == 1
    assert extrair_titulo("I bought a mixer")["tem_eu"] == 1
    assert extrair_titulo("pão para você")["tem_voce"] == 1


def test_capitulos_seguem_a_regra_do_estudo():
    assert tem_capitulos("0:00 abertura\n0:45 massa\n2:10 forno\n")
    assert not tem_capitulos("1:00 abertura\n2:00 massa\n3:00 forno\n")
    assert not tem_capitulos("0:00 só o começo")


def test_duracao_iso_e_porte_do_estudo():
    assert iso_duracao("PT8M") == 480
    assert iso_duracao("PT1H2M3S") == 3723
    assert iso_duracao("P1DT1H") == 90000
    assert porte_de(199_999) == "pequeno"
    assert porte_de(200_000) == "medio"
    assert porte_de(2_000_000) == "grande"
    assert porte_de(20_000_000) == "gigante"
    assert porte_de(None) == "desconhecido"
    assert porte_de(10, oculto=True) == "oculto"


def test_ocr_mesmos_limiares_do_estudo():
    repete = metricas_ocr("PAO CASEIRO", "pao caseiro facil")
    assert repete["ocr_repete_titulo"] == 1
    assert repete["ocr_caps"] == 1
    assert metricas_ocr("outra coisa nova", "pao caseiro facil")["ocr_repete_titulo"] == 0
    assert metricas_ocr("custa R$ 10", "oferta")["ocr_dinheiro"] == 1
    assert metricas_ocr("Ola", "ola")["ocr_caps"] == 0


def test_catalogo_separa_sinal_forte_de_efeito_nulo():
    assert achar("legenda_canal")["forca"] == "forte"
    assert achar("duracao")["forca"] == "forte"
    assert achar("emoji_titulo")["forca"] == "provavel"
    assert achar("tamanho_titulo")["forca"] == "sem_efeito"
    assert achar("rosto_grande")["forca"] == "fraco"
    assert achar("expressao_ia")["forca"] == "fraco"
    assert "1,5%" in NOTA_GERAL
    assert all(item["forca"] != "forte" or chave in {"legenda_canal", "duracao"} for chave, item in FINDINGS.items())
