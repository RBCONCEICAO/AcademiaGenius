import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  BookOpen, MessageCircle, HelpCircle, Clock, Mic,
  Send, Loader2, ArrowLeft, ChevronDown, ChevronUp, ExternalLink, Trash2
} from 'lucide-react';
import { getKeyForProvider } from '../lib/apiKeys';
import { API_URL } from '../lib/config';
import { authFetch } from '../lib/supabase';

const API = `${API_URL}/api/v1/notebook`;
const DEFAULT_MODEL = 'gemini-2.5-flash';

type Tab = 'chat' | 'study-guide' | 'faq' | 'timeline' | 'audio';

interface ChatMessage { role: 'user' | 'assistant'; content: string; citations?: any[]; }

function useNotebookData() {
  const { state } = useLocation();
  const provider = state?.llmProvider || 'gemini';
  return {
    theme: state?.theme || '',
    document: state?.document || '',
    papers: state?.papers || [],
    llmModel: state?.llmModel || DEFAULT_MODEL,
    llmProvider: provider,
    apiKey: state?.apiKey || getKeyForProvider(provider),
  };
}

// ── Banner de chave ausente ──────────────────────────────────────────────────
function KeyMissingBanner() {
  return (
    <div className="flex flex-col items-center gap-3 bg-amber-50 border border-amber-200 rounded-xl px-6 py-5 text-center max-w-sm">
      <p className="text-sm font-semibold text-amber-800">Chave de API não configurada</p>
      <p className="text-xs text-amber-700 leading-relaxed">
        Configure sua chave de API nas Configurações para usar esta funcionalidade.
        Gemini e Groq possuem planos gratuitos.
      </p>
      <a href="/settings"
        className="text-xs font-bold bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700 transition">
        Ir para Configurações →
      </a>
    </div>
  );
}

// ── helpers de persistência ──────────────────────────────────────────────────
function chatStorageKey(theme: string) {
  return `notebook_chat_${theme.trim().toLowerCase().replace(/\s+/g, '_').slice(0, 80)}`;
}

function loadChatHistory(theme: string): ChatMessage[] {
  try {
    const raw = localStorage.getItem(chatStorageKey(theme));
    if (raw) return JSON.parse(raw) as ChatMessage[];
  } catch { /* ignore */ }
  return [];
}

function saveChatHistory(theme: string, messages: ChatMessage[]) {
  try {
    localStorage.setItem(chatStorageKey(theme), JSON.stringify(messages.slice(-60)));
  } catch { /* ignore */ }
}

// ── Componente Chat ──────────────────────────────────────────────────────────
function ChatTab({ theme, document, papers, apiKey, llmModel, llmProvider }: any) {
  const greeting: ChatMessage = {
    role: 'assistant',
    content: `Olá! Sou seu assistente de pesquisa sobre **"${theme}"**. Tenho acesso a ${papers.length} artigos científicos. Faça qualquer pergunta sobre as fontes.`,
  };

  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const saved = loadChatHistory(theme);
    return saved.length > 0 ? saved : [greeting];
  });
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [keyError, setKeyError] = useState(false);

  // persiste sempre que messages muda (exceto estado inicial de 1 msg)
  useEffect(() => {
    if (messages.length > 1) saveChatHistory(theme, messages);
  }, [messages, theme]);

  const clearHistory = () => {
    localStorage.removeItem(chatStorageKey(theme));
    setMessages([greeting]);
  };

  const send = async () => {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput('');
    setMessages(m => [...m, { role: 'user', content: question }]);

    let currentKey = apiKey === 'server-fallback' ? '' : apiKey;
    if (!currentKey) { setKeyError(true); return; }

    setLoading(true);
    try {
      const history = messages.filter(m => m.role !== 'assistant' || messages.indexOf(m) > 0)
        .map(m => ({ role: m.role, content: m.content }));
      const r = await authFetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme, document, papers, api_key: currentKey, llm_model: llmModel, llm_provider: llmProvider, question, history }),
      });
      const data = await r.json();
      setMessages(m => [...m, { role: 'assistant', content: data.answer, citations: data.citations }]);
    } catch {
      setMessages(m => [...m, { role: 'assistant', content: 'Erro ao conectar com a API.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {keyError && (
        <div className="mb-3 flex justify-center">
          <KeyMissingBanner />
        </div>
      )}
      {messages.length > 1 && !keyError && (
        <div className="flex justify-end pb-2">
          <button onClick={clearHistory}
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-red-500 transition">
            <Trash2 className="w-3 h-3" /> Limpar histórico
          </button>
        </div>
      )}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
              m.role === 'user' ? 'bg-primary text-white' : 'bg-white border border-gray-200 text-gray-800'
            }`}>
              <p className="whitespace-pre-wrap">{m.content}</p>
              {m.citations && m.citations.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-100 space-y-1">
                  {m.citations.map((c: any, ci: number) => (
                    <p key={ci} className="text-xs text-indigo-600">
                      [{c.index}] {c.authors} ({c.year}) — {c.source}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-xl px-4 py-3">
              <Loader2 className="w-4 h-4 animate-spin text-primary" />
            </div>
          </div>
        )}
      </div>
      <div className="flex gap-2 pt-4 border-t border-gray-200">
        <input
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          placeholder="Pergunte sobre a pesquisa..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
        />
        <button onClick={send} disabled={loading || !input.trim()}
          className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-opacity-90 disabled:opacity-50 transition">
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// ── Componente Guia de Estudo ────────────────────────────────────────────────
function StudyGuideTab({ theme, document, papers, apiKey, llmModel, llmProvider }: any) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    let currentKey = apiKey === 'server-fallback' ? '' : apiKey;
    if (!currentKey) { setError('key'); return; }
    setError(null);
    setLoading(true);
    try {
      const r = await authFetch(`${API}/study-guide`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme, document, papers, api_key: currentKey, llm_model: llmModel, llm_provider: llmProvider }),
      });
      const d = await r.json();
      if (!r.ok) { setError(d.detail || 'Erro desconhecido.'); return; }
      setData(d.guide);
    } catch (e: any) {
      setError(e.message || 'Erro de conexão.');
    } finally {
      setLoading(false);
    }
  };

  if (!data) return (
    <div className="flex flex-col items-center justify-center h-48 gap-4">
      {error === 'key'
        ? <KeyMissingBanner />
        : error ? <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">{error}</p>
        : <><BookOpen className="w-12 h-12 text-indigo-200" /><p className="text-gray-500 text-sm">Clique para gerar o Guia de Estudo com base nas fontes.</p></>
      }
      {error !== 'key' && (
        <button onClick={generate} disabled={loading}
          className="bg-primary text-white px-6 py-2.5 rounded-lg font-medium hover:bg-opacity-90 disabled:opacity-60 flex items-center gap-2">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <BookOpen className="w-4 h-4" />}
          {loading ? 'Gerando...' : 'Gerar Guia de Estudo'}
        </button>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-5">
        <h3 className="font-bold text-indigo-900 text-lg mb-2">{data.titulo}</h3>
        <p className="text-indigo-800 text-sm leading-relaxed">{data.resumo_executivo}</p>
      </div>

      {data.conceitos_chave?.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-700 mb-3 text-sm uppercase tracking-wide">Conceitos-Chave</h4>
          <div className="grid gap-3">
            {data.conceitos_chave.map((c: any, i: number) => (
              <div key={i} className="bg-white border border-gray-200 rounded-lg p-4">
                <p className="font-semibold text-gray-900 text-sm">{c.conceito}</p>
                <p className="text-gray-600 text-sm mt-1">{c.definicao}</p>
                {c.fonte && <p className="text-xs text-indigo-500 mt-1">Fonte: {c.fonte}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {data.topicos_principais?.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-700 mb-3 text-sm uppercase tracking-wide">Tópicos Principais</h4>
          <div className="space-y-2">
            {data.topicos_principais.map((t: any, i: number) => (
              <div key={i} className="border border-gray-200 rounded-lg overflow-hidden">
                <button onClick={() => setOpen(open === i ? null : i)}
                  className="w-full flex justify-between items-center px-4 py-3 bg-white hover:bg-gray-50 text-left">
                  <span className="font-medium text-gray-800 text-sm">{t.titulo}</span>
                  {open === i ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                </button>
                {open === i && (
                  <div className="px-4 pb-4 bg-gray-50 border-t border-gray-100">
                    <p className="text-gray-600 text-sm mt-3">{t.descricao}</p>
                    {t.pontos_chave?.length > 0 && (
                      <ul className="mt-2 space-y-1">
                        {t.pontos_chave.map((p: string, pi: number) => (
                          <li key={pi} className="text-sm text-gray-600 flex gap-2"><span className="text-primary">•</span>{p}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {data.perguntas_reflexao?.length > 0 && (
        <div className="bg-amber-50 border border-amber-100 rounded-xl p-5">
          <h4 className="font-semibold text-amber-800 mb-3 text-sm">💡 Perguntas para Reflexão</h4>
          <ol className="space-y-2">
            {data.perguntas_reflexao.map((q: string, i: number) => (
              <li key={i} className="text-sm text-amber-900">{i + 1}. {q}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

// ── FAQ ──────────────────────────────────────────────────────────────────────
function FaqTab({ theme, document, papers, apiKey, llmModel, llmProvider }: any) {
  const [faq, setFaq] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    let currentKey = apiKey === 'server-fallback' ? '' : apiKey;
    if (!currentKey) { setError('key'); return; }
    setError(null);
    setLoading(true);
    try {
      const r = await authFetch(`${API}/faq`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme, document, papers, api_key: currentKey, llm_model: llmModel, llm_provider: llmProvider }),
      });
      const d = await r.json();
      setFaq(d.faq || []);
    } catch (e: any) {
      setError(e.message || 'Erro de conexão.');
    } finally { setLoading(false); }
  };

  if (!faq.length) return (
    <div className="flex flex-col items-center justify-center h-48 gap-4">
      {error === 'key'
        ? <KeyMissingBanner />
        : error ? <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">{error}</p>
        : <><HelpCircle className="w-12 h-12 text-indigo-200" /><p className="text-gray-500 text-sm">Gera perguntas frequentes com respostas baseadas nas fontes.</p></>
      }
      {error !== 'key' && (
        <button onClick={generate} disabled={loading}
          className="bg-primary text-white px-6 py-2.5 rounded-lg font-medium hover:bg-opacity-90 disabled:opacity-60 flex items-center gap-2">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <HelpCircle className="w-4 h-4" />}
          {loading ? 'Gerando...' : 'Gerar FAQ'}
        </button>
      )}
    </div>
  );

  return (
    <div className="space-y-2">
      {faq.map((item: any, i: number) => (
        <div key={i} className="border border-gray-200 rounded-lg overflow-hidden">
          <button onClick={() => setOpen(open === i ? null : i)}
            className="w-full flex justify-between items-center px-4 py-3 bg-white hover:bg-gray-50 text-left gap-3">
            <span className="font-medium text-gray-800 text-sm">{item.pergunta}</span>
            {open === i ? <ChevronUp className="w-4 h-4 text-gray-400 shrink-0" /> : <ChevronDown className="w-4 h-4 text-gray-400 shrink-0" />}
          </button>
          {open === i && (
            <div className="px-4 pb-4 bg-gray-50 border-t border-gray-100">
              <p className="text-gray-700 text-sm mt-3">{item.resposta}</p>
              {item.fonte && <p className="text-xs text-indigo-500 mt-2">Fonte: {item.fonte}</p>}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Linha do Tempo ───────────────────────────────────────────────────────────
function TimelineTab({ theme, document, papers, apiKey, llmModel, llmProvider }: any) {
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    let currentKey = apiKey === 'server-fallback' ? '' : apiKey;
    if (!currentKey) { setError('key'); return; }
    setError(null);
    setLoading(true);
    try {
      const r = await authFetch(`${API}/timeline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme, document, papers, api_key: currentKey, llm_model: llmModel, llm_provider: llmProvider }),
      });
      const d = await r.json();
      setTimeline(d.timeline || []);
    } catch (e: any) {
      setError(e.message || 'Erro de conexão.');
    } finally { setLoading(false); }
  };

  if (!timeline.length) return (
    <div className="flex flex-col items-center justify-center h-48 gap-4">
      {error === 'key'
        ? <KeyMissingBanner />
        : error ? <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">{error}</p>
        : <><Clock className="w-12 h-12 text-indigo-200" /><p className="text-gray-500 text-sm">Extrai os marcos históricos e cronológicos da área.</p></>
      }
      {error !== 'key' && (
        <button onClick={generate} disabled={loading}
          className="bg-primary text-white px-6 py-2.5 rounded-lg font-medium hover:bg-opacity-90 disabled:opacity-60 flex items-center gap-2">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Clock className="w-4 h-4" />}
          {loading ? 'Gerando...' : 'Gerar Linha do Tempo'}
        </button>
      )}
    </div>
  );

  return (
    <div className="relative">
      <div className="absolute left-16 top-0 bottom-0 w-0.5 bg-indigo-100" />
      <div className="space-y-6">
        {timeline.map((item: any, i: number) => (
          <div key={i} className="flex gap-6 items-start">
            <div className="w-16 shrink-0 text-right">
              <span className="text-sm font-bold text-primary">{item.ano}</span>
            </div>
            <div className="relative">
              <div className="absolute -left-[25px] top-1.5 w-3 h-3 rounded-full bg-primary border-2 border-white shadow" />
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-4 flex-1">
              <p className="font-semibold text-gray-800 text-sm">{item.evento}</p>
              {item.autores && <p className="text-xs text-indigo-600 mt-1">{item.autores}</p>}
              {item.impacto && <p className="text-xs text-gray-500 mt-1">{item.impacto}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Audio Overview ───────────────────────────────────────────────────────────
function AudioTab({ theme, document, papers, apiKey, llmModel, llmProvider }: any) {
  const [script, setScript] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [duration, setDuration] = useState(5);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    let currentKey = apiKey === 'server-fallback' ? '' : apiKey;
    if (!currentKey) { setError('key'); return; }
    setError(null);
    setLoading(true);
    try {
      const r = await authFetch(`${API}/audio-script`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme, document, papers, api_key: currentKey, llm_model: llmModel, llm_provider: llmProvider, duration_minutes: duration }),
      });
      const d = await r.json();
      setScript(d.script);
    } catch (e: any) {
      setError(e.message || 'Erro de conexão.');
    } finally { setLoading(false); }
  };

  if (!script) return (
    <div className="flex flex-col items-center justify-center h-56 gap-4">
      {error === 'key' ? <KeyMissingBanner /> : <>
        {error && <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">{error}</p>}
        <Mic className="w-12 h-12 text-indigo-200" />
        <p className="text-gray-500 text-sm text-center max-w-xs">
          Gera um roteiro dialógico estilo podcast com 2 apresentadores baseado nas fontes.
        </p>
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-600">Duração:</label>
          {[3, 5, 10].map(d => (
            <button key={d} onClick={() => setDuration(d)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${duration === d ? 'bg-primary text-white' : 'border border-gray-300 text-gray-600 hover:bg-gray-50'}`}>
              {d} min
            </button>
          ))}
        </div>
        <button onClick={generate} disabled={loading}
          className="bg-primary text-white px-6 py-2.5 rounded-lg font-medium hover:bg-opacity-90 disabled:opacity-60 flex items-center gap-2">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mic className="w-4 h-4" />}
          {loading ? 'Gerando roteiro...' : 'Gerar Audio Overview'}
        </button>
      </>}
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-indigo-100 rounded-xl p-5">
        <h3 className="font-bold text-indigo-900">{script.titulo}</h3>
        <p className="text-indigo-600 text-sm mt-1">⏱ {script.duracao_estimada}</p>
      </div>
      <div className="space-y-3">
        {(script.roteiro || []).map((line: any, i: number) => (
          <div key={i} className={`flex gap-3 ${line.apresentador === 'ANA' ? '' : 'flex-row-reverse'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
              line.apresentador === 'ANA' ? 'bg-indigo-100 text-indigo-700' : 'bg-purple-100 text-purple-700'
            }`}>
              {line.apresentador === 'ANA' ? 'A' : 'P'}
            </div>
            <div className={`max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
              line.apresentador === 'ANA' ? 'bg-white border border-gray-200' : 'bg-purple-50 border border-purple-100'
            }`}>
              <p className={`text-xs font-semibold mb-1 ${line.apresentador === 'ANA' ? 'text-indigo-600' : 'text-purple-600'}`}>
                {line.apresentador}
              </p>
              <p className="text-gray-800">{line.fala}</p>
            </div>
          </div>
        ))}
      </div>
      <div className="flex gap-3 pt-2">
        <button onClick={() => navigator.clipboard.writeText(
          (script.roteiro || []).map((l: any) => `${l.apresentador}: ${l.fala}`).join('\n\n')
        )} className="text-sm border border-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-50 transition">
          Copiar Roteiro
        </button>
        <button onClick={() => setScript(null)}
          className="text-sm border border-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-50 transition ml-auto">
          Novo Roteiro
        </button>
      </div>
    </div>
  );
}

// ── Página Principal ─────────────────────────────────────────────────────────
const TABS: { id: Tab; label: string; icon: any; desc: string }[] = [
  { id: 'chat',        label: 'Chat',          icon: MessageCircle, desc: 'Converse com suas fontes' },
  { id: 'study-guide', label: 'Guia de Estudo', icon: BookOpen,      desc: 'Resumo estruturado' },
  { id: 'faq',         label: 'FAQ',            icon: HelpCircle,    desc: 'Perguntas frequentes' },
  { id: 'timeline',    label: 'Linha do Tempo', icon: Clock,         desc: 'Marcos históricos' },
  { id: 'audio',       label: 'Audio Overview', icon: Mic,           desc: 'Roteiro de podcast' },
];

export function Notebook() {
  const navigate = useNavigate();
  const data = useNotebookData();
  const [tab, setTab] = useState<Tab>('chat');
  const [serverKeys, setServerKeys] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetch(`${API_URL}/api/v1/config/status`)
      .then(res => res.json())
      .then(data => setServerKeys(data))
      .catch(() => {});
  }, []);

  if (!data.theme) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-gray-500">Nenhum projeto selecionado.</p>
        <button onClick={() => navigate('/projects')}
          className="text-primary text-sm font-medium hover:underline">
          ← Ir para Meus Projetos
        </button>
      </div>
    );
  }

  const resolvedApiKey = data.apiKey || (serverKeys[data.llmProvider?.toLowerCase()] ? 'server-fallback' : '');
  const tabProps = { ...data, apiKey: resolvedApiKey };
  const ActiveTab = {
    'chat':        <ChatTab        {...tabProps} />,
    'study-guide': <StudyGuideTab  {...tabProps} />,
    'faq':         <FaqTab         {...tabProps} />,
    'timeline':    <TimelineTab    {...tabProps} />,
    'audio':       <AudioTab       {...tabProps} />,
  }[tab];

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button onClick={() => navigate('/projects')}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-3 transition">
          <ArrowLeft className="w-4 h-4" /> Meus Projetos
        </button>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{data.theme}</h1>
            <p className="text-sm text-gray-500 mt-1">
              {data.papers.length} fontes científicas · Notebook AI
            </p>
          </div>
          <span className="bg-indigo-100 text-indigo-700 text-xs font-semibold px-3 py-1.5 rounded-full border border-indigo-200">
            🗒️ Notebook
          </span>
        </div>

        {/* Papers rápidos */}
        {data.papers.length > 0 && (
          <div className="mt-4 flex gap-2 flex-wrap">
            {data.papers.slice(0, 4).map((p: any, i: number) => (
              <span key={i} className="inline-flex items-center gap-1.5 bg-white border border-gray-200 text-gray-600 text-xs px-2.5 py-1 rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
                {p.authors?.split(';')[0]} {p.year}
                {p.url && (
                  <a href={p.url} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-primary">
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </span>
            ))}
            {data.papers.length > 4 && (
              <span className="text-xs text-gray-400 self-center">+{data.papers.length - 4} fontes</span>
            )}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl mb-6 overflow-x-auto">
        {TABS.map(t => {
          const Icon = t.icon;
          const active = tab === t.id;
          return (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition whitespace-nowrap flex-1 justify-center ${
                active ? 'bg-white text-primary shadow-sm border border-gray-200' : 'text-gray-600 hover:text-gray-800'
              }`}>
              <Icon className="w-4 h-4" />
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Conteúdo da aba */}
      <div className="bg-gray-50 rounded-xl border border-gray-200 p-6 min-h-[500px]">
        {ActiveTab}
      </div>
    </div>
  );
}
