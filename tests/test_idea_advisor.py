"""Testes do motor de consulta (pytest). Rodam offline, só com o knowledge_base.json."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

try:  # dentro do pacote youtube_seo
    from youtube_seo.advisor import idea_advisor as ia
except ImportError:  # pasta solta: motor_consulta/tests
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import idea_advisor as ia  # type: ignore

SECOES = ["1_diagnostico", "2_duracao", "3_titulo", "4_thumbnail", "5_cadencia", "6_exemplos_reais", "7_checklist"]


def test_kb_compacto_e_completo():
    kb = ia.carregar_kb(str(ia.KB_PADRAO))
    assert ia.KB_PADRAO.stat().st_size < 3_000_000
    assert kb["meta"]["videos"] == 26194 and kb["meta"]["canais"] == 310
    assert kb["meta"]["videos_200k"] == 17882 and kb["meta"]["videos_pequenos"] == 8312
    for chave in ("portes", "duracao", "titulo", "thumbnail", "cadencia", "nicho_idioma", "referencias"):
        assert chave in kb
    assert set(kb["portes"]) == {"pequeno", "emergente", "medio", "grande", "gigante"}
    assert len(kb["referencias"]["linhas"]) > 1000


def test_parecer_tem_as_7_secoes_e_avisos_de_limite():
    p = ia.aconselhar(ia.Ideia(titulo="Quanto rende 1000 reais no Tesouro Direto em 2026", nicho="financas", idioma="pt", porte="grande", duracao_min=22))
    for s in SECOES:
        assert s in p
    md = ia.para_markdown(p)
    assert "CTR" in md and "retenção" in md
    assert "nunca promete viralização" in md
    assert len(p["6_exemplos_reais"]) == 5
    assert all(e["nicho"] == "financas" for e in p["6_exemplos_reais"])


def test_tracos_de_titulo():
    t = ia.analisar_titulo("I Tried The SECRET iPhone Trick For 30 Days")
    assert t["primeira_pessoa"] and t["numero"] and "iphone" in t["entidade_famosa"] and "SECRET" in t["palavra_caixa_alta"]
    t2 = ia.analisar_titulo("O segredo do sucesso e da felicidade")
    assert set(t2["abstrato"]) >= {"sucesso", "felicidade"}
    assert ia.analisar_titulo("Messi vs Ronaldo")["colab_vs"]


def test_alertas_principais():
    p = ia.aconselhar(ia.Ideia(titulo="My journey to success and happiness", nicho="tech", idioma="en", porte="grande",
                               duracao_min=65, dias_desde_ultimo=1, ultimo_resultado="flop"))
    riscos = " ".join(p["1_diagnostico"]["riscos"])
    assert "abstrato" in riscos
    assert "1ª pessoa" in riscos
    assert "Menos de 2 dias" in riscos
    assert "fracasso" in riscos
    assert "Tech é o único nicho" in riscos


def test_pequenos_nao_recebem_penalidade_forte_de_intervalo():
    p = ia.aconselhar(ia.Ideia(titulo="Receita de pão caseiro fácil", nicho="culinaria", idioma="pt", porte="pequeno", dias_desde_ultimo=1))
    assert not any("Menos de 2 dias desde o vídeo anterior em canal 200k+" in r for r in p["1_diagnostico"]["riscos"])
    assert any("inconclusivo" in n for n in p["5_cadencia"]["notas"])


def test_capa_e_alinhamento():
    p = ia.aconselhar(ia.Ideia(titulo="Os 3 piores investimentos depois dos 40", nicho="financas", idioma="pt", porte="emergente",
                               thumb_notes='fundo verde, sem rosto, seta, texto: "3 PIORES INVESTIMENTOS"'))
    nomes = {d["padrao"] for d in p["4_thumbnail"]["padroes_detectados_nas_notas"]}
    assert {"Cor dominante verde", "Sem rosto", "Seta ou círculo"} <= nomes
    assert p["4_thumbnail"]["alinhamento_titulo_capa"]["nivel"] in ("médio", "alto")
    assert any(m["padrao"] == "Rosto grande" for m in p["4_thumbnail"]["mitos_a_ignorar"])


def test_porte_e_aliases():
    assert ia.porte_por_inscritos(12_000) == "pequeno"
    assert ia.porte_por_inscritos(120_000) == "emergente"
    assert ia.porte_por_inscritos(900_000) == "medio"
    assert ia.porte_por_inscritos(5_000_000) == "grande"
    assert ia.porte_por_inscritos(20_000_000) == "gigante"
    i = ia.Ideia(titulo="x", nicho="Finance", idioma="EN", porte="small").normalizar()
    assert (i.nicho, i.idioma, i.porte) == ("financas", "en", "pequeno")
    with pytest.raises(ValueError):
        ia.Ideia(titulo="x", nicho="astrologia").normalizar()


def test_consistencia_tematica_com_titulos_recentes():
    recentes = ["Receita de bolo de cenoura", "Bolo de chocolate fofinho", "Receita de bolo de laranja"]
    p = ia.aconselhar(ia.Ideia(titulo="Review do novo iPhone 18", nicho="culinaria", idioma="pt", porte="pequeno", titulos_recentes=recentes))
    assert any("desvio temático" in r for r in p["1_diagnostico"]["riscos"])


def test_cli_do_pacote_advise_e_idea_sem_rede(monkeypatch):
    import io

    from youtube_seo.cli import main

    def boom(*_a, **_k):
        raise AssertionError("o advisor não pode abrir rede")

    monkeypatch.setattr("youtube_seo.cli.UrllibTransport", boom)
    saida = io.StringIO()
    codigo = main(
        [
            "advise",
            "--title",
            "5 celulares baratos que valem a pena em 2026",
            "--niche",
            "tech",
            "--lang",
            "pt",
            "--tier",
            "pequeno",
            "--duration-min",
            "18",
        ],
        stdout=saida,
        env={},
    )
    assert codigo == 0
    texto = saida.getvalue()
    assert texto.startswith("# Parecer da ideia")
    assert "CTR" in texto and "retenção" in texto

    saida_json = io.StringIO()
    codigo_json = main(
        [
            "idea",
            "--title",
            "50 Geography Facts You Won't Believe",
            "--niche",
            "educacao",
            "--lang",
            "en",
            "--subscribers",
            "19500",
            "--duration-min",
            "21",
            "--format",
            "json",
        ],
        stdout=saida_json,
        env={},
    )
    assert codigo_json == 0
    corpo = json.loads(saida_json.getvalue())
    assert corpo["ideia"]["porte"] == "pequeno"

    erro = io.StringIO()
    codigo_ruim = main(
        ["advise", "--title", "x", "--niche", "astrologia"],
        stdout=io.StringIO(),
        stderr=erro,
        env={},
    )
    assert codigo_ruim == 2
    assert "nicho" in erro.getvalue()


def test_cli_json_e_markdown():
    script = Path(ia.__file__)
    out = subprocess.run([sys.executable, str(script), "--title", "50 Geography Facts You Won't Believe", "--niche", "educacao",
                          "--lang", "en", "--subscribers", "19500", "--duration-min", "21", "--format", "json"],
                         capture_output=True, text=True, check=True)
    d = json.loads(out.stdout)
    assert d["ideia"]["porte"] == "pequeno"
    out2 = subprocess.run([sys.executable, str(script), "--title", "Teste", "--niche", "games", "--format", "markdown"], capture_output=True, text=True, check=True)
    assert out2.stdout.startswith("# Parecer da ideia")
    bad = subprocess.run([sys.executable, str(script), "--title", "x", "--niche", "astrologia"], capture_output=True, text=True)
    assert bad.returncode == 2


def test_sem_travessao_no_texto_gerado():
    p = ia.aconselhar(ia.Ideia(titulo="Como montar um PC gamer barato", nicho="games", idioma="pt", porte="medio", duracao_min=25,
                               thumb_notes="rosto surpreso, fundo vermelho", dias_desde_ultimo=4))
    md = ia.para_markdown(p)
    corpo = md.split("## 6.")[0] + md.split("## 7.")[1]  # exemplos reais trazem títulos verbatim
    assert "—" not in corpo and "–" not in corpo and " - " not in corpo
