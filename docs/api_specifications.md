API Specifications
          
Project: AcademiaGenius

          
            Version 1.0
            Status: Approved
            Confidential
          
      
      
        
    
    
        Este documento detalha a especificação da API principal para a aplicação de geração de TCCs, Estudos de Caso e Artigos Científicos.
        Ele segue princípios RESTful, utilizando FastAPI no backend e Supabase para autenticação e banco de dados.
    

    
    
        
## 1. Estratégia de Autenticação

        
            A autenticação será gerenciada pelo Supabase Auth, que fornece JSON Web Tokens (JWTs) após o login bem-sucedido.
            Estes tokens devem ser incluídos em todas as requisições protegidas para o backend FastAPI.
        

        
### Formato do Header

        
            O token JWT deve ser enviado no cabeçalho `Authorization` com o esquema `Bearer`.
        
        
            `Authorization: Bearer <seu_token_jwt_aqui>`
        
        
            O backend FastAPI validará este token usando a biblioteca `python-jose`, garantindo que ele seja emitido pelo Supabase e que sua assinatura seja válida.
        

        
### Roles e Escopos (RLS)

        
            Utilizaremos as roles padrão do Supabase (`anon`, `authenticated`) e podemos estender com roles personalizadas se necessário (ex: `admin`).
            A autorização será primariamente imposta através de:
        
        

            
                Row Level Security (RLS) no Supabase: Políticas RLS serão aplicadas em todas as tabelas sensíveis (ex: `themes`, `research_tasks`, `generated_contents`) para garantir que os usuários só possam acessar ou modificar seus próprios dados.
                Isso é crucial para a segurança e privacidade dos documentos e conteúdos gerados.
            
            
                Verificação no Backend (FastAPI): Além do RLS, o FastAPI realizará verificações adicionais para operações críticas, garantindo que o usuário autenticado tenha permissão para realizar a ação solicitada. O `user_id` do JWT será extraído e usado para consultas e validações.
            
            
                Supabase Edge Functions: Funções de borda que realizam a busca e geração de conteúdo também receberão o JWT e poderão realizar validações de autorização, ou confiarão que a chamada para elas já foi autenticada pelo FastAPI ou RLS.
            
        

        
            Exemplo de RLS: Uma política na tabela `themes` garantiria que `SELECT` e `INSERT` só fossem permitidos para `auth.uid() = user_id` na linha.
        
    

    
    
        
## 2. Referência de Endpoints

        
            Os endpoints são agrupados por recurso principal. Todos os endpoints estarão sob o prefixo `/api/v1`.
            O FastAPI será o gateway para as operações mais complexas, orquestrando chamadas para Supabase (diretamente ou via Edge Functions) e serviços externos.
        

        
        
            
### Recurso: Usuários

            
Gerenciamento de perfis de usuário (além da autenticação básica do Supabase).


            
            
                
                    GET
                    `/api/v1/users/me`
                
                
Obtém os detalhes do perfil do usuário autenticado.

                Resposta (200 OK)
                {
    "id": "uuid-do-usuario",
    "email": "usuario@example.com",
    "nome": "Nome do Usuário",
    "data_criacao": "2023-10-27T10:00:00Z"
}
            

            
            
                
                    PUT
                    `/api/v1/users/me`
                
                
Atualiza os detalhes do perfil do usuário autenticado.

                Corpo da Requisição
                {
    "nome": "Novo Nome do Usuário"
}
                Resposta (200 OK)
                {
    "id": "uuid-do-usuario",
    "email": "usuario@example.com",
    "nome": "Novo Nome do Usuário",
    "data_criacao": "2023-10-27T10:00:00Z"
}
            
        

        
        
            
### Recurso: Temas

            
Gerenciamento dos temas que o usuário deseja pesquisar e gerar conteúdo.


            
            
                
                    POST
                    `/api/v1/themes`
                
                
Cria um novo tema para pesquisa.

                Corpo da Requisição
                {
    "titulo": "Impacto da Inteligência Artificial na Educação Superior",
    "descricao": "Análise dos efeitos da IA nas metodologias de ensino e aprendizagem em universidades.",
    "palavras_chave": ["IA", "Educação", "Ensino Superior", "Tecnologia"]
}
                Resposta (201 Created)
                {
    "id": "uuid-do-tema",
    "user_id": "uuid-do-usuario",
    "titulo": "Impacto da Inteligência Artificial na Educação Superior",
    "descricao": "Análise dos efeitos da IA nas metodologias de ensino e aprendizagem em universidades.",
    "palavras_chave": ["IA", "Educação", "Ensino Superior", "Tecnologia"],
    "data_criacao": "2023-10-27T10:30:00Z"
}
            

            
            
                
                    GET
                    `/api/v1/themes?limit=10&offset=0`
                
                
Lista os temas criados pelo usuário autenticado, com opções de paginação.

                Parâmetros de Query
                

                    - `limit` (opcional): Número máximo de temas a retornar (padrão: 10).
                    - `offset` (opcional): Número de temas a pular (padrão: 0).
                

                Resposta (200 OK)
                [
    {
        "id": "uuid-do-tema-1",
        "user_id": "uuid-do-usuario",
        "titulo": "Impacto da Inteligência Artificial na Educação Superior",
        "descricao": "...",
        "palavras_chave": ["IA", "Educação"],
        "data_criacao": "2023-10-27T10:30:00Z"
    },
    {
        "id": "uuid-do-tema-2",
        "user_id": "uuid-do-usuario",
        "titulo": "Metodologias Ágeis em Projetos de Software",
        "descricao": "...",
        "palavras_chave": ["Ágil", "Software"],
        "data_criacao": "2023-10-26T09:00:00Z"
    }
]
            

            
            
                
                    GET
                    `/api/v1/themes/{theme_id}`
                
                
Obtém os detalhes de um tema específico pelo seu ID.

                Resposta (200 OK)
                {
    "id": "uuid-do-tema",
    "user_id": "uuid-do-usuario",
    "titulo": "Impacto da Inteligência Artificial na Educação Superior",
    "descricao": "Análise dos efeitos da IA nas metodologias de ensino e aprendizagem em universidades.",
    "palavras_chave": ["IA", "Educação", "Ensino Superior", "Tecnologia"],
    "data_criacao": "2023-10-27T10:30:00Z"
}
            
        

        
        
            
### Recurso: Tarefas de Pesquisa

            
Gerenciamento das tarefas assíncronas de busca de artigos e construção da memória sobre o tema.


            
            
                
                    POST
                    `/api/v1/research-tasks`
                
                
Inicia uma nova tarefa de pesquisa para um tema existente. Isso acionará uma Supabase Edge Function para processamento em segundo plano.

                Corpo da Requisição
                {
    "theme_id": "uuid-do-tema",
    "idioma": "pt-BR",
    "num_documentos": 10,
    "periodo_anos": 5
}
                Resposta (202 Accepted)
                {
    "id": "uuid-da-tarefa-pesquisa",
    "theme_id": "uuid-do-tema",
    "user_id": "uuid-do-usuario",
    "status": "PENDING",
    "progresso": 0,
    "data_inicio": "2023-10-27T11:00:00Z",
    "documentos_encontrados": [],
    "memoria_gerada": null
}
                
                    Nota: O status da tarefa pode ser acompanhado via polling neste endpoint ou, idealmente, via Supabase Realtime para atualizações em tempo real no frontend.
                
            

            
            
                
                    GET
                    `/api/v1/research-tasks/{task_id}`
                
                
Obtém o status e os resultados de uma tarefa de pesquisa específica.

                Resposta (200 OK - Em Progresso)
                {
    "id": "uuid-da-tarefa-pesquisa",
    "theme_id": "uuid-do-tema",
    "user_id": "uuid-do-usuario",
    "status": "IN_PROGRESS",
    "progresso": 50,
    "data_inicio": "2023-10-27T11:00:00Z",
    "data_atualizacao": "2023-10-27T11:05:00Z",
    "documentos_encontrados": [
        {"titulo": "Artigo 1", "url": "http://...", "resumo": "..."},
        {"titulo": "Artigo 2", "url": "http://...", "resumo": "..."}
    ],
    "memoria_gerada": null
}
                Resposta (200 OK - Concluída)
                {
    "id": "uuid-da-tarefa-pesquisa",
    "theme_id": "uuid-do-tema",
    "user_id": "uuid-do-usuario",
    "status": "COMPLETED",
    "progresso": 100,
    "data_inicio": "2023-10-27T11:00:00Z",
    "data_conclusao": "2023-10-27T11:15:00Z",
    "documentos_encontrados": [
        {"titulo": "Artigo 1", "url": "http://...", "resumo": "..."},
        // ... até 10 documentos
    ],
    "memoria_gerada": "Texto consolidado da memória sobre o assunto, sem viés de IA."
}
            
        

        
        
            
### Recurso: Conteúdos Gerados

            
Gerenciamento dos TCCs, Estudos de Caso e Artigos científicos gerados.


            
            
                
                    POST
                    `/api/v1/generated-contents`
                
                
Gera um novo conteúdo (TCC, Estudo de Caso, Artigo) a partir de uma tarefa de pesquisa concluída. Isso acionará uma Supabase Edge Function.

                Corpo da Requisição
                {
    "research_task_id": "uuid-da-tarefa-pesquisa-concluida",
    "tipo_conteudo": "TCC",
    "formato_saida": "ABNT"
}
                Resposta (202 Accepted)
                {
    "id": "uuid-do-conteudo-gerado",
    "research_task_id": "uuid-da-tarefa-pesquisa-concluida",
    "user_id": "uuid-do-usuario",
    "tipo_conteudo": "TCC",
    "formato_saida": "ABNT",
    "status": "PENDING",
    "data_solicitacao": "2023-10-27T12:00:00Z",
    "conteudo": null
}
            

            
            
                
                    GET
                    `/api/v1/generated-contents/{content_id}`
                
                
Obtém os detalhes e o conteúdo de um item gerado específico.

                Resposta (200 OK - Concluída)
                {
    "id": "uuid-do-conteudo-gerado",
    "research_task_id": "uuid-da-tarefa-pesquisa-concluida",
    "user_id": "uuid-do-usuario",
    "tipo_conteudo": "TCC",
    "formato_saida": "ABNT",
    "status": "COMPLETED",
    "data_solicitacao": "2023-10-27T12:00:00Z",
    "data_conclusao": "2023-10-27T12:10:00Z",
    "conteudo": {
        "titulo": "Impacto da Inteligência Artificial na Educação Superior",
        "resumo": "Este TCC explora...",
        "introducao": "A inteligência artificial tem revolucionado...",
        "desenvolvimento": [
            {"titulo_secao": "Fundamentação Teórica", "texto": "..."},
            {"titulo_secao": "Análise de Casos", "texto": "..."}
        ],
        "conclusao": "Em suma, a IA apresenta desafios e oportunidades...",
        "referencias": [
            {"autor": "Silva, J.", "ano": "2022", "titulo": "...", "publicacao": "..."}
        ]
    }
}
            
        
    

    
    
        
## 3. Tratamento de Erros

        
            A API retornará códigos de status HTTP padrão para indicar o resultado de uma requisição.
            Para erros, um corpo de resposta JSON será fornecido com detalhes adicionais.
        

        
### Códigos de Status HTTP Padrão

        

            
                200 OK: A requisição foi bem-sucedida. Usado para GET, PUT, DELETE bem-sucedidos.
            
            
                201 Created: A requisição foi bem-sucedida e um novo recurso foi criado. Usado para POST bem-sucedidos.
            
            
                202 Accepted: A requisição foi aceita para processamento, mas o processamento não foi concluído. Usado para operações assíncronas (ex: iniciar tarefa de pesquisa).
            
            
                400 Bad Request: A requisição não pôde ser entendida ou processada devido a sintaxe inválida, parâmetros ausentes ou dados inválidos (ex: validação Pydantic falhou).
            
            
                401 Unauthorized: A requisição requer autenticação. O token JWT está ausente, é inválido ou expirou.
            
            
                403 Forbidden: O servidor entendeu a requisição, mas se recusa a autorizá-la. O usuário autenticado não tem permissão para acessar o recurso ou realizar a ação (ex: RLS negou acesso).
            
            
                404 Not Found: O recurso solicitado não foi encontrado no servidor.
            
            
                500 Internal Server Error: O servidor encontrou uma condição inesperada que o impediu de atender à requisição. Erros não tratados no backend.
            
        


        
### Formato de Resposta de Erro

        
            Em caso de erro (códigos 4xx ou 5xx), a API retornará um objeto JSON com os seguintes campos:
        
        {
    "detail": "Mensagem descritiva do erro.",
    "code": "CODIGO_INTERNO_DO_ERRO" (opcional, para erros específicos),
    "errors": [
        {"field": "nome_do_campo", "message": "Mensagem de validação"}
    ] (opcional, para erros 400 de validação)
}
        Exemplo de Erro (400 Bad Request)
        {
    "detail": "Erro de validação nos dados fornecidos.",
    "errors": [
        {
            "loc": ["body", "titulo"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}
        Exemplo de Erro (401 Unauthorized)
        {
    "detail": "Credenciais de autenticação inválidas ou token expirado."
}
        Exemplo de Erro (403 Forbidden)
        {
    "detail": "Você não tem permissão para acessar este recurso."
}
    

    
        
Documento gerado por Senior API Architect.

        
Tecnologias chave: Supabase (PostgreSQL, RLS, Edge Functions, Auth, Realtime), React 19+, Python (FastAPI, Pydantic, async/await), Vercel.