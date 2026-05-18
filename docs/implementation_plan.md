Technical Implementation Plan
          
Project: AcademiaGenius

          
            Version 1.0
            Status: Approved
            Confidential
          
      
      
        
  
    
      🏗️ Estrutura do Projeto (Opinião de Arquiteto)
    
    
      Adotaremos uma estrutura de monorepo para simplificar o gerenciamento de dependências e permitir o compartilhamento de tipos entre o frontend e o backend, o que é crucial para nossa filosofia de Type Safety. Esta organização oferece clareza, modularidade e escalabilidade.
    
    
projeto-tcc/
├── web/                  # Frontend React com Vite
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── services/     # Requisições API (usando TanStack Query)
│   │   ├── store/        # Zustand stores
│   │   ├── styles/       # Tailwind CSS
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── api/                  # Backend FastAPI (Python)
│   ├── app/
│   │   ├── api/          # Endpoints FastAPI
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── projects.py
│   │   │   │   └── documents.py
│   │   │   └── __init__.py
│   │   ├── core/         # Configurações (settings, logger, auth)
│   │   ├── db/           # Interação com Supabase (SQLAlchemy, pool)
│   │   ├── models/       # Pydantic models para request/response
│   │   ├── services/     # Lógica de negócio (busca, geração, KG)
│   │   └── main.py       # Aplicação FastAPI principal
│   ├── tests/
│   ├── .env.example
│   ├── Dockerfile
│   ├── requirements.txt
│   └── uvicorn_run.py
├── supabase/             # Gerenciamento Supabase (migrações, RLS, Edge Functions)
│   ├── migrations/       # Scripts de migração SQL
│   ├── functions/        # Supabase Edge Functions (Deno/TypeScript)
│   │   └── auth-webhook.ts
│   └── seed.sql
├── shared/               # Tipos e Schemas compartilhados
│   ├── src/
│   │   ├── types.ts      # Tipos TypeScript (derivados de Pydantic/Zod)
│   │   └── schemas.ts    # Zod schemas para validação em runtime (opcional)
│   └── tsconfig.json
├── .github/
│   └── workflows/        # CI/CD com GitHub Actions
│       ├── web-ci.yml
│       └── api-ci.yml
├── .env.example
├── .gitignore
└── README.md

    
      **Justificativa:**
      

        - `web/` e `api/` isolam as responsabilidades de frontend e backend.
        - `supabase/` centraliza toda a lógica de banco de dados, facilitando a gestão de esquema e segurança.
        - `shared/` é vital para a **type safety**: definimos interfaces e schemas uma vez, usando Pydantic para o Python e gerando tipos TypeScript para o frontend, garantindo consistência e reduzindo erros em tempo de execução.
        - O uso de Vite para o React garante um desenvolvimento rápido e builds otimizados.
        - FastAPI é a escolha ideal para o backend Python devido ao seu desempenho assíncrono e validação Pydantic integrada.
      

    
  

  
    
      🚀 Fase 1: A Fundação de Ferro
    

    
      Variáveis de Ambiente & Validação Estrita (Zod/Pydantic)
    
    
      A segurança e a robustez começam com a configuração adequada das variáveis de ambiente. Usaremos **Zod** no frontend (TypeScript) e **Pydantic** no backend (Python) para garantir que todas as variáveis essenciais estejam presentes e no formato correto, falhando rapidamente em caso de erro de configuração.
    
    
# .env (exemplo)
VITE_SUPABASE_URL="https://your-project-id.supabase.co"
VITE_SUPABASE_ANON_KEY="your-anon-key"
DATABASE_URL="postgresql://..." # Para o backend FastAPI
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key" # Usado apenas no backend
EXTERNAL_SEARCH_API_KEY="your-external-api-key"

    
      **Exemplo de Validação Frontend (web/src/config/env.ts):**
    
    
import { z } from 'zod';

const envSchema = z.object({
  VITE_SUPABASE_URL: z.string().url(),
  VITE_SUPABASE_ANON_KEY: z.string().min(1),
  // Outras variáveis específicas do frontend
});

export const env = envSchema.parse(import.meta.env);

    
      As variáveis de ambiente serão gerenciadas no Vercel Dashboard para o deployment, garantindo que nunca sejam expostas publicamente (exceto as chaves `VITE_` que são públicas por design no Vite).
    

    
      Estratégia de CI/CD (GitHub Actions)
    
    
      Implementaremos pipelines de CI/CD robustos usando **GitHub Actions** para automatizar testes, linting, build e deployment, garantindo a qualidade e a velocidade de entrega.
    
    
      
        **`web-ci.yml` (Frontend React):**
        

          - Gatilho: `push` e `pull_request` para o diretório `web/`.
          - Passos: Instalar dependências, rodar `eslint`, `prettier`, testes unitários (Vitest/Jest), e build da aplicação.
          - Deployment: No `push` para `main`, deploy automático para Vercel.
        

      
      
        **`api-ci.yml` (Backend FastAPI):**
        

          - Gatilho: `push` e `pull_request` para o diretório `api/`.
          - Passos: Configurar ambiente Python, instalar dependências, rodar `black` (formatação), `flake8` (linting), testes unitários (Pytest).
          - Deployment: O deployment do backend FastAPI para Vercel será configurado para o diretório `api/` via `vercel.json` ou as configurações do projeto Vercel, ativando as Serverless Functions Python.
        

      
      
        **`supabase-migrations.yml` (Opcional - para automação):**
        

          - Gatilho: `push` para o diretório `supabase/migrations/` (ou manualmente).
          - Passos: Rodar `supabase migration up` em um ambiente de staging/desenvolvimento. Para produção, a aplicação de migrações pode ser manual ou semi-automática para garantir revisão.
        

      
    
    
      Para o deploy no Vercel, faremos uso das integrações diretas com GitHub, configurando os diretórios `web` e `api` como projetos separados ou subdiretórios em um monorepo, aproveitando as Vercel Serverless Functions para o backend Python.
    
  

  
    
      💾 Fase 2: Estratégia de Dados e Estado
    

    
      Migrações de Banco de Dados (Supabase CLI & RLS)
    
    
      Utilizaremos o **Supabase CLI** para gerenciar as migrações do PostgreSQL, garantindo um controle de versão robusto do nosso esquema de banco de dados.
    
    
      
        **Inicialização:** `supabase init` para configurar o projeto local.
      
      
        **Criação de Migrações:** `supabase migration new <nome_da_migracao>` para gerar arquivos SQL.
      
      
        **Aplicação:** `supabase db diff` para verificar as mudanças e `supabase db push` (ou `supabase db reset` durante o desenvolvimento) para aplicar as migrações. Em produção, `supabase migration up`.
      
      
        **Esquema Inicial (Exemplo):**
        
-- supabase/migrations/YYYYMMDDHHMMSS_initial_schema.sql
CREATE TABLE IF NOT EXISTS public.users (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  email text UNIQUE NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.projects (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
  title text NOT NULL,
  theme text NOT NULL,
  status text DEFAULT 'draft' NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.documents (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id uuid REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
  title text NOT NULL,
  authors text[],
  publication_year int,
  summary text,
  url text,
  content text, -- Armazenar o conteúdo completo para processamento
  vector_embedding vector(1536), -- Para busca semântica futura
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.knowledge_graph_nodes (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id uuid REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
  document_id uuid REFERENCES public.documents(id) ON DELETE CASCADE, -- Opcional, nó pode ser um conceito abstrato
  type text NOT NULL, -- e.g., 'concept', 'methodology', 'result', 'source'
  value text NOT NULL,
  metadata jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.knowledge_graph_edges (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id uuid REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
  source_node_id uuid REFERENCES public.knowledge_graph_nodes(id) ON DELETE CASCADE NOT NULL,
  target_node_id uuid REFERENCES public.knowledge_graph_nodes(id) ON DELETE CASCADE NOT NULL,
  type text NOT NULL, -- e.g., 'relates_to', 'supports', 'refers_to'
  metadata jsonb,
  created_at timestamptz DEFAULT now()
);

-- Habilitar RLS para tabelas sensíveis
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_graph_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_graph_edges ENABLE ROW LEVEL SECURITY;

-- Políticas RLS: Usuários só podem ver/modificar seus próprios projetos e dados relacionados
CREATE POLICY "Users can view their own projects." ON public.projects
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create projects." ON public.projects
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own projects." ON public.projects
  FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own projects." ON public.projects
  FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view project documents." ON public.documents
  FOR SELECT USING (EXISTS (SELECT 1 FROM public.projects WHERE public.projects.id = documents.project_id AND public.projects.user_id = auth.uid()));
CREATE POLICY "Users can insert project documents." ON public.documents
  FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM public.projects WHERE public.projects.id = documents.project_id AND public.projects.user_id = auth.uid()));
-- ... e assim por diante para update/delete em documents, knowledge_graph_nodes, knowledge_graph_edges

      
    
    
      **RLS (Row Level Security) é Mandatório:** As políticas acima garantem que cada usuário só possa acessar os dados (projetos, documentos, nós do grafo) que ele criou ou aos quais tem permissão, reforçando a segurança no nível do banco de dados, independente da camada de aplicação. Usaremos o **Supabase Auth** para gerenciar usuários e `auth.uid()` para as políticas RLS.
    

    
      Gerenciamento de Estado Frontend (Zustand & TanStack Query)
    
    
      Para o gerenciamento de estado no React, usaremos uma abordagem combinada:
    
    

      
        **Estado de UI (Zustand):** Escolheremos **Zustand** por sua leveza, simplicidade e API baseada em hooks, que se integra perfeitamente com o React. É ideal para gerenciar o estado local da UI, preferências do usuário, estado de formulários complexos e qualquer dado que não necessite de caching ou sincronização com o servidor de forma automática.
        
// web/src/store/projectStore.ts
import { create } from 'zustand';
import { Project } from 'shared/src/types'; // Importando do módulo shared

interface ProjectState {
  currentProject: Project | null;
  setCurrentProject: (project: Project | null) => void;
  // ...outros estados de UI relacionados a projetos
}

export const useProjectStore = create((set) => ({
  currentProject: null,
  setCurrentProject: (project) => set({ currentProject: project }),
}));

      
      
        **Estado de Servidor (TanStack Query / `react-query`):** Para dados vindos da API (projetos, documentos, etc.), utilizaremos **TanStack Query (React Query)**. Ele lida de forma excelente com caching, revalidação, sincronização de dados, erros e otimizações de requisições, simplificando enormemente a interação com o backend e melhorando a experiência do usuário com updates otimistas e refetching inteligente.
        
// web/src/services/projectService.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Project } from 'shared/src/types'; // Compartilhando tipos!

const fetchProjects = async (): Promise => {
  const response = await fetch('/api/v1/projects');
  if (!response.ok) throw new Error('Failed to fetch projects');
  return response.json();
};

const createProject = async (newProjectData: { title: string; theme: string }): Promise => {
  const response = await fetch('/api/v1/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(newProjectData),
  });
  if (!response.ok) throw new Error('Failed to create project');
  return response.json();
};

export const useProjects = () => useQuery({ queryKey: ['projects'], queryFn: fetchProjects });

export const useCreateProject = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] }); // Refetch projects list
    },
  });
};

      
    

    
      Essa combinação permite um gerenciamento de estado eficiente, separando claramente as preocupações de UI e de dados do servidor, o que leva a uma arquitetura mais limpa e manutenível.
    
  

  
    
      ⚡ Fase 3: Endpoints Críticos da API
    
    
      Os endpoints mais complexos do sistema serão aqueles que orquestram a busca, processamento e geração de conteúdo. Todos esses serão implementados com **FastAPI (Python)**, rodando como Serverless Functions no Vercel, devido à necessidade de processamento intensivo de texto, manipulação de dados e orquestração de APIs externas.
    
    
      **Supabase Edge Functions vs. FastAPI Serverless:**
      

        
          **FastAPI (Python Serverless):** Essencial para cargas de trabalho pesadas: busca em múltiplas fontes externas, processamento de NLP, construção do grafo de conhecimento, e a lógica central de geração de conteúdo. Python tem uma vasta gama de bibliotecas para essas tarefas (e.g., `requests`, `BeautifulSoup`, `SpaCy`, `NLTK`, `SciPy`). O Vercel pode hospedar essas funções Python.
        
        
          **Supabase Edge Functions (Deno/TypeScript):** Seriam usadas para tarefas leves, de baixa latência e próximas ao banco de dados, como validação extra de RLS, webhooks simples, ou API proxies muito específicos. Para a complexidade deste projeto, a maior parte da lógica de negócio reside no FastAPI. Vercel Edge Middleware será usado para autenticação global e redirecionamentos antes mesmo da requisição chegar ao FastAPI.
        
      

    

    
      1. POST `/api/v1/projects/{project_id}/search` - Busca e Recuperação de Documentos
    
    
      Este endpoint será a espinha dorsal da fase de pesquisa.
    
    

      - **Método:** `POST`
      **Corpo da Requisição (Pydantic Model):** `SearchRequest(project_id: UUID, topic: str, sources: List[str], filters: Dict)`
        

            - `topic`: O tema central para a busca.
            - `sources`: Lista de bases de dados (e.g., "scielo", "google_scholar").
            - `filters`: Parâmetros como "recent" (bool), "min_impact_factor" (int), etc.
        

      
      **Lógica Central (FastAPI):**
        
          - Autenticação e Autorização (JWT com `python-jose` e verificação de `project_id` contra `user_id`).
          - Orquestração de chamadas assíncronas para APIs externas de bases de dados científicas (Scielo, Google Scholar, etc.).
          - Parsing e normalização dos resultados de diferentes fontes para um formato unificado.
          - Filtragem e ranqueamento (buscar os "10 melhores, principais") baseado em relevância, data e critérios de impacto.
          - Armazenamento de metadados dos documentos encontrados na tabela `documents` do Supabase.
          - Retorno de uma lista de metadados dos documentos encontrados ao frontend.
        
      
      - **Retorno:** `List[DocumentMetadata]` (Pydantic Model)
    


    
      2. POST `/api/v1/projects/{project_id}/knowledge-base` - Construção da Base de Conhecimento
    
    
      Este endpoint processará o conteúdo dos documentos selecionados para criar a "memória" estruturada.
    
    

      - **Método:** `POST`
      - **Corpo da Requisição (Pydantic Model):** `KnowledgeBaseRequest(project_id: UUID, document_ids: List[UUID])`
      **Lógica Central (FastAPI):**
        
          - Recuperação dos conteúdos completos dos documentos da tabela `documents` (armazenados anteriormente).
          - Processamento de Linguagem Natural (NLP): Extração de conceitos-chave, metodologias, resultados, argumentos.
          - Construção de um Grafo de Conhecimento: Identificação de entidades e relações entre elas, armazenando em `knowledge_graph_nodes` e `knowledge_graph_edges`.
          - Armazenamento do grafo no Supabase, vinculado ao `project_id`.
          - Retorno de um resumo da base de conhecimento construída ou status de sucesso.
        
      
      - **Retorno:** `KnowledgeBaseSummary` (Pydantic Model) ou `{"status": "success", "message": "Knowledge base built."}`
    


    
      3. POST `/api/v1/projects/{project_id}/generate-content` - Geração de Conteúdo Científico
    
    
      Este é o endpoint final, responsável por sintetizar o conteúdo a partir da base de conhecimento.
    
    

      - **Método:** `POST`
      **Corpo da Requisição (Pydantic Model):** `GenerateContentRequest(project_id: UUID, content_type: str, format_norm: str, sections: List[str])`
        

          - `content_type`: "TCC", "Estudo de Caso", "Artigo".
          - `format_norm`: "ABNT", "APA", "Vancouver".
          - `sections`: Lista de seções a serem geradas (ex: "introdução", "revisão da literatura", "metodologia").
        

      
      **Lógica Central (FastAPI):**
        
          - Recuperação do grafo de conhecimento associado ao `project_id`.
          - Algoritmos de síntese e recontextualização que navegam no grafo para construir o conteúdo.
          - Geração de conteúdo autoral, sem plágio direto e sem o "viés de IA generativa massiva", focando na reinterpretação e argumentação baseada nas fontes.
          - Inclusão automática de citações no texto e construção da lista de referências bibliográficas, conforme a norma escolhida (ABNT, APA, etc.).
          - Formatação do texto final em um padrão científico.
          - Armazenamento do conteúdo gerado (e.g., em um campo `generated_content` na tabela `projects` ou em uma nova tabela `outputs`).
          - Retorno do texto gerado e metadados de formatação.
        
      
      - **Retorno:** `GeneratedContentResponse(text: str, citations: List[Citation], references: List[Reference])`
    

    
      A natureza assíncrona do FastAPI é crucial para gerenciar a execução dessas tarefas potencialmente longas sem bloquear o servidor. Consideraremos o uso de um background task queue (como Celery ou FastAPI Background Tasks) para as operações mais demoradas, notificando o frontend via **Supabase Realtime** sobre o progresso.
    
  

  
    
      🚧 Fase 4: "Gotchas" no Frontend
    
    
      O frontend React, embora poderoso, apresentará desafios significativos, especialmente na criação de uma experiência de usuário fluida e responsiva para um aplicativo com operações de backend de longa duração.
    
    
      
        **Feedback em Tempo Real e Barras de Progresso:** As etapas de busca de documentos, construção da base de conhecimento e geração de conteúdo podem levar tempo. É crucial fornecer feedback constante ao usuário.
        

          - **Desafio:** Sincronizar o estado do backend (progresso da tarefa) com a UI.
          - **Solução:** Utilizar **Supabase Realtime** para que o backend envie atualizações de status para o frontend. O frontend assina um canal Realtime (`project_status:`) e atualiza uma barra de progresso ou mensagens na UI (usando Zustand para o estado de UI).
          - **Exemplo:** "Buscando documentos (3/10 concluídos)...", "Processando grafo de conhecimento (70%)...", "Gerando seção de Introdução...".
        

      
      
        **Visualização Interativa do Grafo de Conhecimento:** Se a "memória" for realmente um grafo de conhecimento, a visualização e interação com ele será um recurso poderoso, mas complexo.
        

          - **Desafio:** Renderizar grafos complexos de forma performática, permitir zoom, pan, seleção de nós/arestas, e exibir detalhes ao interagir.
          - **Solução:** Utilizar bibliotecas robustas de visualização de grafos como **`react-flow`** ou integrar **D3.js** diretamente. Isso exigirá um cuidadoso gerenciamento de estado e otimizações de renderização para grafos com muitos nós.
        

      
      
        **Edição de Conteúdo Gerado e Formatação Científica:** Permitir que o usuário revise e edite o conteúdo gerado, mantendo a formatação científica (citações, referências, estrutura).
        

          - **Desafio:** Implementar um editor de texto rico (WYSIWYG) que entenda e respeite as normas ABNT/APA, e que possa ser pré-preenchido com o texto do backend. Inserção e gerenciamento de citações dentro do editor.
          - **Solução:** Adotar uma biblioteca como **Tiptap** ou **Slate.js**. Será necessário desenvolver plugins personalizados para lidar com a inserção e formatação de citações/referências, talvez integrando com o estado do grafo de conhecimento.
        

      
      
        **Atualizações Otimistas para Ações Rápidas:** Para ações como "salvar rascunho de projeto" ou "selecionar documento", o feedback visual imediato é crucial.
        

          - **Desafio:** Ações de rede podem ser lentas e criar uma experiência de usuário travada.
          - **Solução:** Implementar **atualizações otimistas** usando **TanStack Query**. A UI atualiza o estado imediatamente, assumindo que a operação terá sucesso, e reverte em caso de erro da API. Isso cria uma percepção de velocidade e responsividade.