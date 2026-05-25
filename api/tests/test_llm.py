"""
Testes unitários para call_llm(), generate_free_fallback_content() e helpers de llm.py.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from app.services.llm import call_llm, generate_free_fallback_content, _fb_section


# ── _fb_section ───────────────────────────────────────────────────────────────

class TestFbSection:
    def test_extrai_secao_existente(self):
        prompt = "Algum texto\n**Temas principais:** machine learning, NLP\n**Outras seções**"
        assert "machine learning" in _fb_section(prompt, "Temas principais")

    def test_retorna_vazio_para_secao_ausente(self):
        assert _fb_section("sem seção", "Metodologias") == ""

    def test_case_insensitive(self):
        prompt = "**TEMAS PRINCIPAIS:** IA, Robótica\n**Fim**"
        assert "IA" in _fb_section(prompt, "Temas principais")


# ── call_llm dispatcher ───────────────────────────────────────────────────────

class TestCallLlm:
    # CALLERS é construído no módulo com referências diretas → patch via patch.dict
    def test_provider_desconhecido_levanta_value_error(self):
        with pytest.raises(ValueError, match="não suportado"):
            call_llm("unknown_provider", "model", "key", "prompt")

    def test_free_fallback_nao_chama_caller_externo(self):
        with patch("app.services.llm.generate_free_fallback_content", return_value="ok") as mock:
            result = call_llm("gemini", "model", "FREE_FALLBACK", "some prompt", "extracao")
        mock.assert_called_once()
        assert result == "ok"

    def test_roteia_para_gemini(self):
        mock_fn = MagicMock(return_value="gemini response")
        with patch.dict("app.services.llm.CALLERS", {"gemini": mock_fn}):
            result = call_llm("gemini", "gemini-2.5-flash", "real-key", "prompt")
        mock_fn.assert_called_once_with("real-key", "gemini-2.5-flash", "prompt", "")
        assert result == "gemini response"

    def test_roteia_para_openai(self):
        mock_fn = MagicMock(return_value="openai response")
        with patch.dict("app.services.llm.CALLERS", {"openai": mock_fn}):
            call_llm("openai", "gpt-4o", "key", "prompt", "redacao")
        mock_fn.assert_called_once_with("key", "gpt-4o", "prompt", "redacao")

    def test_roteia_para_groq(self):
        mock_fn = MagicMock(return_value="groq response")
        with patch.dict("app.services.llm.CALLERS", {"groq": mock_fn}):
            call_llm("groq", "llama3-70b", "key", "prompt")
        mock_fn.assert_called_once()

    def test_roteia_para_mistral(self):
        mock_fn = MagicMock(return_value="mistral response")
        with patch.dict("app.services.llm.CALLERS", {"mistral": mock_fn}):
            call_llm("mistral", "mistral-large-latest", "key", "prompt")
        mock_fn.assert_called_once()

    def test_roteia_para_anthropic(self):
        mock_fn = MagicMock(return_value="claude response")
        with patch.dict("app.services.llm.CALLERS", {"anthropic": mock_fn}):
            call_llm("anthropic", "claude-sonnet-4-6", "key", "prompt")
        mock_fn.assert_called_once()


# ── generate_free_fallback_content ────────────────────────────────────────────

class TestFreeFallbackTranslation:
    def test_branch_traducao_de_tema(self):
        prompt = "Extraia as principais palavras-chave do tema abaixo e traduza-as para o inglês.\nTema: Aprendizado de Máquina em Saúde"
        result = generate_free_fallback_content("gemini", "model", prompt)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_branch_traducao_retorna_palavras_significativas(self):
        prompt = "crie a melhor string de busca (search query).\nTema: inteligência artificial medicina"
        result = generate_free_fallback_content("gemini", "model", prompt)
        # Palavras com > 3 chars do tema devem estar no resultado
        assert any(w in result for w in ["inteligência", "artificial", "medicina"])


class TestFreeFallbackClarification:
    def test_branch_clarificacao_retorna_3_perguntas(self):
        prompt = 'Você é um orientador científico de IA. O usuário deseja pesquisar sobre o tema: "Redes Neurais".'
        result = generate_free_fallback_content("gemini", "model", prompt)
        data = json.loads(result)
        assert "questions" in data
        assert len(data["questions"]) == 3

    def test_branch_clarificacao_perguntas_tem_id_e_question(self):
        prompt = "perguntas de esclarecimento para o tema: Machine Learning"
        result = generate_free_fallback_content("gemini", "model", prompt)
        data = json.loads(result)
        for q in data["questions"]:
            assert "id" in q
            assert "question" in q


class TestFreeFallbackFilter:
    def test_branch_filtro_mantem_todos_os_papers(self):
        payload = [{"id": 0, "title": "Artigo A", "abstract": "..."},
                   {"id": 1, "title": "Artigo B", "abstract": "..."}]
        prompt = f"Você é um validador de relevância científica.\n{json.dumps(payload)}"
        result = generate_free_fallback_content("gemini", "model", prompt)
        data = json.loads(result)
        assert len(data["results"]) == 2
        assert all(r["decision"] == "keep" for r in data["results"])

    def test_branch_filtro_json_malformado_retorna_lista_vazia(self):
        prompt = "validador de relevância científica — nenhum payload aqui"
        result = generate_free_fallback_content("gemini", "model", prompt)
        data = json.loads(result)
        assert data["results"] == []


class TestFreeFallbackPaperTranslation:
    def test_branch_traducao_papers_retorna_titulo_e_resumo(self):
        payload = [{"id": 0, "title": "ML in Finance", "abstract": "This paper analyzes ML."}]
        prompt = f"Você é um Tradutor Científico Especializado.\n{json.dumps(payload)}"
        result = generate_free_fallback_content("gemini", "model", prompt, task="traducao")
        data = json.loads(result)
        assert data[0]["titulo_pt"] == "ML in Finance"
        assert "This paper" in data[0]["resumo_pt"]

    def test_branch_traducao_por_task_string(self):
        payload = [{"id": 0, "title": "Deep Learning", "abstract": "Abstract here."}]
        prompt = f"Dados:\n{json.dumps(payload)}"
        result = generate_free_fallback_content("gemini", "model", prompt, task="traducao")
        data = json.loads(result)
        assert len(data) == 1


class TestFreeFallbackExtraction:
    def test_branch_extracao_retorna_json_com_temas(self):
        prompt = """revisão sistemática de literatura.
--- Artigo 1 ---
Título: Machine Learning em Saúde
Autores: Silva, J.
Ano: 2022
Abstract: Este artigo analisa o uso de Redes Neurais para diagnóstico clínico.
"""
        result = generate_free_fallback_content("gemini", "model", prompt, task="extracao")
        data = json.loads(result)
        assert "temas_principais" in data
        assert "metodologias_identificadas" in data
        assert "sintese_geral" in data
        assert isinstance(data["temas_principais"], list)

    def test_branch_extracao_achados_menciona_numero_de_artigos(self):
        prompt = """revisão sistemática\n--- Artigo 1 ---\nTítulo: Artigo X\nAbstract: Texto."""
        result = generate_free_fallback_content("gemini", "model", prompt, task="extracao")
        data = json.loads(result)
        assert any("1" in a for a in data["principais_achados"])


class TestFreeFallbackWriting:
    def test_branch_redacao_gera_documento_com_secoes(self):
        prompt = """tema: **Inteligência Artificial na Medicina**
## Fontes Reais Disponíveis:
- [1] SILVA, J. IA Médica. 2022. (Citações: 42)
- [2] COSTA, M. Deep Learning. 2021. (Citações: 18)
## Base de Conhecimento Extraída:
**Temas principais:** IA, Diagnóstico
**Metodologias:** Redes Neurais, CNN
**Principais achados:**
- Alta acurácia no diagnóstico
**Lacunas de pesquisa:**
- Poucos datasets públicos
**Síntese e Consensos:** IA é promissora na medicina.
"""
        result = generate_free_fallback_content("gemini", "model", prompt, task="redacao")
        assert "INTELIGÊNCIA ARTIFICIAL NA MEDICINA" in result.upper()
        assert "INTRODUÇÃO" in result.upper()
        assert "REFERÊNCIAS" in result.upper()
        assert "SILVA, J." in result

    def test_branch_redacao_cita_referencias_reais(self):
        prompt = """tema: **Educação Digital**
## Fontes Reais Disponíveis:
- [1] OLIVEIRA, A. EaD. 2020. (Citações: 5)
## Base de Conhecimento Extraída:
**Temas principais:** EaD
**Metodologias:** Qualitativa
**Principais achados:**
- Crescimento do EaD
**Lacunas de pesquisa:**
- Poucos estudos longitudinais
**Síntese e Consensos:** EaD cresce no Brasil.
"""
        result = generate_free_fallback_content("gemini", "model", prompt)
        assert "OLIVEIRA, A." in result
