"""
Testes unitários para detect_area() — sem I/O, sem mocks necessários.
"""
import pytest
from app.agents.orchestrator import detect_area


class TestDetectArea:
    def test_saude_por_medicina(self):
        assert detect_area("Impacto da medicina preventiva na saúde pública") == "saude"

    def test_saude_por_covid(self):
        assert detect_area("Análise epidemiológica do covid-19 no Brasil") == "saude"

    def test_saude_ingles_health(self):
        assert detect_area("Mental health interventions in primary care") == "saude"

    def test_computacao_por_machine_learning(self):
        assert detect_area("machine learning aplicado à detecção de fraudes") == "computacao"

    def test_computacao_por_ia(self):
        assert detect_area("O impacto da IA generativa no mercado de trabalho") == "computacao"

    def test_computacao_por_deep_learning(self):
        assert detect_area("deep learning para segmentação de imagens médicas") == "computacao"

    def test_educacao_por_evasao(self):
        assert detect_area("Evasão escolar no ensino médio público") == "educacao"

    def test_educacao_por_pedagogia(self):
        assert detect_area("Metodologias pedagógicas no ensino superior") == "educacao"

    def test_direito_por_lei(self):
        # 'lei' tem 3 chars → precisa de word boundary
        assert detect_area("Aplicação da lei maria da penha") == "direito"

    def test_direito_por_jurisprudencia(self):
        assert detect_area("Análise de jurisprudência do STF") == "direito"

    def test_economia_por_pib(self):
        # 'pib' tem 3 chars → word boundary
        assert detect_area("Crescimento do PIB brasileiro pós-pandemia") == "economia"

    def test_economia_por_inflacao(self):
        assert detect_area("Inflação e política monetária no Brasil") == "economia"

    def test_default_tema_desconhecido(self):
        assert detect_area("Gastronomia molecular e técnicas culinárias") == "default"

    def test_default_string_vazia(self):
        assert detect_area("") == "default"

    def test_case_insensitive(self):
        # keyword matching deve ser case-insensitive
        assert detect_area("MEDICINA E SAÚDE PÚBLICA") == "saude"

    def test_ai_short_word_boundary(self):
        # 'ai' tem 2 chars — word boundary evita falsos positivos como "trainable"
        result = detect_area("AI-based systems for document processing")
        assert result == "computacao"

    def test_ai_inside_word_no_match(self):
        # 'ai' embutido em outra palavra NÃO deve disparar
        assert detect_area("The trainable neural network architecture") != "computacao"
