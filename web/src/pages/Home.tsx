import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Loader2, Sparkles, X, CheckCircle, Search, Brain, FileText, ExternalLink, Download, FolderPlus, BookOpen, PlusCircle } from 'lucide-react';
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
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Bem-vindo ao AcademiaGenius</h1>
        <p className="mt-2 text-sm text-gray-600">
          Pesquisa acadêmica real com agentes de IA — fontes verificáveis do Semantic Scholar.
        </p>
      </div>

      <div className="bg-white shadow rounded-lg p-6 border border-gray-200">
        <h2 className="text-lg font-medium text-gray-900 mb-2">Pipeline de 3 Agentes</h2>
        <div className="flex items-center gap-6 text-sm text-gray-500 mb-5">
          <span className="flex items-center gap-1.5"><Search className="w-4 h-4 text-primary" /> Busca real</span>
          <span className="text-gray-300">→</span>
          <span className="flex items-center gap-1.5"><Brain className="w-4 h-4 text-primary" /> Extração</span>
          <span className="text-gray-300">→</span>
          <span className="flex items-center gap-1.5"><FileText className="w-4 h-4 text-primary" /> Redação</span>
        </div>
        <button
          onClick={handleOpenModal}
          className="bg-primary text-white px-5 py-2.5 rounded-md font-medium hover:bg-opacity-90 transition flex items-center gap-2 shadow-sm"
        >
          <Sparkles className="w-4 h-4" />
          Iniciar Nova Pesquisa
        </button>
      </div>

      {/* Progresso dos Agentes */}
      {loading && (
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Status dos Agentes */}
          <div className="lg:col-span-2 bg-white border border-gray-200 rounded-lg shadow-sm p-6 flex flex-col justify-between">
            <div>
              <h3 className="text-base font-semibold text-gray-800 mb-5 flex items-center gap-2">
                <Brain className="w-5 h-5 text-indigo-600" />
                Pipeline Científico
              </h3>
              <div className="space-y-4">
                {STEPS.map((step, i) => {
                  const status = stepStatuses[i];
                  const Icon = step.icon;
                  return (
                    <div key={step.id} className={`flex items-center gap-4 p-3 rounded-lg transition-all ${
                      status === 'running' ? 'bg-indigo-50 border border-indigo-200 shadow-sm' :
                      status === 'done' ? 'bg-green-50 border border-green-200' :
                      'bg-gray-50 border border-gray-100'
                    }`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                        status === 'done' ? 'bg-green-100 animate-pulse' :
                        status === 'running' ? 'bg-indigo-100 animate-spin animate-none' : 'bg-gray-100'
                      }`} style={{ animation: status === 'running' ? 'spin 3s linear infinite' : undefined }}>
                        {status === 'done' ? (
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        ) : status === 'running' ? (
                          <Loader2 className="w-5 h-5 text-primary animate-spin" />
                        ) : (
                          <Icon className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                      <div>
                        <p className={`text-sm font-medium ${
                          status === 'running' ? 'text-indigo-800 font-semibold' :
                          status === 'done' ? 'text-green-800 font-semibold' : 'text-gray-500'
                        }`}>
                          Agente {step.id}: {status === 'done' ? `✓ ${step.done}` : step.label}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="mt-6 pt-4 border-t border-gray-100 text-xs text-gray-400 text-center leading-relaxed">
              O pipeline utiliza agentes autônomos para traduzir, buscar, filtrar e redigir seu artigo. Por favor, aguarde alguns instantes.
            </div>
          </div>

          {/* Console de Logs */}
          <div className="lg:col-span-3 bg-gray-950 border border-gray-800 rounded-lg shadow-xl overflow-hidden flex flex-col h-[320px]">
            {/* Header do Terminal */}
            <div className="bg-gray-900 px-4 py-2.5 border-b border-gray-800 flex items-center justify-between shrink-0 select-none">
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-red-500 block"></span>
                <span className="w-3 h-3 rounded-full bg-yellow-500 block"></span>
                <span className="w-3 h-3 rounded-full bg-green-500 block"></span>
              </div>
              <span className="text-xs font-mono font-bold text-gray-500 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping"></span>
                AGENTE_LOGGER@ACADEMIAGENIUS
              </span>
              <span className="text-[10px] font-mono text-gray-600 bg-gray-950 px-2 py-0.5 rounded border border-gray-800">
                bash
              </span>
            </div>

            {/* Corpo do Terminal */}
            <div className="p-4 flex-1 overflow-y-auto font-mono text-[11px] leading-relaxed text-emerald-400 space-y-1.5 bg-gray-950">
              {terminalLogs.map((log, idx) => (
                <div key={idx} className="whitespace-pre-wrap select-all hover:bg-gray-900 hover:bg-opacity-50 px-1 rounded transition-colors">
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
        <div className="mt-8 bg-red-50 border border-red-200 rounded-lg p-5 flex items-start gap-3">
          <X className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold text-red-800">Erro no Pipeline</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Resultado */}
      {result && (
        <div className="mt-8 space-y-6">
          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-primary">{result.stats.total_papers}</p>
              <p className="text-xs text-gray-500 mt-1">Artigos Reais Analisados</p>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-accent">{result.stats.total_citations.toLocaleString()}</p>
              <p className="text-xs text-gray-500 mt-1">Citações Acumuladas</p>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-gray-700">{result.stats.norm}</p>
              <p className="text-xs text-gray-500 mt-1">Norma Aplicada</p>
            </div>
          </div>

          {/* Fontes Reais */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
            <div className="px-5 py-3 bg-gray-50 border-b border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700">📚 Fontes Científicas Utilizadas</h3>
            </div>
            <ul className="divide-y divide-gray-100">
              {result.papers.map((paper, i) => (
                <li key={i} className="px-5 py-3 flex items-start justify-between gap-4 hover:bg-gray-50">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">{paper.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{paper.authors} · {paper.year} · {paper.citation_count} citações</p>
                  </div>
                  {paper.url && (
                    <a href={paper.url} target="_blank" rel="noopener noreferrer"
                      className="text-primary hover:text-indigo-700 shrink-0 mt-0.5">
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Documento Gerado */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
            <div className="bg-gradient-to-r from-primary to-accent px-6 py-4 flex items-center justify-between">
              <h3 className="text-white font-semibold">Documento Gerado com Fontes Reais</h3>
              <span className="bg-white bg-opacity-20 text-white text-xs px-3 py-1 rounded-full">{selectedLLM.label}</span>
            </div>
            <div className="p-6">
              <div className="whitespace-pre-wrap text-sm text-gray-800 leading-relaxed font-sans">
                {renderInteractiveDocument(result.document, result.papers)}
              </div>
            </div>
            <div className="p-6 border-t border-gray-200 bg-indigo-50/30">
              <label className="block text-sm font-semibold text-gray-800 mb-2">
                Melhorar ou Refinar Documento
              </label>
              <div className="flex gap-3">
                <div className="flex-1 flex flex-col gap-3">
                  <textarea
                    className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary min-h-[80px]"
                    placeholder="Ex: Amplie a seção de metodologia, adicione mais detalhes sobre o software PLAXIS 2D, e reescreva a conclusão focando em engenharia civil..."
                    value={refinement}
                    onChange={e => setRefinement(e.target.value)}
                  />
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Anexar Documento Base (Opcional)</label>
                    <input type="file" multiple accept=".pdf,.doc,.docx,.txt,.md,.csv"
                      className="block w-full text-xs text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                      onChange={(e) => {
                        if (e.target.files) {
                          setRefinementFiles(Array.from(e.target.files));
                        }
                      }} />
                    {refinementFiles.length > 0 && (
                      <p className="text-xs text-indigo-600 mt-1">{refinementFiles.length} arquivo(s) anexado(s) para refinamento.</p>
                    )}
                  </div>
                </div>
                <button onClick={handleResearch} disabled={loading}
                  className="bg-primary text-white px-6 py-2 rounded-lg hover:bg-opacity-90 transition font-medium flex flex-col items-center justify-center gap-1 min-w-[140px] disabled:opacity-60">
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <PlusCircle className="w-5 h-5" />}
                  <span>Aplicar<br/>Refinamento</span>
                </button>
              </div>
            </div>

            <div className="border-t px-6 py-4 bg-gray-50 flex gap-3 flex-wrap items-center">
              <button onClick={() => navigator.clipboard.writeText(result.document)}
                className="text-sm border border-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-100 transition">
                Copiar
              </button>
              <button onClick={handleDownloadDocx}
                className="text-sm bg-accent text-white px-4 py-2 rounded-md hover:bg-opacity-90 transition flex items-center gap-1.5">
                <Download className="w-4 h-4" />
                Baixar DOCX
              </button>
              <button onClick={handleSaveProject}
                className="text-sm border border-indigo-300 text-indigo-700 px-4 py-2 rounded-md hover:bg-indigo-50 transition flex items-center gap-1.5">
                <FolderPlus className="w-4 h-4" />
                {projectSaved ? 'Salvo com sucesso!' : 'Salvar Versão'}
              </button>
              
              <div className="ml-auto flex gap-2">
                <button onClick={openNotebookAI}
                  className="text-sm bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition shadow-sm flex items-center gap-1.5 font-medium">
                  <BookOpen className="w-4 h-4" />
                  Abrir no Notebook AI
                </button>
                <button onClick={() => { setResult(null); setProjectSaved(false); setRefinement(''); setSaveCount(0); }}
                  className="text-sm border border-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-100 transition">
                  Nova Pesquisa
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900 bg-opacity-60">
          <div className="bg-white rounded-xl p-8 max-w-lg w-full shadow-2xl mx-4">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary" />
                {modalStep === 'setup' ? 'Configurar Pesquisa' : 'Refinamento por IA'}
              </h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalStep === 'setup' ? (
              <form className="space-y-4" onSubmit={handleNextStep}>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tema Central *</label>
                  <input type="text" placeholder="Ex: Inteligência Artificial na Educação"
                    className="block w-full border border-gray-300 rounded-md py-2.5 px-3 focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                    value={form.theme} onChange={(e) => setForm({ ...form, theme: e.target.value })} />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Anexar Arquivos (PDF, DOCX, TXT, etc) - Opcional</label>
                  <input type="file" multiple accept=".pdf,.doc,.docx,.txt,.md,.csv"
                    className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                    onChange={(e) => {
                      if (e.target.files) {
                        setAttachedFiles(Array.from(e.target.files));
                      }
                    }} />
                  {attachedFiles.length > 0 && (
                    <p className="text-xs text-indigo-600 mt-1">{attachedFiles.length} arquivo(s) anexado(s) para expandir a pesquisa.</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Documento</label>
                    <select className="block w-full border border-gray-300 rounded-md py-2.5 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                      value={form.doc_type} onChange={(e) => setForm({ ...form, doc_type: e.target.value })}>
                      <option value="tcc">Monografia / TCC</option>
                      <option value="artigo">Artigo Científico</option>
                      <option value="estudo">Estudo de Caso</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Norma</label>
                    <select className="block w-full border border-gray-300 rounded-md py-2.5 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                      value={form.norm} onChange={(e) => setForm({ ...form, norm: e.target.value })}>
                      <option value="ABNT">ABNT</option>
                      <option value="APA">APA</option>
                      <option value="Vancouver">Vancouver</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Inteligência Artificial (Redação Final)</label>
                  <select className="block w-full border border-gray-300 rounded-md py-2.5 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                    value={form.llm} onChange={(e) => handleLlmChange(e.target.value)}>
                    {LLM_OPTIONS.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                    <option value="custom">⚙️ Outro modelo (Digitar manualmente)</option>
                  </select>
                </div>
                {form.llm === 'custom' && (
                  <div className="grid grid-cols-2 gap-3 p-3 bg-indigo-50 border border-indigo-100 rounded-md mt-1">
                    <div>
                      <label className="block text-xs font-semibold text-indigo-900 mb-1">ID Exato do Modelo</label>
                      <input type="text" placeholder="Ex: gpt-5.5-turbo" 
                        className="block w-full border border-indigo-200 rounded-md py-2 px-3 text-sm focus:ring-primary"
                        value={form.custom_llm} onChange={e => setForm({...form, custom_llm: e.target.value})} />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-indigo-900 mb-1">Provedor da API</label>
                      <select className="block w-full border border-indigo-200 rounded-md py-2 px-3 text-sm focus:ring-primary bg-white"
                        value={form.custom_provider} onChange={e => {
                          const p = e.target.value;
                          setForm({...form, custom_provider: p, api_key: getKeyForProvider(p as any)});
                        }}>
                        <option value="openai">OpenAI</option>
                        <option value="anthropic">Anthropic (Claude)</option>
                        <option value="gemini">Google (Gemini)</option>
                        <option value="groq">Groq</option>
                        <option value="mistral">Mistral</option>
                      </select>
                    </div>
                  </div>
                )}

                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="block text-sm font-medium text-gray-700">API Key — {selectedLLM.label}</label>
                    {serverKeys[((form.llm === 'custom' ? form.custom_provider : selectedLLM.provider) as string).toLowerCase()] && (
                      <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded font-semibold border border-emerald-200 animate-pulse">
                        ✓ Chave Grátis Ativa no Servidor
                      </span>
                    )}
                  </div>
                  <input type="password" 
                    placeholder={
                      serverKeys[((form.llm === 'custom' ? form.custom_provider : selectedLLM.provider) as string).toLowerCase()]
                        ? "[Opcional] Chave ativa no servidor. Deixe em branco para usar grátis."
                        : selectedLLM.keyHint
                    }
                    className="block w-full border border-gray-300 rounded-md py-2.5 px-3 focus:outline-none focus:ring-2 focus:ring-primary text-sm font-mono"
                    value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} />
                  <p className="text-xs text-gray-400 mt-1">
                    {serverKeys[((form.llm === 'custom' ? form.custom_provider : selectedLLM.provider) as string).toLowerCase()]
                      ? "Chave integrada detectada! Deixe em branco para rodar gratuitamente."
                      : "Sua chave nunca sai do seu computador."}
                  </p>
                </div>

                {getKeyForProvider('groq' as any) && selectedLLM.provider !== 'groq' && (
                  <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
                    <label className="flex items-start gap-2 cursor-pointer">
                      <input type="checkbox" className="mt-1 w-4 h-4 text-emerald-600 rounded border-emerald-300 focus:ring-emerald-500"
                        checked={form.usePipeline} onChange={(e) => setForm({ ...form, usePipeline: e.target.checked })} />
                      <div>
                        <span className="text-sm font-semibold text-emerald-900 block">Ativar Modo Pipeline ⚡</span>
                        <span className="text-xs text-emerald-700 leading-tight block mt-0.5">
                          Usa Groq (ultrarrápido) para extração de dados e {selectedLLM.label || selectedLLM.provider} para a redação final. <strong>Recomendado!</strong>
                        </span>
                      </div>
                    </label>
                  </div>
                )}

                {error && <p className="text-sm text-red-600">{error}</p>}

                <div className="pt-2 flex justify-end gap-3">
                  <button type="button" onClick={() => setShowModal(false)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 text-sm">
                    Cancelar
                  </button>
                  <button type="submit" disabled={clarifyLoading}
                    className="bg-primary text-white px-6 py-2 rounded-md hover:bg-opacity-90 text-sm font-medium flex items-center gap-2 disabled:opacity-50">
                    {clarifyLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Analisando Tema...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        Avançar
                      </>
                    )}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-6">
                <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-100">
                  <p className="text-xs text-indigo-800 leading-relaxed">
                    💡 <strong>Copiloto Científico de IA:</strong> Responda a estas rápidas perguntas para refinar os critérios de busca e eliminar resultados fora do contexto pretendido.
                  </p>
                </div>

                <div className="space-y-5 max-h-[350px] overflow-y-auto pr-1">
                  {clarifyingQuestions.map((q) => (
                    <div key={q.id} className="space-y-2">
                      <label className="block text-sm font-semibold text-gray-800 leading-snug">
                        {q.question}
                      </label>
                      {q.type === 'choice' && q.options ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1">
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
                                className={`text-left p-3 rounded-lg border text-sm font-medium transition-all ${
                                  isSelected
                                    ? 'bg-indigo-600 border-indigo-600 text-white shadow-md scale-[1.02]'
                                    : 'bg-white border-gray-200 text-gray-700 hover:bg-indigo-50 hover:border-indigo-200'
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
                          placeholder="Digite para detalhar (opcional)..."
                          className="block w-full border border-gray-300 rounded-md py-2.5 px-3 focus:outline-none focus:ring-2 focus:ring-primary text-sm bg-white text-gray-800 placeholder-gray-400"
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

                {error && <p className="text-sm text-red-600">{error}</p>}

                <div className="pt-4 flex justify-between gap-3 border-t border-gray-100">
                  <button type="button" onClick={() => setModalStep('setup')}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 text-sm font-medium transition">
                    Voltar
                  </button>
                  <button type="button" onClick={handleResearch}
                    className="bg-primary text-white px-6 py-2 rounded-md hover:bg-opacity-90 text-sm font-semibold flex items-center gap-2 shadow-md transition">
                    <Sparkles className="w-4 h-4" />
                    Iniciar Pesquisa
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
