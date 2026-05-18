import json
import re
import logging
from typing import List, Dict, Any
from app.services.llm import call_llm

logger = logging.getLogger(__name__)

def filter_papers_by_domain(
    papers: List[Dict[str, Any]],
    theme: str,
    provider: str,
    model: str,
    api_key: str,
    clarifications: Dict[str, Any] = None,
) -> List[Dict[str, Any]]:
    """
    Filtra os artigos recuperados garantindo que pertençam ao mesmo domínio acadêmico
    do tema do usuário, eliminando homônimos e ambiguidades semânticas (ex: contenção civil vs médica).
    """
    if not papers:
        return papers

    logger.info("Iniciando filtro semântico de domínio para %d artigos...", len(papers))

    # Prepara o payload leve para o LLM analisar
    payload = []
    for i, p in enumerate(papers):
        payload.append({
            "id": i,
            "title": p.get("title", ""),
            "abstract": p.get("abstract", "")[:400] + ("..." if len(p.get("abstract", "")) > 400 else "")
        })

    clarifications_text = ""
    if clarifications:
        clarifications_text = "\nRespostas do Usuário para Refinamento de Escopo:\n" + "\n".join([f"- {q}: {a}" for q, a in clarifications.items()])

    prompt = f"""Você é um validador de relevância científica e filtro semântico de alta precisão.
Sua missão é classificar os artigos científicos encontrados e ELIMINAR artigos que estejam fora do domínio acadêmico correto do tema de pesquisa do usuário.

Tema de Pesquisa do Usuário: {theme}
{clarifications_text}

Aqui está a lista de artigos recuperados para análise:
{json.dumps(payload, ensure_ascii=False, indent=2)}

DIRETRIZES DE VALIDAÇÃO:
1. Identifique o domínio principal do tema do usuário (ex: Engenharia Civil, Geotecnia, Medicina, Economia, Direito, etc.), prestando atenção especial às respostas de refinamento fornecidas pelo usuário acima.
2. Analise cada artigo para ver se ele pertence ao mesmo domínio ou se é um homônimo ou ambiguidade (por exemplo, se as respostas indicarem foco em Engenharia Civil/Geotecnia, descarte artigos sobre "Contenção Física no Leito" em Psiquiatria ou "Infecção Mista" em Medicina).
3. Classifique cada artigo com "keep" (manter) se for do mesmo domínio científico e diretamente relevante, ou "discard" (descartar) se for de outra área científica ou irrelevante.

Retorne APENAS um objeto JSON no formato abaixo, sem markdown, sem crases ```json, sem comentários extras:
{{
  "results": [
    {{
      "id": 0,
      "decision": "keep",
      "reason": "Explicação curta do motivo."
    }}
  ]
}}"""

    try:
        response_text = call_llm(provider, model, api_key, prompt, "pesquisa").strip()
        
        # Limpa crases markdown se houver
        cleaned = re.sub(r"```(?:json)?", "", response_text).strip().rstrip("```").strip()
        
        data = json.loads(cleaned)
        decisions = {item["id"]: item["decision"] for item in data.get("results", [])}
        
        filtered_papers = []
        discarded_count = 0
        
        for idx, paper in enumerate(papers):
            decision = decisions.get(idx, "keep") # Padrão para não perder papers em caso de falha de ID
            if decision == "keep":
                filtered_papers.append(paper)
            else:
                discarded_count += 1
                logger.info("Artigo descartado pelo filtro semântico: '%s' (Fora do domínio do tema)", paper.get("title"))
                
        logger.info("Filtro semântico concluído. Mantidos: %d | Descartados: %d", len(filtered_papers), discarded_count)
        return filtered_papers

    except Exception as e:
        logger.error("Erro no filtro semântico de domínio: %s. Retornando artigos originais como fallback.", e)
        return papers
