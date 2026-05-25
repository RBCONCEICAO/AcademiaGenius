"""
Testes unitários para translate_papers().
"""
import json
import pytest
from unittest.mock import patch

from app.agents.translator_agent import translate_papers

PROVIDER = "groq"
MODEL    = "llama3-70b-8192"
API_KEY  = "test-key"

PAPERS = [
    {"title": "Machine Learning in Fraud Detection", "abstract": "This paper analyzes neural networks.", "source": "arxiv"},
    {"title": "Deep Learning for Time Series", "abstract": "LSTM model for demand forecasting.", "source": "pubmed"},
]


def _translated_response(papers):
    return json.dumps([
        {"id": i, "titulo_pt": f"Título traduzido {i}", "resumo_pt": f"Resumo traduzido {i}"}
        for i in range(len(papers))
    ])


class TestTranslatePapers:
    def test_traduz_titulo_e_abstract(self):
        with patch("app.agents.translator_agent.call_llm", return_value=_translated_response(PAPERS)):
            result = translate_papers(PAPERS.copy(), PROVIDER, MODEL, API_KEY)

        assert result[0]["title"] == "Título traduzido 0"
        assert result[0]["abstract"] == "Resumo traduzido 0"
        assert result[1]["title"] == "Título traduzido 1"

    def test_retorna_originais_quando_llm_falha(self):
        originals = [p.copy() for p in PAPERS]
        with patch("app.agents.translator_agent.call_llm", side_effect=RuntimeError("timeout")):
            result = translate_papers([p.copy() for p in PAPERS], PROVIDER, MODEL, API_KEY)

        assert result[0]["title"] == originals[0]["title"]
        assert result[1]["title"] == originals[1]["title"]

    def test_retorna_originais_quando_json_invalido(self):
        originals = [p.copy() for p in PAPERS]
        with patch("app.agents.translator_agent.call_llm", return_value="não é json"):
            result = translate_papers([p.copy() for p in PAPERS], PROVIDER, MODEL, API_KEY)

        assert result[0]["title"] == originals[0]["title"]

    def test_lista_vazia_retorna_lista_vazia(self):
        result = translate_papers([], PROVIDER, MODEL, API_KEY)
        assert result == []

    def test_aceita_resposta_com_markdown_code_block(self):
        raw = f"```json\n{_translated_response(PAPERS)}\n```"
        with patch("app.agents.translator_agent.call_llm", return_value=raw):
            result = translate_papers(PAPERS.copy(), PROVIDER, MODEL, API_KEY)

        assert result[0]["title"] == "Título traduzido 0"

    def test_id_fora_do_range_ignorado(self):
        bad_response = json.dumps([
            {"id": 0, "titulo_pt": "Título OK", "resumo_pt": "Resumo OK"},
            {"id": 99, "titulo_pt": "Fora do range", "resumo_pt": "Não existe"},
        ])
        papers = [PAPERS[0].copy()]
        with patch("app.agents.translator_agent.call_llm", return_value=bad_response):
            result = translate_papers(papers, PROVIDER, MODEL, API_KEY)

        assert result[0]["title"] == "Título OK"
        assert len(result) == 1

    def test_sem_traducao_quando_titulo_pt_ausente(self):
        response = json.dumps([{"id": 0, "resumo_pt": "Resumo traduzido"}])
        papers = [PAPERS[0].copy()]
        with patch("app.agents.translator_agent.call_llm", return_value=response):
            result = translate_papers(papers, PROVIDER, MODEL, API_KEY)

        # título não foi sobrescrito porque titulo_pt estava ausente
        assert result[0]["title"] == PAPERS[0]["title"]
        assert result[0]["abstract"] == "Resumo traduzido"
