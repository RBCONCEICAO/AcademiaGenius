import json
import re
import logging
from typing import List, Dict, Any
from app.services.llm import call_llm

logger = logging.getLogger(__name__)

def generate_clarifying_questions(
    theme: str,
    provider: str,
    model: str,
    api_key: str,
) -> Dict[str, Any]:
    """
    Gera de forma dinâmica 3 perguntas de esclarecimento focadas em refinar e delimitar 
    o escopo da pesquisa com base no tema fornecido pelo usuário.
    """
    prompt = f"""Você é um orientador científico de IA especializado. O usuário deseja fazer uma pesquisa sobre o tema: "{theme}".
Para tornar a pesquisa científica mais específica, evitar homônimos (ex: misturar engenharia com medicina) e definir o escopo exato, gere 3 perguntas de esclarecimento cruciais.

REGRAS:
1. A primeira pergunta DEVE focar no domínio/área científica principal para desambiguar homônimos (ex: "Sua pesquisa é focada na área de Engenharia Civil ou Medicina/Psiquiatria?"). Ela DEVE ser do tipo "choice" com opções claras.
2. A segunda pergunta deve delimitar abordagens, softwares, materiais ou técnicas específicas associadas a esse tema (pode ser "choice" ou "text").
3. A terceira pergunta deve focar em contexto geográfico, tipo de estudo ou abrangência (ex: "Você prefere focar em estudos de caso no Brasil ou em normas e dados internacionais?").
4. Mantenha as perguntas e opções curtas e objetivas.

Retorne APENAS um objeto JSON válido, sem markdown, sem crases ```json, com o seguinte formato exato:
{{
  "questions": [
    {{
      "id": 1,
      "question": "Pergunta 1...",
      "type": "choice",
      "options": ["Opção A", "Opção B"]
    }},
    {{
      "id": 2,
      "question": "Pergunta 2...",
      "type": "text"
    }},
    {{
      "id": 3,
      "question": "Pergunta 3...",
      "type": "choice",
      "options": ["Opção X", "Opção Y"]
    }}
  ]
}}"""

    try:
        response_text = call_llm(provider, model, api_key, prompt, "pesquisa").strip()
        cleaned = re.sub(r"```(?:json)?", "", response_text).strip().rstrip("```").strip()
        return json.loads(cleaned)
    except Exception as e:
        logger.error("Erro ao gerar perguntas de clarificação: %s. Retornando padrão.", e)
        # Fallback genérico e seguro
        return {
            "questions": [
                {
                    "id": 1,
                    "question": "Qual é a principal área científica ou foco do seu estudo para este tema?",
                    "type": "text"
                },
                {
                    "id": 2,
                    "question": "Deseja restringir a pesquisa a algum software, metodologia ou país específico?",
                    "type": "choice",
                    "options": ["Focar em metodologias do Brasil", "Focar em dados e normas globais", "Sem restrição específica"]
                },
                {
                    "id": 3,
                    "question": "Descreva brevemente qualquer detalhe adicional importante para a busca dos artigos:",
                    "type": "text"
                }
            ]
        }
