#!/usr/bin/env python3
"""
test_pipeline.py
Testa o fluxo completo do AcademiaGenius sem precisar subir o servidor:
  Detecta Área → Seleciona Bases → Busca Paralela →
  Deduplica → Filtra → Extrator LLM → Redator LLM → DOCX

As API Keys são lidas automaticamente do arquivo .env na raiz do projeto.
"""

import os
import sys
import json
import time

# Garante que o Python encontra os módulos da api/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api"))


def _load_env(env_path: str) -> None:
    """Carrega variáveis do .env sem depender de python-dotenv."""
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            if key.strip() and value:
                os.environ.setdefault(key.strip(), value)


# Carrega o .env da raiz do projeto
_load_env(os.path.join(os.path.dirname(__file__), ".env"))

# ── Configuração do Teste ─────────────────────────────────────────────────
TEMA        = "Inteligência Artificial na Educação Básica"
DOC_TYPE    = "artigo"
NORM        = "ABNT"
PAPER_LIMIT = 6

# Lê as keys do .env (ou deixa vazio para pular as etapas de LLM)
LLM_PROVIDER = "gemini"                          # gemini | openai | anthropic
LLM_MODEL    = "gemini-2.5-flash-preview-04-17"  # modelo padrão
LLM_API_KEY  = os.environ.get("GEMINI_API_KEY", "")

INCLUDE_UNIVERSITIES = False  # True = mais lento mas mais completo


# ── Cores para terminal ───────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):    print(f"  {GREEN}✓{RESET} {msg}")
def warn(msg):  print(f"  {YELLOW}⚠{RESET} {msg}")
def fail(msg):  print(f"  {RED}✗{RESET} {msg}")
def step(n, msg): print(f"\n{BOLD}{CYAN}[ETAPA {n}]{RESET} {BOLD}{msg}{RESET}")
def info(msg):  print(f"    {msg}")


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 0 — Detectar Área
# ═══════════════════════════════════════════════════════════════════════════
step(0, "Detectar Área do Tema")
from app.agents.orchestrator import detect_area

area = detect_area(TEMA)
ok(f"Área detectada: '{area}'")

from app.agents.multi_source_search import AREA_TO_SOURCES
bases = AREA_TO_SOURCES.get(area, AREA_TO_SOURCES["default"])
ok(f"Bases selecionadas: {bases}")


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 1 — Busca Multi-Fonte Paralela
# ═══════════════════════════════════════════════════════════════════════════
step(1, f"Busca Paralela — tema: '{TEMA}'")

from app.agents.multi_source_search import (
    multi_source_search,
    search_openalex, search_scielo, search_bdtd,
    search_pubmed, search_arxiv, search_crossref,
)

# Testa cada fonte individualmente primeiro
print(f"\n  {BOLD}Testando fontes individualmente:{RESET}")

sources_individual = [
    ("OpenAlex",  lambda: search_openalex(TEMA, 3)),
    ("SciELO",    lambda: search_scielo(TEMA, 3)),
    ("BDTD",      lambda: search_bdtd(TEMA, 3)),
    ("Crossref",  lambda: search_crossref(TEMA, 3)),
    ("arXiv",     lambda: search_arxiv("Artificial Intelligence Basic Education", 3)),
    ("PubMed",    lambda: search_pubmed("Artificial Intelligence Basic Education", 3)),
]

source_results = {}
for name, fn in sources_individual:
    t0 = time.time()
    try:
        papers = fn()
        elapsed = time.time() - t0
        source_results[name] = papers
        if papers:
            ok(f"{name:<12} → {len(papers)} artigos ({elapsed:.1f}s)")
            for p in papers[:2]:
                info(f"  • [{p['source']}] {p['title'][:65]}... ({p['year']})")
        else:
            warn(f"{name:<12} → 0 artigos ({elapsed:.1f}s) — sem resultados")
    except Exception as e:
        elapsed = time.time() - t0
        fail(f"{name:<12} → ERRO ({elapsed:.1f}s): {e}")
        source_results[name] = []

# Agora testa a busca paralela completa
print(f"\n  {BOLD}Executando busca paralela completa:{RESET}")
t0 = time.time()
try:
    result = multi_source_search(
        query=TEMA,
        query_en="Artificial Intelligence Basic Education",
        area=area,
        limit_per_source=PAPER_LIMIT,
        include_universities=INCLUDE_UNIVERSITIES,
    )
    elapsed = time.time() - t0
    papers = result["papers"]
    qi = result["query_info"]

    ok(f"Busca completa em {elapsed:.1f}s")
    info(f"Bruto: {qi['total_raw']} | Após filtro: {qi['after_filter']} | Únicos: {len(papers)}")
    info(f"Fontes que retornaram: {qi['sources_searched']}")
except Exception as e:
    fail(f"Busca paralela falhou: {e}")
    sys.exit(1)

if not papers:
    fail("Nenhum artigo encontrado! Verifique conectividade.")
    sys.exit(1)

ok(f"Pipeline continuará com {len(papers)} artigos")


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 2 — Validação de Qualidade dos Papers
# ═══════════════════════════════════════════════════════════════════════════
step(2, "Validação de Qualidade e Deduplicação")

campos_obrigatorios = ["title", "authors", "year", "abstract", "source", "abnt_reference"]
problemas = 0
for i, p in enumerate(papers):
    for campo in campos_obrigatorios:
        if not p.get(campo):
            warn(f"Artigo {i+1}: campo '{campo}' ausente ou vazio")
            problemas += 1

# Verifica distribuição por fonte
from collections import Counter
por_fonte = Counter(p["source"] for p in papers)
ok("Distribuição por fonte:")
for fonte, qtd in por_fonte.most_common():
    info(f"  {fonte:<30} → {qtd} artigos")

# Verifica duplicatas restantes (não deveria ter)
dois_titulos = [p["title"][:80].lower() for p in papers]
duplicatas = len(dois_titulos) - len(set(dois_titulos))
if duplicatas:
    warn(f"{duplicatas} possíveis duplicatas de título ainda presentes")
else:
    ok("Sem duplicatas de título")

if problemas == 0:
    ok("Todos os campos obrigatórios presentes")
else:
    warn(f"{problemas} problema(s) encontrado(s) nos metadados")

# Mostra os top 3 artigos mais citados
print(f"\n  {BOLD}Top artigos encontrados:{RESET}")
for i, p in enumerate(papers[:3], 1):
    info(f"  {i}. [{p['source']}] {p['title'][:60]}...")
    info(f"     Autores: {p['authors'][:50]} | Ano: {p['year']} | Citações: {p['citation_count']}")
    info(f"     Abstract: {p['abstract'][:100]}...")
    info("")


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 3 — Extrator LLM (pula se sem API Key)
# ═══════════════════════════════════════════════════════════════════════════
step(3, "Extrator LLM — Base de Conhecimento")

knowledge = None
if not LLM_API_KEY:
    warn("LLM_API_KEY não configurada — pulando extração e redação.")
    warn("Configure LLM_PROVIDER, LLM_MODEL e LLM_API_KEY no script para testar.")
    info("Estrutura esperada do 'knowledge':")
    knowledge_mock = {
        "temas_principais": ["IA na educação", "aprendizagem adaptativa"],
        "metodologias_identificadas": ["revisão sistemática", "experimentos controlados"],
        "principais_achados": ["IA melhora engajamento", "resultados mistos em avaliação"],
        "lacunas_pesquisa": ["poucos estudos longitudinais", "contextos de baixa renda"],
        "consensos": "A maioria dos estudos aponta benefícios no engajamento.",
        "divergencias": "Há debate sobre eficácia em avaliações padronizadas.",
        "sintese_geral": "Estado da arte indica crescimento acelerado mas necessidade de mais evidências.",
    }
    info(json.dumps(knowledge_mock, ensure_ascii=False, indent=4))
    knowledge = knowledge_mock
else:
    try:
        from app.agents.extractor_agent import extract_knowledge
        t0 = time.time()
        knowledge = extract_knowledge(
            papers=papers[:PAPER_LIMIT],
            provider=LLM_PROVIDER,
            model=LLM_MODEL,
            api_key=LLM_API_KEY,
        )
        elapsed = time.time() - t0
        ok(f"Conhecimento extraído em {elapsed:.1f}s")
        info(f"Temas: {knowledge.get('temas_principais', [])}")
        info(f"Metodologias: {knowledge.get('metodologias_identificadas', [])}")
        info(f"Achados: {len(knowledge.get('principais_achados', []))} identificados")
        info(f"Lacunas: {knowledge.get('lacunas_pesquisa', [])}")
    except Exception as e:
        fail(f"Extrator falhou: {e}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 4 — Redator LLM (pula se sem API Key)
# ═══════════════════════════════════════════════════════════════════════════
step(4, "Redator LLM — Documento Acadêmico")

document = None
if not LLM_API_KEY:
    warn("Pulando redação (sem API Key).")
    document = f"[MOCK] Documento sobre {TEMA} seria gerado aqui com {len(papers)} fontes reais."
else:
    try:
        from app.agents.writer_agent import write_document
        t0 = time.time()
        document = write_document(
            theme=TEMA,
            doc_type=DOC_TYPE,
            papers=papers[:PAPER_LIMIT],
            knowledge=knowledge,
            provider=LLM_PROVIDER,
            model=LLM_MODEL,
            api_key=LLM_API_KEY,
            norm=NORM,
        )
        elapsed = time.time() - t0
        ok(f"Documento gerado em {elapsed:.1f}s ({len(document)} chars)")
        info(f"Prévia: {document[:200]}...")
    except Exception as e:
        fail(f"Redator falhou: {e}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 5 — Export DOCX
# ═══════════════════════════════════════════════════════════════════════════
step(5, "Export DOCX")

try:
    from app.services.docx_exporter import generate_docx
    t0 = time.time()
    docx_bytes = generate_docx(
        title=TEMA,
        content=document,
        norm=NORM,
    )
    elapsed = time.time() - t0
    output_path = "/tmp/academiagenius_test.docx"
    with open(output_path, "wb") as f:
        f.write(docx_bytes)
    ok(f"DOCX gerado em {elapsed:.1f}s → {len(docx_bytes):,} bytes")
    ok(f"Arquivo salvo em: {output_path}")
except Exception as e:
    fail(f"Export DOCX falhou: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# RESUMO FINAL
# ═══════════════════════════════════════════════════════════════════════════
print(f"\n{'═'*60}")
print(f"{BOLD}{GREEN}  RESULTADO DO TESTE{RESET}")
print(f"{'═'*60}")
print(f"  Tema:          {TEMA}")
print(f"  Área:          {area}")
print(f"  Bases usadas:  {', '.join(qi['sources_searched'])}")
print(f"  Papers brutos: {qi['total_raw']}")
print(f"  Papers únicos: {len(papers)}")
print(f"  Distribuição:  {dict(por_fonte.most_common())}")
if LLM_API_KEY:
    print(f"  Documento:     {len(document):,} caracteres")
else:
    print(f"  LLM:           não testado (configure API Key no script)")
print(f"{'═'*60}\n")
