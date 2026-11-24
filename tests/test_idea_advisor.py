"""Testes completos do motor de consulta offline (pytest, biblioteca padrão, sem rede)."""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

try:
    from youtube_seo.advisor import idea_advisor as ia
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import idea_advisor as ia  # type: ignore

SECOES = [
    "1_diagnostico",
    "2_duracao",
    "3_titulo",
    "4_thumbnail",
    "5_cadencia",
    "6_exemplos_reais",
    "7_checklist",
]

COMBINACOES_SUPORTADAS = [
    (nicho, porte, idioma)
    for nicho in ia.NICHOS
    for porte in ia.PORTES
    for idioma in ("pt", "en")
]


def _extrair_qs_do_texto(textos: list[str]) -> list[float]:
    qs: list[float] = []
    for txt in textos:
        for _ in re.finditer(r"q\s*<\s*0,001", txt, flags=re.I):
            qs.append(0.0005)
        for m in re.finditer(r"(?<!diferença\s)(?<!interação\s)q\s*=\s*([01],\d{1,4})", txt, flags=re.I):
            qs.append(float(m.group(1).replace(",", ".")))
    return qs


def _extrair_qs_de_regras_no_markdown(md: str) -> list[float]:
    """Extrai valores-q de regras exibidas no Markdown inteiro (incluindo a coluna numérica da tabela da Seção 3),
    ignorando linhas explicativas de mitos/ruído explicitamente descartados.
    """
    qs: list[float] = []
    em_secao_3 = False
    em_bloco_nao_importa = False
    for linha in _sem_linhas_de_titulos_verbatim(md).splitlines():
        if linha.startswith("## 3."):
            em_secao_3 = True
            em_bloco_nao_importa = False
        elif linha.startswith("## ") and not linha.startswith("## 3."):
            em_secao_3 = False
            em_bloco_nao_importa = False
        if linha.startswith("**O que não importa"):
            em_bloco_nao_importa = True
        if em_bloco_nao_importa:
            continue
        if "sem efeito estatístico intra-canal" in linha or "Mitos populares sem efeito" in linha:
            continue

        # Tabela da Seção 3: | Traço | Presente | Efeito | IC 95% | q | Classificação |
        if em_secao_3 and linha.startswith("|") and not linha.startswith("| Traço |") and not linha.startswith("|---"):
            colunas = [c.strip() for c in linha.strip("|").split("|")]
            if len(colunas) >= 5:
                col_q = colunas[4]
                if "< 0,001" in col_q:
                    qs.append(0.0005)
                else:
                    m_tab = re.search(r"\b([01],\d{1,4})\b", col_q)
                    if m_tab:
                        qs.append(float(m_tab.group(1).replace(",", ".")))
            continue

        qs.extend(_extrair_qs_do_texto([linha]))
    return qs


def _sem_linhas_de_titulos_verbatim(md: str) -> str:
    """Remove apenas as linhas de dados da tabela de exemplos reais (onde o título do vídeo é verbatim),
    preservando cabeçalho, cabeçalho da tabela e rodapé da Seção 6 para checagem estrita.
    """
    linhas_limpas: list[str] = []
    em_secao_6 = False
    for linha in md.splitlines():
        if linha.startswith("## 6."):
            em_secao_6 = True
        elif linha.startswith("## 7."):
            em_secao_6 = False
        if em_secao_6 and linha.startswith("|") and not linha.startswith("| Título |") and not linha.startswith("|---"):
            continue
        linhas_limpas.append(linha)
    return "\n".join(linhas_limpas)


def test_kb_compacto_normalizado_e_sem_clusters_banidos():
    kb = ia.carregar_kb(str(ia.KB_PADRAO))
    assert ia.KB_PADRAO.stat().st_size < 3_000_000
    assert kb.get("_normalizado") is True
    assert kb["meta"]["videos"] == 26194 and kb["meta"]["canais"] == 310
    assert kb["meta"]["videos_200k"] == 17882 and kb["meta"]["videos_pequenos"] == 8312
    for chave in ("portes", "duracao", "titulo", "thumbnail", "cadencia", "nicho_idioma", "referencias"):
        assert chave in kb
    assert set(kb["portes"]) == {"pequeno", "emergente", "medio", "grande", "gigante"}
    assert len(kb["referencias"]["linhas"]) > 1000

    # Unificação de chaves 200k+ / 200k_mais
    grupos_dur = kb["duracao"]["curvas_pequenos_vs_200k"]["grupos"]
    assert "200k+" in grupos_dur and "pequenos" in grupos_dur

    # Expurgo total de clusters HDB-* e KM12-* no bloco thumbnail
    th_dump = json.dumps(kb["thumbnail"], ensure_ascii=False)
    assert "HDB-" not in th_dump and "KM12-" not in th_dump

    # Imutabilidade do cache interno contra mutações feitas pelo chamador externo
    kb["meta"]["videos"] = -999
    kb["thumbnail"]["padroes"]["INJETADO"] = {"efeito": 999}
    kb_limpo = ia.carregar_kb(str(ia.KB_PADRAO))
    assert kb_limpo["meta"]["videos"] == 26194
    assert "INJETADO" not in kb_limpo["thumbnail"]["padroes"]


def test_parecer_tem_as_7_secoes_limites_conhecidos_e_avisos():
    p = ia.aconselhar(
        ia.Ideia(
            titulo="Quanto rende 1000 reais no Tesouro Direto em 2026",
            nicho="financas",
            idioma="pt",
            porte="grande",
            duracao_min=22,
        )
    )
    for s in SECOES:
        assert s in p
    diag = p["1_diagnostico"]
    assert len(diag["limites_conhecidos_desta_base"]) >= 8
    assert any("[Item 1]" in lim for lim in diag["limites_conhecidos_desta_base"])
    assert any("[Item 9]" in lim for lim in diag["limites_conhecidos_desta_base"])

    md = ia.para_markdown(p)
    assert "### Limites conhecidos desta base" in md
    assert "CTR" in md and "retenção" in md
    assert "nunca promete viralização" in md
    assert 0 < len(p["6_exemplos_reais"]) <= 5
    assert all(e["nicho"] == "financas" for e in p["6_exemplos_reais"])
    assert all(e["sobreposicao_lexical"] >= 0.05 for e in p["6_exemplos_reais"])


@pytest.mark.parametrize(("nicho", "porte", "idioma"), COMBINACOES_SUPORTADAS)
def test_nenhum_nd_nem_cluster_banido_em_todas_combinacoes(nicho: str, porte: str, idioma: str):
    titulo = (
        "Como organizar 3 ideias praticas de estudo em 2026"
        if idioma == "pt"
        else "How to build 3 practical projects in 2026"
    )
    p = ia.aconselhar(
        ia.Ideia(
            titulo=titulo,
            nicho=nicho,
            idioma=idioma,
            porte=porte,
            duracao_min=16,
            thumb_notes='fundo escuro, objeto em destaque, texto: "3 PROJETOS 2026"',
            dias_desde_ultimo=5,
        )
    )
    md = ia.para_markdown(p)
    md_proprio = _sem_linhas_de_titulos_verbatim(md)

    assert "n/d" not in md_proprio.lower()
    assert "HDB-" not in md_proprio and "KM12-" not in md_proprio
    assert ">45d" not in md_proprio
    if ia.GRUPO[porte] == "pequenos":
        assert p["5_cadencia"]["efeito_curva_200k_vs_7d"] is None
        assert "referência descritiva na curva 200k+ vs 7 dias" not in md_proprio

    dump_sem_exemplos = json.dumps({k: v for k, v in p.items() if k != "6_exemplos_reais"}, ensure_ascii=False)
    assert "n/d" not in dump_sem_exemplos.lower()
    assert "HDB-" not in dump_sem_exemplos and "KM12-" not in dump_sem_exemplos


def test_pequeno_ancorado_na_celula_ou_curva_propria_e_teto_35min():
    for nicho in ("culinaria", "documentario", "tech", "games", "educacao"):
        p_peq = ia.aconselhar(
            ia.Ideia(titulo="Guia pratico com 5 exemplos reais", nicho=nicho, idioma="pt", porte="pequeno", duracao_min=18)
        )
        dur = p_peq["2_duracao"]
        faixa = dur["faixa_recomendada_min"]
        origem = dur["origem_faixa_recomendada"]
        assert faixa is not None and len(faixa) == 2
        assert faixa[0] >= 8
        assert faixa[1] <= (25 if nicho == "tech" else 35)
        assert ("célula empírica" in origem) or ("pequenos" in origem)
        assert "200k+" not in origem


def test_duracao_porte_medio_respeita_teto_pratico_do_regime_5k_2m():
    for nicho in ia.NICHOS:
        p_med = ia.aconselhar(
            ia.Ideia(titulo="Analise completa do cenario atual", nicho=nicho, idioma="pt", porte="medio", duracao_min=28)
        )
        dur = p_med["2_duracao"]
        faixa = dur["faixa_recomendada_min"]
        teto_esperado = 30 if nicho == "tech" else 45
        assert faixa is not None and len(faixa) == 2
        assert faixa[0] < faixa[1] <= teto_esperado
        # Coerência entre topo da seção, checklist e nota estrutural de 60+ min
        md = ia.para_markdown(p_med)
        assert f"**{faixa[0]} a {faixa[1]} min**" in md
        assert f"{faixa[0]} a {faixa[1]} min" in p_med["7_checklist"][0]
        assert "não copie formatos de 60+ min de canais gigantes" in md


def test_tokens_preserva_digito_de_1_caractere_e_paris():
    tks = ia.tokens("Top 3 roteiros em Paris por 5 dias e 1 noite", idioma="pt")
    assert "3" in tks
    assert "5" in tks
    assert "1" in tks
    assert "paris" in tks
    # Conjunções/artigos de 1 caractere continuam filtrados
    assert "e" not in tks


def test_classificar_evidencia_exige_ic_valido_para_firme():
    assert ia.classificar_evidencia(0.01, ic=None) == "hipotese_ab"
    assert ia.classificar_evidencia(0.01, ic=[None, None]) == "hipotese_ab"
    assert ia.classificar_evidencia(0.01, ic=[-2.0, 5.0]) == "descartado"
    assert ia.classificar_evidencia(0.01, ic=[3.0, 12.0]) == "firme"
    assert ia.classificar_evidencia(0.01, ic=[3.0, 12.0], afetada_por_limite_bruto=True) == "hipotese_ab"
    assert ia.classificar_evidencia(0.08, ic=[1.0, 9.0]) == "hipotese_ab"
    assert ia.classificar_evidencia(0.15, ic=[5.0, 15.0]) == "descartado"
    assert ia.classificar_evidencia(None, ic=[5.0, 15.0]) == "descartado"


def test_tracos_de_titulo_idioma_contexto_e_regex_x():
    t_en = ia.analisar_titulo("I Tried The SECRET iPhone Trick For 30 Days", idioma="en", nicho="tech")
    assert t_en["primeira_pessoa"] is True
    assert t_en["numero"] is True
    assert "iphone" in t_en["entidade_famosa"]
    assert "For 30" not in t_en["modelo_ou_produto_detectado"]
    assert t_en["modelo_ou_produto_detectado"] == []
    assert "SECRET" in t_en["palavra_caixa_alta"]

    # Falso positivo bloqueado para palavras comuns capitalizadas + número em tech/games
    for titulo_sem_produto in (
        "Top 10 dicas de codigo limpo",
        "Dia 1 aprendendo logica de programacao",
        "For 30 days coding in assembly",
    ):
        analise = ia.analisar_titulo(titulo_sem_produto, idioma="pt", nicho="tech")
        assert analise["modelo_ou_produto_detectado"] == []
        assert analise["entidade_famosa"] == []

    # Modelos reais continuam detectados
    assert "RTX 5090" in ia.analisar_titulo("Teste da placa RTX 5090 em 4K", idioma="pt", nicho="tech")["modelo_ou_produto_detectado"]
    assert "S24" in ia.analisar_titulo("Camera do S24 depois da atualizacao", idioma="pt", nicho="tech")["modelo_ou_produto_detectado"]
    assert "M4 Pro" in ia.analisar_titulo("Compilando projetos no chip M4 Pro", idioma="pt", nicho="tech")["modelo_ou_produto_detectado"]

    t_pt = ia.analisar_titulo("O segredo do sucesso e da felicidade", idioma="pt", nicho="lifestyle")
    assert set(t_pt["abstrato"]) >= {"sucesso", "felicidade"}

    # Isenção de termos físicos/técnicos em educação, tech e documentário
    assert "energia" not in ia.analisar_titulo("Como funciona a energia solar", idioma="pt", nicho="educacao")["abstrato"]
    assert "energia" in ia.analisar_titulo("A energia da manha perfeita", idioma="pt", nicho="lifestyle")["abstrato"]

    # Regex de 'x' / colaboração: não marca iPhone X, Xbox Series X nem resoluções 1920 x 1080
    assert ia.analisar_titulo("Review do iPhone X em 2026", idioma="pt", nicho="tech")["colab_vs"] is False
    assert ia.analisar_titulo("iPhone X vale a pena hoje?", idioma="en", nicho="tech")["colab_vs"] is False
    assert ia.analisar_titulo("Xbox Series X depois de 4 anos", idioma="pt", nicho="games")["colab_vs"] is False
    assert ia.analisar_titulo("Teste em 1920 x 1080 no monitor novo", idioma="pt", nicho="tech")["colab_vs"] is False
    assert ia.analisar_titulo("1920 x 1080 gaming benchmark", idioma="en", nicho="games")["colab_vs"] is False
    assert ia.analisar_titulo("Ganhei 10 x mais produtividade", idioma="pt", nicho="tech")["colab_vs"] is False

    # Colaborações e versus reais continuam detectados
    assert ia.analisar_titulo("Messi vs Ronaldo", idioma="pt", nicho="esportes")["colab_vs"] is True
    assert ia.analisar_titulo("Flamengo x Palmeiras na final", idioma="pt", nicho="esportes")["colab_vs"] is True
    assert ia.analisar_titulo("Desafio com @MrBeast", idioma="pt", nicho="entretenimento")["colab_vs"] is True


def test_alertas_firmes_vs_hipoteses_ab_e_gate_de_q():
    p = ia.aconselhar(
        ia.Ideia(
            titulo="My journey to success and happiness",
            nicho="tech",
            idioma="en",
            porte="grande",
            duracao_min=65,
            thumb_notes="fundo verde, peso a esquerda, rosto grande, seta",
            dias_desde_ultimo=1,
            ultimo_resultado="flop",
        )
    )
    diag = p["1_diagnostico"]
    riscos = diag["riscos"]
    favor = diag["pontos_a_favor"]
    hipoteses = diag["hipoteses_ab"]

    riscos_txt = " ".join(riscos)
    hipoteses_txt = " ".join(hipoteses)

    # Sinais firmes (q < 0,05): vocabulário abstrato e tech > 30 min
    assert "Vocabulário abstrato" in riscos_txt
    assert "em tech: único nicho com inclinação negativa" in riscos_txt

    # Sinais rebaixados ou 0,05 <= q < 0,15 vão APENAS para Hipóteses para teste A/B
    assert "Intervalo menor que 2 dias" not in riscos_txt
    assert "Intervalo menor que 2 dias" in hipoteses_txt
    assert "após um vídeo fraco" not in riscos_txt
    assert "após um vídeo fraco" in hipoteses_txt
    assert "Cor dominante verde" not in " ".join(riscos + favor)
    assert "Cor dominante verde" in hipoteses_txt
    assert "Peso visual à esquerda" not in " ".join(riscos + favor)
    assert "Peso visual à esquerda" in hipoteses_txt

    # Gate estrito de q: nada com q >= 0,05 em riscos/recomendações firmes; nada com q >= 0,15 em parte alguma
    for q_val in _extrair_qs_do_texto(riscos + favor):
        assert q_val < 0.05
    for q_val in _extrair_qs_do_texto(hipoteses):
        assert q_val < 0.15

    # Padrões nulos (Rosto grande, Seta ou círculo) têm q >= 0,15 e são isolados em padroes_detectados_nulos_ignorados
    th = p["4_thumbnail"]
    nomes_validos = {d["padrao"] for d in th["padroes_detectados_nas_notas"]}
    nomes_nulos = {d["padrao"] for d in th["padroes_detectados_nulos_ignorados"]}
    assert {"Cor dominante verde", "Peso visual à esquerda"} <= nomes_validos
    assert {"Rosto grande", "Seta ou círculo"} <= nomes_nulos
    for item in th["padroes_detectados_nas_notas"]:
        assert item["q"] is not None and item["q"] < 0.15
    for item in th["recomendados_no_nicho"] + th["evitar_no_nicho"]:
        assert item["q"] is not None and item["q"] < 0.15

    # Ausência de marca em tech vira lembrete neutro, nunca risco
    assert p["3_titulo"]["lembretes_neutros"]
    assert not any("marca" in r.lower() for r in riscos)

    md = ia.para_markdown(p)
    assert "### Hipóteses para teste A/B" in md
    qs_md_inteiro = _extrair_qs_de_regras_no_markdown(md)
    assert len(qs_md_inteiro) >= 6
    assert all(q_val < 0.15 for q_val in qs_md_inteiro)


def test_pequenos_nao_recebem_risco_de_intervalo_curto_nem_curva_200k_nem_pausa_45d():
    p = ia.aconselhar(
        ia.Ideia(
            titulo="Receita de pao caseiro facil",
            nicho="culinaria",
            idioma="pt",
            porte="pequeno",
            dias_desde_ultimo=5,
        )
    )
    assert p["5_cadencia"]["efeito_curva_200k_vs_7d"] is None
    assert all(f["faixa"] != ">45d" for f in p["5_cadencia"]["intervalo_por_faixa_ref_5a9d"])
    md_5d = ia.para_markdown(p)
    assert "referência descritiva na curva 200k+ vs 7 dias" not in md_5d
    assert ">45d" not in md_5d

    p_1d = ia.aconselhar(
        ia.Ideia(
            titulo="Receita de pao caseiro facil",
            nicho="culinaria",
            idioma="pt",
            porte="pequeno",
            dias_desde_ultimo=1,
        )
    )
    assert not any("Intervalo menor que 2 dias" in r for r in p_1d["1_diagnostico"]["riscos"])
    assert any(
        ("não tem efeito estatisticamente significativo" in n) or ("inconclusivo" in n)
        for n in p_1d["5_cadencia"]["notas"]
    )


def test_capa_alinhamento_lexical_e_mitos():
    p = ia.aconselhar(
        ia.Ideia(
            titulo="Os 3 piores investimentos depois dos 40",
            nicho="financas",
            idioma="pt",
            porte="emergente",
            thumb_notes='fundo verde, sem rosto, seta, texto: "3 PIORES INVESTIMENTOS"',
        )
    )
    th = p["4_thumbnail"]
    nomes_validos = {d["padrao"] for d in th["padroes_detectados_nas_notas"]}
    nomes_nulos = {d["padrao"] for d in th["padroes_detectados_nulos_ignorados"]}
    assert "Cor dominante verde" in nomes_validos
    assert {"Sem rosto", "Seta ou círculo"} <= nomes_nulos

    alinh = th["alinhamento_titulo_capa"]
    assert alinh is not None
    assert alinh["nivel"] in ("média", "alta")
    assert alinh["sobreposicao_lexical"] > 0.12
    assert any(m["padrao"] == "Rosto grande" for m in th["mitos_a_ignorar"])


def test_capa_sem_falsos_positivos_em_seria_claro_e_texto_preto():
    p_seria = ia.aconselhar(
        ia.Ideia(
            titulo="Guia pratico de financas pessoais",
            nicho="financas",
            idioma="pt",
            porte="pequeno",
            thumb_notes="fundo limpo, texto que seria curto",
        )
    )
    todos_seria = {
        d["padrao"]
        for d in p_seria["4_thumbnail"]["padroes_detectados_nas_notas"]
        + p_seria["4_thumbnail"]["padroes_detectados_nulos_ignorados"]
    }
    assert "Expressão seria" not in todos_seria

    p_claro = ia.aconselhar(
        ia.Ideia(
            titulo="Guia pratico de financas pessoais",
            nicho="financas",
            idioma="pt",
            porte="pequeno",
            thumb_notes="deixar claro o tema principal com objeto",
        )
    )
    todos_claro = {
        d["padrao"]
        for d in p_claro["4_thumbnail"]["padroes_detectados_nas_notas"]
        + p_claro["4_thumbnail"]["padroes_detectados_nulos_ignorados"]
    }
    assert "Clara (top 20% brilho)" not in todos_claro

    p_preto = ia.aconselhar(
        ia.Ideia(
            titulo="Guia pratico de financas pessoais",
            nicho="financas",
            idioma="pt",
            porte="pequeno",
            thumb_notes="texto preto no fundo branco",
        )
    )
    todos_preto = {
        d["padrao"]
        for d in p_preto["4_thumbnail"]["padroes_detectados_nas_notas"]
        + p_preto["4_thumbnail"]["padroes_detectados_nulos_ignorados"]
    }
    assert "Cor dominante preto" not in todos_preto
    assert "Clara (top 20% brilho)" in todos_preto

    # Casos verdadeiros continuam funcionando
    p_pos = ia.aconselhar(
        ia.Ideia(
            titulo="Guia pratico de financas pessoais",
            nicho="financas",
            idioma="pt",
            porte="pequeno",
            thumb_notes="rosto serio, fundo preto",
        )
    )
    todos_pos = {
        d["padrao"]
        for d in p_pos["4_thumbnail"]["padroes_detectados_nas_notas"]
        + p_pos["4_thumbnail"]["padroes_detectados_nulos_ignorados"]
    }
    assert "Expressão seria" in todos_pos
    assert "Cor dominante preto" in todos_pos


def test_grau_de_confianca_independente_de_alertas_e_gatilhos():
    # Extrator auxiliar captura q = 1,000 no texto corrido e também números puros na tabela Markdown da Seção 3
    assert _extrair_qs_do_texto(["Regra nula (q = 1,000) e outra (q = 0,042)"]) == [1.0, 0.042]
    md_falso = "## 3. Título\n\n| Traço | Presente | Efeito | IC 95% | q | Classificação |\n|---|---|---:|---|---:|---|\n| teste | sim | +5,0% | +1,0% a +9,0% | 1,000 | descartado |\n| outro | não | −8,1% | −14,0% a −2,0% | 0,066 | hipótese A/B |\n"
    assert _extrair_qs_de_regras_no_markdown(md_falso) == [1.0, 0.066]

    # Função pura: depende apenas da cobertura amostral e do q médio das regras do recorte
    g1, det1 = ia.calcular_grau_de_confianca(18, 1400, [0.008, 0.010])
    g2, _det2 = ia.calcular_grau_de_confianca(18, 1400, [0.009])
    assert g1 == g2 == "moderado a alto"
    assert "independe de a ideia ter riscos" in det1["nota_metodologica"]

    # Teste na célula de borda (pts_cel == 2, ex.: financas x PT x grande: 8 canais, 652 vídeos),
    # onde qualquer variação em pts_q mudaria o rótulo final:
    # 1) ideia enxuta sem duração, sem notas de capa e sem nenhum gatilho léxico;
    # 2) ideia que dispara apenas hipóteses A/B (q ~ 0,09 a 0,136);
    # 3) ideia carregada de alertas firmes (q < 0,005).
    p_zero_gatilhos = ia.aconselhar(
        ia.Ideia(
            titulo="Comparativo de renda fixa prefixada para reserva",
            nicho="financas",
            idioma="pt",
            porte="grande",
        )
    )
    p_so_hipotese = ia.aconselhar(
        ia.Ideia(
            titulo="Comparativo de renda fixa prefixada 🚀",
            nicho="financas",
            idioma="pt",
            porte="grande",
            thumb_notes="fundo verde, peso a esquerda",
        )
    )
    p_com_alertas = ia.aconselhar(
        ia.Ideia(
            titulo="A verdade sobre o sucesso e a felicidade na minha vida",
            nicho="financas",
            idioma="pt",
            porte="grande",
            duracao_min=4,
            dias_desde_ultimo=1,
            ultimo_resultado="flop",
        )
    )
    assert len(p_zero_gatilhos["1_diagnostico"]["riscos"]) == 0
    assert len(p_zero_gatilhos["1_diagnostico"]["pontos_a_favor"]) == 0
    assert len(p_so_hipotese["1_diagnostico"]["riscos"]) == 0
    assert len(p_so_hipotese["1_diagnostico"]["hipoteses_ab"]) >= 1
    assert len(p_com_alertas["1_diagnostico"]["riscos"]) >= 2

    g_zero = p_zero_gatilhos["1_diagnostico"]["grau_de_confianca"]
    g_hip = p_so_hipotese["1_diagnostico"]["grau_de_confianca"]
    g_alertas = p_com_alertas["1_diagnostico"]["grau_de_confianca"]
    assert g_zero == g_hip == g_alertas
    mc_zero = p_zero_gatilhos["1_diagnostico"]["metricas_de_confianca"]
    assert "n_regras_da_celula_com_q" in mc_zero and "q_medio_regras_da_celula" in mc_zero
    assert "n_regras_acionadas_com_q" not in mc_zero and "q_medio_regras_acionadas" not in mc_zero
    assert (
        mc_zero["q_medio_regras_da_celula"]
        == p_so_hipotese["1_diagnostico"]["metricas_de_confianca"]["q_medio_regras_da_celula"]
        == p_com_alertas["1_diagnostico"]["metricas_de_confianca"]["q_medio_regras_da_celula"]
    )


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
    with pytest.raises(ValueError):
        ia.Ideia(titulo="   ", nicho="tech").normalizar()
    with pytest.raises(ValueError):
        ia.Ideia(titulo="x", nicho="tech", ultimo_resultado="viral").normalizar()


def test_consistencia_tematica_com_titulos_recentes_e_borda_zero():
    recentes = ["Receita de bolo de cenoura", "Bolo de chocolate fofinho", "Receita de bolo de laranja"]
    p = ia.aconselhar(
        ia.Ideia(
            titulo="Review do novo iPhone 18",
            nicho="culinaria",
            idioma="pt",
            porte="pequeno",
            titulos_recentes=recentes,
        )
    )
    # Desvio temático é hipótese rebaixada (Item 2c), não risco firme
    assert not any("sobreposição de palavras em relação aos vídeos recentes" in r for r in p["1_diagnostico"]["riscos"])
    assert any("baixa sobreposição de palavras em relação aos vídeos recentes" in h for h in p["1_diagnostico"]["hipoteses_ab"])

    # Caso ref == 0.0 (títulos recentes sem palavras em comum entre si): não dispara falso alarme
    recentes_variados = ["Lasagna bolonhesa rapida", "Pudim cremoso caseiro", "Churrasco gaucho tradicional"]
    p_zero = ia.aconselhar(
        ia.Ideia(
            titulo="Salada mediterranea refrescante",
            nicho="culinaria",
            idioma="pt",
            porte="pequeno",
            titulos_recentes=recentes_variados,
        )
    )
    ct = p_zero["5_cadencia"]["consistencia_tematica"]
    assert ct["sobreposicao_entre_recentes"] == 0.0
    assert "não configura anomalia lexical" in ct["avaliacao_recentes"]


def test_sem_travessao_no_texto_gerado():
    casos = [
        ia.Ideia(
            titulo="Como montar um PC gamer barato",
            nicho="games",
            idioma="pt",
            porte="medio",
            duracao_min=25,
            thumb_notes='rosto surpreso, fundo vermelho, texto: "PC GAMER BARATO"',
            dias_desde_ultimo=4,
        ),
        ia.Ideia(
            titulo="My truth about success in 2026",
            nicho="tech",
            idioma="en",
            porte="pequeno",
            duracao_min=5,
            thumb_notes="dark background, green, arrow",
            dias_desde_ultimo=1,
            ultimo_resultado="flop",
            titulos_recentes=["Best laptops 2026", "Cheap gaming laptops 2026"],
        ),
    ]
    rx_parenteses_aninhados = re.compile(r"\([^()\n]*\([^()\n]*\)")
    for ideia in casos:
        md = ia.para_markdown(ia.aconselhar(ideia))
        corpo = _sem_linhas_de_titulos_verbatim(md)
        assert "—" not in corpo
        assert "–" not in corpo
        assert " - " not in corpo
        assert "informando (" not in corpo
        assert not rx_parenteses_aninhados.search(corpo)


def test_cli_idea_advisor_json_markdown_e_saida_2(capsys):
    rc_json = ia.main(
        [
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
        ]
    )
    assert rc_json == 0
    capturado_json = capsys.readouterr()
    dados = json.loads(capturado_json.out)
    assert dados["ideia"]["porte"] == "pequeno"
    assert dados["ideia"]["nicho"] == "educacao"

    rc_md = ia.main(["--title", "Teste de bancada", "--niche", "games", "--format", "markdown"])
    assert rc_md == 0
    capturado_md = capsys.readouterr()
    assert capturado_md.out.startswith("# Parecer da ideia: Teste de bancada")

    rc_invalido = ia.main(["--title", "x", "--niche", "astrologia"])
    assert rc_invalido == 2
    capturado_err = capsys.readouterr()
    assert "nicho desconhecido" in capturado_err.err

    # Subprocesso direto no arquivo para validar entrypoint __main__
    script = Path(ia.__file__)
    proc_bad = subprocess.run(
        [sys.executable, str(script), "--title", "x", "--niche", "astrologia"],
        capture_output=True,
        text=True,
    )
    assert proc_bad.returncode == 2
    assert "nicho" in proc_bad.stderr


def test_cli_do_pacote_advise_e_idea_sem_rede(monkeypatch):
    cli_mod = pytest.importorskip("youtube_seo.cli")

    def boom(*_a, **_k):
        raise AssertionError("o advisor não pode abrir rede")

    if hasattr(cli_mod, "UrllibTransport"):
        monkeypatch.setattr(cli_mod, "UrllibTransport", boom)

    saida = io.StringIO()
    codigo = cli_mod.main(
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
    codigo_json = cli_mod.main(
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
    codigo_ruim = cli_mod.main(
        ["advise", "--title", "x", "--niche", "astrologia"],
        stdout=io.StringIO(),
        stderr=erro,
        env={},
    )
    assert codigo_ruim == 2
    assert "nicho" in erro.getvalue()
