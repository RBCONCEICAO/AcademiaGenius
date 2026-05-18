"""
Agente Extrator — Análise de Literatura
Usa a LLM para extrair conceitos-chave, metodologias e achados
dos abstracts dos artigos encontrados pelo Agente Buscador.
"""
import json
import re
from typing import List, Dict, Any
from app.services.llm import call_llm


def extract_knowledge(
    papers: List[Dict[str, Any]],
    provider: str,
    model: str,
    api_key: str,
) -> Dict[str, Any]:
    """
    Analisa os artigos e extrai uma base de conhecimento estruturada.

    Args:
        papers: Lista de artigos do search_agent.
        provider: Provedor LLM ('gemini', 'openai', 'anthropic', 'groq', 'mistral').
        model: Modelo específico.
        api_key: Chave da API.

    Returns:
        Dicionário com conceitos extraídos, gaps e síntese geral.
    """
    if not papers:
        raise ValueError("Nenhum artigo fornecido para extração.")

    # Monta o corpus de abstracts para análise
    abstracts_text = ""
    for i, paper in enumerate(papers, 1):
        abstracts_text += (
            f"\n--- Artigo {i} ---\n"
            f"Título: {paper['title']}\n"
            f"Autores: {paper['authors']}\n"
            f"Ano: {paper['year']}\n"
            f"Abstract: {paper['abstract']}\n"
        )

    prompt = f"""Você é um pesquisador acadêmico especialista em revisão sistemática de literatura.

Analise os seguintes artigos científicos e extraia uma síntese estruturada:

{abstracts_text}

Produza uma análise em JSON com o seguinte formato:
{{
  "temas_principais": ["tema1", "tema2", "tema3"],
  "metodologias_identificadas": ["metodo1", "metodo2"],
  "principais_achados": ["achado1", "achado2", "achado3"],
  "lacunas_pesquisa": ["lacuna1", "lacuna2"],
  "consensos": "Parágrafo descrevendo o que os autores concordam.",
  "divergencias": "Parágrafo descrevendo pontos de debate entre os autores.",
  "sintese_geral": "Parágrafo completo sintetizando o estado da arte baseado nos artigos."
}}

Responda SOMENTE com o JSON válido, sem markdown ou explicações adicionais."""

    try:
        raw = call_llm(provider, model, api_key, prompt, "extracao")

        # Limpa a resposta e parseia o JSON
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
        knowledge = json.loads(cleaned)

    except Exception:
        # Fallback: estrutura mínima se o JSON falhar
        knowledge = {
            "temas_principais": [],
            "metodologias_identificadas": [],
            "principais_achados": [],
            "lacunas_pesquisa": [],
            "consensos": "",
            "divergencias": "",
            "sintese_geral": raw if 'raw' in locals() else "Falha na extração.",
        }

    return knowledge
