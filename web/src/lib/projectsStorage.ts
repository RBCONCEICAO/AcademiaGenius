import type { Project } from '../types';

const STORAGE_KEY = 'academiagenius_projects';

export function loadProjects(): Project[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as Project[];
  } catch {
    return [];
  }
}

export function saveProject(project: Project): void {
  const projects = loadProjects().filter(p => p.id !== project.id);
  projects.unshift(project);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(projects));
}

export function deleteProject(id: string): void {
  const projects = loadProjects().filter(p => p.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(projects));
}

export function createProject(
  theme: string,
  docType: string,
  llmModel: string,
  document: string,
  papers: any[],
  stats: any,
): Project {
  return {
    id: crypto.randomUUID(),
    user_id: 'local',
    titulo: theme,
    descricao: `${docType.toUpperCase()} · ${String(stats.norm ?? 'ABNT')}`,
    tema_pesquisa: theme,
    status: 'concluido',
    configuracoes: {
      llm: llmModel,
      doc_type: docType,
      norm: stats.norm,
      total_papers: stats.total_papers,
      total_citations: stats.total_citations,
      document,
      papers,
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}
