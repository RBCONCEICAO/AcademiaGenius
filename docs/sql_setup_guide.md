Supabase Setup Guide
          
Project: AcademiaGenius

          
            Version 1.0
            Status: Approved
            Confidential
          
      
      
        
    
    
        Como Principal DBA, com profunda expertise em Supabase (PostgreSQL, RLS, Edge Functions, Auth, Realtime), React e Python (FastAPI, Pydantic), apresento um script de inicialização SQL robusto e um guia de implementação detalhado para o seu aplicativo de geração de TCC, Estudo de Caso e Artigos Científicos. Este esquema é otimizado para a pilha tecnológica selecionada e incorpora as melhores práticas de segurança e escalabilidade.
    

    
## 1. O Script SQL de Inicialização

    
        Este script cria as tabelas necessárias, define chaves primárias e estrangeiras, configura índices para otimização de consultas, implementa Row Level Security (RLS) para garantir a segurança dos dados do usuário e adiciona funcionalidades de busca textual avançada.
    
    

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
-- Tabela: projetos
-- Representa um projeto de geração de conteúdo (TCC, Artigo, Estudo de Caso).
--
CREATE TABLE public.projetos (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL, -- Vincula ao usuário que criou o projeto
    titulo text NOT NULL,
    descricao text,
    tema_pesquisa text NOT NULL, -- O tema informado pelo usuário
    status project_status DEFAULT 'rascunho' NOT NULL,
    configuracoes jsonb DEFAULT '{}'::jsonb, -- Configurações específicas do projeto (ex: formato de saída, estilo)
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

-- Índices para otimização
CREATE INDEX idx_projetos_user_id ON public.projetos (user_id);
CREATE INDEX idx_projetos_status ON public.projetos (status);
CREATE INDEX idx_projetos_created_at ON public.projetos (created_at);

-- Triggers para 'updated_at'
CREATE TRIGGER set_timestamp_projetos
BEFORE UPDATE ON public.projetos
FOR EACH ROW
EXECUTE PROCEDURE update_timestamp();

--
-- Row Level Security (RLS) para 'projetos'
--
ALTER TABLE public.projetos ENABLE ROW LEVEL SECURITY;

-- Política para permitir que usuários acessem apenas seus próprios projetos
CREATE POLICY "Usuários podem acessar seus próprios projetos." ON public.projetos
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);


--
-- Tabela: documentos_fonte
-- Armazena os artigos, estudos de caso e documentos relevantes encontrados para um projeto.
--
CREATE TABLE public.documentos_fonte (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    projeto_id uuid REFERENCES public.projetos(id) ON DELETE CASCADE NOT NULL,
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
    projeto_id uuid REFERENCES public.projetos(id) ON DELETE CASCADE NOT NULL,
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
    projeto_id uuid REFERENCES public.projetos(id) ON DELETE CASCADE NOT NULL,
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
GRANT ALL ON public.projetos TO anon, authenticated;
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



    
## 2. Guia de Implementação


    
### Passo a Passo: Como Rodar Este Script

    
        
            **Crie um Projeto Supabase:**
            

                - Acesse o Dashboard do Supabase.
                - Clique em "New project" e siga as instruções para criar um novo projeto. Escolha uma região próxima aos seus usuários ou ao seu backend Vercel.
            

        
        
            **Acesse o SQL Editor:**
            

                - Após a criação do projeto, navegue até a seção "SQL Editor" no menu lateral esquerdo do seu dashboard Supabase.
            

        
        
            **Execute o Script:**
            

                - No SQL Editor, você verá uma área para digitar ou colar comandos SQL.
                - Copie todo o conteúdo do "Script SQL de Inicialização" fornecido acima.
                - Cole o script na área do editor e clique no botão "Run" (geralmente um ícone de "play").
                - Verifique a saída para garantir que todas as tabelas, índices, triggers e políticas RLS foram criados com sucesso.
            

        
        
            **Verifique as Tabelas e RLS:**
            

                - Vá para a seção "Table Editor" no Supabase para confirmar que todas as tabelas (`profiles`, `projetos`, `documentos_fonte`, `conhecimento_base`, `conteudo_gerado`) foram criadas.
                - Na seção "Authentication" > "Policies", você deve ver as políticas RLS listadas para cada tabela. Confirme que estão habilitadas.
            

        
        
            **Teste a Autenticação:**
            

                - Crie um novo usuário através da interface de autenticação do Supabase ou via sua aplicação React/FastAPI.
                - Verifique se um registro correspondente é automaticamente criado na tabela `public.profiles`, graças ao trigger `handle_new_user`.
            

        
    

    
### Melhores Práticas de Segurança

    

        
            **Row Level Security (RLS) Imediata:** O script já habilita e configura RLS para todas as tabelas sensíveis. É crucial que você nunca desabilite o RLS em produção. Ele garante que os usuários só possam acessar seus próprios dados.
        
        
            **Nunca Exponha a Chave de Serviço (Service Role Key):** A chave `anon` do Supabase é segura para uso no frontend. A `service_role` key tem privilégios de superusuário e deve ser usada apenas no backend (FastAPI) ou em Edge Functions (Vercel) e nunca exposta ao cliente.
        
        
            **Variáveis de Ambiente:** Armazene todas as chaves e URLs do Supabase como variáveis de ambiente no Vercel (para Edge Functions/Serverless Functions) e no seu ambiente de desenvolvimento Python/FastAPI.
        
        
            **Validação de Entrada no Backend:** Embora o banco de dados tenha restrições, sempre valide e sanitize todas as entradas de dados no seu backend FastAPI usando Pydantic antes de enviá-las ao Supabase. Isso previne injeções SQL e outros ataques.
        
        
            **Rate Limiting:** Implemente rate limiting no seu backend FastAPI e/ou nas Edge Functions da Vercel para proteger contra ataques de força bruta e uso excessivo da API.
        
        
            **Monitoramento e Logs:** Monitore regularmente os logs do Supabase e do Vercel para identificar atividades suspeitas ou erros.
        
    


    
### Gerenciamento de Migrações

    
        À medida que seu aplicativo evolui, você precisará fazer alterações no esquema do banco de dados. O Supabase CLI é a ferramenta recomendada para gerenciar migrações de forma eficiente e segura.
    
    
        
            **Instale o Supabase CLI:**
            

npm install -g supabase
# ou
brew install supabase/supabase/supabase

        
        
            **Inicialize o Projeto Localmente:**
            

                No diretório raiz do seu projeto (onde você tem seu código React/Python), execute:
                    

supabase init
supabase login
supabase link --project-ref <YOUR_SUPABASE_PROJECT_REF>

                
                - O `project-ref` pode ser encontrado na URL do seu dashboard Supabase (ex: `https://app.supabase.com/project/<project-ref>/...`).
            

        
        
            **Puxe o Esquema Atual:**
            

                Para sincronizar seu ambiente local com o esquema atual do Supabase (após rodar o script inicial), execute:
                    

supabase db pull

                
                - Isso criará um arquivo `schema.sql` no diretório `supabase/migrations` que representa o estado atual do seu banco de dados.
            

        
        
            **Crie uma Nova Migração:**
            

                - Quando precisar fazer uma alteração no esquema (ex: adicionar uma nova coluna, criar uma nova tabela), faça as alterações no seu banco de dados local (se estiver usando `supabase start`) ou diretamente no arquivo `schema.sql` (com cuidado).
                Em seguida, gere um novo arquivo de migração:
                    

supabase migration new nome_da_sua_migracao

                
                - O CLI tentará detectar as diferenças e gerar um arquivo SQL com os comandos `ALTER TABLE` necessários. Revise este arquivo cuidadosamente.
            

        
        
            **Aplique a Migração:**
            

                Para aplicar a migração ao seu banco de dados remoto (Supabase), execute:
                    

supabase db push

                
                - É altamente recomendável testar as migrações em um ambiente de staging antes de aplicá-las em produção.
            

        
    
    
        Seguindo estas diretrizes, você terá uma base de dados segura, escalável e fácil de manter para o seu aplicativo de geração de conteúdo científico.