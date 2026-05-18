"""
llm.py — Roteador de LLMs do AcademiaGenius
Suporta: Gemini · OpenAI · Anthropic · Groq · Mistral
Modo Pipeline: diferentes LLMs por etapa para máxima velocidade + qualidade.
"""
import os
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
    from google.genai.errors import APIError
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
