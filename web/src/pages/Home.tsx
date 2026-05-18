import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Loader2, X, CheckCircle, Search, Brain, FileText, ExternalLink, Download, FolderPlus, BookOpen, PlusCircle } from 'lucide-react';
import { getKeyForProvider, getSemanticScholarKey, loadApiKeys } from '../lib/apiKeys';
import type { ApiKeys } from '../lib/apiKeys';
import { createProject, saveProject } from '../lib/projectsStorage';
import { API_URL } from '../lib/config';

interface LLMOption {
  label: string;
  value: string;
  provider: string;
  keyHint: string;
}

const LLM_OPTIONS: LLMOption[] = [
  // --- Google ---
  { label: 'Gemini 2.5 Pro (Mais Inteligente)', value: 'gemini-2.5-pro', provider: 'gemini', keyHint: 'AIza...' },
  { label: 'Gemini 2.5 Flash (Mais Rápido)', value: 'gemini-2.5-flash', provider: 'gemini', keyHint: 'AIza...' },
  { label: 'Gemini 1.5 Pro', value: 'gemini-1.5-pro', provider: 'gemini', keyHint: 'AIza...' },
  { label: 'Gemini 1.5 Flash', value: 'gemini-1.5-flash', provider: 'gemini', keyHint: 'AIza...' },

  // --- OpenAI ---
  { label: 'OpenAI GPT-4.5 Preview', value: 'gpt-4.5-preview', provider: 'openai', keyHint: 'sk-...' },
  { label: 'OpenAI GPT-4o', value: 'gpt-4o', provider: 'openai', keyHint: 'sk-...' },
  { label: 'OpenAI GPT-4o-mini', value: 'gpt-4o-mini', provider: 'openai', keyHint: 'sk-...' },
  { label: 'OpenAI o3-mini', value: 'o3-mini', provider: 'openai', keyHint: 'sk-...' },
  { label: 'OpenAI o1', value: 'o1', provider: 'openai', keyHint: 'sk-...' },

  // --- Anthropic ---
  { label: 'Claude 3.7 Sonnet', value: 'claude-3-7-sonnet-20250219', provider: 'anthropic', keyHint: 'sk-ant-...' },
  { label: 'Claude 3.5 Sonnet', value: 'claude-3-5-sonnet-20241022', provider: 'anthropic', keyHint: 'sk-ant-...' },
  { label: 'Claude 3.5 Haiku', value: 'claude-3-5-haiku-20241022', provider: 'anthropic', keyHint: 'sk-ant-...' },
  { label: 'Claude 3 Opus', value: 'claude-3-opus-20240229', provider: 'anthropic', keyHint: 'sk-ant-...' },

  // --- Groq ---
  { label: 'Groq (Llama 3.3 70B)', value: 'llama-3.3-70b-versatile', provider: 'groq', keyHint: 'gsk_...' },
  { label: 'Groq (Mixtral 8x7B)', value: 'mixtral-8x7b-32768', provider: 'groq', keyHint: 'gsk_...' },
  { label: 'Groq (Gemma 2 9B)', value: 'gemma2-9b-it', provider: 'groq', keyHint: 'gsk_...' },

  // --- Mistral ---
  { label: 'Mistral Large', value: 'mistral-large-latest', provider: 'mistral', keyHint: 'api_key...' },
  { label: 'Mistral Small', value: 'mistral-small-latest', provider: 'mistral', keyHint: 'api_key...' },
];

const STEPS = [
  { id: 1, icon: Search, label: 'Buscando artigos científicos reais...', done: 'artigos encontrados' },
  { id: 2, icon: Brain, label: 'Construindo base de conhecimento...', done: 'conceitos extraídos' },
  { id: 3, icon: FileText, label: 'Redigindo documento acadêmico...', done: 'documento gerado' },
];

type StepStatus = 'idle' | 'running' | 'done';

interface Paper {
  title: string;
  authors: string;
  year: number | string;
  citation_count: number;
  doi: string;
  url: string;
  abnt_reference: string;
}

interface ResearchResult {
  document: string;
  papers: Paper[];
  stats: { total_papers: number; total_citations: number; norm: string };
}

interface ClarifyingQuestion {
  id: number;
  question: string;
  type: 'choice' | 'text';
  options?: string[];
}

export function Home() {
  const [showModal, setShowModal] = useState(false);
  const [modalStep, setModalStep] = useState<'setup' | 'clarifying'>('setup');
  const [clarifyingQuestions, setClarifyingQuestions] = useState<ClarifyingQuestion[]>([]);
  const [clarificationsAnswers, setClarificationsAnswers] = useState<Record<string, string>>({});
  const [clarifyLoading, setClarifyLoading] = useState(false);
  
  const [stepStatuses, setStepStatuses] = useState<StepStatus[]>(['idle', 'idle', 'idle']);
  const [loading, setLoading] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([]);
  const terminalEndRef = useRef<HTMLDivElement>(null);
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refinement, setRefinement] = useState<string>('');
  const [saveCount, setSaveCount] = useState(0);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [refinementFiles, setRefinementFiles] = useState<File[]>([]);
  const navigate = useNavigate();
  const location = useLocation();

  const [serverKeys, setServerKeys] = useState<Record<string, boolean>>({
    gemini: false,
    openai: false,
    anthropic: false,
    groq: false,
    mistral: false
  });

  useEffect(() => {
    const fetchServerConfig = async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/config/status`);
        if (res.ok) {
          const data = await res.json();
          setServerKeys(data);
        }
      } catch (e) {
        console.warn("Could not load server keys status:", e);
      }
    };
    fetchServerConfig();
  }, []);

  useEffect(() => {
    if (location.state?.loadProject) {
      const p = location.state.loadProject;
      setForm(f => ({
        ...f,
        theme: p.theme || '',
        doc_type: p.doc_type || 'artigo',
        norm: p.norm || 'ABNT',
        llm: p.llm || 'gemini-2.5-flash',
        api_key: getKeyForProvider(LLM_OPTIONS.find(o => o.value === p.llm)?.provider as any || 'gemini')
      }));
      setResult({
        document: p.document,
        papers: p.papers,
        stats: p.stats
      });
      // Clear router state to prevent reloading on next mount
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  // --- Terminal Logs Simulation ---
  const STEP_1_LOGS = [
    "Traduzindo tema central para busca científica internacional...",
    "Tema traduzido com sucesso para a base global.",
    "Consultando banco de dados do Semantic Scholar...",
    "Buscando publicações indexadas na base de dados PubMed...",
    "Buscando publicações indexadas no repositório CORE...",
    "Cruzando referências bibliográficas encontradas...",
    "Localizados 14 artigos científicos relevantes."
  ];

  const STEP_2_LOGS = [
    "Iniciando Agente de Alinhamento Semântico...",
    "Filtrando artigos com base nas respostas de escopo do Copiloto...",
    "Analisando compatibilidade de domínio dos artigos encontrados...",
    "Removendo artigos com sobreposição e desvios semânticos...",
    "Artigos cientificamente validados com sucesso!",
    "Extraindo dados estatísticos e métricas de impacto de citação...",
    "Agrupando base de conhecimento para a redação acadêmica..."
  ];

  const STEP_3_LOGS = [
    "Compilando base de conhecimento estruturada...",
    "Formatando referências científicas conforme as normas especificadas...",
    "Redigindo Introdução com contextualização do tema...",
    "Redigindo seção de Metodologia com base nos artigos selecionados...",
    "Desenvolvendo seção de Resultados e Discussão de dados...",
    "Estruturando conclusão e limitações do estudo...",
    "Finalizando formatação final do documento acadêmico..."
  ];

  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [terminalLogs]);

  useEffect(() => {
    if (!loading) {
      setTerminalLogs([]);
      return;
    }

    setTerminalLogs([
      `[${new Date().toLocaleTimeString()}] [SISTEMA] Inicializando pipeline de agentes do AcademiaGenius...`,
      `[${new Date().toLocaleTimeString()}] [SISTEMA] Conectando com a API do provedor de IA escolhido...`
    ]);

    let logIndex = 0;
    const interval = setInterval(() => {
      // Find which step is running
      const runningStepIndex = stepStatuses.findIndex(s => s === 'running');
      if (runningStepIndex === -1) return;

      let logPool = STEP_1_LOGS;
      let logPrefix = "BUSCA";
      if (runningStepIndex === 1) {
        logPool = STEP_2_LOGS;
        logPrefix = "FILTRO";
      } else if (runningStepIndex === 2) {
        logPool = STEP_3_LOGS;
        logPrefix = "REDATOR";
      }

      if (logIndex < logPool.length) {
        const nextLog = logPool[logIndex];
        setTerminalLogs(prev => [
          ...prev,
          `[${new Date().toLocaleTimeString()}] [${logPrefix}] ${nextLog}`
        ]);
        logIndex++;
      } else {
        setTerminalLogs(prev => [
          ...prev,
          `[${new Date().toLocaleTimeString()}] [${logPrefix}] Processando dados avançados da etapa...`
        ]);
      }
    }, 4000);

    return () => clearInterval(interval);
  }, [loading, stepStatuses]);

  const [form, setForm] = useState(() => {
    let defaultLlm = 'gemini-2.5-flash';
    let defaultProvider = 'gemini' as any;

    const keys = loadApiKeys();
    if (!keys.gemini) {
      const configuredOption = LLM_OPTIONS.find(o => keys[o.provider as keyof ApiKeys]);
      if (configuredOption) {
        defaultLlm = configuredOption.value;
        defaultProvider = configuredOption.provider as any;
      }
    }

    return {
      theme: '',
      doc_type: 'tcc',
      llm: defaultLlm,
      custom_llm: '',
      custom_provider: defaultProvider,
      api_key: keys[defaultProvider as keyof ApiKeys] || '',
      norm: 'ABNT',
      usePipeline: false,
    };
  });

  const selectedLLM = LLM_OPTIONS.find(o => o.value === form.llm) || { label: 'Custom', value: form.custom_llm, provider: form.custom_provider, keyHint: 'Chave...' };

  const handleLlmChange = (value: string) => {
    if (value === 'custom') {
      setForm(f => ({
        ...f,
        llm: 'custom',
        api_key: getKeyForProvider(f.custom_provider as any),
      }));
      return;
    }
    const opt = LLM_OPTIONS.find(o => o.value === value)!;
    setForm(f => ({
      ...f,
      llm: value,
      api_key: getKeyForProvider(opt.provider as any),
    }));
  };

  const applyStepsLog = (stepsLog: Array<{step: number; status: string}>) => {
    const statuses: StepStatus[] = ['idle', 'idle', 'idle'];
    for (const entry of stepsLog) {
      const idx = entry.step - 1;
      if (idx >= 0 && idx < 3) statuses[idx] = entry.status as StepStatus;
    }
    setStepStatuses([...statuses]);
  };

  const handleNextStep = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.theme.trim()) { setError('Informe o tema da pesquisa.'); return; }
    
    let currentApiKey = form.api_key.trim();
    const p = (form.llm === 'custom' ? form.custom_provider : selectedLLM.provider) as string;
    
    if (!currentApiKey) {
      currentApiKey = getKeyForProvider(p as any).trim();
      if (!currentApiKey && !serverKeys[p.toLowerCase()]) {
        setError('Informe sua API Key da IA escolhida.');
        return;
      }
      setForm(f => ({ ...f, api_key: currentApiKey }));
    }

    setClarifyLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/v1/research/clarify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          theme: form.theme,
          llm_provider: form.llm === 'custom' ? form.custom_provider : selectedLLM.provider,
          llm_model: form.llm === 'custom' ? form.custom_llm : form.llm,
          api_key: currentApiKey,
        })
      });
      const data = await response.json();
      if (response.ok && data.questions && data.questions.length > 0) {
        setClarifyingQuestions(data.questions);
        setClarificationsAnswers({});
        setModalStep('clarifying');
      } else {
        // Fallback para pesquisa direta se falhar
        handleResearch();
      }
    } catch (err) {
      console.error("Erro ao gerar perguntas de clarificação:", err);
      handleResearch();
    } finally {
      setClarifyLoading(false);
    }
  };

  const handleResearch = async () => {
    if (!form.theme.trim()) { setError('Informe o tema da pesquisa.'); return; }
    
    let currentApiKey = form.api_key.trim();
    const p = (form.llm === 'custom' ? form.custom_provider : selectedLLM.provider) as string;
    
    if (!currentApiKey) {
      currentApiKey = getKeyForProvider(p as any).trim();
      if (!currentApiKey && !serverKeys[p.toLowerCase()]) {
        setError('Informe sua API Key da IA escolhida.');
        return;
      }
      setForm(f => ({ ...f, api_key: currentApiKey }));
    }

    const currentDoc = result ? result.document : undefined;

    setLoading(true);
    setError(null);
    setResult(null);
    setShowModal(false);

    try {
      setStepStatuses(['running', 'idle', 'idle']);

      let extractedFilesText = '';
      const allFiles = [...attachedFiles, ...refinementFiles];
      if (allFiles.length > 0) {
        const formData = new FormData();
        allFiles.forEach(f => formData.append('files', f));
        try {
          const extractRes = await fetch(`${API_URL}/api/v1/extract_text`, {
            method: 'POST',
            body: formData
          });
          if (extractRes.ok) {
            const data = await extractRes.json();
            if (data.text) extractedFilesText = `\n\n[CONTEXTO ADICIONAL DE ARQUIVOS ANEXADOS]:\n${data.text}`;
          }
        } catch (e) {
          console.error("Erro ao extrair texto dos arquivos", e);
        }
      }

      const groqKey = getKeyForProvider('groq' as any);
      const isPipelineAvailable = !!groqKey && selectedLLM.provider !== 'groq';
      const enablePipeline = form.usePipeline && isPipelineAvailable;

      const fullTheme = form.theme 
        + (refinement ? `\n\nINSTRUÇÕES ADICIONAIS DE REFINAMENTO: ${refinement}` : '')
        + extractedFilesText;

      const payload = {
        theme: fullTheme,
        doc_type: form.doc_type,
        llm_provider: form.llm === 'custom' ? form.custom_provider : selectedLLM.provider,
        llm_model: form.llm === 'custom' ? form.custom_llm : form.llm,
        api_key: currentApiKey,
        norm: form.norm,
        paper_limit: 8,
        include_universities: true,
        semantic_scholar_key: getSemanticScholarKey() || undefined,
        pubmed_key: getKeyForProvider('pubmed' as any) || undefined,
        core_key: getKeyForProvider('core' as any) || undefined,
        groq_key: enablePipeline ? groqKey : undefined,
        existing_document: currentDoc,
        clarifications: Object.keys(clarificationsAnswers).length > 0 ? clarificationsAnswers : undefined,
      };

      const response = await fetch(`${API_URL}/api/v1/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Erro desconhecido na API.');

      if (data.steps_log) applyStepsLog(data.steps_log);
      else setStepStatuses(['done', 'done', 'done']);

      setResult(data as ResearchResult);
      setRefinement('');
      setRefinementFiles([]);
    } catch (err: any) {
      setError(err.message || 'Não foi possível conectar ao servidor.');
      setStepStatuses(['idle', 'idle', 'idle']);
    } finally {
      setLoading(false);
    }
  };

  const [projectSaved, setProjectSaved] = useState(false);

  const handleSaveProject = () => {
    if (!result) return;
    const dataHora = new Date().toLocaleString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
    const versionStr = saveCount > 0 ? ` (V${saveCount + 1} - ${dataHora})` : ` (${dataHora})`;
    const prj = createProject(
      form.theme + versionStr,
      form.doc_type,
      form.llm,
      result.document,
      result.papers,
      result.stats
    );
    prj.tema_pesquisa = form.theme;
    saveProject(prj);
    setProjectSaved(true);
    setSaveCount(s => s + 1);
    setTimeout(() => setProjectSaved(false), 3000);
  };

  const renderInteractiveDocument = (text: string, papers: any[]) => {
    // Regex splits by [1], [2], etc.
    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, i) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        const idx = parseInt(match[1], 10) - 1;
        const paper = papers[idx];
        if (paper) {
          return (
            <span key={i} className="group relative inline-block cursor-help text-indigo-700 font-bold bg-indigo-50 hover:bg-indigo-100 px-1 rounded mx-0.5 border border-indigo-200 transition-colors">
              {part}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block w-72 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl z-10 whitespace-normal text-left font-normal leading-relaxed">
                <p className="font-bold mb-1 text-indigo-200">{paper.title}</p>
                <p className="text-gray-300">{paper.authors} ({paper.year})</p>
                <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-900 rotate-45"></div>
              </div>
            </span>
          );
        }
      }
      return <span key={i}>{part}</span>;
    });
  };

  const handleOpenModal = () => {
    const provider = form.llm === 'custom' ? form.custom_provider : selectedLLM.provider;
    setForm(f => ({ ...f, api_key: getKeyForProvider(provider as any) }));
    setModalStep('setup');
    setClarifyingQuestions([]);
    setClarificationsAnswers({});
    setShowModal(true);
    setError(null);
    setResult(null);
    setStepStatuses(['idle','idle','idle']);
  };

  const openNotebookAI = () => {
    if (!result) return;
    const isCustom = form.llm === 'custom';
    navigate('/notebook', {
      state: {
        theme: form.theme,
        document: result.document,
        papers: result.papers,
        llmModel: isCustom ? form.custom_llm : form.llm,
        llmProvider: isCustom ? form.custom_provider : selectedLLM.provider,
        apiKey: form.api_key,
      }
    });
  };

  const handleDownloadDocx = async () => {
    if (!result) return;
    try {
      const response = await fetch(`${API_URL}/api/v1/export/docx`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: form.theme,
          document: result.document,
          norm: form.norm,
        }),
      });
      if (!response.ok) throw new Error('Falha ao gerar DOCX.');
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${form.theme.slice(0, 60)}.docx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || 'Erro ao baixar o documento.');
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Elegant Academic Editorial Header */}
      <div className="text-center mb-12 mt-4">
        <span className="text-[10px] font-bold text-slate-400 tracking-[0.25em] uppercase block mb-3">Plataforma de Investigação Científica</span>
        <h1 className="text-4xl font-serif-academic font-bold text-slate-900 leading-tight">AcademiaGenius</h1>
        <div className="w-16 h-[2px] bg-[#C5A880] mx-auto mt-4 mb-4"></div>
        <p className="text-base font-serif-academic italic text-slate-600 max-w-2xl mx-auto">
          Mecanismo autônomo de busca acadêmica integrado ao Semantic Scholar. Redação estruturada segundo normas científicas com fontes auditáveis.
        </p>
      </div>

      {/* Main Scholarly Desk Landing Card */}
      {!result && !loading && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-8 max-w-3xl mx-auto relative overflow-hidden bg-grid">
          <div className="absolute top-0 right-0 w-32 h-32 bg-[#C5A880]/5 rounded-bl-full pointer-events-none"></div>
          <h2 className="text-xs font-semibold tracking-wider text-slate-400 uppercase mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Ambiente de Trabalho Científico
          </h2>
          <h3 className="text-2xl font-serif-academic text-slate-800 font-bold mb-3">
            Pesquisa de Fontes e Redação Autônoma
          </h3>
          <p className="text-sm text-slate-500 leading-relaxed mb-6">
            O pipeline orquestra três agentes de IA para pesquisar bases científicas, qualificar as melhores fontes bibliográficas e redigir revisões bibliográficas rigorosas e estruturadas em formato acadêmico.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8 border-t border-b border-slate-100 py-6">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center shrink-0 border border-slate-200">
                <Search className="w-4 h-4 text-slate-700" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-800">1. Busca Bibliográfica</p>
                <p className="text-[11px] text-slate-500">Varredura no Semantic Scholar & PubMed</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center shrink-0 border border-slate-200">
                <Brain className="w-4 h-4 text-slate-700" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-800">2. Extração Semântica</p>
                <p className="text-[11px] text-slate-500">Filtro de papers por relevância e rigor</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center shrink-0 border border-slate-200">
                <FileText className="w-4 h-4 text-slate-700" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-800">3. Redação Acadêmica</p>
                <p className="text-[11px] text-slate-500">Revisão bibliográfica com citações reais</p>
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <span className="text-xs text-slate-400 font-serif-academic italic">Sem custos adicionais. Chave grátis ativada no servidor.</span>
            <button
              onClick={handleOpenModal}
              className="bg-slate-900 text-white px-6 py-3 rounded-xl font-medium hover:bg-slate-800 transition-all flex items-center gap-2 shadow-sm font-sans active:scale-[0.98]"
            >
              <BookOpen className="w-4 h-4 text-[#C5A880]" />
              Iniciar Nova Investigação
            </button>
          </div>
        </div>
      )}

      {/* Progresso dos Agentes */}
      {loading && (
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Status dos Agentes */}
          <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl shadow-sm p-6 flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-bold tracking-wider text-slate-800 mb-5 flex items-center gap-2 font-serif-academic uppercase">
                <Brain className="w-4 h-4 text-[#C5A880]" />
                Investigação Ativa
              </h3>
              <div className="space-y-4">
                {STEPS.map((step, i) => {
                  const status = stepStatuses[i];
                  const Icon = step.icon;
                  return (
                    <div key={step.id} className={`flex items-center gap-4 p-3.5 rounded-xl transition-all border ${
                      status === 'running' ? 'bg-[#FCFAF7] border-[#C5A880]/50 shadow-sm' :
                      status === 'done' ? 'bg-slate-50/50 border-slate-200' :
                      'bg-gray-50/30 border-gray-100'
                    }`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                        status === 'done' ? 'bg-green-100 animate-pulse' :
                        status === 'running' ? 'bg-slate-100 animate-spin animate-none' : 'bg-gray-100'
                      }`} style={{ animation: status === 'running' ? 'spin 3s linear infinite' : undefined }}>
                        {status === 'done' ? (
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        ) : status === 'running' ? (
                          <Loader2 className="w-5 h-5 text-slate-800 animate-spin" />
                        ) : (
                          <Icon className="w-5 h-5 text-slate-400" />
                        )}
                      </div>
                      <div>
                        <p className={`text-xs font-bold ${
                          status === 'running' ? 'text-slate-900' :
                          status === 'done' ? 'text-slate-800' : 'text-slate-400'
                        }`}>
                          Agente {step.id}: {status === 'done' ? `✓ ${step.done}` : step.label}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100 text-xs text-slate-400 text-center leading-relaxed font-serif-academic italic">
              O pipeline científico orquestra agentes de busca, extração e redação em tempo real.
            </div>
          </div>

          {/* Console de Logs */}
          <div className="lg:col-span-3 bg-slate-950 border border-slate-850 rounded-xl shadow-xl overflow-hidden flex flex-col h-[340px]">
            {/* Header do Terminal */}
            <div className="bg-slate-900/80 px-4 py-3 border-b border-slate-900 flex items-center justify-between shrink-0 select-none">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-800 block"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-slate-800 block"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-slate-800 block"></span>
              </div>
              <span className="text-xs font-mono font-bold text-slate-400 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping"></span>
                AUDITORIA_CIENTIFICA_LOG
              </span>
              <span className="text-[10px] font-mono text-slate-500 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                system
              </span>
            </div>

            {/* Corpo do Terminal */}
            <div className="p-4 flex-1 overflow-y-auto font-mono text-[11px] leading-relaxed text-slate-300 space-y-1.5 bg-slate-950/90">
              {terminalLogs.map((log, idx) => (
                <div key={idx} className="whitespace-pre-wrap select-all hover:bg-slate-900/50 px-1 rounded transition-colors">
                  {log}
                </div>
              ))}
              <div ref={terminalEndRef} />
            </div>
          </div>
        </div>
      )}

      {/* Erro */}
      {error && (
        <div className="mt-8 bg-red-50 border border-red-200 rounded-xl p-5 flex items-start gap-3 max-w-3xl mx-auto">
          <X className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold text-red-800">Erro no Pipeline Científico</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Resultado */}
      {result && (
        <div className="mt-8 space-y-8">
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <div className="bg-white border border-slate-200 rounded-xl p-5 text-center shadow-sm relative overflow-hidden">
              <div className="absolute top-0 inset-x-0 h-1 bg-[#C5A880]"></div>
              <p className="text-3xl font-serif-academic font-bold text-slate-900">{result.stats.total_papers}</p>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mt-2">Artigos Científicos Analisados</p>
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-5 text-center shadow-sm relative overflow-hidden">
              <div className="absolute top-0 inset-x-0 h-1 bg-slate-800"></div>
              <p className="text-3xl font-serif-academic font-bold text-slate-900">{result.stats.total_citations.toLocaleString()}</p>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mt-2">Citações Totais Consolidadas</p>
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-5 text-center shadow-sm relative overflow-hidden">
              <div className="absolute top-0 inset-x-0 h-1 bg-slate-900"></div>
              <p className="text-3xl font-serif-academic font-bold text-slate-750">{result.stats.norm}</p>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mt-2">Metodologia / Norma Aplicada</p>
            </div>
          </div>

          {/* Fontes Reais */}
          <div className="bg-[#FAF9F5] border border-slate-200 rounded-xl shadow-sm overflow-hidden max-w-4xl mx-auto">
            <div className="px-6 py-4 bg-white border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-xs font-bold tracking-wider text-slate-400 uppercase flex items-center gap-2">
                <BookOpen className="w-3.5 h-3.5 text-[#C5A880]" />
                Bibliografia & Referências Utilizadas
              </h3>
              <span className="text-xs text-slate-400 italic">Semantic Scholar & PubMed catalogados</span>
            </div>
            <ul className="divide-y divide-slate-100 bg-white">
              {result.papers.map((paper, i) => (
                <li key={i} className="px-6 py-4 flex items-start justify-between gap-4 hover:bg-slate-50/50 transition">
                  <div className="min-w-0 flex gap-4">
                    <span className="font-serif-academic font-bold text-[#C5A880] text-sm shrink-0">[{i + 1}]</span>
                    <div>
                      <p className="text-sm font-serif-academic font-bold text-slate-800 leading-snug">{paper.title}</p>
                      <p className="text-xs text-slate-500 mt-1">
                        <span className="italic font-serif-academic text-slate-600">{paper.authors}</span> · {paper.year} · <span className="font-mono text-[10px] bg-slate-50 border border-slate-200/60 px-1.5 py-0.5 rounded text-slate-500">{paper.citation_count} citações</span>
                      </p>
                    </div>
                  </div>
                  {paper.url && (
                    <a href={paper.url} target="_blank" rel="noopener noreferrer"
                      className="text-slate-400 hover:text-slate-800 shrink-0 p-1 hover:bg-slate-100 rounded transition-colors">
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Documento Gerado */}
          <div className="academic-paper rounded-xl overflow-hidden max-w-4xl mx-auto">
            <div className="px-8 py-5 bg-white border-b border-slate-200/60 flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold tracking-wider text-slate-400 uppercase">Artigo Científico Produzido</h3>
                <p className="text-xs text-slate-500 mt-0.5">Norma: {form.norm} · Processado por {selectedLLM.label}</p>
              </div>
              <span className="bg-slate-50 border border-slate-200 text-slate-600 text-xs px-3 py-1 rounded-full font-serif-academic italic">
                Citações Indexadas
              </span>
            </div>
            <div className="p-10 bg-white">
              {/* LaTeX-like paper display */}
              <div className="max-w-2xl mx-auto">
                <div className="whitespace-pre-wrap text-[15px] text-slate-800 leading-relaxed font-serif-academic space-y-4">
                  {renderInteractiveDocument(result.document, result.papers)}
                </div>
              </div>
            </div>

            {/* Refinamento Acadêmico */}
            <div className="p-8 border-t border-slate-200/60 bg-[#FAF9F5]/40">
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2.5">
                Refinar e Expandir Argumentação Científica
              </label>
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1 flex flex-col gap-3">
                  <textarea
                    className="w-full border border-slate-200 rounded-xl p-3.5 text-sm focus:outline-none focus:ring-2 focus:ring-slate-800 min-h-[90px] bg-white placeholder-slate-400"
                    placeholder="Ex: Expanda a análise estrutural da contenção mista e adicione mais dados sobre a deformação das estacas..."
                    value={refinement}
                    onChange={e => setRefinement(e.target.value)}
                  />
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Contexto Adicional (PDF, DOC, TXT) - Opcional</label>
                      <input type="file" multiple accept=".pdf,.doc,.docx,.txt,.md,.csv"
                        className="block w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-xl file:border-0 file:font-semibold file:bg-slate-100 file:text-slate-800 hover:file:bg-slate-200 cursor-pointer"
                        onChange={(e) => {
                          if (e.target.files) {
                            setRefinementFiles(Array.from(e.target.files));
                          }
                        }} />
                      {refinementFiles.length > 0 && (
                        <p className="text-xs text-slate-600 mt-1 font-serif-academic italic">✓ {refinementFiles.length} arquivo(s) anexado(s) para refinamento.</p>
                      )}
                    </div>
                  </div>
                </div>
                <button onClick={handleResearch} disabled={loading}
                  className="bg-slate-900 text-white px-6 py-4 rounded-xl hover:bg-slate-800 transition-all font-medium flex flex-col items-center justify-center gap-1.5 min-w-[150px] disabled:opacity-60 active:scale-[0.98]">
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <PlusCircle className="w-5 h-5 text-[#C5A880]" />}
                  <span className="text-xs font-bold tracking-wider uppercase">Aplicar Ajustes</span>
                </button>
              </div>
            </div>

            {/* Ações de Documento */}
            <div className="border-t border-slate-200/60 px-8 py-5 bg-slate-50/50 flex gap-3 flex-wrap items-center">
              <button onClick={() => navigator.clipboard.writeText(result.document)}
                className="text-xs font-bold tracking-wider uppercase border border-slate-200 text-slate-700 px-5 py-2.5 rounded-xl hover:bg-slate-100 transition active:scale-[0.98] bg-white">
                Copiar Texto
              </button>
              <button onClick={handleDownloadDocx}
                className="text-xs font-bold tracking-wider uppercase bg-slate-900 text-white px-5 py-2.5 rounded-xl hover:bg-slate-800 transition flex items-center gap-1.5 active:scale-[0.98]">
                <Download className="w-4 h-4 text-[#C5A880]" />
                Baixar DOCX
              </button>
              <button onClick={handleSaveProject}
                className="text-xs font-bold tracking-wider uppercase border border-slate-200 text-slate-700 px-5 py-2.5 rounded-xl hover:bg-slate-100 transition flex items-center gap-1.5 bg-white active:scale-[0.98]">
                <FolderPlus className="w-4 h-4 text-slate-500" />
                {projectSaved ? 'Versão Salva ✓' : 'Salvar Versão'}
              </button>
              
              <div className="ml-auto flex gap-3">
                <button onClick={openNotebookAI}
                  className="text-xs font-bold tracking-wider uppercase bg-[#C5A880] text-white px-5 py-2.5 rounded-xl hover:bg-[#B48E50] transition shadow-sm flex items-center gap-1.5 active:scale-[0.98]">
                  <BookOpen className="w-4 h-4" />
                  Abrir no Notebook AI
                </button>
                <button onClick={() => { setResult(null); setProjectSaved(false); setRefinement(''); setSaveCount(0); }}
                  className="text-xs font-bold tracking-wider uppercase border border-slate-200 text-slate-700 px-5 py-2.5 rounded-xl hover:bg-slate-100 transition bg-white active:scale-[0.98]">
                  Nova Investigação
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-2xl p-8 max-w-xl w-full shadow-2xl border border-slate-200/80 mx-4">
            <div className="flex items-center justify-between mb-6 border-b border-slate-100 pb-4">
              <h3 className="text-lg font-serif-academic font-bold text-slate-900 flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-slate-700" />
                {modalStep === 'setup' ? 'Parâmetros de Investigação' : 'Delimitação de Escopo Científico'}
              </h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600 p-1 hover:bg-slate-50 rounded-full transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalStep === 'setup' ? (
              <form className="space-y-5" onSubmit={handleNextStep}>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">Tema Central / Objeto de Estudo *</label>
                  <input type="text" placeholder="Ex: Análise de tensões em contenções mistas com PLAXIS 2D"
                    className="block w-full border border-slate-200 rounded-xl py-2.5 px-4 focus:outline-none focus:ring-2 focus:ring-slate-800 text-sm placeholder-slate-400 bg-[#FCFAF7]"
                    value={form.theme} onChange={(e) => setForm({ ...form, theme: e.target.value })} />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">Anexar Documentos de Base (PDF, DOCX, TXT) - Opcional</label>
                  <input type="file" multiple accept=".pdf,.doc,.docx,.txt,.md,.csv"
                    className="block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-100 file:text-slate-800 hover:file:bg-slate-200 cursor-pointer"
                    onChange={(e) => {
                      if (e.target.files) {
                        setAttachedFiles(Array.from(e.target.files));
                      }
                    }} />
                  {attachedFiles.length > 0 && (
                    <p className="text-xs text-slate-600 mt-1.5 font-serif-academic italic">✓ {attachedFiles.length} documento(s) anexado(s) para contextualização.</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">Formato de Saída</label>
                    <select className="block w-full border border-slate-200 rounded-xl py-2.5 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-slate-800 text-sm bg-[#FCFAF7] text-slate-800"
                      value={form.doc_type} onChange={(e) => setForm({ ...form, doc_type: e.target.value })}>
                      <option value="artigo">Artigo Científico</option>
                      <option value="tcc">Monografia / TCC</option>
                      <option value="estudo">Estudo de Caso</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">Normas Metodológicas</label>
                    <select className="block w-full border border-slate-200 rounded-xl py-2.5 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-slate-800 text-sm bg-[#FCFAF7] text-slate-800"
                      value={form.norm} onChange={(e) => setForm({ ...form, norm: e.target.value })}>
                      <option value="ABNT">ABNT (Brasil)</option>
                      <option value="APA">APA Style</option>
                      <option value="Vancouver">Vancouver</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">Mecanismo de Redação (LLM)</label>
                  <select className="block w-full border border-slate-200 rounded-xl py-2.5 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-slate-800 text-sm bg-[#FCFAF7] text-slate-800"
                    value={form.llm} onChange={(e) => handleLlmChange(e.target.value)}>
                    {LLM_OPTIONS.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                    <option value="custom">⚙️ Especificar outro modelo</option>
                  </select>
                </div>
                {form.llm === 'custom' && (
                  <div className="grid grid-cols-2 gap-3 p-4 bg-slate-50 border border-slate-200 rounded-xl mt-1">
                    <div>
                      <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">Identificador do Modelo</label>
                      <input type="text" placeholder="Ex: gpt-4o-mini" 
                        className="block w-full border border-slate-200 rounded-lg py-2 px-3 text-sm focus:ring-slate-800 bg-white"
                        value={form.custom_llm} onChange={e => setForm({...form, custom_llm: e.target.value})} />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">Provedor</label>
                      <select className="block w-full border border-slate-200 rounded-lg py-2 px-3 text-sm focus:ring-slate-800 bg-white text-slate-800"
                        value={form.custom_provider} onChange={e => {
                          const p = e.target.value;
                          setForm({...form, custom_provider: p, api_key: getKeyForProvider(p as any)});
                        }}>
                        <option value="openai">OpenAI</option>
                        <option value="anthropic">Anthropic</option>
                        <option value="gemini">Google Gemini</option>
                        <option value="groq">Groq</option>
                        <option value="mistral">Mistral</option>
                      </select>
                    </div>
                  </div>
                )}

                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider">Credencial da API — {selectedLLM.label}</label>
                    {serverKeys[((form.llm === 'custom' ? form.custom_provider : selectedLLM.provider) as string).toLowerCase()] && (
                      <span className="text-[10px] bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full font-bold border border-emerald-200 animate-pulse">
                        ✓ Chave Integrada Ativa no Servidor
                      </span>
                    )}
                  </div>
                  <input type="password" 
                    placeholder={
                      serverKeys[((form.llm === 'custom' ? form.custom_provider : selectedLLM.provider) as string).toLowerCase()]
                        ? "Usando chave pré-configurada no servidor (Grátis)"
                        : selectedLLM.keyHint
                    }
                    className="block w-full border border-slate-200 rounded-xl py-2.5 px-4 focus:outline-none focus:ring-2 focus:ring-slate-800 text-sm font-mono bg-[#FCFAF7]"
                    value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} />
                  <p className="text-[10px] text-slate-400 mt-1 font-serif-academic italic">
                    {serverKeys[((form.llm === 'custom' ? form.custom_provider : selectedLLM.provider) as string).toLowerCase()]
                      ? "Processamento gratuito via chaves integradas de forma segura."
                      : "Sua credencial de API é salva estritamente local no seu navegador."}
                  </p>
                </div>

                {getKeyForProvider('groq' as any) && selectedLLM.provider !== 'groq' && (
                  <div className="bg-emerald-50/50 border border-emerald-200 rounded-xl p-4">
                    <label className="flex items-start gap-3 cursor-pointer">
                      <input type="checkbox" className="mt-1 w-4 h-4 text-emerald-600 rounded border-emerald-300 focus:ring-emerald-500"
                        checked={form.usePipeline} onChange={(e) => setForm({ ...form, usePipeline: e.target.checked })} />
                      <div>
                        <span className="text-xs font-bold text-emerald-950 block">Ativar Pré-Processamento Científico ⚡</span>
                        <span className="text-[11px] text-emerald-700 leading-snug block mt-0.5">
                          Usa a tecnologia Groq de ultra-baixa latência para extração bibliográfica e reserva o {selectedLLM.label} para a redação acadêmica final.
                        </span>
                      </div>
                    </label>
                  </div>
                )}

                {error && <p className="text-xs font-semibold text-red-600">{error}</p>}

                <div className="pt-3 border-t border-slate-100 flex justify-end gap-3">
                  <button type="button" onClick={() => setShowModal(false)}
                    className="px-4 py-2.5 border border-slate-200 rounded-xl text-slate-600 hover:bg-slate-50 text-sm font-medium transition active:scale-[0.98]">
                    Cancelar
                  </button>
                  <button type="submit" disabled={clarifyLoading}
                    className="bg-slate-900 text-white px-6 py-2.5 rounded-xl hover:bg-slate-800 text-sm font-semibold flex items-center gap-2 disabled:opacity-50 transition active:scale-[0.98]">
                    {clarifyLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Qualificando Objeto...
                      </>
                    ) : (
                      <>
                        <span>Avançar para Filtros</span>
                        <span>→</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-6">
                <div className="bg-slate-50 rounded-xl p-4.5 border border-slate-200/60">
                  <p className="text-xs text-slate-600 leading-relaxed font-serif-academic italic">
                    💡 <strong>Delimitação de Objeto Acadêmico:</strong> Responda às perguntas formuladas pelos agentes para otimizar os filtros de exclusão e precisão bibliográfica.
                  </p>
                </div>

                <div className="space-y-5 max-h-[350px] overflow-y-auto pr-1">
                  {clarifyingQuestions.map((q) => (
                    <div key={q.id} className="space-y-2">
                      <label className="block text-sm font-serif-academic font-bold text-slate-800 leading-snug">
                        {q.question}
                      </label>
                      {q.type === 'choice' && q.options ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1.5">
                          {q.options.map((opt) => {
                            const isSelected = clarificationsAnswers[q.question] === opt;
                            return (
                              <button
                                key={opt}
                                type="button"
                                onClick={() => setClarificationsAnswers({
                                  ...clarificationsAnswers,
                                  [q.question]: opt
                                })}
                                className={`text-left p-3.5 rounded-xl border text-xs font-bold leading-normal transition-all duration-200 ${
                                  isSelected
                                    ? 'bg-slate-900 border-slate-900 text-white shadow-md scale-[1.01]'
                                    : 'bg-[#FCFAF7] border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300'
                                }`}
                              >
                                {opt}
                              </button>
                            );
                          })}
                        </div>
                      ) : (
                        <input
                           type="text"
                           placeholder="Responda para melhor detalhar..."
                           className="block w-full border border-slate-200 rounded-xl py-2.5 px-4 focus:outline-none focus:ring-2 focus:ring-slate-800 text-sm bg-[#FCFAF7] text-slate-800 placeholder-slate-400 transition"
                           value={clarificationsAnswers[q.question] || ''}
                           onChange={(e) => setClarificationsAnswers({
                             ...clarificationsAnswers,
                             [q.question]: e.target.value
                           })}
                        />
                      )}
                    </div>
                  ))}
                </div>

                {error && <p className="text-xs font-semibold text-red-600">{error}</p>}

                <div className="pt-4 flex justify-between gap-3 border-t border-slate-100">
                  <button type="button" onClick={() => setModalStep('setup')}
                    className="px-4 py-2.5 border border-slate-200 rounded-xl text-slate-600 hover:bg-slate-50 text-sm font-medium transition active:scale-[0.98]">
                    Voltar
                  </button>
                  <button type="button" onClick={handleResearch}
                    className="bg-slate-900 text-white px-6 py-2.5 rounded-xl hover:bg-slate-800 text-sm font-bold flex items-center gap-2 shadow-sm transition active:scale-[0.98]">
                    <Search className="w-4 h-4" />
                    Iniciar Investigação
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
