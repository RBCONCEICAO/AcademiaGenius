"""
Testes unitários para run_research_pipeline() e detect_area().

Notas de patch:
- multi_source_search, extract_knowledge, write_document são importados no topo
  do orchestrator → patch no namespace do orchestrator.
- call_llm, filter_papers_by_domain, translate_papers são importados lazily
  (inside the function body) → patch no módulo fonte.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.agents.orchestrator import run_research_pipeline

PROVIDER = "gemini"
MODEL    = "gemini-2.5-flash"
API_KEY  = "test-key"

SAMPLE_PAPERS = [
    {
        "title": "Redes Neurais em Finanças",
        "authors": "Silva, J.",
        "year": 2022,
        "abstract": "Estudo sobre redes neurais.",
        "source": "arxiv",
        "abnt_reference": "SILVA, J. Redes Neurais. 2022.",
        "citation_count": 10,
    }
]

SAMPLE_KNOWLEDGE = {
    "temas_principais": ["Redes Neurais"],
    "metodologias_identificadas": ["CNN"],
    "principais_achados": ["Alta acurácia"],
    "lacunas_pesquisa": [],
    "consensos": "Consenso sobre DL.",
    "divergencias": "",
    "sintese_geral": "DL é a abordagem dominante.",
}

SAMPLE_SEARCH_RESULT = {
    "papers": SAMPLE_PAPERS,
    "query_info": {"sources_searched": ["arxiv", "pubmed"]},
}

# Imports são todos no topo do módulo → patch no namespace do orchestrator
_CALL_LLM        = "app.agents.orchestrator.call_llm"
_FILTER_PAPERS   = "app.agents.orchestrator.filter_papers_by_domain"
_TRANSLATE       = "app.agents.orchestrator.translate_papers"
_SEARCH          = "app.agents.orchestrator.multi_source_search"
_EXTRACT         = "app.agents.orchestrator.extract_knowledge"
_WRITE           = "app.agents.orchestrator.write_document"


class TestRunResearchPipelineHappyPath:
    def test_retorna_documento_gerado(self):
        with patch(_SEARCH,        return_value=SAMPLE_SEARCH_RESULT), \
             patch(_EXTRACT,       return_value=SAMPLE_KNOWLEDGE), \
             patch(_WRITE,         return_value="meu documento"), \
             patch(_CALL_LLM,      return_value="neural networks finance"), \
             patch(_FILTER_PAPERS, return_value=SAMPLE_PAPERS), \
             patch(_TRANSLATE,     side_effect=lambda papers, **kw: papers):

            result = run_research_pipeline(
                theme="Redes Neurais em Finanças",
                doc_type="artigo",
                provider=PROVIDER,
                model=MODEL,
                api_key=API_KEY,
            )

        assert result["document"] == "meu documento"
        assert result["papers"] == SAMPLE_PAPERS
        assert result["knowledge"] == SAMPLE_KNOWLEDGE

    def test_steps_log_tem_3_etapas_concluidas(self):
        with patch(_SEARCH,        return_value=SAMPLE_SEARCH_RESULT), \
             patch(_EXTRACT,       return_value=SAMPLE_KNOWLEDGE), \
             patch(_WRITE,         return_value="ok"), \
             patch(_CALL_LLM,      return_value="en query"), \
             patch(_FILTER_PAPERS, return_value=SAMPLE_PAPERS), \
             patch(_TRANSLATE,     side_effect=lambda papers, **kw: papers):

            result = run_research_pipeline("Redes Neurais", "artigo", PROVIDER, MODEL, API_KEY)

        done_steps = [e for e in result["steps_log"] if e["status"] == "done"]
        assert len(done_steps) == 3
        assert {e["step"] for e in done_steps} == {1, 2, 3}

    def test_stats_contem_area_detectada(self):
        with patch(_SEARCH,        return_value=SAMPLE_SEARCH_RESULT), \
             patch(_EXTRACT,       return_value=SAMPLE_KNOWLEDGE), \
             patch(_WRITE,         return_value="ok"), \
             patch(_CALL_LLM,      return_value="en"), \
             patch(_FILTER_PAPERS, return_value=SAMPLE_PAPERS), \
             patch(_TRANSLATE,     side_effect=lambda papers, **kw: papers):

            result = run_research_pipeline("machine learning fraudes", "artigo", PROVIDER, MODEL, API_KEY)

        assert result["stats"]["area_detected"] == "computacao"

    def test_progress_callback_e_chamado(self):
        events = []

        with patch(_SEARCH,        return_value=SAMPLE_SEARCH_RESULT), \
             patch(_EXTRACT,       return_value=SAMPLE_KNOWLEDGE), \
             patch(_WRITE,         return_value="ok"), \
             patch(_CALL_LLM,      return_value="en"), \
             patch(_FILTER_PAPERS, return_value=SAMPLE_PAPERS), \
             patch(_TRANSLATE,     side_effect=lambda papers, **kw: papers):

            run_research_pipeline(
                "ML", "artigo", PROVIDER, MODEL, API_KEY,
                progress_callback=events.append,
            )

        assert len(events) > 0
        assert any(e["step"] == 1 and e["status"] == "done" for e in events)
        assert any(e["step"] == 3 and e["status"] == "done" for e in events)

    def test_query_en_fornecida_nao_chama_call_llm_para_traducao(self):
        with patch(_SEARCH,        return_value=SAMPLE_SEARCH_RESULT), \
             patch(_EXTRACT,       return_value=SAMPLE_KNOWLEDGE), \
             patch(_WRITE,         return_value="ok"), \
             patch(_CALL_LLM,      return_value="not used") as mock_llm, \
             patch(_FILTER_PAPERS, return_value=SAMPLE_PAPERS), \
             patch(_TRANSLATE,     side_effect=lambda papers, **kw: papers):

            run_research_pipeline(
                "Redes Neurais", "artigo", PROVIDER, MODEL, API_KEY,
                query_en="neural networks finance",
            )

        # call_llm para tradução NÃO deve ter sido invocado
        mock_llm.assert_not_called()


class TestRunResearchPipelineRetry:
    def test_retry_com_query_en_quando_sem_artigos(self):
        empty_result = {"papers": [], "query_info": {"sources_searched": []}}
        retry_result = {"papers": SAMPLE_PAPERS, "query_info": {"sources_searched": ["arxiv"]}}

        mock_search = MagicMock(side_effect=[empty_result, retry_result])

        with patch(_SEARCH,        mock_search), \
             patch(_EXTRACT,       return_value=SAMPLE_KNOWLEDGE), \
             patch(_WRITE,         return_value="ok"), \
             patch(_CALL_LLM,      return_value="neural networks"), \
             patch(_FILTER_PAPERS, return_value=SAMPLE_PAPERS), \
             patch(_TRANSLATE,     side_effect=lambda papers, **kw: papers):

            result = run_research_pipeline("Redes Neurais", "artigo", PROVIDER, MODEL, API_KEY)

        assert mock_search.call_count == 2
        assert result["papers"] == SAMPLE_PAPERS

    def test_sem_retry_quando_query_en_igual_ao_tema(self):
        empty_result = {"papers": [], "query_info": {"sources_searched": []}}
        mock_search = MagicMock(return_value=empty_result)

        with patch(_SEARCH,        mock_search), \
             patch(_CALL_LLM,      return_value="ml"), \
             patch(_FILTER_PAPERS, return_value=[]), \
             patch(_TRANSLATE,     side_effect=lambda papers, **kw: papers):

            with pytest.raises(Exception, match="Nenhum artigo encontrado"):
                run_research_pipeline("ml", "artigo", PROVIDER, MODEL, API_KEY, query_en="ml")

        # Sem retry porque query_en == theme
        assert mock_search.call_count == 1


class TestRunResearchPipelineErrors:
    def test_levanta_excecao_quando_nenhum_artigo_encontrado(self):
        empty_result = {"papers": [], "query_info": {"sources_searched": []}}

        with patch(_SEARCH,        return_value=empty_result), \
             patch(_CALL_LLM,      return_value="en"), \
             patch(_FILTER_PAPERS, return_value=[]), \
             patch(_TRANSLATE,     side_effect=lambda papers, **kw: papers):

            with pytest.raises(Exception, match="Nenhum artigo encontrado"):
                run_research_pipeline("Tema Improvável XYZ", "artigo", PROVIDER, MODEL, API_KEY)

    def test_levanta_excecao_quando_busca_falha(self):
        with patch(_SEARCH,   side_effect=RuntimeError("rede indisponível")), \
             patch(_CALL_LLM, return_value="en"):

            with pytest.raises(Exception, match="Falha na busca"):
                run_research_pipeline("ML", "artigo", PROVIDER, MODEL, API_KEY)

    def test_levanta_excecao_quando_extracao_falha(self):
        with patch(_SEARCH,        return_value=SAMPLE_SEARCH_RESULT), \
             patch(_EXTRACT,       side_effect=RuntimeError("llm timeout")), \
             patch(_CALL_LLM,      return_value="en"), \
             patch(_FILTER_PAPERS, return_value=SAMPLE_PAPERS), \
             patch(_TRANSLATE,     side_effect=lambda papers, **kw: papers):

            with pytest.raises(Exception, match="Falha na extração"):
                run_research_pipeline("ML", "artigo", PROVIDER, MODEL, API_KEY)

    def test_levanta_excecao_quando_redacao_falha(self):
        with patch(_SEARCH,        return_value=SAMPLE_SEARCH_RESULT), \
             patch(_EXTRACT,       return_value=SAMPLE_KNOWLEDGE), \
             patch(_WRITE,         side_effect=RuntimeError("context too large")), \
             patch(_CALL_LLM,      return_value="en"), \
             patch(_FILTER_PAPERS, return_value=SAMPLE_PAPERS), \
             patch(_TRANSLATE,     side_effect=lambda papers, **kw: papers):

            with pytest.raises(Exception, match="Falha na redação"):
                run_research_pipeline("ML", "artigo", PROVIDER, MODEL, API_KEY)

    def test_progress_callback_exception_nao_propaga(self):
        def bad_callback(_):
            raise RuntimeError("callback explodiu")

        with patch(_SEARCH,        return_value=SAMPLE_SEARCH_RESULT), \
             patch(_EXTRACT,       return_value=SAMPLE_KNOWLEDGE), \
             patch(_WRITE,         return_value="ok"), \
             patch(_CALL_LLM,      return_value="en"), \
             patch(_FILTER_PAPERS, return_value=SAMPLE_PAPERS), \
             patch(_TRANSLATE,     side_effect=lambda papers, **kw: papers):

            result = run_research_pipeline(
                "ML", "artigo", PROVIDER, MODEL, API_KEY,
                progress_callback=bad_callback,
            )

        assert "document" in result
