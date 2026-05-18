"""
Agente Redator — Geração de Conteúdo Acadêmico
Usa a base de conhecimento extraída dos artigos reais para
redigir um documento acadêmico fundamentado em evidências.
"""
from typing import List, Dict, Any, Optional
from app.services.llm import call_llm


DOC_TYPE_LABELS = {
    "tcc": "Monografia/TCC",
    "artigo": "Artigo Científico",
    "estudo": "Estudo de Caso",
}

NORM_INSTRUCTIONS = {
    "ABNT": "Utilize o formato ABNT para citações no texto: (SOBRENOME, ano). Liste as referências em ordem alfabética ao final.",
    "APA": "Utilize o formato APA para citações no texto: (Sobrenome, ano). Liste as referências ao final no padrão APA 7ª edição.",
    "Vancouver": "Utilize o formato Vancouver com citações numeradas entre colchetes [1], [2].",
}


def write_document(
    theme: str,
    doc_type: str,
    papers: List[Dict[str, Any]],
    knowledge: Dict[str, Any],
    provider: str,
    model: str,
    api_key: str,
    norm: str = "ABNT",
    existing_document: Optional[str] = None,
) -> str:
    """
    Redige o documento acadêmico completo baseado nos artigos e conhecimento reais.

    Args:
        theme: Tema central da pesquisa.
        doc_type: Tipo de documento ('tcc', 'artigo', 'estudo').
        papers: Lista de artigos reais encontrados.
        knowledge: Base de conhecimento extraída pelo extractor_agent.
        provider / model / api_key: Configuração da LLM.
        norm: Norma de formatação ('ABNT', 'APA', 'Vancouver').

    Returns:
        Texto completo do documento acadêmico.
    """
    doc_label = DOC_TYPE_LABELS.get(doc_type, "Documento Científico")
    norm_instruction = NORM_INSTRUCTIONS.get(norm, NORM_INSTRUCTIONS["ABNT"])

    # Formata referências reais para o prompt
    references_block = "\n".join([
        f"- [{i+1}] {p['abnt_reference']} (Citações: {p['citation_count']})"
        for i, p in enumerate(papers)
    ])

    # Formata o conhecimento extraído
    temas = ", ".join(knowledge.get("temas_principais", []))
    metodologias = ", ".join(knowledge.get("metodologias_identificadas", []))
    achados = "\n".join([f"- {a}" for a in knowledge.get("principais_achados", [])])
    lacunas = "\n".join([f"- {l}" for l in knowledge.get("lacunas_pesquisa", [])])
    sintese = knowledge.get("sintese_geral", "")
    consensos = knowledge.get("consensos", "")

    # Estruturas Dinâmicas por Tipo de Documento
    structures = {
        "tcc": """1. **Introdução** — Contextualização profunda, justificativa, problema e objetivos (geral e específicos). Cite os autores.
2. **Referencial Teórico** — Revisão bibliográfica extensa e cruzamento de autores. Debata os textos, não apenas liste.
3. **Metodologia da Pesquisa** — Como a pesquisa teórica e os testes foram estruturados.
4. **Programa Experimental e Simulações (Ex: PLAXIS 2D)** — Descreva detalhadamente a modelagem numérica, parâmetros e fases de cálculo.
5. **Resultados e Discussão** — Apresentação dos achados cruzados com as simulações.
6. **Considerações Finais** — Síntese autoral e lacunas futuras.
7. **Referências Bibliográficas** — Lista de todas as fontes no padrão exigido.
8. **Quadro Comparativo do Estado da Arte** — Uma tabela obrigatória em Markdown comparando todos os artigos estudados (Colunas: Autor, Ano, Metodologia, Foco Principal, Limitações).""",
        
        "artigo": """1. **Resumo e Palavras-chave** — Síntese do artigo em um parágrafo.
2. **Introdução** — Contexto, lacuna de pesquisa e objetivo do artigo.
3. **Fundamentação Teórica** — Principais conceitos da literatura.
4. **Materiais e Métodos (incluindo Simulações)** — Como o estudo foi conduzido, incluindo modelagem (Ex: PLAXIS 2D) se aplicável.
5. **Resultados e Discussão** — Análise dos dados e comparação com a literatura.
6. **Conclusão** — Fechamento conciso.
7. **Referências Bibliográficas** — Lista de fontes.
8. **Quadro Comparativo** — Tabela em Markdown comparando a literatura revisada (Autor, Metodologia, Resultados, Limitações).""",

        "estudo": """1. **Introdução ao Caso** — Contextualização do problema prático e objetivo do estudo.
2. **Revisão da Literatura** — Base teórica para sustentar a análise do caso.
3. **Apresentação do Caso e Metodologia** — Detalhes práticos do objeto de estudo (Ex: Modelagem e Testes no PLAXIS 2D).
4. **Análise Crítica e Discussão dos Resultados** — Cruzamento entre a teoria e o caso prático.
5. **Conclusões e Recomendações** — Lições aprendidas e propostas de solução.
6. **Referências Bibliográficas** — Lista de fontes.
7. **Matriz de Similaridade** — Tabela em Markdown cruzando o caso estudado com os artigos base (Referência, Contribuição para o Caso, Diferenças)."""
    }

    estrutura_texto = structures.get(doc_type, structures["tcc"])

    # Instrução Adicional de Refinamento (se o usuário mandou no tema)
    instrucao_adicional = ""
    if "INSTRUÇÕES ADICIONAIS DE REFINAMENTO:" in theme:
        partes = theme.split("INSTRUÇÕES ADICIONAIS DE REFINAMENTO:")
        theme = partes[0].strip()
        instrucao_adicional = f"\n\n## INSTRUÇÃO ESPECIAL DO USUÁRIO PARA ESTA VERSÃO:\n{partes[1].strip()}\nCertifique-se de seguir a instrução especial do usuário ao redigir ou alterar o texto."

    existing_doc_block = ""
    if existing_document:
        existing_doc_block = f"""
## VERSÃO ANTERIOR DO DOCUMENTO (A ser refinada/atualizada):
{existing_document}

**IMPORTANTE:** O usuário deseja que você ATUALIZE, REESCREVA ou EXPANDA o documento acima com base nas novas instruções e novos dados fornecidos. Mantenha as partes existentes de qualidade e integre o novo conhecimento harmoniosamente.
"""

    prompt = f"""Você é um Pesquisador Sênior e Especialista Acadêmico redigindo um material de nível de Graduação/Pós-Graduação.
Seu objetivo é escrever ou refinar um(a) {doc_label} EXTREMAMENTE COMPLETO, PROFUNDO E AUTORAL sobre o tema: **{theme}**
{existing_doc_block}

## DIRETRIZES DE ESTILO E LINGUAGEM (MUITO IMPORTANTE):
1. **Sem Viés de IA:** Evite jargões clichês de IA (ex: "em suma", "mergulhar", "teia", "jornada", "fascinante", "no cenário atual", "crucial").
2. **Linguagem Humana e Técnica:** O tom deve ser de um engenheiro/pesquisador real. Use voz passiva ou primeira pessoa do plural.
3. **Profundidade:** NUNCA faça um resumo básico. O texto deve ser extenso, detalhado, com argumentação sólida (mínimo de 3000 palavras).
4. **Ortografia:** Correção ortográfica, gramatical e de concordância impecável.{instrucao_adicional}

## Fontes Reais Disponíveis (use SOMENTE estas para citar):
{references_block}

## Base de Conhecimento Extraída:
- **Temas principais:** {temas}
- **Metodologias:** {metodologias}
- **Principais achados:** {achados}
- **Lacunas de pesquisa:** {lacunas}
- **Síntese e Consensos:** {sintese} | {consensos}

## Instruções de Formatação:
{norm_instruction}

## ESTRUTURA OBRIGATÓRIA DO DOCUMENTO ({doc_label}):
{estrutura_texto}

## Regras Críticas:
- Cite SOMENTE os artigos da lista acima.
- Cada seção DEVE ter múltiplos parágrafos bem desenvolvidos. Não economize palavras.
- O texto final deve ser completo e sem placeholders."""

    return call_llm(provider, model, api_key, prompt, "redacao")
