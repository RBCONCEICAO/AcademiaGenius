const STORAGE_KEY = 'academiagenius_api_keys';

export interface ApiKeys {
  // LLMs principais
  gemini:    string;
  openai:    string;
  anthropic: string;
  // LLMs rápidas / alternativas
  groq:      string;
  mistral:   string;
  // Bases acadêmicas
  semanticScholar: string;
  pubmed:    string;
  core:      string;
}

const EMPTY: ApiKeys = {
  gemini: '', openai: '', anthropic: '',
  groq: '', mistral: '',
  semanticScholar: '', pubmed: '', core: '',
};

export function loadApiKeys(): ApiKeys {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...EMPTY };
    const p = JSON.parse(raw) as Partial<ApiKeys>;
    return { ...EMPTY, ...p };
  } catch {
    return { ...EMPTY };
  }
}

export function saveApiKeys(keys: ApiKeys): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
}

export type LlmProvider = 'gemini' | 'openai' | 'anthropic' | 'groq' | 'mistral';
export type AcademicProvider = 'semanticScholar' | 'pubmed' | 'core';

export function getKeyForProvider(provider: LlmProvider | AcademicProvider): string {
  return loadApiKeys()[provider] ?? '';
}

export function getSemanticScholarKey(): string {
  return loadApiKeys().semanticScholar ?? '';
}
