"""
llm.py — Roteador de LLMs do AcademiaGenius
Suporta: Gemini · OpenAI · Anthropic · Groq · Mistral
Modo Pipeline: diferentes LLMs por etapa para máxima velocidade + qualidade.
"""
import re
import json
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Você é um especialista em pesquisa e redação acadêmica científica de alto nível. "
    "Sempre redija em Português do Brasil seguindo rigorosamente as normas ABNT. "
    "Seja objetivo, denso em informação e use linguagem técnica adequada ao nível acadêmico."
)

# ── Capacidades por provedor ──────────────────────────────────────────────────
PROVIDER_META = {
    "gemini":    {"name": "Google Gemini",  "speed": "fast",      "quality": "high"},
    "openai":    {"name": "OpenAI",         "speed": "medium",    "quality": "highest"},
    "anthropic": {"name": "Anthropic",      "speed": "medium",    "quality": "highest"},
    "groq":      {"name": "Groq",           "speed": "ultra",     "quality": "medium"},
    "mistral":   {"name": "Mistral AI",     "speed": "fast",      "quality": "high"},
}


# ── Gemini ────────────────────────────────────────────────────────────────────
def call_gemini(api_key: str, model: str, prompt: str, _task: str = "") -> str:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    
    def _do_call(m: str):
        return client.models.generate_content(
            model=m,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            ),
        ).text

    try:
        return _do_call(model)
    except Exception as e:
        error_msg = str(e).upper()
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            fallback = "gemini-2.5-flash"
            if model != fallback:
                logger.warning(f"Gemini limit reached for {model}. Falling back to {fallback}.")
                return _do_call(fallback)
        raise e


# ── OpenAI ────────────────────────────────────────────────────────────────────
def call_openai(api_key: str, model: str, prompt: str, _task: str = "") -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content


# ── Anthropic ─────────────────────────────────────────────────────────────────
def call_anthropic(api_key: str, model: str, prompt: str, _task: str = "") -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ── Groq (ultra-rápido, OpenAI-compat) ───────────────────────────────────────
def call_groq(api_key: str, model: str, prompt: str, _task: str = "") -> str:
    """
    Groq usa a API compatível com OpenAI.
    Modelos: llama-3.3-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it
    """
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.7,
        max_tokens=8192,
    )
    return response.choices[0].message.content


# ── Mistral AI ────────────────────────────────────────────────────────────────
def call_mistral(api_key: str, model: str, prompt: str, _task: str = "") -> str:
    """
    Mistral usa API REST própria, compatível com OpenAI.
    Modelos: mistral-large-latest, mistral-small-latest, open-mixtral-8x22b
    """
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.mistral.ai/v1")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.7,
        max_tokens=8192,
    )
    return response.choices[0].message.content


# ── Dispatcher principal ──────────────────────────────────────────────────────

def _fb_section(prompt: str, label: str) -> str:
    """Extrai conteúdo de uma seção '**Label:** ...' do prompt."""
    m = re.search(rf'\*\*{re.escape(label)}[:\*\s]+\*?\*?(.+?)(?=\n\s*\*\*|\Z)', prompt, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else ""


def generate_free_fallback_content(_provider: str, _model: str, prompt: str, task: str = "") -> str:

    # 1. Tradução de termos para inglês
    if "search query" in prompt.lower() or "traduz-as para o inglês" in prompt.lower():
        theme_match = re.search(r"Tema:\s*(.*)", prompt, re.IGNORECASE)
        theme = theme_match.group(1).strip() if theme_match else ""
        # Remove pontuação, pega palavras significativas (>3 chars)
        words = [w for w in re.sub(r'[^\w\s]', ' ', theme).split() if len(w) > 3]
        return " ".join(words[:7]) or "academic research"

    # 2. Perguntas de esclarecimento
    elif "perguntas de esclarecimento" in prompt.lower() or "orientador científico" in prompt.lower():
        theme_match = re.search(r'tema:\s*["\']?(.*?)["\']?\s*(?:\n|$)', prompt, re.IGNORECASE)
        theme = theme_match.group(1).strip() if theme_match else "o tema informado"
        return json.dumps({"questions": [
            {"id": 1, "question": f"Qual é o enfoque principal do trabalho sobre '{theme}'?",
             "type": "choice", "options": ["Revisão teórica e bibliográfica", "Estudo de caso aplicado", "Análise comparativa entre abordagens"]},
            {"id": 2, "question": "Qual contexto geográfico ou institucional deve ser priorizado?",
             "type": "choice", "options": ["Contexto brasileiro / nacional", "Abordagem internacional", "Sem restrição geográfica"]},
            {"id": 3, "question": "Deseja focar em publicações recentes ou incluir clássicos seminais?",
             "type": "choice", "options": ["Últimos 5 anos (2020–2025)", "Clássicos + recentes (sem limite)", "Sem restrição temporal"]},
        ]}, ensure_ascii=False)

    # 3. Filtro semântico — manter todos os papers (fallback conservador)
    elif "filtro semântico" in prompt.lower() or "validador de relevância" in prompt.lower():
        try:
            payload = json.loads(re.search(r'\[\s*\{.*?\}\s*\]', prompt, re.DOTALL).group(0))
            return json.dumps({"results": [
                {"id": p["id"], "decision": "keep", "reason": "Relevante ao domínio."}
                for p in payload
            ]}, ensure_ascii=False)
        except Exception:
            return json.dumps({"results": []}, ensure_ascii=False)

    # 4. Tradução de artigos — retorna títulos/abstracts originais sem prefixo falso
    elif "tradutor científico" in prompt.lower() or task == "traducao":
        try:
            payload = json.loads(re.search(r'\[\s*\{.*?\}\s*\]', prompt, re.DOTALL).group(0))
            return json.dumps([
                {"id": p["id"], "titulo_pt": p.get("title", ""), "resumo_pt": p.get("abstract", "")[:600]}
                for p in payload
            ], ensure_ascii=False)
        except Exception:
            return json.dumps([], ensure_ascii=False)

    # 5. Extração de conhecimento — usa títulos/abstracts reais do prompt
    elif task == "extracao" or "revisão sistemática" in prompt.lower():
        titles   = re.findall(r'Título[:\s]+(.+?)(?:\n|$)',   prompt, re.IGNORECASE)
        abstracts = re.findall(r'Abstract[:\s]+(.+?)(?:\n{2,}|\Z)', prompt, re.IGNORECASE | re.DOTALL)
        all_text = " ".join(titles + [a[:300] for a in abstracts])
        # Extrai substantivos capitalizados como proxy de temas
        words = re.findall(r'\b[A-ZÁÉÍÓÚÀÃÕÂÊÔÇ][a-záéíóúàãõâêôç]{4,}\b', all_text)
        freq: dict = {}
        for w in words:
            freq[w.lower()] = freq.get(w.lower(), 0) + 1
        top = sorted(freq, key=lambda x: -freq[x])
        temas = top[:3] if top else ["análise teórica", "revisão bibliográfica", "metodologia"]
        mets  = top[3:6] if len(top) > 3 else ["revisão sistemática", "análise qualitativa"]
        n = len(titles)
        return json.dumps({
            "temas_principais": temas,
            "metodologias_identificadas": mets,
            "principais_achados": [
                f"Evidências de relevância identificadas em {n} publicações científicas.",
                f"Convergência metodológica em torno de {temas[0] if temas else 'abordagens sistemáticas'}.",
            ],
            "lacunas_pesquisa": [
                "Necessidade de estudos empíricos complementares na área.",
                "Escassez de dados longitudinais para validação dos modelos propostos.",
            ],
            "consensos": f"A literatura converge sobre a centralidade de {temas[0] if temas else 'abordagens integradas'} no avanço do campo.",
            "divergencias": "Persistem debates sobre as metodologias mais adequadas e seus limites de generalização.",
            "sintese_geral": f"O conjunto de {n} artigos revisados revela um campo em desenvolvimento ativo, com oportunidades claras de aprofundamento.",
        }, ensure_ascii=False)

    # 6. Redação acadêmica — usa referências e conhecimento reais extraídos do prompt
    else:
        theme_match = re.search(r"tema:\s*\*\*?(.*?)\*\*?", prompt, re.IGNORECASE)
        theme = theme_match.group(1).strip() if theme_match else "Pesquisa Acadêmica"

        # Referências reais do bloco "Fontes Reais Disponíveis"
        ref_matches = re.findall(r'- \[(\d+)\] (.+?) \(Citações:', prompt)
        n_refs = len(ref_matches)
        ref_list = "\n".join(f"{num}. {ref}" for num, ref in ref_matches)

        # Conhecimento extraído (seções reais do prompt)
        temas        = _fb_section(prompt, "Temas principais")
        metodologias = _fb_section(prompt, "Metodologias")
        achados_raw  = _fb_section(prompt, "Principais achados")
        lacunas_raw  = _fb_section(prompt, "Lacunas de pesquisa")
        sintese      = _fb_section(prompt, "Síntese e Consensos")

        achados = [l.lstrip("- ").strip() for l in achados_raw.splitlines() if l.strip().startswith("-")]
        lacunas = [l.lstrip("- ").strip() for l in lacunas_raw.splitlines() if l.strip().startswith("-")]
        cit1 = f"[{ref_matches[0][0]}]" if ref_matches else ""
        cit2 = f"[{ref_matches[1][0]}]" if len(ref_matches) > 1 else cit1

        achados_block = "\n".join(f"- {a}" for a in achados[:3]) or f"- Evidências relevantes identificadas nas {n_refs} fontes revisadas."
        lacunas_block = "\n".join(f"- {l}" for l in lacunas[:2]) or "- Necessidade de estudos empíricos complementares."

        return f"""# {theme.upper()}

## RESUMO
Esta pesquisa analisa **{theme}**, fundamentada em {n_refs} artigos científicos indexados. Os principais eixos temáticos identificados foram: {temas or theme}. {(sintese[:250] + ".") if sintese else "A revisão sistemática conduzida permitiu consolidar o estado da arte e identificar as principais lacunas da área."}

**Palavras-chave:** {", ".join(t.strip() for t in (temas or theme).split(",")[:4])}.

---

## 1. INTRODUÇÃO
O campo de **{theme}** constitui uma área de relevância crescente no contexto acadêmico e prático. A presente investigação parte da seguinte questão: *Qual é o estado da arte, as metodologias predominantes e as lacunas identificadas na literatura sobre {theme.lower()}?*

A justificativa reside na necessidade de consolidação do conhecimento disponível. Com base em {n_refs} fontes científicas selecionadas por critérios de pertinência temática e impacto bibliométrico {cit1}, esta pesquisa busca contribuir para o avanço da área.

---

## 2. REFERENCIAL TEÓRICO
{temas or f"A literatura sobre {theme.lower()} abrange múltiplas perspectivas teóricas e metodológicas."}

As principais abordagens metodológicas identificadas {cit1} incluem: {metodologias or "revisão sistemática, análise qualitativa e estudos de caso aplicados"}.

---

## 3. METODOLOGIA
A presente investigação adotou revisão sistemática de literatura como método central. As bases consultadas incluíram Semantic Scholar, OpenAlex, PubMed, BDTD e SciELO, resultando em {n_refs} artigos selecionados por relevância temática e rigor científico.

---

## 4. RESULTADOS E DISCUSSÃO
A análise das publicações revisadas {cit2} revelou os seguintes achados:

{achados_block}

---

## 5. CONSIDERAÇÕES FINAIS
{(sintese[:400] + ".") if sintese else f"A investigação sobre {theme.lower()} com base em {n_refs} fontes científicas permitiu consolidar o estado da arte da área."}

Lacunas identificadas para pesquisas futuras:
{lacunas_block}

---

## REFERÊNCIAS
{ref_list or "Referências não disponíveis."}
"""

CALLERS = {
    "gemini":    call_gemini,
    "openai":    call_openai,
    "anthropic": call_anthropic,
    "groq":      call_groq,
    "mistral":   call_mistral,
}


def call_llm(provider: str, model: str, api_key: str, prompt: str, task: str = "") -> str:
    """
    Ponto de entrada unificado. Roteia para o provedor correto.

    Args:
        provider: 'gemini' | 'openai' | 'anthropic' | 'groq' | 'mistral'
        model:    ID do modelo específico
        api_key:  Chave do provedor
        prompt:   Prompt completo
        task:     Rótulo da tarefa ('extracao' | 'redacao') para logging
    """
    if api_key == "FREE_FALLBACK":
        return generate_free_fallback_content(provider, model, prompt, task)

    caller = CALLERS.get(provider)
    if not caller:
        raise ValueError(f"Provedor '{provider}' não suportado. Use: {list(CALLERS.keys())}")

    meta = PROVIDER_META.get(provider, {})
    logger.info("LLM call | provider=%-10s model=%-40s task=%s speed=%s",
                provider, model, task or "geral", meta.get("speed", "?"))
    return caller(api_key, model, prompt, task)


# ── Modo Pipeline Multi-LLM ───────────────────────────────────────────────────
def call_llm_pipeline(
    fast_provider: str, fast_model: str, fast_key: str,
    quality_provider: str, quality_model: str, quality_key: str,
    extraction_prompt: str,
    writing_prompt: str,
) -> tuple[str, str]:
    """
    Executa o pipeline com dois LLMs diferentes:
      - fast_*:    LLM rápido (ex: Groq) para extração de conhecimento
      - quality_*: LLM de qualidade (ex: Gemini Pro, GPT-4o) para redação final

    Returns:
        (knowledge_text, document_text)
    """
    logger.info("Pipeline: extração=%s/%s  redação=%s/%s",
                fast_provider, fast_model, quality_provider, quality_model)

    knowledge = call_llm(fast_provider, fast_model, fast_key, extraction_prompt, "extracao")
    document  = call_llm(quality_provider, quality_model, quality_key, writing_prompt, "redacao")
    return knowledge, document


# ── Endpoint legado ───────────────────────────────────────────────────────────
def _build_legacy_prompt(theme: str, doc_type: str) -> str:
    label = {"tcc": "Monografia/TCC", "artigo": "Artigo Científico",
             "estudo": "Estudo de Caso"}.get(doc_type, "Documento Científico")
    return (
        f"Escreva o esboço detalhado de um(a) {label} sobre o seguinte tema:\n\n"
        f"**{theme}**\n\n"
        f"Inclua: Introdução, Referencial Teórico (com pelo menos 3 autores citados em ABNT), "
        f"Metodologia, Resultados Esperados e Conclusão. "
        f"Seja específico e use parágrafos completos para cada seção."
    )


def generate(provider: str, model: str, api_key: str, theme: str, doc_type: str) -> str:
    """Ponto de entrada para o endpoint legado /api/v1/generate."""
    prompt = _build_legacy_prompt(theme, doc_type)
    return call_llm(provider, model, api_key, prompt, "legado")
