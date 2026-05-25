-- Auto-extracted from PRD Stacks SQL Guide
-- Generated: 2026-04-14T02:27:44.177Z



-- Habilita extensões essenciais para UUIDs, busca textual e similaridade de texto
-- 'uuid-ossp' para geração de UUIDs (alternativa: 'pgcrypto' com gen_random_uuid())
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- 'unaccent' para busca textual sem acentos
CREATE EXTENSION IF NOT EXISTS "unaccent";
-- 'pg_trgm' para busca por similaridade de texto (útil para encontrar artigos "melhores" ou "relacionados")
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

--
-- Tipos ENUM para status de projetos e conteúdo gerado
--
CREATE TYPE project_status AS ENUM ('rascunho', 'pesquisando', 'gerando_conteudo', 'revisando', 'concluido', 'arquivado');
CREATE TYPE content_status AS ENUM ('rascunho', 'gerado', 'revisado', 'finalizado', 'publicado');

--
-- Função de trigger para atualizar automaticamente a coluna 'updated_at'
--
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

--
-- Tabela: profiles
-- Armazena informações adicionais do usuário, vinculadas ao sistema de autenticação do Supabase (auth.users).
--
CREATE TABLE public.profiles (
    id uuid REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    nome_completo text,
    avatar_url text,
    -- Adicione outras colunas de perfil conforme necessário
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

-- Índices para otimização
CREATE INDEX idx_profiles_created_at ON public.profiles (created_at);

-- Triggers para 'updated_at'
CREATE TRIGGER set_timestamp_profiles
BEFORE UPDATE ON public.profiles
FOR EACH ROW
EXECUTE PROCEDURE update_timestamp();

--
-- Row Level Security (RLS) para 'profiles'
--
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Política para permitir que usuários vejam e editem seu próprio perfil
CREATE POLICY "Usuários podem ver e editar seu próprio perfil." ON public.profiles
FOR ALL USING (auth.uid() = id) WITH CHECK (auth.uid() = id);


--
-- Tabela: projects
-- Representa um projeto de geração de conteúdo (TCC, Artigo, Estudo de Caso).
--
CREATE TABLE public.projects (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    titulo text NOT NULL,
    descricao text,
    tema_pesquisa text NOT NULL,
    status project_status DEFAULT 'rascunho' NOT NULL,
    configuracoes jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

-- Índices para otimização
CREATE INDEX idx_projects_user_id ON public.projects (user_id);
CREATE INDEX idx_projects_status ON public.projects (status);
CREATE INDEX idx_projects_created_at ON public.projects (created_at);

-- Triggers para 'updated_at'
CREATE TRIGGER set_timestamp_projects
BEFORE UPDATE ON public.projects
FOR EACH ROW
EXECUTE PROCEDURE update_timestamp();

--
-- Row Level Security (RLS) para 'projects'
--
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

-- Política para permitir que usuários acessem apenas seus próprios projetos
CREATE POLICY "Usuários podem acessar seus próprios projetos." ON public.projects
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);


--
-- Tabela: documentos_fonte
-- Armazena os artigos, estudos de caso e documentos relevantes encontrados para um projeto.
--
CREATE TABLE public.documentos_fonte (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    projeto_id uuid REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL, -- Para RLS direto
    titulo text NOT NULL,
    autores text,
    url text,
    data_publicacao date,
    resumo text,
    conteudo_texto text, -- Conteúdo completo ou parcial do documento, para análise
    metadata jsonb DEFAULT '{}'::jsonb, -- Metadados adicionais (ex: DOI, editora, palavras-chave)
    relevancia integer DEFAULT 0, -- Pontuação de relevância (pode ser calculada ou manual)
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    -- Coluna gerada para busca textual completa (Full-Text Search)
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('portuguese', coalesce(titulo, '')), 'A') ||
        setweight(to_tsvector('portuguese', coalesce(autores, '')), 'B') ||
        setweight(to_tsvector('portuguese', coalesce(resumo, '')), 'C') ||
        setweight(to_tsvector('portuguese', coalesce(conteudo_texto, '')), 'D')
    ) STORED
);

-- Índices para otimização
CREATE INDEX idx_documentos_fonte_projeto_id ON public.documentos_fonte (projeto_id);
CREATE INDEX idx_documentos_fonte_user_id ON public.documentos_fonte (user_id);
CREATE INDEX idx_documentos_fonte_data_publicacao ON public.documentos_fonte (data_publicacao DESC);
CREATE INDEX idx_documentos_fonte_relevancia ON public.documentos_fonte (relevancia DESC);
-- Índice GIN para a coluna de busca textual completa
CREATE INDEX idx_documentos_fonte_search_vector ON public.documentos_fonte USING GIN (search_vector);

-- Triggers para 'updated_at'
CREATE TRIGGER set_timestamp_documentos_fonte
BEFORE UPDATE ON public.documentos_fonte
FOR EACH ROW
EXECUTE PROCEDURE update_timestamp();

--
-- Row Level Security (RLS) para 'documentos_fonte'
--
ALTER TABLE public.documentos_fonte ENABLE ROW LEVEL SECURITY;

-- Política para permitir que usuários acessem apenas documentos de seus próprios projetos
CREATE POLICY "Usuários podem acessar documentos de seus próprios projetos." ON public.documentos_fonte
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);


--
-- Tabela: conhecimento_base
-- Armazena a "memória" ou base de conhecimento estruturada extraída dos documentos fonte.
-- Isso pode incluir resumos sintetizados, conceitos-chave, citações importantes, etc.
--
CREATE TABLE public.conhecimento_base (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    projeto_id uuid REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL, -- Para RLS direto
    documento_fonte_id uuid REFERENCES public.documentos_fonte(id) ON DELETE SET NULL, -- Opcional: de qual documento veio
    tipo_informacao text, -- Ex: 'resumo', 'conceito_chave', 'citacao', 'analise'
    conteudo text NOT NULL, -- O texto do conhecimento extraído
    dados_extraidos jsonb DEFAULT '{}'::jsonb, -- Dados estruturados (ex: { "conceito": "...", "definicao": "..." })
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

-- Índices para otimização
CREATE INDEX idx_conhecimento_base_projeto_id ON public.conhecimento_base (projeto_id);
CREATE INDEX idx_conhecimento_base_user_id ON public.conhecimento_base (user_id);
CREATE INDEX idx_conhecimento_base_documento_fonte_id ON public.conhecimento_base (documento_fonte_id);

-- Triggers para 'updated_at'
CREATE TRIGGER set_timestamp_conhecimento_base
BEFORE UPDATE ON public.conhecimento_base
FOR EACH ROW
EXECUTE PROCEDURE update_timestamp();

--
-- Row Level Security (RLS) para 'conhecimento_base'
--
ALTER TABLE public.conhecimento_base ENABLE ROW LEVEL SECURITY;

-- Política para permitir que usuários acessem apenas a base de conhecimento de seus próprios projetos
CREATE POLICY "Usuários podem acessar a base de conhecimento de seus próprios projetos." ON public.conhecimento_base
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);


--
-- Tabela: conteudo_gerado
-- Armazena o conteúdo final gerado (TCC, Artigo, Estudo de Caso).
--
CREATE TABLE public.conteudo_gerado (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    projeto_id uuid REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL, -- Para RLS direto
    titulo text NOT NULL,
    formato text, -- Ex: 'TCC', 'Artigo Científico', 'Estudo de Caso'
    conteudo_final text NOT NULL, -- O texto completo do conteúdo gerado
    status content_status DEFAULT 'rascunho' NOT NULL,
    versao integer DEFAULT 1 NOT NULL, -- Controle de versão do conteúdo
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

-- Índices para otimização
CREATE INDEX idx_conteudo_gerado_projeto_id ON public.conteudo_gerado (projeto_id);
CREATE INDEX idx_conteudo_gerado_user_id ON public.conteudo_gerado (user_id);
CREATE INDEX idx_conteudo_gerado_status ON public.conteudo_gerado (status);

-- Triggers para 'updated_at'
CREATE TRIGGER set_timestamp_conteudo_gerado
BEFORE UPDATE ON public.conteudo_gerado
FOR EACH ROW
EXECUTE PROCEDURE update_timestamp();

--
-- Row Level Security (RLS) para 'conteudo_gerado'
--
ALTER TABLE public.conteudo_gerado ENABLE ROW LEVEL SECURITY;

-- Política para permitir que usuários acessem apenas o conteúdo gerado de seus próprios projetos
CREATE POLICY "Usuários podem acessar o conteúdo gerado de seus próprios projetos." ON public.conteudo_gerado
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);


--
-- Configuração inicial para a função de perfil (opcional, mas recomendado)
-- Esta função é executada automaticamente pelo Supabase Auth quando um novo usuário é criado.
-- Ela cria um registro na tabela 'profiles' para cada novo usuário.
--
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, nome_completo, avatar_url)
  VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'avatar_url');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

--
-- Trigger para 'handle_new_user'
--
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

--
-- Permissões para a função 'handle_new_user'
--
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO anon, authenticated;

--
-- Permissões para as tabelas (apenas para o serviço anon/authenticated, RLS cuidará do resto)
--
GRANT ALL ON public.profiles TO anon, authenticated;
GRANT ALL ON public.projects TO anon, authenticated;
GRANT ALL ON public.documentos_fonte TO anon, authenticated;
GRANT ALL ON public.conhecimento_base TO anon, authenticated;
GRANT ALL ON public.conteudo_gerado TO anon, authenticated;

--
-- Permissões para as sequências (se houver, para colunas SERIAL)
-- Embora não tenhamos SERIAL aqui, é uma boa prática incluir.
--
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
GRANT ALL ON TABLES TO anon, authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
GRANT ALL ON SEQUENCES TO anon, authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
GRANT ALL ON FUNCTIONS TO anon, authenticated;



supabase migration new nome_da_sua_migracao


-- =====================



supabase db push
