"""
Testes unitários para write_document().
Inclui teste de regressão: PLAXIS 2D não deve aparecer em temas genéricos.
"""
import pytest
from unittest.mock import patch

from app.agents.writer_agent import write_document

PROVIDER = "gemini"
MODEL    = "gemini-2.5-flash"
API_KEY  = "test-key"

PAPERS = [
    {
        "abnt_reference": "SILVA, J. Machine Learning em Finanças. 2022.",
        "citation_count": 42,
        "title": "ML em Finanças",
        "authors": "Silva, J.",
        "year": 2022,
    }
]

KNOWLEDGE = {
    "temas_principais": ["ML", "Finanças"],
    "metodologias_identificadas": ["Random Forest"],
    "principais_achados": ["Alta acurácia"],
    "lacunas_pesquisa": ["Datasets limitados"],
    "consensos": "Autores concordam sobre ML.",
    "divergencias": "Divergem sobre modelos.",
    "sintese_geral": "ML é promissor em finanças.",
}


class TestWriteDocument:
    def test_chama_call_llm_com_provider_model_key(self):
        with patch("app.agents.writer_agent.call_llm", return_value="documento gerado") as mock:
            write_document("ML em Finanças", "artigo", PAPERS, KNOWLEDGE, PROVIDER, MODEL, API_KEY)

        mock.assert_called_once()
        args = mock.call_args[0]
        assert args[0] == PROVIDER
        assert args[1] == MODEL
        assert args[2] == API_KEY

    def test_retorna_output_da_llm(self):
        with patch("app.agents.writer_agent.call_llm", return_value="texto do documento"):
            result = write_document("ML em Finanças", "artigo", PAPERS, KNOWLEDGE, PROVIDER, MODEL, API_KEY)

        assert result == "texto do documento"

    def test_prompt_contem_tema(self):
        with patch("app.agents.writer_agent.call_llm", return_value="ok") as mock:
            write_document("Machine Learning em Saúde", "artigo", PAPERS, KNOWLEDGE, PROVIDER, MODEL, API_KEY)

        prompt = mock.call_args[0][3]
        assert "Machine Learning em Saúde" in prompt

    def test_prompt_contem_referencia_do_paper(self):
        with patch("app.agents.writer_agent.call_llm", return_value="ok") as mock:
            write_document("ML em Finanças", "artigo", PAPERS, KNOWLEDGE, PROVIDER, MODEL, API_KEY)

        prompt = mock.call_args[0][3]
        assert "SILVA, J. Machine Learning em Finanças." in prompt

    def test_prompt_contem_instrucao_de_norma_abnt(self):
        with patch("app.agents.writer_agent.call_llm", return_value="ok") as mock:
            write_document("ML em Finanças", "artigo", PAPERS, KNOWLEDGE, PROVIDER, MODEL, API_KEY, norm="ABNT")

        prompt = mock.call_args[0][3]
        assert "ABNT" in prompt

    def test_prompt_contem_instrucao_de_norma_apa(self):
        with patch("app.agents.writer_agent.call_llm", return_value="ok") as mock:
            write_document("ML em Finanças", "artigo", PAPERS, KNOWLEDGE, PROVIDER, MODEL, API_KEY, norm="APA")

        prompt = mock.call_args[0][3]
        assert "APA" in prompt

    # ── TESTE DE REGRESSÃO: PLAXIS 2D ─────────────────────────────────────
    def test_plaxis_2d_nao_aparece_no_prompt_para_tema_generico(self):
        """Regressão: estruturas fixas não devem mencionar PLAXIS 2D para temas não geotécnicos."""
        for doc_type in ("tcc", "artigo", "estudo"):
            with patch("app.agents.writer_agent.call_llm", return_value="ok") as mock:
                write_document("Educação e Tecnologia", doc_type, PAPERS, KNOWLEDGE, PROVIDER, MODEL, API_KEY)

            prompt = mock.call_args[0][3]
            assert "PLAXIS" not in prompt, f"PLAXIS 2D encontrado no prompt de doc_type='{doc_type}'"

    def test_existing_document_aparece_no_prompt(self):
        with patch("app.agents.writer_agent.call_llm", return_value="ok") as mock:
            write_document(
                "ML em Finanças", "artigo", PAPERS, KNOWLEDGE,
                PROVIDER, MODEL, API_KEY,
                existing_document="Versão anterior do documento.",
            )

        prompt = mock.call_args[0][3]
        assert "Versão anterior do documento." in prompt
        assert "ATUALIZ" in prompt.upper() or "REFIN" in prompt.upper()

    def test_instrucao_adicional_extraida_do_tema(self):
        tema_com_instrucao = "ML em Finanças\nINSTRUÇÕES ADICIONAIS DE REFINAMENTO:\nAmplie a seção de metodologia."
        with patch("app.agents.writer_agent.call_llm", return_value="ok") as mock:
            write_document(tema_com_instrucao, "artigo", PAPERS, KNOWLEDGE, PROVIDER, MODEL, API_KEY)

        prompt = mock.call_args[0][3]
        assert "Amplie a seção de metodologia." in prompt
        # O tema principal não deve conter a instrução
        assert "INSTRUÇÕES ADICIONAIS" not in prompt.split("INSTRUÇÃO ESPECIAL")[0]

    @pytest.mark.parametrize("doc_type,expected_section", [
        ("tcc", "Referencial Teórico"),
        ("artigo", "Resumo e Palavras-chave"),
        ("estudo", "Introdução ao Caso"),
    ])
    def test_estrutura_correta_por_tipo_de_documento(self, doc_type, expected_section):
        with patch("app.agents.writer_agent.call_llm", return_value="ok") as mock:
            write_document("Tema Genérico", doc_type, PAPERS, KNOWLEDGE, PROVIDER, MODEL, API_KEY)

        prompt = mock.call_args[0][3]
        assert expected_section in prompt
