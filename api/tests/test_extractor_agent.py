"""
Testes unitários para extract_knowledge().
call_llm é sempre mockado — sem chamadas reais de rede.
"""
import json
import pytest
from unittest.mock import patch

from app.agents.extractor_agent import extract_knowledge

PROVIDER = "gemini"
MODEL    = "gemini-2.5-flash"
API_KEY  = "test-key"

PAPERS = [
    {
        "title": "Machine Learning na Detecção de Fraudes",
        "authors": "Silva, J.; Costa, M.",
        "year": 2022,
        "abstract": "Este artigo analisa o uso de redes neurais para detecção de transações fraudulentas.",
    },
    {
        "title": "Deep Learning para Séries Temporais",
        "authors": "Oliveira, A.",
        "year": 2023,
        "abstract": "Proposta de modelo LSTM para previsão de demanda em tempo real.",
    },
]

VALID_KNOWLEDGE = {
    "temas_principais": ["Machine Learning", "Detecção de Fraudes"],
    "metodologias_identificadas": ["Redes Neurais", "LSTM"],
    "principais_achados": ["Alta acurácia", "Tempo real"],
    "lacunas_pesquisa": ["Datasets públicos limitados"],
    "consensos": "Os autores concordam sobre o potencial do ML.",
    "divergencias": "Divergem sobre a arquitetura ideal.",
    "sintese_geral": "O estado da arte aponta para DL como principal abordagem.",
}


class TestExtractKnowledge:
    def test_retorna_estrutura_correta_com_json_valido(self):
        with patch("app.agents.extractor_agent.call_llm", return_value=json.dumps(VALID_KNOWLEDGE)):
            result = extract_knowledge(PAPERS, PROVIDER, MODEL, API_KEY)

        assert result["temas_principais"] == ["Machine Learning", "Detecção de Fraudes"]
        assert result["metodologias_identificadas"] == ["Redes Neurais", "LSTM"]
        assert "sintese_geral" in result

    def test_chama_call_llm_com_provider_model_key_corretos(self):
        with patch("app.agents.extractor_agent.call_llm", return_value=json.dumps(VALID_KNOWLEDGE)) as mock_llm:
            extract_knowledge(PAPERS, PROVIDER, MODEL, API_KEY)

        mock_llm.assert_called_once()
        args = mock_llm.call_args[0]
        assert args[0] == PROVIDER
        assert args[1] == MODEL
        assert args[2] == API_KEY

    def test_prompt_contem_titulos_dos_artigos(self):
        with patch("app.agents.extractor_agent.call_llm", return_value=json.dumps(VALID_KNOWLEDGE)) as mock_llm:
            extract_knowledge(PAPERS, PROVIDER, MODEL, API_KEY)

        prompt = mock_llm.call_args[0][3]
        assert "Machine Learning na Detecção de Fraudes" in prompt
        assert "Deep Learning para Séries Temporais" in prompt

    def test_aceita_json_com_marcadores_markdown(self):
        llm_response = f"```json\n{json.dumps(VALID_KNOWLEDGE)}\n```"
        with patch("app.agents.extractor_agent.call_llm", return_value=llm_response):
            result = extract_knowledge(PAPERS, PROVIDER, MODEL, API_KEY)

        assert isinstance(result["temas_principais"], list)

    def test_fallback_quando_json_invalido(self):
        with patch("app.agents.extractor_agent.call_llm", return_value="isso não é json"):
            result = extract_knowledge(PAPERS, PROVIDER, MODEL, API_KEY)

        assert isinstance(result, dict)
        assert "temas_principais" in result
        assert result["temas_principais"] == []

    def test_fallback_quando_llm_lanca_excecao(self):
        with patch("app.agents.extractor_agent.call_llm", side_effect=RuntimeError("timeout")):
            result = extract_knowledge(PAPERS, PROVIDER, MODEL, API_KEY)

        assert isinstance(result, dict)
        assert result["sintese_geral"] == "Falha na extração."

    def test_levanta_erro_sem_artigos(self):
        with pytest.raises(ValueError, match="Nenhum artigo"):
            extract_knowledge([], PROVIDER, MODEL, API_KEY)
