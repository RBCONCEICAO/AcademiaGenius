import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FileText, MoreHorizontal, Clock, CheckCircle, SearchCode, Trash2, Eye, X, BookOpen, Sparkles } from 'lucide-react';
import type { Project, ProjectStatus } from '../types';
import { loadProjects, deleteProject } from '../lib/projectsStorage';
import { loadApiKeys } from '../lib/apiKeys';

const statusColorMap: Record<ProjectStatus, string> = {
  rascunho: 'bg-gray-100 text-gray-800 border-gray-200',
  pesquisando: 'bg-indigo-100 text-indigo-800 border-indigo-200',
  gerando_conteudo: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  revisando: 'bg-blue-100 text-blue-800 border-blue-200',
  concluido: 'bg-green-100 text-green-800 border-green-200',
  arquivado: 'bg-gray-100 text-gray-600 border-gray-200',
};

const statusIconMap: Record<ProjectStatus, React.ReactNode> = {
  rascunho: <FileText className="w-4 h-4 mr-1.5" />,
  pesquisando: <SearchCode className="w-4 h-4 mr-1.5" />,
  gerando_conteudo: <Clock className="w-4 h-4 mr-1.5" />,
  revisando: <FileText className="w-4 h-4 mr-1.5" />,
  concluido: <CheckCircle className="w-4 h-4 mr-1.5" />,
  arquivado: <FileText className="w-4 h-4 mr-1.5" />,
};

const formatStatus = (status: ProjectStatus) =>
  status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

export function Projects() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>(loadProjects);
  const [menuOpen, setMenuOpen] = useState<string | null>(null);
  const [viewing, setViewing] = useState<Project | null>(null);

  const handleDelete = (id: string) => {
    deleteProject(id);
    setProjects(loadProjects());
    setMenuOpen(null);
  };

  const handleView = (project: Project) => {
    setViewing(project);
    setMenuOpen(null);
  };

  return (
    <div className="max-w-7xl">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Meus Projetos</h1>
          <p className="mt-2 text-sm text-gray-600">
            Acompanhe todos os seus portfólios de geração autoral e pesquisas.
          </p>
        </div>
        <Link to="/"
          className="bg-primary text-white px-5 py-2.5 rounded-md font-medium hover:bg-opacity-90 transition shadow-sm text-sm">
          + Nova Pesquisa
        </Link>
      </div>

      <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Projeto / Tema
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  IA Motor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Criado em
                </th>
                <th className="relative px-6 py-3">
                  <span className="sr-only">Ações</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {projects.map((project) => (
                <tr key={project.id} className="hover:bg-gray-50 transition">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 bg-indigo-50 flex items-center justify-center rounded-lg text-primary shadow-sm border border-indigo-100">
                        <FileText className="h-5 w-5" />
                      </div>
                      <div className="ml-4 max-w-xs overflow-hidden">
                        <div className="text-sm font-semibold text-gray-900 truncate" title={project.titulo}>
                          {project.titulo}
                        </div>
                        <div className="text-xs text-gray-500 mt-0.5 truncate">{project.descricao}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${statusColorMap[project.status]}`}>
                      {statusIconMap[project.status]}
                      {formatStatus(project.status)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className="bg-gray-50 px-2 py-1 rounded text-xs border border-gray-200 font-medium text-gray-700">
                      {project.configuracoes?.llm || '—'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(project.created_at).toLocaleDateString('pt-BR')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right relative">
                    <button
                      onClick={() => setMenuOpen(menuOpen === project.id ? null : project.id)}
                      className="text-gray-400 hover:text-primary transition p-2 bg-gray-50 rounded-md hover:bg-indigo-50 border border-transparent hover:border-indigo-100">
                      <MoreHorizontal className="h-5 w-5" />
                    </button>
                    {menuOpen === project.id && (
                      <div className="absolute right-6 top-12 z-10 bg-white border border-gray-200 rounded-lg shadow-lg w-48 py-1">
                        <button
                          onClick={() => {
                              const keys = loadApiKeys();
                              const model = project.configuracoes?.llm || 'gemini-2.5-flash';
                              let provider = 'gemini';
                              if (model.startsWith('gpt') || model.startsWith('o1') || model.startsWith('o3')) {
                                provider = 'openai';
                              } else if (model.startsWith('claude')) {
                                provider = 'anthropic';
                              } else if (model.includes('llama') || model.includes('mixtral') || model.includes('gemma')) {
                                provider = 'groq';
                              } else if (model.includes('mistral')) {
                                provider = 'mistral';
                              }
                              const apiKey = keys[provider as keyof typeof keys] || keys.gemini || '';

                              navigate('/notebook', {
                                state: {
                                  theme: project.tema_pesquisa || project.titulo,
                                  document: project.configuracoes?.document || '',
                                  papers: project.configuracoes?.papers || [],
                                  llmModel: model,
                                  llmProvider: provider,
                                  apiKey: apiKey,
                                }
                              });
                              setMenuOpen(null);
                            }}
                          className="flex items-center gap-2 w-full px-4 py-2 text-sm text-indigo-700 hover:bg-indigo-50">
                          <BookOpen className="w-4 h-4" /> Abrir no Notebook
                        </button>
                        <button
                          onClick={() => {
                            navigate('/', {
                              state: {
                                loadProject: {
                                  theme: project.tema_pesquisa || project.titulo,
                                  doc_type: project.configuracoes?.doc_type || 'artigo',
                                  norm: project.configuracoes?.norm || 'ABNT',
                                  llm: project.configuracoes?.llm || 'gemini-2.5-flash',
                                  document: project.configuracoes?.document || '',
                                  papers: project.configuracoes?.papers || [],
                                  stats: {
                                    total_papers: project.configuracoes?.papers?.length || 0,
                                    total_citations: project.configuracoes?.total_citations || 0,
                                    norm: project.configuracoes?.norm || 'ABNT'
                                  }
                                }
                              }
                            });
                            setMenuOpen(null);
                          }}
                          className="flex items-center gap-2 w-full px-4 py-2 text-sm text-accent hover:bg-amber-50">
                          <Sparkles className="w-4 h-4" /> Continuar Pesquisa
                        </button>
                        <button
                          onClick={() => handleView(project)}
                          className="flex items-center gap-2 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                          <Eye className="w-4 h-4" /> Ver documento
                        </button>
                        <button
                          onClick={() => handleDelete(project.id)}
                          className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50">
                          <Trash2 className="w-4 h-4" /> Excluir
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {projects.length === 0 && (
            <div className="text-center py-16">
              <FileText className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 text-sm font-medium">Nenhum projeto salvo ainda.</p>
              <p className="text-gray-400 text-xs mt-1">
                Inicie uma pesquisa na página inicial e clique em "Salvar Projeto".
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Modal de visualização do documento */}
      {viewing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900 bg-opacity-60 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <div>
                <h3 className="text-lg font-bold text-gray-900">{viewing.titulo}</h3>
                <p className="text-xs text-gray-500 mt-0.5">{viewing.descricao}</p>
              </div>
              <button onClick={() => setViewing(null)} className="text-gray-400 hover:text-gray-600 p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            {viewing.configuracoes?.papers && (
              <div className="px-6 py-3 bg-gray-50 border-b border-gray-100">
                <p className="text-xs text-gray-500 font-medium">
                  {(viewing.configuracoes.papers as unknown[]).length} artigos analisados ·{' '}
                  {viewing.configuracoes.total_citations?.toLocaleString()} citações acumuladas ·{' '}
                  Norma {viewing.configuracoes.norm}
                </p>
              </div>
            )}

            <div className="flex-1 overflow-y-auto p-6">
              <pre className="whitespace-pre-wrap text-sm text-gray-800 leading-relaxed font-sans">
                {viewing.configuracoes?.document || 'Documento não disponível.'}
              </pre>
            </div>

            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex gap-3">
              <button
                onClick={() => navigator.clipboard.writeText(viewing.configuracoes?.document || '')}
                className="text-sm bg-primary text-white px-4 py-2 rounded-md hover:bg-opacity-90 transition">
                Copiar
              </button>
              <button
                onClick={() => {
                  navigate('/', {
                    state: {
                      loadProject: {
                        theme: viewing.tema_pesquisa || viewing.titulo,
                        doc_type: viewing.configuracoes?.doc_type || 'artigo',
                        norm: viewing.configuracoes?.norm || 'ABNT',
                        llm: viewing.configuracoes?.llm || 'gemini-2.5-flash',
                        document: viewing.configuracoes?.document || '',
                        papers: viewing.configuracoes?.papers || [],
                        stats: {
                          total_papers: viewing.configuracoes?.papers?.length || 0,
                          total_citations: viewing.configuracoes?.total_citations || 0,
                          norm: viewing.configuracoes?.norm || 'ABNT'
                        }
                      }
                    }
                  });
                  setViewing(null);
                }}
                className="text-sm bg-accent text-white px-4 py-2 rounded-md hover:bg-opacity-90 transition flex items-center gap-1">
                <Sparkles className="w-4 h-4" /> Continuar Pesquisa
              </button>
              <button onClick={() => setViewing(null)}
                className="text-sm border border-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-100 transition ml-auto">
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
