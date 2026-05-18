export type ProjectStatus = 'rascunho' | 'pesquisando' | 'gerando_conteudo' | 'revisando' | 'concluido' | 'arquivado';

export interface Profile {
  id: string;
  nome_completo: string | null;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectConfig {
  llm: string;
  doc_type: string;
  norm: string;
  total_papers: number;
  total_citations: number;
  document: string;
  papers: any[];
}

export interface Project {
  id: string;
  user_id: string;
  titulo: string;
  descricao: string | null;
  tema_pesquisa: string;
  status: ProjectStatus;
  configuracoes: ProjectConfig;
  created_at: string;
  updated_at: string;
}
