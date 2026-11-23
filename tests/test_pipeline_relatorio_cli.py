import io
import json

from tests.roteador import CANAL_C, NOW, Roteador
from youtube_seo.cli import main
from youtube_seo.modulos.pipeline import executar_pipeline
from youtube_seo.saida import salvar


def test_pipeline_reusa_a_busca_e_grava_os_cinco_relatorios(servicos):
    payload = executar_pipeline(
        "pao caseiro",
        hl="pt",
        gl="BR",
        client=servicos["client"],
        transport=servicos["transport"],
        cache=servicos["cache"],
        quota=servicos["quota"],
        now=servicos["now"],
        canais=[CANAL_C],
        max_serp=1,
        letras="",
        usar_prefixos=False,
        gemini_enabled=False,
        gemini_key="nao-usar",
    )
    assert payload["ordem"] == ["keywords", "serp", "competitors", "titles", "gaps"]
    assert payload["keywords"]["ok"] and payload["serp"]["ok"] and payload["gaps"]["ok"]
    assert payload["competitors"]["canais"][0]["n_videos"] == 5
    assert payload["titles"]["gemini"]["habilitado"] is False
    assert payload["titles"]["n"] == 3
    cobradas = [e for e in servicos["quota"].session_events if e["method"] == "search.list" and not e["cached"]]
    assert len(cobradas) == 1
    assert servicos["quota"].session_avoided >= 100
    assert not servicos["transport"].posts
    caminhos = salvar(servicos["tmp"] / "saida", payload)
    nomes = {p.name for p in caminhos}
    assert nomes >= {
        "keywords.json",
        "keywords.md",
        "serp.json",
        "serp.md",
        "competitors.json",
        "competitors.md",
        "titles.json",
        "titles.md",
        "gaps.json",
        "gaps.md",
        "pipeline.json",
        "pipeline.md",
    }
    gaps_md = (servicos["tmp"] / "saida" / "gaps.md").read_text(encoding="utf-8")
    serp_md = (servicos["tmp"] / "saida" / "serp.md").read_text(encoding="utf-8")
    assert "não publica volume oficial" in gaps_md
    assert "search.list custa 100" in serp_md
    assert "10.000" in serp_md
    assert "oportunidade" in gaps_md
    bruto = "".join(p.read_text(encoding="utf-8") for p in caminhos)
    assert "test-key" not in bruto
    assert "nao-usar" not in bruto


def test_cli_keywords_serp_e_pipeline(tmp_path):
    transporte = Roteador()
    saida = io.StringIO()
    codigo = main(
        [
            "keywords",
            "pao caseiro",
            "--hl",
            "pt",
            "--gl",
            "BR",
            "--letras",
            "",
            "--sem-prefixos",
            "-o",
            str(tmp_path / "kw"),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--quota-file",
            str(tmp_path / "quota.json"),
        ],
        env={"YOUTUBE_API_KEY": "test-key"},
        transport=transporte,
        now=lambda: NOW,
        stdout=saida,
    )
    assert codigo == 0
    corpo = json.loads((tmp_path / "kw" / "keywords.json").read_text(encoding="utf-8"))
    assert corpo["sugestoes"][0]["termo"] == "pao caseiro facil"
    assert "test-key" not in saida.getvalue()

    sem_chave = main(
        ["serp", "pao caseiro", "-o", str(tmp_path / "serp"), "--cache-dir", str(tmp_path / "cache2"), "--quota-file", str(tmp_path / "q2.json")],
        env={},
        transport=Roteador(),
        now=lambda: NOW,
        stdout=io.StringIO(),
    )
    assert sem_chave == 2
    assert (tmp_path / "serp" / "serp.md").exists()

    transporte = Roteador()
    codigo = main(
        [
            "pipeline",
            "pao caseiro",
            "--hl",
            "pt",
            "--gl",
            "BR",
            "--letras",
            "",
            "--sem-prefixos",
            "--max-serp",
            "1",
            "--canais",
            CANAL_C,
            "-o",
            str(tmp_path / "pipe"),
            "--cache-dir",
            str(tmp_path / "cache3"),
            "--quota-file",
            str(tmp_path / "q3.json"),
        ],
        env={"YOUTUBE_API_KEY": "test-key", "GEMINI_API_KEY": "nao-chamar"},
        transport=transporte,
        now=lambda: NOW,
        stdout=io.StringIO(),
    )
    assert codigo == 0
    assert (tmp_path / "pipe" / "competitors.md").exists()
    assert (tmp_path / "pipe" / "titles.md").exists()
    assert transporte.posts == []
    quota = json.loads((tmp_path / "q3.json").read_text(encoding="utf-8"))
    assert quota["used"] < 200
    assert "test-key" not in json.dumps(quota)


def test_ajuda():
    import pytest

    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert main([]) == 0


def test_pacote_nao_traz_segredo_nem_env():
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[1]
    proibidos = ("AIza", "BEGIN PRIVATE KEY", "sk-")
    for pasta in ("youtube_seo",):
        for arquivo in (raiz / pasta).rglob("*.py"):
            texto = arquivo.read_text(encoding="utf-8")
            for marca in proibidos:
                assert marca not in texto, arquivo
    assert not (raiz / ".env").exists()
