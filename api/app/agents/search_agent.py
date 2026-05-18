"""
Agente Buscador — Semantic Scholar API
Busca artigos científicos reais.
Semantic Scholar: https://api.semanticscholar.org/
"""
import time
import requests
from typing import List, Dict, Any, Optional


SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

FIELDS = ",".join([
    "title",
    "authors",
    "year",
    "abstract",
    "externalIds",
    "citationCount",
    "url",
    "openAccessPdf",
    "publicationTypes",
    "venue",
])

# Retry config
MAX_RETRIES = 4
RETRY_DELAYS = [5, 15, 30, 60]  # segundos entre tentativas


def search_papers(
    query: str,
    limit: int = 10,
    min_year: int = 2018,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Busca artigos científicos reais no Semantic Scholar.

    Args:
        query: Tema central da pesquisa.
        limit: Número máximo de artigos a retornar.
        min_year: Ano mínimo de publicação para filtrar artigos recentes.
        api_key: Chave da Semantic Scholar API (opcional, aumenta rate limit).

    Returns:
        Lista de artigos com metadados completos.
    """
    params = {
        "query": query,
        "limit": min(limit * 2, 50),
        "fields": FIELDS,
    }

    headers = {
        "User-Agent": "AcademiaGenius/1.0 (academic research assistant)",
    }
    if api_key:
        headers["x-api-key"] = api_key

    last_error: Exception = Exception("Falha desconhecida")

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                SEMANTIC_SCHOLAR_URL,
                params=params,
                headers=headers,
                timeout=20,
            )

            if response.status_code == 429:
                wait = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                if attempt < MAX_RETRIES - 1:
                    time.sleep(wait)
                    continue
                raise Exception(
                    "Limite de requisições da Semantic Scholar atingido após várias tentativas. "
                    "Aguarde alguns minutos e tente novamente, ou cadastre uma API Key gratuita em "
                    "semanticscholar.org/product/api e informe-a nas Configurações."
                )

            if response.status_code != 200:
                raise Exception(
                    f"Semantic Scholar API retornou status {response.status_code}."
                )

            data = response.json()
            papers_raw = data.get("data", [])

            # Filtra artigos sem abstract útil
            filtered = [
                p for p in papers_raw
                if p.get("abstract") and len(p.get("abstract", "")) > 100
                and (p.get("year") or 0) >= min_year
            ]

            # Se o filtro por ano trouxer poucos, usa sem filtro de ano
            if len(filtered) < 3:
                filtered = [
                    p for p in papers_raw
                    if p.get("abstract") and len(p.get("abstract", "")) > 100
                ]

            # Ordena por citações (mais citados = mais relevantes)
            filtered.sort(key=lambda x: x.get("citationCount") or 0, reverse=True)

            return _format_papers(filtered[:limit])

        except Exception as e:
            last_error = e
            if "429" not in str(e) and attempt < MAX_RETRIES - 1:
                # Erro de rede — tenta de novo com backoff menor
                time.sleep(RETRY_DELAYS[0])
                continue
            raise

    raise last_error


def _format_authors(authors: List[Dict]) -> str:
    """Formata lista de autores para o padrão ABNT."""
    if not authors:
        return "Autor desconhecido"
    names = [a.get("name", "") for a in authors[:3]]
    if len(authors) > 3:
        names.append("et al.")
    return "; ".join(names)


def _format_abnt(paper: Dict) -> str:
    """Gera referência ABNT a partir dos metadados do artigo."""
    authors_raw = paper.get("authors", [])
    authors = _format_authors(authors_raw)
    title = paper.get("title", "Título desconhecido")
    year = paper.get("year", "s.d.")
    venue = paper.get("venue", "Publicação Científica")
    doi = (paper.get("externalIds") or {}).get("DOI", "")

    ref = f"{authors}. **{title}**. {venue}, {year}."
    if doi:
        ref += f" DOI: {doi}."
    return ref


def _format_papers(papers_raw: List[Dict]) -> List[Dict[str, Any]]:
    """Normaliza os dados dos artigos para o formato interno do pipeline."""
    result = []
    for p in papers_raw:
        doi = (p.get("externalIds") or {}).get("DOI", "")
        pdf_url = (p.get("openAccessPdf") or {}).get("url", "")
        url = p.get("url") or (f"https://doi.org/{doi}" if doi else "")

        result.append({
            "id": p.get("paperId", ""),
            "title": p.get("title", "Título desconhecido"),
            "authors": _format_authors(p.get("authors", [])),
            "authors_raw": p.get("authors", []),
            "year": p.get("year", "s.d."),
            "abstract": p.get("abstract", ""),
            "citation_count": p.get("citationCount", 0),
            "venue": p.get("venue", ""),
            "doi": doi,
            "url": url,
            "pdf_url": pdf_url,
            "abnt_reference": _format_abnt(p),
        })

    return result
