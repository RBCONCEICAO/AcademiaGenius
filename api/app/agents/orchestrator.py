"""
Orquestrador — Pipeline de Pesquisa Acadêmica Multi-Fonte
Executa: MultiSourceSearch → Extrator → Redator
Suporta modo Pipeline: LLM rápida (Groq) para extração + LLM de qualidade para redação.
"""
from typing import Dict, Any, Optional
from app.agents.multi_source_search import multi_source_search
from app.agents.extractor_agent import extract_knowledge
from app.agents.writer_agent import write_document


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
    import re
    theme_lower = theme.lower()
    for area, keywords in AREA_KEYWORDS.items():
        for kw in keywords:
            if len(kw) <= 3:
                # Usa limites de palavras \b para evitar bater em sufixos como "engenharia" ou "história"
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
    # ── Modo Pipeline Multi-LLM ────────────────────────────────
    # Se fornecidos, usa fast_* para extração e provider/model para redação
    fast_provider: Optional[str] = None,  # ex: 'groq'
    fast_model: Optional[str] = None,     # ex: 'llama-3.3-70b-versatile'
    fast_key: Optional[str] = None,       # chave do provedor rápido
    existing_document: Optional[str] = None,
    clarifications: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Pipeline completo: busca multi-fonte → extração → redação.

    Modo Pipeline: se fast_provider + fast_key forem fornecidos,
    a extração de conhecimento usa a LLM rápida (ex: Groq) e a
    redação usa o provider principal (ex: Gemini 2.5 Pro).

    Retorna:
        papers, knowledge, document, steps_log, stats
    """
    steps_log = []
    area = detect_area(theme)

    # ── ETAPA 1: Busca Multi-Fonte ─────────────────────────────────────
    steps_log.append({"step": 1, "status": "running",
                       "message": f"Preparando e traduzindo termos de busca para '{theme}'..."})

    # Otimização Inteligente da Query: se query_en não existe, gera automaticamente palavras-chave em inglês
    if not query_en:
        try:
            clarifications_text = ""
            if clarifications:
                clarifications_text = "\nRespostas de esclarecimento do usuário sobre o tema:\n" + "\n".join([f"- {q}: {a}" for q, a in clarifications.items()])

            translation_prompt = f"""Extraia as principais palavras-chave do tema abaixo e traduza-as para o inglês. 
Seu objetivo é criar a melhor string de busca (search query) possível para bases como PubMed, ArXiv e CrossRef.
Retorne APENAS os termos em inglês, separados por espaço, sem aspas, sem pontos e sem explicações.{clarifications_text}

Tema: {theme}"""
            
            # Usar o provedor rápido se disponível (para não perder tempo)
            t_provider = fast_provider or provider
            t_model = fast_model or model
            t_key = fast_key or api_key
            
            from app.services.llm import call_llm
            query_en = call_llm(t_provider, t_model, t_key, translation_prompt, "pesquisa").strip()
        except Exception as e:
            query_en = theme # Fallback seguro

    steps_log[-1]["message"] = f"Buscando artigos globais para '{query_en}'..."

    try:
        # Busca com um limite ligeiramente maior por fonte para permitir filtragem posterior sem faltar papers
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
        
        # Etapa de Filtragem Semântica de Domínio (Evita misturar Engenharia com Medicina/Homônimos)
        steps_log.append({
            "step": 1,
            "status": "running",
            "message": "Validando alinhamento temático e eliminando artigos fora do domínio científico..."
        })
        
        try:
            from app.agents.semantic_filter_agent import filter_papers_by_domain
            filtered_papers = filter_papers_by_domain(
                papers=all_papers,
                theme=theme,
                provider=fast_provider or provider,
                model=fast_model or model,
                api_key=fast_key or api_key,
                clarifications=clarifications
            )
            papers = filtered_papers if filtered_papers else all_papers
        except Exception as e:
            papers = all_papers

        papers = papers[:paper_limit]
        
        # Etapa Invisível: Traduzir os resultados em inglês de volta para PT-BR
        steps_log.append({"step": 1, "status": "running", "message": "Traduzindo abstracts e títulos internacionais para Português..."})
        try:
            from app.agents.translator_agent import translate_papers
            papers = translate_papers(
                papers=papers,
                provider=fast_provider or provider,
                model=fast_model or model,
                api_key=fast_key or api_key
            )
        except Exception as e:
            pass # Continua em inglês se falhar
            
        query_info = search_result["query_info"]
    except Exception as e:
        raise Exception(f"Falha na busca multi-fonte: {str(e)}")

    if not papers:
        raise Exception(
            f"Nenhum artigo encontrado para '{theme}'. "
            "Tente um tema mais amplo ou em inglês."
        )

    steps_log.append({
        "step": 1, "status": "done",
        "message": (
            f"{len(papers)} artigos de {len(query_info['sources_searched'])} bases: "
            f"{', '.join(query_info['sources_searched'])}."
        ),
        "data": [{"title": p["title"], "authors": p["authors"],
                  "year": p["year"], "source": p["source"]} for p in papers],
    })

    # ── ETAPA 2: Extração de Conhecimento ─────────────────────────────
    # Decide qual LLM usar na extração
    extraction_provider = fast_provider or provider
    extraction_model    = fast_model    or model
    extraction_key      = fast_key      or api_key

    pipeline_mode = bool(fast_provider and fast_key and fast_provider != provider)
    extract_label = (
        f"extração via {extraction_provider.upper()} (rápido) + redação via {provider.upper()} (qualidade)"
        if pipeline_mode else f"via {provider.upper()}"
    )

    steps_log.append({"step": 2, "status": "running",
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

    steps_log.append({
        "step": 2, "status": "done",
        "message": f"Base construída. {len(knowledge.get('temas_principais', []))} temas identificados.",
    })

    # ── ETAPA 3: Redação do Documento ──────────────────────────────────
    steps_log.append({"step": 3, "status": "running",
                       "message": "Redigindo documento acadêmico com base nas fontes reais..."})

    try:
        document = write_document(
            theme=theme, doc_type=doc_type, papers=papers, knowledge=knowledge,
            provider=provider, model=model, api_key=api_key, norm=norm,
            existing_document=existing_document,
        )
    except Exception as e:
        raise Exception(f"Falha na redação: {str(e)}")

    steps_log.append({"step": 3, "status": "done", "message": "Documento gerado com sucesso!"})

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
