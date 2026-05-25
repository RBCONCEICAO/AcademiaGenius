import { supabase } from './supabase';
import type { Project } from '../types';

// ── Helpers ─────────────────────────────────────────────────────────────────

async function currentUserId(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  return data.session?.user.id ?? null;
}

// ── CRUD ────────────────────────────────────────────────────────────────────

export async function loadProjects(): Promise<Project[]> {
  const userId = await currentUserId();
  if (!userId) return [];

  const { data, error } = await supabase
    .from('projects')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (error) {
    console.error('Erro ao carregar projetos:', error.message);
    return [];
  }
  return (data ?? []) as Project[];
}

export async function saveProject(project: Project): Promise<void> {
  const userId = await currentUserId();
  if (!userId) return;

  const { error } = await supabase
    .from('projects')
    .upsert({ ...project, user_id: userId, updated_at: new Date().toISOString() });

  if (error) console.error('Erro ao salvar projeto:', error.message);
}

export async function deleteProject(id: string): Promise<void> {
  const userId = await currentUserId();
  if (!userId) return;

  const { error } = await supabase
    .from('projects')
    .delete()
    .eq('id', id)
    .eq('user_id', userId);

  if (error) console.error('Erro ao excluir projeto:', error.message);
}

// ── Factory (síncrono — só cria o objeto, não persiste) ──────────────────────

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
    user_id: '',
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
