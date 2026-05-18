import { useState } from 'react';
import { CheckCircle, Save, ExternalLink, Zap, Star, Cpu, Database, ChevronDown, ChevronUp, Eye, EyeOff } from 'lucide-react';
import { loadApiKeys, saveApiKeys } from '../lib/apiKeys';
import type { ApiKeys } from '../lib/apiKeys';

// ── Catálogo de provedores LLM ────────────────────────────────────────────────
const LLM_PROVIDERS = [
  {
    id: 'gemini' as keyof ApiKeys,
    name: 'Google Gemini',
    badge: 'Recomendado',
    badgeColor: 'bg-indigo-100 text-indigo-700 border-indigo-200',
    icon: '✦',
    iconBg: 'bg-gradient-to-br from-blue-500 to-indigo-600',
    speed: '★★★★☆',
    quality: '★★★★★',
    placeholder: 'AIzaSy...',
    hint: 'Obter em',
    hintUrl: 'https://aistudio.google.com',
    hintLabel: 'aistudio.google.com',
    models: ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-1.5-pro', 'gemini-1.5-flash'],
    free: false,
    desc: 'Melhor custo-benefício. Flash para velocidade, Pro para profundidade máxima.',
  },
  {
    id: 'groq' as keyof ApiKeys,
    name: 'Groq',
    badge: 'Ultra-rápido',
    badgeColor: 'bg-green-100 text-green-700 border-green-200',
    icon: '⚡',
    iconBg: 'bg-gradient-to-br from-green-400 to-emerald-600',
    speed: '★★★★★',
    quality: '★★★☆☆',
    placeholder: 'gsk_...',
    hint: 'Gratuito em',
    hintUrl: 'https://console.groq.com',
    hintLabel: 'console.groq.com',
    models: ['llama-3.3-70b-versatile', 'mixtral-8x7b-32768', 'gemma2-9b-it'],
    free: true,
    desc: 'Ideal para extração rápida no modo Pipeline. 10× mais veloz que GPT-4o. API gratuita.',
  },
  {
    id: 'openai' as keyof ApiKeys,
    name: 'OpenAI (GPT-4o)',
    badge: 'Alta qualidade',
    badgeColor: 'bg-purple-100 text-purple-700 border-purple-200',
    icon: '◎',
    iconBg: 'bg-gradient-to-br from-purple-500 to-violet-600',
    speed: '★★★☆☆',
    quality: '★★★★★',
    placeholder: 'sk-...',
    hint: 'Obter em',
    hintUrl: 'https://platform.openai.com/api-keys',
    hintLabel: 'platform.openai.com',
    models: ['gpt-4.5-preview', 'gpt-4o', 'gpt-4o-mini', 'o3-mini', 'o1'],
    free: false,
    desc: 'Excelente qualidade para redação final. GPT-4o mini é mais econômico.',
  },
  {
    id: 'anthropic' as keyof ApiKeys,
    name: 'Anthropic Claude',
    badge: 'Alta qualidade',
    badgeColor: 'bg-orange-100 text-orange-700 border-orange-200',
    icon: '◈',
    iconBg: 'bg-gradient-to-br from-orange-400 to-red-500',
    speed: '★★★☆☆',
    quality: '★★★★★',
    placeholder: 'sk-ant-...',
    hint: 'Obter em',
    hintUrl: 'https://console.anthropic.com/keys',
    hintLabel: 'console.anthropic.com',
    models: ['claude-3-7-sonnet-20250219', 'claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'],
    free: false,
    desc: 'Excelente em textos longos e análise crítica acadêmica.',
  },
  {
    id: 'mistral' as keyof ApiKeys,
    name: 'Mistral AI',
    badge: 'Europa · LGPD',
    badgeColor: 'bg-sky-100 text-sky-700 border-sky-200',
    icon: '◬',
    iconBg: 'bg-gradient-to-br from-sky-400 to-blue-600',
    speed: '★★★★☆',
    quality: '★★★★☆',
    placeholder: 'api_key...',
    hint: 'Obter em',
    hintUrl: 'https://console.mistral.ai',
    hintLabel: 'console.mistral.ai',
    models: ['mistral-large-latest', 'mistral-small-latest'],
    free: false,
    desc: 'Servidores na Europa — boa opção para dados sensíveis e conformidade LGPD.',
  },
] as const;

const ACADEMIC_KEYS = [
  {
    id: 'semanticScholar' as keyof ApiKeys,
    name: 'Semantic Scholar',
    badge: 'Gratuito',
    placeholder: 'Deixe vazio para usar sem chave (rate limit menor)',
    desc: 'Aumenta o rate limit de requisições. 200M+ artigos acadêmicos.',
    url: 'https://www.semanticscholar.org/product/api',
  },
  {
    id: 'pubmed' as keyof ApiKeys,
    name: 'PubMed / NCBI',
    badge: 'Gratuito · Saúde',
    placeholder: 'Obtenha em ncbi.nlm.nih.gov/account/',
    desc: 'Essencial para pesquisas na área da saúde e biomedicina.',
    url: 'https://www.ncbi.nlm.nih.gov/account/',
  },
  {
    id: 'core' as keyof ApiKeys,
    name: 'CORE',
    badge: 'Gratuito · 200M artigos',
    placeholder: 'Obtenha em core.ac.uk/services/api',
    desc: 'Maior repositório de artigos open access do mundo.',
    url: 'https://core.ac.uk/services/api',
  },
] as const;

// ── Componente: campo de senha com toggle ────────────────────────────────────
function SecretInput({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder: string }) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="relative">
      <input
        type={visible ? 'text' : 'password'}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="input pr-10 font-mono text-xs"
      />
      <button type="button" onClick={() => setVisible(v => !v)}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition">
        {visible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
      </button>
    </div>
  );
}

// ── Componente: card de provedor LLM ─────────────────────────────────────────
function LlmCard({ provider, keyValue, onChange }: { provider: typeof LLM_PROVIDERS[number]; keyValue: string; onChange: (v: string) => void }) {
  const [expanded, setExpanded] = useState(!!keyValue);
  const hasKey = !!keyValue;

  return (
    <div className={`border rounded-2xl overflow-hidden transition-all ${hasKey ? 'border-indigo-200 bg-indigo-50/30' : 'border-gray-200 bg-white'}`}>
      {/* Header */}
      <button type="button" onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center gap-4 px-5 py-4 text-left hover:bg-gray-50/50 transition">
        <div className={`w-10 h-10 rounded-xl ${provider.iconBg} flex items-center justify-center text-white font-bold text-lg shrink-0`}>
          {provider.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-gray-900 text-sm">{provider.name}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${provider.badgeColor}`}>
              {provider.badge}
            </span>
            {provider.free && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 border border-green-200 font-medium">
                API Gratuita
              </span>
            )}
            {hasKey && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200 font-medium flex items-center gap-1">
                <CheckCircle className="w-3 h-3" /> Configurado
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-0.5 truncate">{provider.desc}</p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <div className="hidden sm:flex flex-col items-end text-xs text-gray-400 gap-0.5">
            <span className="flex items-center gap-1"><Zap className="w-3 h-3" />{provider.speed}</span>
            <span className="flex items-center gap-1"><Star className="w-3 h-3" />{provider.quality}</span>
          </div>
          {expanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
        </div>
      </button>

      {/* Expanded */}
      {expanded && (
        <div className="px-5 pb-5 pt-1 border-t border-gray-100 space-y-3 bg-white/50">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>{provider.hint}:</span>
            <a href={provider.hintUrl} target="_blank" rel="noopener noreferrer"
              className="text-indigo-600 hover:underline flex items-center gap-1">
              {provider.hintLabel} <ExternalLink className="w-3 h-3" />
            </a>
          </div>
          <SecretInput value={keyValue} onChange={onChange} placeholder={provider.placeholder} />
          <div className="flex flex-wrap gap-1.5">
            {provider.models.map(m => (
              <span key={m} className="text-xs font-mono bg-gray-100 text-gray-600 px-2 py-0.5 rounded-md border border-gray-200">
                {m}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Página principal ──────────────────────────────────────────────────────────
export function Settings() {
  const [keys, setKeys] = useState<ApiKeys>(loadApiKeys);
  const [saved, setSaved] = useState(false);

  const set = (field: keyof ApiKeys) => (v: string) => setKeys(k => ({ ...k, [field]: v }));

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    saveApiKeys(keys);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const configuredLlms = LLM_PROVIDERS.filter(p => keys[p.id]);
  const pipelineReady  = configuredLlms.length >= 2;

  return (
    <div className="max-w-3xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Configurações</h1>
        <p className="text-sm text-gray-500 mt-1">
          Modelo <span className="font-semibold text-gray-700">Bring Your Own Key</span> — suas chaves ficam
          apenas no seu navegador e nunca são enviadas a terceiros.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-8">
        {/* Pipeline status */}
        {pipelineReady && (
          <div className="bg-gradient-to-r from-emerald-50 to-green-50 border border-emerald-200 rounded-2xl p-5 flex gap-4 items-start">
            <div className="w-9 h-9 bg-emerald-100 rounded-xl flex items-center justify-center shrink-0">
              <Cpu className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <p className="font-semibold text-emerald-800 text-sm">Modo Pipeline Multi-LLM disponível 🚀</p>
              <p className="text-xs text-emerald-700 mt-1 leading-relaxed">
                Você tem <strong>{configuredLlms.length} LLMs configuradas</strong>. No Dashboard, ative o Modo Pipeline para usar
                uma LLM rápida (ex: Groq) na extração e uma de alta qualidade (ex: Gemini Pro) na redação final.
              </p>
            </div>
          </div>
        )}

        {/* LLM Providers */}
        <section className="space-y-3">
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-5 h-5 text-indigo-600" />
            <h2 className="text-base font-semibold text-gray-900">Modelos de IA</h2>
            <span className="text-xs text-gray-400 ml-auto">{configuredLlms.length}/{LLM_PROVIDERS.length} configurados</span>
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-xs text-amber-800 leading-relaxed">
            💡 <strong>Dica Pipeline:</strong> Configure <strong>Groq</strong> (gratuito) + <strong>Gemini</strong> para pesquisas
            até 3× mais rápidas — Groq extrai o conhecimento em segundos, Gemini escreve com qualidade máxima.
          </div>

          <div className="space-y-3">
            {LLM_PROVIDERS.map(p => (
              <LlmCard key={p.id} provider={p} keyValue={keys[p.id] as string}
                onChange={set(p.id)} />
            ))}
          </div>
        </section>

        {/* Academic keys */}
        <section className="space-y-3">
          <div className="flex items-center gap-2 mb-1">
            <Database className="w-5 h-5 text-indigo-600" />
            <h2 className="text-base font-semibold text-gray-900">Bases de Pesquisa</h2>
            <span className="text-xs text-gray-400 ml-auto">Todas gratuitas</span>
          </div>
          <div className="bg-white border border-gray-200 rounded-2xl divide-y divide-gray-100">
            {ACADEMIC_KEYS.map(ak => (
              <div key={ak.id} className="px-5 py-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-medium text-gray-800">{ak.name}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 border border-green-200 font-medium">
                    {ak.badge}
                  </span>
                  <a href={ak.url} target="_blank" rel="noopener noreferrer"
                    className="ml-auto text-xs text-indigo-600 hover:underline flex items-center gap-1">
                    Obter chave <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
                <p className="text-xs text-gray-500 mb-2">{ak.desc}</p>
                <SecretInput value={keys[ak.id] as string} onChange={set(ak.id)} placeholder={ak.placeholder} />
              </div>
            ))}
          </div>
        </section>

        {/* Save */}
        <div className="flex items-center justify-between pt-2">
          <p className="text-xs text-gray-400">
            🔒 Armazenado no localStorage do navegador — nunca enviado a servidores externos.
          </p>
          <button type="submit" className="btn-primary">
            {saved
              ? <><CheckCircle className="w-4 h-4" /> Salvo!</>
              : <><Save className="w-4 h-4" /> Salvar</>
            }
          </button>
        </div>
      </form>
    </div>
  );
}
