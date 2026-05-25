"""
notebook_service.py
Módulo NotebookLM-style — suporta múltiplos provedores LLM.
Funcionalidades: Chat, Guia de Estudo, FAQ, Linha do Tempo, Roteiro de Áudio.
"""
import json
import re
import logging
from typing import List, Dict, Any, Optional

from app.services.llm import call_llm

logger = logging.getLogger(__name__)


def _build_corpus_text(papers: List[Dict], document: str) -> str:
    """Monta o corpus textual a partir dos papers e do documento gerado."""
    parts = [f"# DOCUMENTO GERADO\n\n{document}\n\n---\n\n# FONTES CIENTÍFICAS\n"]
    for i, p in enumerate(papers, 1):
        abstract = p.get('abstract', '')
        if len(abstract) > 500:
            abstract = abstract[:500] + "..."
        parts.append(
            f"\n## Fonte {i}: {p.get('title', '')}\n"
            f"**Autores:** {p.get('authors', '')}\n"
            f"**Ano:** {p.get('year', '')}\n"
            f"**Base:** {p.get('source', '')}\n"
            f"**Citações:** {p.get('citation_count', 0)}\n"
            f"**DOI:** {p.get('doi', '')}\n\n"
            f"**Abstract:** {abstract}\n\n"
            f"**Referência ABNT:** {p.get('abnt_reference', '')}\n"
        )
    return "\n".join(parts)


SYSTEM = (
    "Você é um assistente de pesquisa acadêmica especializado. "
    "Responda sempre em Português do Brasil com linguagem técnica e precisa."
)


def _call(provider: str, model: str, api_key: str, prompt: str) -> str:
    """Wrapper que chama o dispatcher unificado de LLM."""
    return call_llm(provider, model, api_key, prompt, "notebook")


# ─── 1. CHAT COM A PESQUISA (RAG) ────────────────────────────────────────────

def chat_with_research(
    question: str,
    papers: List[Dict],
    document: str,
    api_key: str,
    model: str = "gemini-2.0-flash",
    provider: str = "gemini",
    history: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Responde perguntas sobre a pesquisa com base nas fontes reais.
    Inclui citações quando relevante.
    """
    corpus = _build_corpus_text(papers, document)
    history_text = ""
    if history:
        for h in history[-6:]:  # mantém as últimas 6 trocas de contexto
            role = "Pesquisador" if h["role"] == "user" else "Assistente"
            history_text += f"\n{role}: {h['content']}"

    prompt = f"""Você tem acesso ao seguinte corpus de pesquisa acadêmica:

{corpus}

{f'Histórico da conversa:{history_text}' if history_text else ''}

Com base EXCLUSIVAMENTE nas fontes acima, responda à pergunta a seguir.
Quando citar informações específicas, indique a fonte (ex: "[Fonte 3 — Autor, ano]").
Se a informação não estiver nas fontes, diga claramente.

**Pergunta:** {question}

**Resposta:**"""

    answer = _call(provider, model, api_key, prompt)

    # Extrai citações mencionadas na resposta
    citations = re.findall(r'\[Fonte\s+(\d+)[^\]]*\]', answer)
    cited_papers = []
    for idx_str in set(citations):
        idx = int(idx_str) - 1
        if 0 <= idx < len(papers):
            cited_papers.append({
                "index": idx + 1,
                "title": papers[idx].get("title", ""),
                "authors": papers[idx].get("authors", ""),
                "year": papers[idx].get("year", ""),
                "source": papers[idx].get("source", ""),
            })

    return {"answer": answer, "citations": cited_papers}


# ─── 2. GUIA DE ESTUDO ───────────────────────────────────────────────────────

def generate_study_guide(
    theme: str,
    papers: List[Dict],
    document: str,
    api_key: str,
    model: str = "gemini-2.0-flash",
    provider: str = "gemini",
) -> Dict[str, Any]:
    """Gera um Guia de Estudo estruturado com base nas fontes."""
    corpus = _build_corpus_text(papers, document)

    prompt = f"""Com base nas fontes de pesquisa abaixo, crie um Guia de Estudo completo sobre:
**{theme}**

## CORPUS:
{corpus}

## FORMATO DO GUIA (responda em JSON válido):
{{
  "titulo": "Guia de Estudo: {theme}",
  "resumo_executivo": "2-3 parágrafos resumindo o estado da arte",
  "conceitos_chave": [
    {{"conceito": "...", "definicao": "...", "fonte": "Autor, ano"}}
  ],
  "topicos_principais": [
    {{
      "titulo": "...",
      "descricao": "...",
      "pontos_chave": ["...", "..."],
      "autores_relevantes": ["..."]
    }}
  ],
  "perguntas_reflexao": ["...", "...", "..."],
  "lacunas_identificadas": ["...", "..."],
  "proximos_passos": ["...", "..."]
}}

Responda SOMENTE com o JSON válido, sem markdown."""

    raw = _call(provider, model, api_key, prompt)
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
    try:
        return json.loads(cleaned)
    except Exception:
        return {"titulo": f"Guia de Estudo: {theme}", "resumo_executivo": raw,
                "conceitos_chave": [], "topicos_principais": [],
                "perguntas_reflexao": [], "lacunas_identificadas": [], "proximos_passos": []}


# ─── 3. FAQ AUTOMÁTICO ───────────────────────────────────────────────────────

def generate_faq(
    theme: str,
    papers: List[Dict],
    document: str,
    api_key: str,
    model: str = "gemini-2.0-flash",
    provider: str = "gemini",
    n_questions: int = 8,
) -> List[Dict[str, str]]:
    """Gera perguntas frequentes com respostas baseadas nas fontes."""
    corpus = _build_corpus_text(papers, document)

    prompt = f"""Com base nas fontes de pesquisa sobre "{theme}", gere {n_questions} perguntas frequentes
com respostas detalhadas baseadas exclusivamente nas fontes fornecidas.

## CORPUS:
{corpus}

## FORMATO (responda em JSON válido):
[
  {{
    "pergunta": "...",
    "resposta": "...",
    "fonte": "Autor, ano"
  }}
]

Responda SOMENTE com o JSON válido, sem markdown."""

    raw = _call(provider, model, api_key, prompt)
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
    try:
        return json.loads(cleaned)
    except Exception:
        return [{"pergunta": "Qual o estado da arte?", "resposta": raw, "fonte": ""}]


# ─── 4. LINHA DO TEMPO ───────────────────────────────────────────────────────

def generate_timeline(
    theme: str,
    papers: List[Dict],
    document: str,
    api_key: str,
    model: str = "gemini-2.0-flash",
    provider: str = "gemini",
) -> List[Dict[str, str]]:
    """Extrai uma linha do tempo dos marcos na área de pesquisa."""
    corpus = _build_corpus_text(papers, document)

    prompt = f"""Com base nas fontes de pesquisa sobre "{theme}", crie uma linha do tempo
dos principais marcos, descobertas e eventos na área.

## CORPUS:
{corpus}

## FORMATO (responda em JSON válido):
[
  {{
    "ano": "2020",
    "evento": "Descrição do marco ou descoberta",
    "autores": "Autor(es) responsáveis",
    "impacto": "Breve descrição do impacto"
  }}
]

Ordene cronologicamente. Responda SOMENTE com o JSON válido, sem markdown."""

    raw = _call(provider, model, api_key, prompt)
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
    try:
        result = json.loads(cleaned)
        return sorted(result, key=lambda x: str(x.get("ano", "0")))
    except Exception:
        return []


# ─── 5. ROTEIRO DE ÁUDIO (Audio Overview) ────────────────────────────────────

def generate_audio_script(
    theme: str,
    papers: List[Dict],
    document: str,
    api_key: str,
    model: str = "gemini-2.0-flash",
    provider: str = "gemini",
    duration_minutes: int = 5,
) -> Dict[str, Any]:
    """
    Gera um roteiro dialógico estilo podcast (2 apresentadores)
    baseado nas fontes da pesquisa — no estilo Audio Overview do NotebookLM.
    """
    corpus = _build_corpus_text(papers, document)
    word_count = duration_minutes * 130  # ~130 palavras/minuto

    prompt = f"""Crie um roteiro de podcast de aproximadamente {duration_minutes} minutos
({word_count} palavras) sobre o tema: **{theme}**

O roteiro deve ter DOIS apresentadores:
- **ANA**: especialista em pesquisa acadêmica, mais técnica
- **PEDRO**: mediador curioso, faz perguntas que o público leigo faria

Baseie-se EXCLUSIVAMENTE nas fontes abaixo. Mencione os autores reais.
Tom: envolvente, acessível, mas com rigor acadêmico.

## CORPUS:
{corpus}

## FORMATO (responda em JSON válido):
{{
  "titulo": "...",
  "descricao": "...",
  "duracao_estimada": "{duration_minutes} minutos",
  "roteiro": [
    {{"apresentador": "ANA", "fala": "..."}},
    {{"apresentador": "PEDRO", "fala": "..."}},
    {{"apresentador": "ANA", "fala": "..."}}
  ]
}}

Responda SOMENTE com o JSON válido, sem markdown."""

    raw = _call(provider, model, api_key, prompt)
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
    try:
        return json.loads(cleaned)
    except Exception:
        return {
            "titulo": f"Podcast: {theme}",
            "descricao": "",
            "duracao_estimada": f"{duration_minutes} minutos",
            "roteiro": [{"apresentador": "ANA", "fala": raw}],
        }
