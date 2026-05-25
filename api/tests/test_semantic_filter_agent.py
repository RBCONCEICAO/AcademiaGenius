"""
Testes unitários para filter_papers_by_domain().
"""
import json
import pytest
from unittest.mock import patch

from app.agents.semantic_filter_agent import filter_papers_by_domain

PROVIDER = "groq"
MODEL    = "llama3-70b-8192"
API_KEY  = "test-key"

PAPERS = [
    {"title": "Contenção de Encostas com Estacas", "abstract": "Estudo geotécnico sobre taludes.", "source": "arxiv"},
    {"title": "Contenção Física no Leito Hospitalar", "abstract": "Protocolo psiquiátrico de contenção.", "source": "pubmed"},
    {"title": "Análise de Estabilidade em Muros de Arrimo", "abstract": "Modelos de elementos finitos.", "source": "crossref"},
]


def _make_llm_response(decisions):
    results = [{"id": i, "decision": d, "reason": "test"} for i, d in enumerate(decisions)]
    return json.dumps({"results": results})


class TestFilterPapersByDomain:
    def test_filtra_artigo_fora_do_dominio(self):
        # Keep papers 0 e 2 (geotecnia), descarta 1 (medicina)
        llm_resp = _make_llm_response(["keep", "discard", "keep"])
        with patch("app.agents.semantic_filter_agent.call_llm", return_value=llm_resp):
            result = filter_papers_by_domain(PAPERS, "Contenção de Encostas Geotécnicas", PROVIDER, MODEL, API_KEY)

        assert len(result) == 2
        titles = [p["title"] for p in result]
        assert "Contenção Física no Leito Hospitalar" not in titles
        assert "Contenção de Encostas com Estacas" in titles

    def test_mantém_todos_quando_todos_aprovados(self):
        llm_resp = _make_llm_response(["keep", "keep", "keep"])
        with patch("app.agents.semantic_filter_agent.call_llm", return_value=llm_resp):
            result = filter_papers_by_domain(PAPERS, "Geotecnia", PROVIDER, MODEL, API_KEY)

        assert len(result) == 3

    def test_fallback_retorna_originais_quando_llm_falha(self):
        with patch("app.agents.semantic_filter_agent.call_llm", side_effect=RuntimeError("timeout")):
            result = filter_papers_by_domain(PAPERS, "Geotecnia", PROVIDER, MODEL, API_KEY)

        assert result == PAPERS

    def test_fallback_retorna_originais_quando_json_invalido(self):
        with patch("app.agents.semantic_filter_agent.call_llm", return_value="não é json"):
            result = filter_papers_by_domain(PAPERS, "Geotecnia", PROVIDER, MODEL, API_KEY)

        assert result == PAPERS

    def test_lista_vazia_retorna_lista_vazia(self):
        result = filter_papers_by_domain([], "Geotecnia", PROVIDER, MODEL, API_KEY)
        assert result == []

    def test_id_ausente_na_resposta_mantem_paper(self):
        # LLM retorna decisão só para id=0 — os demais devem usar default "keep"
        llm_resp = json.dumps({"results": [{"id": 0, "decision": "discard", "reason": "fora do tema"}]})
        with patch("app.agents.semantic_filter_agent.call_llm", return_value=llm_resp):
            result = filter_papers_by_domain(PAPERS, "Geotecnia", PROVIDER, MODEL, API_KEY)

        # ids 1 e 2 não tiveram decisão → mantidos por default
        assert len(result) == 2

    def test_prompt_contem_tema(self):
        llm_resp = _make_llm_response(["keep", "keep", "keep"])
        with patch("app.agents.semantic_filter_agent.call_llm", return_value=llm_resp) as mock_llm:
            filter_papers_by_domain(PAPERS, "Contenção de Encostas", PROVIDER, MODEL, API_KEY)

        prompt = mock_llm.call_args[0][3]
        assert "Contenção de Encostas" in prompt

    def test_clarifications_aparecem_no_prompt(self):
        llm_resp = _make_llm_response(["keep", "keep", "keep"])
        clarifications = {"Área?": "Engenharia Civil", "Foco?": "Geotecnia"}
        with patch("app.agents.semantic_filter_agent.call_llm", return_value=llm_resp) as mock_llm:
            filter_papers_by_domain(PAPERS, "Contenção", PROVIDER, MODEL, API_KEY, clarifications=clarifications)

        prompt = mock_llm.call_args[0][3]
        assert "Engenharia Civil" in prompt
        assert "Geotecnia" in prompt
