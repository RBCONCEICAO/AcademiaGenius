"""
Testes unitários para notebook_service.py.
"""
import json
import pytest
from unittest.mock import patch

from app.services.notebook_service import (
    _build_corpus_text,
    chat_with_research,
    generate_study_guide,
    generate_faq,
    generate_timeline,
    generate_audio_script,
)

PAPERS = [
    {
        "title": "ML em Finanças",
        "authors": "Silva, J.",
        "year": 2022,
        "source": "arxiv",
        "citation_count": 42,
        "doi": "10.1234/ml",
        "abstract": "Este artigo analisa o uso de redes neurais para detecção de fraudes financeiras.",
        "abnt_reference": "SILVA, J. ML em Finanças. 2022.",
    }
]
DOCUMENT = "# Documento Gerado\nConteúdo acadêmico sobre ML em finanças."


# ── _build_corpus_text ────────────────────────────────────────────────────────

class TestBuildCorpusText:
    def test_inclui_titulo_do_paper(self):
        corpus = _build_corpus_text(PAPERS, DOCUMENT)
        assert "ML em Finanças" in corpus

    def test_inclui_documento_gerado(self):
        corpus = _build_corpus_text(PAPERS, DOCUMENT)
        assert "Documento Gerado" in corpus

    def test_inclui_autores_e_ano(self):
        corpus = _build_corpus_text(PAPERS, DOCUMENT)
        assert "Silva, J." in corpus
        assert "2022" in corpus

    def test_trunca_abstracts_longos(self):
        long_abstract = "x" * 1000
        papers = [{**PAPERS[0], "abstract": long_abstract}]
        corpus = _build_corpus_text(papers, DOCUMENT)
        assert "x" * 501 not in corpus
        assert "..." in corpus

    def test_abstract_curto_nao_truncado(self):
        papers = [{**PAPERS[0], "abstract": "Resumo curto."}]
        corpus = _build_corpus_text(papers, DOCUMENT)
        assert "Resumo curto." in corpus

    def test_lista_vazia_de_papers(self):
        corpus = _build_corpus_text([], DOCUMENT)
        assert "Documento Gerado" in corpus


# ── chat_with_research ────────────────────────────────────────────────────────

class TestChatWithResearch:
    def test_retorna_resposta(self):
        with patch("app.services.notebook_service._call", return_value="Resposta clara."):
            result = chat_with_research("O que é ML?", PAPERS, DOCUMENT, "key")

        assert result["answer"] == "Resposta clara."

    def test_extrai_citacoes_mencionadas(self):
        answer = "Conforme [Fonte 1 — Silva, 2022], ML é amplamente aplicado."
        with patch("app.services.notebook_service._call", return_value=answer):
            result = chat_with_research("Pergunta", PAPERS, DOCUMENT, "key")

        assert len(result["citations"]) == 1
        assert result["citations"][0]["title"] == "ML em Finanças"

    def test_sem_citacoes_quando_nenhuma_mencionada(self):
        with patch("app.services.notebook_service._call", return_value="Resposta sem citação."):
            result = chat_with_research("Pergunta", PAPERS, DOCUMENT, "key")

        assert result["citations"] == []

    def test_indice_de_citacao_fora_do_range_ignorado(self):
        answer = "Veja [Fonte 99 — X, 2020] para detalhes."
        with patch("app.services.notebook_service._call", return_value=answer):
            result = chat_with_research("Pergunta", PAPERS, DOCUMENT, "key")

        assert result["citations"] == []


# ── generate_study_guide ──────────────────────────────────────────────────────

STUDY_GUIDE = {
    "titulo": "Guia: ML em Finanças",
    "resumo_executivo": "Resumo do estado da arte.",
    "conceitos_chave": [],
    "topicos_principais": [],
    "perguntas_reflexao": [],
    "lacunas_identificadas": [],
    "proximos_passos": [],
}


class TestGenerateStudyGuide:
    def test_retorna_dicionario_com_titulo(self):
        with patch("app.services.notebook_service._call", return_value=json.dumps(STUDY_GUIDE)):
            result = generate_study_guide("ML em Finanças", PAPERS, DOCUMENT, "key")

        assert result["titulo"] == "Guia: ML em Finanças"

    def test_fallback_quando_json_invalido(self):
        with patch("app.services.notebook_service._call", return_value="não é json"):
            result = generate_study_guide("ML em Finanças", PAPERS, DOCUMENT, "key")

        assert "titulo" in result
        assert "resumo_executivo" in result

    def test_aceita_resposta_com_markdown(self):
        wrapped = f"```json\n{json.dumps(STUDY_GUIDE)}\n```"
        with patch("app.services.notebook_service._call", return_value=wrapped):
            result = generate_study_guide("ML", PAPERS, DOCUMENT, "key")

        assert result["titulo"] == "Guia: ML em Finanças"


# ── generate_faq ──────────────────────────────────────────────────────────────

FAQ_RESPONSE = [
    {"pergunta": "O que é ML?", "resposta": "Machine Learning.", "fonte": "Silva, 2022"}
]


class TestGenerateFaq:
    def test_retorna_lista_de_perguntas(self):
        with patch("app.services.notebook_service._call", return_value=json.dumps(FAQ_RESPONSE)):
            result = generate_faq("ML", PAPERS, DOCUMENT, "key")

        assert isinstance(result, list)
        assert result[0]["pergunta"] == "O que é ML?"

    def test_fallback_quando_json_invalido(self):
        with patch("app.services.notebook_service._call", return_value="texto solto"):
            result = generate_faq("ML", PAPERS, DOCUMENT, "key")

        assert isinstance(result, list)
        assert len(result) >= 1


# ── generate_timeline ─────────────────────────────────────────────────────────

TIMELINE_RESPONSE = [
    {"ano": "2023", "evento": "Lançamento de GPT-4", "autores": "OpenAI", "impacto": "Alto"},
    {"ano": "2018", "evento": "BERT publicado", "autores": "Google", "impacto": "Alto"},
    {"ano": "2020", "evento": "GPT-3", "autores": "OpenAI", "impacto": "Muito alto"},
]


class TestGenerateTimeline:
    def test_retorna_lista_ordenada_cronologicamente(self):
        with patch("app.services.notebook_service._call", return_value=json.dumps(TIMELINE_RESPONSE)):
            result = generate_timeline("LLMs", PAPERS, DOCUMENT, "key")

        anos = [int(e["ano"]) for e in result]
        assert anos == sorted(anos)

    def test_fallback_quando_json_invalido(self):
        with patch("app.services.notebook_service._call", return_value="não é json"):
            result = generate_timeline("ML", PAPERS, DOCUMENT, "key")

        assert result == []


# ── generate_audio_script ─────────────────────────────────────────────────────

AUDIO_RESPONSE = {
    "titulo": "Podcast sobre ML",
    "descricao": "Episódio sobre Machine Learning.",
    "duracao_estimada": "5 minutos",
    "roteiro": [
        {"apresentador": "ANA", "fala": "Bem-vindos ao podcast!"},
        {"apresentador": "PEDRO", "fala": "O que é Machine Learning?"},
    ],
}


class TestGenerateAudioScript:
    def test_retorna_dicionario_com_roteiro(self):
        with patch("app.services.notebook_service._call", return_value=json.dumps(AUDIO_RESPONSE)):
            result = generate_audio_script("ML", PAPERS, DOCUMENT, "key", duration_minutes=5)

        assert "roteiro" in result
        assert len(result["roteiro"]) == 2

    def test_apresentadores_ana_e_pedro(self):
        with patch("app.services.notebook_service._call", return_value=json.dumps(AUDIO_RESPONSE)):
            result = generate_audio_script("ML", PAPERS, DOCUMENT, "key")

        apresentadores = {item["apresentador"] for item in result["roteiro"]}
        assert "ANA" in apresentadores
        assert "PEDRO" in apresentadores

    def test_fallback_quando_json_invalido(self):
        with patch("app.services.notebook_service._call", return_value="não é json"):
            result = generate_audio_script("ML", PAPERS, DOCUMENT, "key")

        assert "roteiro" in result
        assert len(result["roteiro"]) >= 1

    def test_prompt_menciona_duracao(self):
        with patch("app.services.notebook_service._call", return_value=json.dumps(AUDIO_RESPONSE)) as mock:
            generate_audio_script("ML", PAPERS, DOCUMENT, "key", duration_minutes=10)

        prompt = mock.call_args[0][3]
        assert "10" in prompt
