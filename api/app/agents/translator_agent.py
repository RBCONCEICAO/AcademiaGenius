import json
from typing import List, Dict, Any
from app.services.llm import call_llm

def translate_papers(
    papers: List[Dict[str, Any]],
    provider: str,
    model: str,
    api_key: str,
) -> List[Dict[str, Any]]:
    """
    Traduz os títulos e abstracts dos artigos encontrados para o Português do Brasil.
    Isso garante que o usuário e os próximos agentes trabalhem 100% em português.
    """
    if not papers:
        return papers

    # Prepara o payload para envio em lote (batch) para economizar tokens e tempo
    payload = []
    for i, p in enumerate(papers):
        # Apenas artigos em inglês (heurística simples ou assume-se todos de fontes internacionais)
        payload.append({
            "id": i,
            "title": p.get("title", ""),
            "abstract": p.get("abstract", "")[:500] + ("..." if len(p.get("abstract", "")) > 500 else "")
        })

    prompt = f"""Você é um Tradutor Científico Especializado.
Traduza os TÍTULOS e os ABSTRACTS dos artigos abaixo do Inglês para o Português do Brasil.
Mantenha a precisão técnica.

DADOS DE ENTRADA (JSON):
{json.dumps(payload, ensure_ascii=False, indent=2)}

REGRAS:
1. Retorne APENAS um JSON válido.
2. O formato de saída deve ser um array de objetos JSON, com as chaves: "id" (número), "titulo_pt" (string) e "resumo_pt" (string).
3. Não adicione crases markdown (```json) ou texto extra, apenas a lista JSON [{{...}}]."""

    try:
        response_text = call_llm(provider, model, api_key, prompt, "traducao").strip()
        
        # Limpa possível formatação markdown
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        translated_data = json.loads(response_text.strip())
        
        # Mapeia de volta para os artigos
        for item in translated_data:
            idx = item.get("id")
            if idx is not None and 0 <= idx < len(papers):
                if item.get("titulo_pt"):
                    papers[idx]["title"] = item["titulo_pt"]
                if item.get("resumo_pt"):
                    papers[idx]["abstract"] = item["resumo_pt"]
                    
    except Exception as e:
        print(f"Erro na tradução em lote: {e}")
        # Em caso de erro, retorna os artigos originais
        
    return papers
