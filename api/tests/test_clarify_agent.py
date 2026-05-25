"""
Testes unitários para generate_clarifying_questions().
"""
import json
import pytest
from unittest.mock import patch

from app.agents.clarify_agent import generate_clarifying_questions

PROVIDER = "gemini"
MODEL    = "gemini-2.5-flash"
API_KEY  = "test-key"

VALID_RESPONSE = json.dumps({
    "questions": [
        {"id": 1, "question": "Área do estudo?", "type": "choice", "options": ["Engenharia", "Medicina"]},
        {"id": 2, "question": "Metodologia preferida?", "type": "text"},
        {"id": 3, "question": "Contexto geográfico?", "type": "choice", "options": ["Brasil", "Internacional"]},
    ]
})


class TestGenerateClarifyingQuestions:
    def test_retorna_lista_de_perguntas_com_json_valido(self):
        with patch("app.agents.clarify_agent.call_llm", return_value=VALID_RESPONSE):
            result = generate_clarifying_questions("Contenção de Encostas", PROVIDER, MODEL, API_KEY)

        assert "questions" in result
        assert len(result["questions"]) == 3

    def test_perguntas_tem_campos_obrigatorios(self):
        with patch("app.agents.clarify_agent.call_llm", return_value=VALID_RESPONSE):
            result = generate_clarifying_questions("ML em Saúde", PROVIDER, MODEL, API_KEY)

        for q in result["questions"]:
            assert "id" in q
            assert "question" in q
            assert "type" in q

    def test_prompt_contem_tema(self):
        with patch("app.agents.clarify_agent.call_llm", return_value=VALID_RESPONSE) as mock_llm:
            generate_clarifying_questions("Direito Digital", PROVIDER, MODEL, API_KEY)

        prompt = mock_llm.call_args[0][3]
        assert "Direito Digital" in prompt

    def test_aceita_resposta_com_markdown(self):
        wrapped = f"```json\n{VALID_RESPONSE}\n```"
        with patch("app.agents.clarify_agent.call_llm", return_value=wrapped):
            result = generate_clarifying_questions("ML", PROVIDER, MODEL, API_KEY)

        assert len(result["questions"]) == 3

    def test_fallback_quando_json_invalido(self):
        with patch("app.agents.clarify_agent.call_llm", return_value="resposta inválida"):
            result = generate_clarifying_questions("Tema X", PROVIDER, MODEL, API_KEY)

        assert "questions" in result
        assert len(result["questions"]) == 3

    def test_fallback_quando_llm_lanca_excecao(self):
        with patch("app.agents.clarify_agent.call_llm", side_effect=RuntimeError("timeout")):
            result = generate_clarifying_questions("Tema X", PROVIDER, MODEL, API_KEY)

        assert "questions" in result
        assert isinstance(result["questions"], list)

    def test_fallback_tem_3_perguntas_validas(self):
        with patch("app.agents.clarify_agent.call_llm", side_effect=RuntimeError("erro")):
            result = generate_clarifying_questions("Tema Y", PROVIDER, MODEL, API_KEY)

        assert len(result["questions"]) == 3
        for q in result["questions"]:
            assert "id" in q and "question" in q and "type" in q
