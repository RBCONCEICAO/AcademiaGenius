"""
multi_source_search.py
Busca paralela nas bases acadêmicas prioritárias:
  SEMPRE: OpenAlex + SciELO + BDTD + Crossref
  SAÚDE:  + PubMed
  EXATAS/IA: + arXiv
  OPCIONAL: + CORE + Semantic Scholar + Repositórios Universitários BR
"""

import re
import time
import logging
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Repositórios universitários brasileiros (OAI-PMH)
# ---------------------------------------------------------------------------

UNIVERSITY_REPOSITORIES = {
    "USP":     "https://repositorio.usp.br/oai/request",
    "UNICAMP": "https://repositorio.unicamp.br/oai/request",
    "UFRJ":    "https://pantheon.ufrj.br/oai/request",
    "UNESP":   "https://repositorio.unesp.br/oai/request",
    "UFMG":    "https://repositorio.ufmg.br/oai/request",
    "UFSC":    "https://repositorio.ufsc.br/oai/request",
    "UFRGS":   "https://lume.ufrgs.br/oai/request",
    "UFPE":    "https://repositorio.ufpe.br/oai/request",
    "FIOCRUZ": "https://www.arca.fiocruz.br/oai/request",
    "FGV":     "https://bibliotecadigital.fgv.br/oai/request",
    "PUC-Rio": "https://www.maxwell.vrac.puc-rio.br/oai/request",
}

# ---------------------------------------------------------------------------
# Seleção de bases por área — combinação validada
# ---------------------------------------------------------------------------
# Regra base (SEMPRE presentes): openalex, scielo, bdtd, crossref
# Regra por área: adiciona pubmed (saúde) ou arxiv (exatas/IA)

BASE_SOURCES = ["openalex", "scielo", "bdtd", "crossref"]

AREA_TO_SOURCES = {
    "saude":      BASE_SOURCES + ["pubmed"],
    "computacao": BASE_SOURCES + ["arxiv", "semantic_scholar"],
    "educacao":   BASE_SOURCES + ["eric_crossref"],
    "direito":    BASE_SOURCES,
    "economia":   BASE_SOURCES,
    "default":    BASE_SOURCES,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_html(text: str) -> str:
    """Remove tags HTML/XML de um texto sem usar ET (evita crashes com &)."""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", " ", text).strip()


def _make_paper(
    title: str,
    authors: str,
    year: Any,
    abstract: str,
    doi: str,
    url: str,
    citation_count: int,
    source: str,
    language: str = "en",
    is_open_access: bool = True,
) -> Dict[str, Any]:
    """Cria dicionário padronizado de artigo."""
    abnt = f"{authors}. {title}. {year}."
    if doi:
        abnt += f" DOI: {doi}."
    return {
        "title": title,
        "authors": authors,
        "year": year,
        "abstract": abstract,
        "doi": doi,
        "url": url,
        "citation_count": citation_count,
        "source": source,
        "language": language,
        "is_open_access": is_open_access,
        "abnt_reference": abnt,
    }


def _is_valid(paper: Dict) -> bool:
    """Retorna True se o artigo tem título e abstract mínimos."""
    return bool(paper.get("title")) and len(paper.get("abstract", "")) >= 80


# ---------------------------------------------------------------------------
# OpenAlex — 250M+ artigos, gratuita, ilimitada
# ---------------------------------------------------------------------------

def search_openalex(query: str, limit: int = 10) -> List[Dict]:
    results = []
    try:
        params = {
            "search": query,
            "per-page": min(limit, 25),
            "sort": "relevance_score:desc",
            "filter": "has_abstract:true",
            "mailto": "academiagenius@app.com",
        }
        r = requests.get("https://api.openalex.org/works", params=params, timeout=15)
        r.raise_for_status()
        for w in r.json().get("results", []):
            doi = (w.get("doi") or "").replace("https://doi.org/", "")
            # Reconstrói abstract do índice invertido
            inv = w.get("abstract_inverted_index") or {}
            if inv:
                word_map = {pos: word for word, positions in inv.items() for pos in positions}
                abstract = " ".join(word_map[i] for i in sorted(word_map))
            else:
                abstract = ""
            if len(abstract) < 80:
                continue
            authors_list = [
                a.get("author", {}).get("display_name", "")
                for a in w.get("authorships", [])[:3]
            ]
            authors = "; ".join(filter(None, authors_list)) or "Autor desconhecido"
            results.append(_make_paper(
                title=(w.get("title") or "").strip(),
                authors=authors,
                year=w.get("publication_year"),
                abstract=abstract,
                doi=doi,
                url=w.get("id", ""),
                citation_count=w.get("cited_by_count", 0),
                source="OpenAlex",
                is_open_access=w.get("open_access", {}).get("is_oa", False),
            ))
    except Exception as e:
        logger.warning("OpenAlex error: %s", e)
    return results


# ---------------------------------------------------------------------------
# SciELO — periódicos brasileiros/latinoamericanos
# ---------------------------------------------------------------------------

def search_scielo(query: str, limit: int = 10) -> List[Dict]:
    """
    Busca no SciELO via SOLR público. Tenta múltiplos endpoints por robustez.
    """
    results = []
    # Lista de endpoints SOLR/REST do SciELO — testa em ordem
    attempts = [
        {
            "url": "https://search.scielo.org/",
            "params": {"q": query, "count": min(limit, 15), "output": "json", "lang": "pt"},
            "headers": {"User-Agent": "AcademiaGenius/2.0", "Accept": "application/json"},
            "path": ["response", "docs"],
        },
        {
            "url": "https://api.scielo.org/api/v2/article/",
            "params": {"q": query, "limit": min(limit, 10), "offset": 0},
            "headers": {"User-Agent": "AcademiaGenius/2.0"},
            "path": ["objects"],
        },
    ]
    for attempt in attempts:
        try:
            r = requests.get(
                attempt["url"],
                params=attempt["params"],
                headers=attempt["headers"],
                timeout=15,
            )
            if r.status_code in (403, 404, 500):
                continue
            r.raise_for_status()
            data = r.json()
            # Navega no path esperado
            docs = data
            for key in attempt["path"]:
                docs = docs.get(key, []) if isinstance(docs, dict) else []
            for hit in (docs or []):
                ab_field = hit.get("ab") or hit.get("abstract", "")
                if isinstance(ab_field, dict):
                    abstract_parts = ab_field.get("en") or ab_field.get("pt") or []
                    abstract = " ".join(abstract_parts) if isinstance(abstract_parts, list) else str(abstract_parts)
                else:
                    abstract = str(ab_field)
                if len(abstract) < 80:
                    continue
                ti_field = hit.get("ti") or hit.get("title", "")
                if isinstance(ti_field, dict):
                    title_val = ti_field.get("en") or ti_field.get("pt") or [""]
                    title = title_val[0] if isinstance(title_val, list) else str(title_val)
                else:
                    title = str(ti_field)
                authors = "; ".join((hit.get("au") or hit.get("authors", []))[:3]) or "Autor desconhecido"
                doi = hit.get("doi", "")
                year_raw = hit.get("dp") or hit.get("publication_date", "")
                year = str(year_raw).split("-")[0] if year_raw else None
                results.append(_make_paper(
                    title=title, authors=authors, year=year, abstract=abstract,
                    doi=doi, url=hit.get("id", f"https://doi.org/{doi}" if doi else ""),
                    citation_count=0, source="SciELO", language="pt",
                ))
            if results:
                break
        except Exception as e:
            logger.warning("SciELO error (%s): %s", attempt["url"], e)
    return results


# ---------------------------------------------------------------------------
# BDTD / IBICT — teses e dissertações brasileiras (OAI-PMH correto)
# ---------------------------------------------------------------------------

def search_bdtd(query: str, limit: int = 10) -> List[Dict]:
    """
    Busca na BDTD. Tenta o endpoint OAI-PMH correto da IBICT.
    """
    return _search_bdtd_oai(query, limit)


def _search_bdtd_oai(query: str, limit: int) -> List[Dict]:
    """Busca OAI-PMH na BDTD com filtragem por keyword."""
    results = []
    # Endpoints OAI-PMH conhecidos da BDTD/IBICT
    oai_urls = [
        "https://bdtd.ibict.br/vufind/OAI/Server",
        "https://oasisbr.ibict.br/vufind/OAI/Server",
    ]
    for oai_url in oai_urls:
        try:
            params = {"verb": "ListRecords", "metadataPrefix": "oai_dc"}
            r = requests.get(
                oai_url, params=params,
                headers={"User-Agent": "AcademiaGenius/2.0 (contact@academiagenius.app)"},
                timeout=25,
            )
            if r.status_code != 200:
                logger.warning("BDTD OAI %s returned %s", oai_url, r.status_code)
                continue
            # Verifica que é XML
            if not r.content.lstrip()[:5] in (b"<?xml", b"<OAI-"):
                logger.warning("BDTD %s não retornou XML válido", oai_url)
                continue
            ns = {
                "oai":    "http://www.openarchives.org/OAI/2.0/",
                "dc":     "http://purl.org/dc/elements/1.1/",
                "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
            }
            root = ET.fromstring(r.content)
            q_tokens = set(t for t in query.lower().split() if len(t) > 3)
            for record in root.findall(".//oai:record", ns):
                meta = record.find(".//oai_dc:dc", ns)
                if meta is None:
                    continue
                title = meta.findtext("dc:title", "", ns)
                abstract = meta.findtext("dc:description", "", ns)
                combined = (title + " " + abstract).lower()
                matches = sum(1 for t in q_tokens if t in combined)
                if matches < 2 or len(abstract) < 80:
                    continue
                creator = meta.findtext("dc:creator", "Autor desconhecido", ns)
                date = (meta.findtext("dc:date", "", ns) or "")[:4]
                identifier = meta.findtext("dc:identifier", "", ns) or ""
                results.append(_make_paper(
                    title=title, authors=creator, year=date, abstract=abstract,
                    doi="", url=identifier, citation_count=0,
                    source="BDTD", language="pt",
                ))
                if len(results) >= limit:
                    break
            if results:
                break
        except ET.ParseError as e:
            logger.warning("BDTD XML parse error (%s): %s", oai_url, e)
        except Exception as e:
            logger.warning("BDTD OAI error (%s): %s", oai_url, e)
    return results




# ---------------------------------------------------------------------------
# PubMed — saúde e biomedicina (NCBI E-utilities)
# ---------------------------------------------------------------------------

def search_pubmed(query: str, limit: int = 10, api_key: Optional[str] = None) -> List[Dict]:
    results = []
    try:
        base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        search_params: Dict[str, Any] = {
            "db": "pubmed", "term": query,
            "retmax": min(limit, 20), "sort": "relevance", "retmode": "json",
        }
        if api_key:
            search_params["api_key"] = api_key
        r = requests.get(f"{base}/esearch.fcgi", params=search_params, timeout=15)
        r.raise_for_status()
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        time.sleep(0.35)  # respeita rate limit NCBI
        fetch_params: Dict[str, Any] = {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}
        if api_key:
            fetch_params["api_key"] = api_key
        rf = requests.get(f"{base}/efetch.fcgi", params=fetch_params, timeout=20)
        rf.raise_for_status()
        root = ET.fromstring(rf.content)
        for article in root.findall(".//PubmedArticle"):
            title = article.findtext(".//ArticleTitle") or ""
            abstract = " ".join(
                (t.text or "") for t in article.findall(".//AbstractText")
            )
            if len(abstract) < 80:
                continue
            authors = "; ".join(
                f"{a.findtext('LastName', '')} {a.findtext('ForeName', '')}".strip()
                for a in article.findall(".//Author")[:3]
            ) or "Autor desconhecido"
            year = (
                article.findtext(".//PubDate/Year")
                or (article.findtext(".//PubDate/MedlineDate") or "")[:4]
            )
            doi = article.findtext(".//ArticleId[@IdType='doi']") or ""
            pmid = article.findtext(".//ArticleId[@IdType='pubmed']") or ""
            results.append(_make_paper(
                title=title, authors=authors, year=year, abstract=abstract,
                doi=doi, url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                citation_count=0, source="PubMed",
            ))
    except Exception as e:
        logger.warning("PubMed error: %s", e)
    return results


# ---------------------------------------------------------------------------
# arXiv — preprints Física, Matemática, CS, IA
# ---------------------------------------------------------------------------

def search_arxiv(query: str, limit: int = 10) -> List[Dict]:
    results = []
    try:
        time.sleep(3)  # arXiv exige respeito ao rate limit: min 3s entre chamadas
        params = {
            "search_query": f"all:{query}",
            "max_results": min(limit, 15),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        r = requests.get("https://export.arxiv.org/api/query", params=params, timeout=20)
        r.raise_for_status()
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(r.content)
        for entry in root.findall("atom:entry", ns):
            abstract = (entry.findtext("atom:summary", "", ns) or "").strip()
            abstract = re.sub(r"\s+", " ", abstract)
            if len(abstract) < 80:
                continue
            title = (entry.findtext("atom:title", "", ns) or "").strip()
            authors = "; ".join(
                a.findtext("atom:name", "", ns)
                for a in entry.findall("atom:author", ns)[:3]
            ) or "Autor desconhecido"
            published = (entry.findtext("atom:published", "", ns) or "")[:4]
            arxiv_id = (entry.findtext("atom:id", "", ns) or "").split("/abs/")[-1]
            results.append(_make_paper(
                title=title, authors=authors, year=published, abstract=abstract,
                doi=f"10.48550/arXiv.{arxiv_id}",
                url=f"https://arxiv.org/abs/{arxiv_id}",
                citation_count=0, source="arXiv",
            ))
    except Exception as e:
        logger.warning("arXiv error: %s", e)
    return results


# ---------------------------------------------------------------------------
# Crossref — 150M+ DOIs com metadados ricos
# ---------------------------------------------------------------------------

def search_crossref(query: str, limit: int = 10) -> List[Dict]:
    results = []
    try:
        params = {
            "query": query,
            "rows": min(limit, 20),
            "sort": "relevance",
            "order": "desc",
            "select": "title,author,published,abstract,DOI,URL,is-referenced-by-count",
            "mailto": "academiagenius@app.com",
        }
        r = requests.get("https://api.crossref.org/works", params=params, timeout=15)
        r.raise_for_status()
        for item in r.json().get("message", {}).get("items", []):
            title_list = item.get("title") or []
            title = title_list[0] if title_list else ""
            abstract = _strip_html(item.get("abstract", ""))
            if not abstract or len(abstract) < 80:
                continue
            authors_raw = (item.get("author") or [])[:3]
            authors = "; ".join(
                f"{a.get('family', '')} {a.get('given', '')}".strip()
                for a in authors_raw
            ) or "Autor desconhecido"
            pub = (item.get("published") or {}).get("date-parts", [[None]])[0]
            year = pub[0] if pub else None
            doi = item.get("DOI", "")
            results.append(_make_paper(
                title=title, authors=authors, year=year, abstract=abstract,
                doi=doi,
                url=item.get("URL", f"https://doi.org/{doi}"),
                citation_count=item.get("is-referenced-by-count", 0),
                source="Crossref",
            ))
    except Exception as e:
        logger.warning("Crossref error: %s", e)
    return results


# ---------------------------------------------------------------------------
# CORE — 200M+ artigos open access (opcional, requer key gratuita)
# ---------------------------------------------------------------------------

def search_core(query: str, limit: int = 10, api_key: Optional[str] = None) -> List[Dict]:
    if not api_key:
        return []  # sem key o CORE retorna 401
    results = []
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {"q": query, "limit": min(limit, 10), "offset": 0}
        r = requests.post(
            "https://api.core.ac.uk/v3/search/works",
            json=payload, headers=headers, timeout=15,
        )
        r.raise_for_status()
        for w in r.json().get("results", []):
            abstract = w.get("abstract") or ""
            if len(abstract) < 80:
                continue
            authors = "; ".join(
                a.get("name", "") for a in (w.get("authors") or [])[:3]
            ) or "Autor desconhecido"
            doi = (w.get("doi") or "").replace("https://doi.org/", "")
            urls = w.get("sourceFulltextUrls") or []
            url = w.get("downloadUrl") or (urls[0] if urls else "")
            results.append(_make_paper(
                title=w.get("title", ""), authors=authors,
                year=w.get("yearPublished"), abstract=abstract,
                doi=doi, url=url, citation_count=0, source="CORE",
            ))
    except Exception as e:
        logger.warning("CORE error: %s", e)
    return results


# ---------------------------------------------------------------------------
# Semantic Scholar — wrapper sobre search_agent existente
# ---------------------------------------------------------------------------

def _search_semantic_scholar(query: str, limit: int, api_key: Optional[str]) -> List[Dict]:
    try:
        from app.agents.search_agent import search_papers
        papers = search_papers(query=query, limit=limit, api_key=api_key)
        for p in papers:
            p.setdefault("source", "Semantic Scholar")
        return papers
    except Exception as e:
        logger.warning("Semantic Scholar error: %s", e)
        return []


# ---------------------------------------------------------------------------
# Repositórios universitários brasileiros (OAI-PMH)
# ---------------------------------------------------------------------------

def search_university_oai(query: str, university: str, endpoint: str, limit: int = 5) -> List[Dict]:
    results = []
    try:
        params = {
            "verb": "ListRecords",
            "metadataPrefix": "oai_dc",
        }
        r = requests.get(endpoint, params=params, timeout=12)
        if r.status_code != 200:
            return []
        ns = {
            "oai":    "http://www.openarchives.org/OAI/2.0/",
            "dc":     "http://purl.org/dc/elements/1.1/",
            "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
        }
        root = ET.fromstring(r.content)
        q_lower = query.lower()
        for record in root.findall(".//oai:record", ns):
            meta = record.find(".//oai_dc:dc", ns)
            if meta is None:
                continue
            title = meta.findtext("dc:title", "", ns)
            abstract = meta.findtext("dc:description", "", ns)
            if q_lower not in (title + abstract).lower():
                continue
            if not title or len(abstract) < 60:
                continue
            creator = meta.findtext("dc:creator", "Autor desconhecido", ns)
            date = meta.findtext("dc:date", "", ns)[:4]
            identifier = meta.findtext("dc:identifier", "", ns)
            results.append(_make_paper(
                title=title, authors=creator, year=date, abstract=abstract,
                doi="", url=identifier, citation_count=0,
                source=f"Repositório {university}", language="pt",
            ))
            if len(results) >= limit:
                break
    except Exception as e:
        logger.warning("OAI %s error: %s", university, e)
    return results


# ---------------------------------------------------------------------------
# Deduplicação por DOI e título
# ---------------------------------------------------------------------------

def _deduplicate(papers: List[Dict]) -> List[Dict]:
    seen_dois: set = set()
    seen_titles: set = set()
    unique = []
    for p in papers:
        doi = (p.get("doi") or "").strip().lower()
        title = (p.get("title") or "").strip().lower()[:90]
        if doi and doi in seen_dois:
            continue
        if title and title in seen_titles:
            continue
        if doi:
            seen_dois.add(doi)
        if title:
            seen_titles.add(title)
        unique.append(p)
    return unique


# ---------------------------------------------------------------------------
# Função principal — busca multi-fonte paralela validada
# ---------------------------------------------------------------------------

def multi_source_search(
    query: str,
    query_en: Optional[str] = None,
    area: str = "default",
    limit_per_source: int = 10,
    include_universities: bool = True,
    pubmed_key: Optional[str] = None,
    core_key: Optional[str] = None,
    semantic_scholar_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Busca paralela nas bases acadêmicas prioritárias.

    Combinação validada (sempre presente):
      OpenAlex + SciELO + BDTD + Crossref

    Adicionais por área:
      saúde      → + PubMed
      computação → + arXiv + Semantic Scholar
      default    → as 4 bases acima

    Args:
        query:                Tema (PT-BR) — usado em SciELO, BDTD e repositórios BR
        query_en:             Tema em inglês — usado em OpenAlex, PubMed, arXiv, Crossref
        area:                 Área do conhecimento detectada pelo orchestrator
        limit_per_source:     Máximo de artigos por base
        include_universities: Incluir repositórios universitários BR via OAI-PMH
        pubmed_key:           NCBI API key (gratuita, aumenta rate limit)
        core_key:             CORE API key (gratuita, obrigatória para usar CORE)
        semantic_scholar_key: Semantic Scholar API key (gratuita)

    Returns:
        {query_info: {...}, papers: [...]}
    """
    q_en = query_en or query
    sources = AREA_TO_SOURCES.get(area, AREA_TO_SOURCES["default"])

    # Mapa de funções por identificador de fonte
    source_fns: Dict[str, Any] = {
        "openalex":        lambda: search_openalex(q_en, limit_per_source),
        "scielo":          lambda: search_scielo(query, limit_per_source),
        "bdtd":            lambda: search_bdtd(query, limit_per_source),
        "crossref":        lambda: search_crossref(q_en, limit_per_source),
        "pubmed":          lambda: search_pubmed(q_en, limit_per_source, pubmed_key),
        "arxiv":           lambda: search_arxiv(q_en, limit_per_source),
        "core":            lambda: search_core(q_en, limit_per_source, core_key),
        "semantic_scholar": lambda: _search_semantic_scholar(q_en, limit_per_source, semantic_scholar_key),
    }

    all_papers: List[Dict] = []
    sources_searched: List[str] = []

    # Execução paralela das fontes selecionadas — timeout amplo para comportar arXiv (3s delay)
    fns_to_run = {s: fn for s, fn in source_fns.items() if s in sources}
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_source = {executor.submit(fn): name for name, fn in fns_to_run.items()}
        try:
            for future in as_completed(future_to_source, timeout=90):
                name = future_to_source[future]
                try:
                    papers = future.result()
                    if papers:
                        all_papers.extend(papers)
                        sources_searched.append(name)
                        logger.info("%-20s → %d artigos", name, len(papers))
                    else:
                        logger.info("%-20s → 0 artigos (sem resultados)", name)
                except Exception as e:
                    logger.warning("Fonte %s falhou: %s", name, e)
        except Exception as e:
            logger.warning("Timeout ou erro global na busca principal. Prosseguindo com os resultados encontrados. Erro: %s", e)

    # Repositórios universitários BR (paralelo, timeout agressivo)
    if include_universities:
        with ThreadPoolExecutor(max_workers=5) as executor:
            uni_futures = {
                executor.submit(search_university_oai, query, uni, endpoint, 4): uni
                for uni, endpoint in UNIVERSITY_REPOSITORIES.items()
            }
            try:
                for future in as_completed(uni_futures, timeout=30):
                    uni = uni_futures[future]
                    try:
                        papers = future.result()
                        if papers:
                            all_papers.extend(papers)
                            logger.info("Repositório %-10s → %d artigos", uni, len(papers))
                    except Exception:
                        pass
            except Exception as e:
                logger.warning("Timeout ou erro global na busca de repositórios. Erro: %s", e)

    # Filtro de qualidade, deduplicação e ordenação
    filtered = [p for p in all_papers if _is_valid(p)]
    unique = _deduplicate(filtered)
    unique.sort(key=lambda p: p.get("citation_count", 0), reverse=True)

    logger.info(
        "multi_source_search: bruto=%d | válidos=%d | únicos=%d | fontes=%s",
        len(all_papers), len(filtered), len(unique), sources_searched,
    )

    return {
        "query_info": {
            "original_query": query,
            "query_en": q_en,
            "area": area,
            "sources_searched": sources_searched,
            "total_raw": len(all_papers),
            "after_filter": len(unique),
        },
        "papers": unique,
    }
