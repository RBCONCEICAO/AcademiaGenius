"""
Orquestrador — Pipeline de Pesquisa Acadêmica Multi-Fonte
Executa: MultiSourceSearch → Extrator → Redator
Suporta modo Pipeline: LLM rápida (Groq) para extração + LLM de qualidade para redação.
"""
import re
import logging
from typing import Callable, Dict, Any, Optional
from app.agents.multi_source_search import multi_source_search
from app.agents.extractor_agent import extract_knowledge
from app.agents.writer_agent import write_document
from app.services.llm import call_llm
from app.agents.semantic_filter_agent import filter_papers_by_domain
from app.agents.translator_agent import translate_papers

logger = logging.getLogger(__name__)


AREA_KEYWORDS = {
    "saude": ["saúde", "saude", "medicina", "médico", "enfermagem", "farmácia",
              "clinical", "health", "medicine", "nursing", "disease", "covid"],
    "computacao": ["computação", "computacao", "software", "algoritmo", "inteligência artificial",
                   "machine learning", "deep learning", "ia", "ai", "redes neurais", "dados"],
    "educacao": ["educação", "educacao", "pedagogia", "ensino", "aprendizagem",
                 "escola", "universidade", "evasão", "docência"],
    "direito": ["direito", "jurídico", "juridico", "lei", "legislação", "constituição",
                "tribunal", "jurisprudência", "legal", "law"],
    "economia": ["economia", "econômico", "mercado", "finanças", "fiscal",
                 "pib", "inflação", "investimento", "negócios"],
}


def detect_area(theme: str) -> str:
    """Detecta a área do conhecimento a partir do tema usando regex de limite de palavra para termos curtos."""
    theme_lower = theme.lower()
    for area, keywords in AREA_KEYWORDS.items():
        for kw in keywords:
            if len(kw) <= 3:
                pattern = rf"\b{re.escape(kw)}\b"
                if re.search(pattern, theme_lower):
                    return area
            else:
                if kw in theme_lower:
                    return area
    return "default"


def run_research_pipeline(
    theme: str,
    doc_type: str,
    provider: str,
    model: str,
    api_key: str,
    norm: str = "ABNT",
    paper_limit: int = 8,
    semantic_scholar_key: Optional[str] = None,
    query_en: Optional[str] = None,
    include_universities: bool = True,
    pubmed_key: Optional[str] = None,
    core_key: Optional[str] = None,
    fast_provider: Optional[str] = None,
    fast_model: Optional[str] = None,
    fast_key: Optional[str] = None,
    existing_document: Optional[str] = None,
    clarifications: Optional[dict] = None,
    progress_callback: Optional[Callable[[dict], None]] = None,
) -> Dict[str, Any]:
    """
    Pipeline completo: busca multi-fonte → extração → redação.

    progress_callback: chamado a cada transição de etapa com o evento emitido.
    """
    steps_log = []

    def emit(event: dict):
        steps_log.append(event)
        if progress_callback:
            try:
                progress_callback(event)
            except Exception:
                pass

    area = detect_area(theme)

    # ── ETAPA 1: Busca Multi-Fonte ─────────────────────────────────────
    emit({"step": 1, "status": "running",
          "message": f"Preparando e traduzindo termos de busca para '{theme}'..."})

    if not query_en:
        try:
            clarifications_text = ""
            if clarifications:
                clarifications_text = "\nRespostas de esclarecimento do usuário sobre o tema:\n" + "\n".join([f"- {q}: {a}" for q, a in clarifications.items()])

            translation_prompt = f"""Extraia as principais palavras-chave do tema abaixo e traduza-as para o inglês.
Seu objetivo é criar a melhor string de busca (search query) possível para bases como PubMed, ArXiv e CrossRef.
Retorne APENAS os termos em inglês, separados por espaço, sem aspas, sem pontos e sem explicações.{clarifications_text}

Tema: {theme}"""

            t_provider = fast_provider or provider
            t_model = fast_model or model
            t_key = fast_key or api_key

            query_en = call_llm(t_provider, t_model, t_key, translation_prompt, "pesquisa").strip()
        except Exception:
            query_en = theme

    emit({"step": 1, "status": "running",
          "message": f"Buscando artigos globais para '{query_en}'..."})

    try:
        search_result = multi_source_search(
            query=theme,
            query_en=query_en,
            area=area,
            limit_per_source=max(6, (paper_limit * 3) // 4),
            include_universities=include_universities,
            pubmed_key=pubmed_key,
            core_key=core_key,
            semantic_scholar_key=semantic_scholar_key,
        )
        all_papers = search_result["papers"]

        # Retry com query apenas em inglês se nenhum artigo foi encontrado na 1ª tentativa
        if not all_papers and query_en and query_en != theme:
            emit({"step": 1, "status": "running",
                  "message": "Nenhum resultado na busca combinada. Retentando com termos em inglês..."})
            retry_result = multi_source_search(
                query=query_en,
                query_en=query_en,
                area=area,
                limit_per_source=max(6, (paper_limit * 3) // 4),
                include_universities=False,
                pubmed_key=pubmed_key,
                core_key=core_key,
                semantic_scholar_key=semantic_scholar_key,
            )
            if retry_result["papers"]:
                search_result = retry_result
                all_papers = retry_result["papers"]
                emit({"step": 1, "status": "running",
                      "message": f"Retry bem-sucedido: {len(all_papers)} artigos encontrados com busca em inglês."})

        emit({"step": 1, "status": "running",
              "message": "Validando alinhamento temático e eliminando artigos fora do domínio científico..."})

        try:
            filtered_papers = filter_papers_by_domain(
                papers=all_papers,
                theme=theme,
                provider=fast_provider or provider,
                model=fast_model or model,
                api_key=fast_key or api_key,
                clarifications=clarifications
            )
            papers = filtered_papers if filtered_papers else all_papers
            discarded = len(all_papers) - len(papers)
            if discarded > 0:
                emit({"step": 1, "status": "running",
                      "message": f"Filtro semântico: {len(papers)} artigos aprovados, {discarded} descartados por desvio temático."})
        except Exception:
            papers = all_papers

        papers = papers[:paper_limit]

        emit({"step": 1, "status": "running",
              "message": "Traduzindo abstracts e títulos internacionais para Português..."})

        try:
            papers = translate_papers(
                papers=papers,
                provider=fast_provider or provider,
                model=fast_model or model,
                api_key=fast_key or api_key
            )
        except Exception as e:
            logger.warning("Tradução falhou, usando títulos originais: %s", e)

        query_info = search_result["query_info"]
    except Exception as e:
        raise Exception(f"Falha na busca multi-fonte: {str(e)}")

    if not papers:
        raise Exception(
            f"Nenhum artigo encontrado para '{theme}'. "
            "Tente um tema mais amplo ou em inglês."
        )

    emit({
        "step": 1, "status": "done",
        "message": (
            f"{len(papers)} artigos de {len(query_info['sources_searched'])} bases: "
            f"{', '.join(query_info['sources_searched'])}."
        ),
        "data": [{"title": p["title"], "authors": p["authors"],
                  "year": p["year"], "source": p["source"]} for p in papers],
    })

    # ── ETAPA 2: Extração de Conhecimento ─────────────────────────────
    extraction_provider = fast_provider or provider
    extraction_model    = fast_model    or model
    extraction_key      = fast_key      or api_key

    pipeline_mode = bool(fast_provider and fast_key and fast_provider != provider)
    extract_label = (
        f"extração via {extraction_provider.upper()} (rápido) + redação via {provider.upper()} (qualidade)"
        if pipeline_mode else f"via {provider.upper()}"
    )

    emit({"step": 2, "status": "running",
          "message": f"Analisando artigos e extraindo base de conhecimento {extract_label}..."})

    try:
        knowledge = extract_knowledge(
            papers=papers,
            provider=extraction_provider,
            model=extraction_model,
            api_key=extraction_key,
        )
    except Exception as e:
        raise Exception(f"Falha na extração de conhecimento: {str(e)}")

    emit({
        "step": 2, "status": "done",
        "message": f"Base construída. {len(knowledge.get('temas_principais', []))} temas identificados.",
    })

    # ── ETAPA 3: Redação do Documento ──────────────────────────────────
    emit({"step": 3, "status": "running",
          "message": "Redigindo documento acadêmico com base nas fontes reais..."})

    try:
        document = write_document(
            theme=theme, doc_type=doc_type, papers=papers, knowledge=knowledge,
            provider=provider, model=model, api_key=api_key, norm=norm,
            existing_document=existing_document,
        )
    except Exception as e:
        raise Exception(f"Falha na redação: {str(e)}")

    emit({"step": 3, "status": "done", "message": "Documento gerado com sucesso!"})

    return {
        "papers": papers,
        "knowledge": knowledge,
        "document": document,
        "steps_log": steps_log,
        "stats": {
            "total_papers": len(papers),
            "total_citations": sum(p.get("citation_count", 0) for p in papers),
            "norm": norm,
            "area_detected": area,
            "sources_searched": query_info["sources_searched"],
            "pipeline_mode": pipeline_mode,
            "extraction_provider": extraction_provider,
            "writing_provider": provider,
        },
    }
