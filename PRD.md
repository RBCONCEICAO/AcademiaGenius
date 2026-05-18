AcademiaGenius


  
    Documento de Requisitos de Produto (PRD)
    
AcademiaGenius: Geração de Conteúdo Científico Autoral

  

  

    
      
## 1. Sumário Executivo

      
        
          
### Problema

          
Estudantes e pesquisadores enfrentam desafios significativos na revisão bibliográfica exaustiva e na elaboração de documentos científicos (TCCs, Artigos, Estudos de Caso). O processo é demorado, propenso a erros de formatação e exige um esforço intelectual considerável para sintetizar informações de múltiplas fontes, resultando em atrasos e estresse.

        
        
          
### Solução

          
AcademiaGenius é uma plataforma SaaS que automatiza a busca, recuperação e síntese de documentos científicos relevantes, construindo uma base de conhecimento estruturada. A partir dessa "memória", gera rascunhos de conteúdo científico autoral, formatado conforme normas acadêmicas (ABNT, APA, etc.), com citações e referências automáticas, garantindo rigor e agilidade sem o viés de IAs generativas massivas.

        
      
    

    
      
## 2. Personas de Usuário

      
        
          
### Ana Paula, Estudante de Mestrado

          

            - **Idade:** 26 anos
            - **Ocupação:** Estudante de Mestrado em Engenharia de Software
            - **Objetivos:** Concluir a dissertação de mestrado com alta qualidade e dentro do prazo; agilizar a revisão bibliográfica para focar na pesquisa empírica.
            - **Frustrações:** Perde muito tempo buscando e lendo artigos; dificuldade em organizar as informações e garantir a coesão do texto; preocupação com plágio e formatação ABNT.
            - **Proficiência Técnica:** Média. Confortável com ferramentas digitais e plataformas acadêmicas, mas não é programadora.
            - **Citação:** "Preciso de uma ferramenta que me ajude a organizar a pesquisa e a escrever o rascunho, para que eu possa me concentrar na análise e na discussão dos resultados."
          

        
        
          
### Dr. Ricardo Silva, Pesquisador Sênior

          

            - **Idade:** 48 anos
            - **Ocupação:** Professor Universitário e Pesquisador (Doutorado)
            - **Objetivos:** Publicar artigos em periódicos de alto impacto; manter-se atualizado com a literatura mais recente em sua área; orientar alunos de pós-graduação de forma mais eficiente.
            - **Frustrações:** Volume imenso de novas publicações; tempo limitado para revisão sistemática; necessidade de adaptar artigos para diferentes normas (APA, IEEE).
            - **Proficiência Técnica:** Alta. Utiliza softwares de análise de dados e ferramentas de produtividade avançadas. Valoriza automação e integração.
            - **Citação:** "Busco uma solução que me permita rapidamente ter uma visão consolidada do estado da arte sobre um tema, liberando meu tempo para a análise crítica e a escrita de alto nível."
          

        
      
    

    
      
## 3. Histórias de Usuário

      
        
          
            
              ID
              Como um(a)
              Eu quero
              Para que
              Prioridade
              Critérios de Aceitação
            
          
          
            
              US-001
              Usuário Autenticado
              Inserir um tema central de pesquisa
              O sistema possa iniciar a busca por documentos relevantes.
              Alta
              O tema é validado (min. 10 caracteres) e o processo de busca é iniciado com status "Em Andamento".
            
            
              US-002
              Usuário Autenticado
              Visualizar os 10 documentos mais relevantes encontrados
              Eu possa verificar a qualidade da pesquisa e selecionar fontes.
              Alta
              Uma lista paginada de no mínimo 5 e no máximo 10 documentos é exibida com título, autores, ano e link, após a conclusão da busca.
            
            
              US-003
              Usuário Autenticado
              Selecionar o tipo de documento a ser gerado (TCC, Artigo, Estudo de Caso) e a norma de formatação (ABNT, APA)
              O conteúdo seja estruturado e formatado corretamente para o meu propósito.
              Alta
              As opções de tipo de documento e norma são apresentadas em um formulário e a seleção é persistida para o projeto.
            
            
              US-004
              Usuário Autenticado
              Gerar um rascunho completo do conteúdo científico
              Eu possa ter uma base sólida para desenvolver meu trabalho autoral.
              Alta
              Um rascunho é gerado e exibido em um editor de texto, contendo introdução, revisão, metodologia, resultados, discussão, conclusão e referências, formatado conforme a norma selecionada.
            
            
              US-005
              Usuário Autenticado
              Exportar o conteúdo gerado
              Eu possa continuar editando em meu editor de texto preferido ou submeter o trabalho.
              Alta
              O conteúdo é exportado com sucesso para DOCX ou PDF, mantendo a formatação original.
            
            
              US-006
              Usuário Autenticado
              Visualizar o status do processo de geração de conteúdo
              Eu possa acompanhar o progresso e saber quando meu trabalho estará pronto.
              Média
              Uma barra de progresso ou indicador de status (e.g., "Buscando Documentos", "Construindo Memória", "Gerando Rascunho") é exibida na interface do usuário.
            
          
        
      
    

    
      
## 4. Requisitos Funcionais

      
        
          
### 4.1. Autenticação e Autorização

          

            - **Autenticação de Usuário:** Implementação via `Supabase Auth`, suportando registro/login por Email/Senha e provedores OAuth (Google, GitHub).
            - **Recuperação de Senha:** Fluxo padrão de redefinição de senha via email do `Supabase Auth`.
            - **Gerenciamento de Sessão:** Tokens JWT gerenciados pelo `Supabase Auth`, com renovação automática e invalidação em logout.
            - **Autorização:** Controle de acesso baseado em `Row Level Security (RLS)` no PostgreSQL do Supabase, garantindo que usuários acessem apenas seus próprios projetos e dados.
          

        

        
          
### 4.2. Gerenciamento de Projetos

          

            - **Criação de Projeto:** Usuário pode criar um novo projeto informando um "Tema Central" (string de texto).
            - **Listagem de Projetos:** Painel de gerenciamento exibe todos os projetos do usuário com status (e.g., "Em Busca", "Memória Construída", "Rascunho Gerado").
            - **Visualização de Projeto:** Acesso a detalhes de um projeto específico, incluindo documentos encontrados, memória construída e rascunhos gerados.
            - **Edição de Projeto:** Permite renomear o tema central ou ajustar parâmetros (e.g., filtros de busca) antes da geração.
          

        

        
          
### 4.3. Busca e Recuperação de Documentos

          

            - **Algoritmo de Busca:** Backend em `Python (FastAPI)` que orquestra a busca em múltiplas fontes.
            - **Fontes de Dados:** Integração com APIs de bases de dados científicas como `Semantic Scholar API` e `CrossRef API`. (Nota: Google Scholar e Web of Science não possuem APIs públicas para busca programática em larga escala; será necessário explorar alternativas ou parcerias futuras para estas).
            - **Filtros de Busca:** Permite filtrar por ano de publicação (e.g., últimos 5 anos), tipo de documento (artigo, tese, dissertação) e relevância.
            - **Recuperação de Metadados:** Extração de título, autores, ano, resumo, palavras-chave, DOI/URL e link para o PDF (se disponível).
            - **Armazenamento de Documentos:** Metadados dos 10 documentos mais relevantes armazenados no `Supabase (PostgreSQL)`.
          

        

        
          
### 4.4. Construção da Base de Conhecimento (Memória)

          

            - **Extração de Informações-Chave:** Utilização de bibliotecas de NLP em `Python` para identificar e extrair conceitos, metodologias, resultados e argumentos dos resumos e textos completos (se acessíveis) dos documentos.
            - **Estruturação da Memória:** Armazenamento de informações-chave no `Supabase (PostgreSQL)`, utilizando colunas `JSONB` para dados semi-estruturados e tabelas de relacionamento para interligar conceitos.
            - **Representação Semântica:** Geração de `vector embeddings` para os trechos de texto extraídos, armazenados no Supabase, permitindo busca semântica e identificação de relações conceituais.
          

        

        
          
### 4.5. Geração de Conteúdo Científico Estruturado

          

            - **Seleção de Tipo de Documento:** Opções para gerar TCC, Estudo de Caso ou Artigo Científico.
            - **Estrutura Padrão:** Geração de seções pré-definidas (Introdução, Revisão de Literatura, Metodologia, Resultados, Discussão, Conclusão, Referências).
            **Conteúdo Autoral e Sem Viés de IA:**
              

                - Sintetização e recontextualização das informações da "memória", focando na construção de argumentos e na apresentação de diferentes perspectivas encontradas nas fontes.
                - Evitar paráfrase direta ou padrões repetitivos de IAs generativas massivas. A lógica de geração será baseada em modelos de linguagem finamente ajustados ou algoritmos de sumarização extrativa/abstrativa controlados, com ênfase na atribuição de fontes.
                - Garantia de coesão e fluidez textual através de algoritmos de encadeamento de ideias.
              

            
            - **Citação e Referenciação Automáticas:** Inclusão de citações no texto e construção da lista de referências bibliográficas com base nos documentos da memória, utilizando bibliotecas `Python` para formatação de citações (e.g., `citeproc-py`).
            - **Formatação Padrão Científica:** Aplicação automática de normas (ABNT, APA, Vancouver, ISO 690) conforme seleção do usuário. Implementação via lógica `Python` que gera um formato intermediário (e.g., Markdown ou LaTeX) e então converte.
          

        

        
          
### 4.6. Exportação

          

            - **Formatos Suportados:** DOCX (via `python-docx`), LaTeX (geração de arquivo .tex), PDF (via conversão de LaTeX ou HTML com `WeasyPrint`/headless browser).
            - **Download:** Opção de download direto do arquivo gerado.
          

        

        
          
### 4.7. Painel de Gerenciamento (Frontend)

          

            - **Interface de Usuário:** Desenvolvida em `React` com `Tailwind CSS`.
            - **Listagem de Projetos:** Exibição de todos os projetos do usuário com status e data de criação/atualização.
            - **Visualização de Rascunho:** Editor de texto simples para visualizar e copiar o conteúdo gerado.
            - **Acompanhamento de Processo:** Utilização de `Supabase Realtime` para atualizações de status em tempo real durante as etapas de busca, construção da memória e geração de conteúdo.
          

        
      
    

    
      
## 5. Requisitos Não Funcionais

      
        
          
### 5.1. Performance

          

            - **Tempo de Resposta da API:** Requisições de dados (listagem de projetos, detalhes) devem ter tempo de resposta inferior a 200ms.
            - **Tempo de Geração de Documentos:** A geração de um rascunho completo (busca, memória, texto) deve ser concluída em até 5 minutos para um tema de complexidade média.
            - **Carregamento da Interface:** O carregamento inicial da aplicação React deve ser inferior a 3 segundos em conexões 3G.
            - **Escalabilidade:** A arquitetura deve suportar 1.000 usuários ativos simultaneamente sem degradação perceptível de performance.
          

        

        
          
### 5.2. Segurança

          

            - **Autenticação Segura:** Implementação de `Supabase Auth` com suporte a MFA (Multi-Factor Authentication) para maior segurança.
            - **Autorização de Dados:** Todas as tabelas sensíveis no `Supabase (PostgreSQL)` devem ter `Row Level Security (RLS)` ativado e configurado para garantir que usuários só acessem seus próprios dados.
            - **Validação de Entrada:** Todas as entradas de usuário no frontend e backend (`Pydantic` no FastAPI) devem ser rigorosamente validadas para prevenir ataques como injeção de SQL, XSS e CSRF.
            - **Proteção de APIs Externas:** Chaves de API para serviços externos devem ser armazenadas de forma segura (e.g., `Vercel Environment Variables`) e nunca expostas no frontend.
            - **HTTPS:** Todas as comunicações entre cliente, backend e banco de dados devem ser criptografadas via HTTPS/SSL.
            - **Auditoria:** Logs de acesso e modificação de dados devem ser mantidos para fins de auditoria e conformidade.
          

        

        
          
### 5.3. Conformidade

          

            - **LGPD/GDPR:** Conformidade com regulamentações de proteção de dados, incluindo direito ao esquecimento, portabilidade de dados e consentimento explícito.
            - **Integridade Acadêmica:** O sistema deve ser projetado para auxiliar na criação de conteúdo autoral, não para gerar plágio. A lógica de síntese deve enfatizar a recontextualização e a citação correta das fontes.
            - **Acessibilidade (WCAG 2.1 AA):** A interface do usuário deve ser projetada para ser acessível a pessoas com deficiência, seguindo as diretrizes WCAG 2.1 Nível AA.
          

        
      
    

    
      
## 6. Sistema de Design UI/UX

      
        
          
### 6.1. Paleta de Cores

          
             Primary: Indigo-700 (#4F46E5)
             Secondary: Gray-700 (#4B5563)
             Accent: Teal-500 (#14B8A6)
             Success: Green-500 (#22C55E)
             Warning: Orange-500 (#F97316)
             Neutral Light: Gray-100 (#F3F4F6)
             Neutral Dark: Gray-800 (#1F2937)
          
        

        
          
### 6.2. Escala Tipográfica

          
            
              
                Elemento
                Tamanho
                Peso
                Classe Tailwind
                Uso
              
            
            
              
                H1
                48px (3rem)
                Extrabold
                `text-5xl font-extrabold`
                Título principal da página
              
              
                H2
                30px (1.875rem)
                Bold
                `text-3xl font-bold`
                Seções principais do conteúdo
              
              
                H3
                24px (1.5rem)
                Semibold
                `text-2xl font-semibold`
                Subseções, títulos de cards
              
              
                H4
                20px (1.25rem)
                Medium
                `text-xl font-medium`
                Títulos de componentes menores
              
              
                Corpo
                16px (1rem)
                Normal
                `text-base`
                Parágrafos, texto geral
              
              
                Legenda
                14px (0.875rem)
                Normal
                `text-sm`
                Textos auxiliares, metadados
              
            
          
          
**Fonte:** Inter (fallback: system-ui, sans-serif)

        

        
          
### 6.3. Sistema de Espaçamento

          
Utilizar uma escala de espaçamento baseada em múltiplos de 4px para consistência:

          

            - **4px (`p-1`, `m-1`):** Espaçamento mínimo, entre ícones e texto.
            - **8px (`p-2`, `m-2`):** Espaçamento entre elementos adjacentes em um grupo.
            - **12px (`p-3`, `m-3`):** Espaçamento entre itens de lista, campos de formulário.
            - **16px (`p-4`, `m-4`):** Espaçamento padrão de padding em cards, seções menores.
            - **24px (`p-6`, `m-6`):** Espaçamento entre seções dentro de um componente.
            - **32px (`p-8`, `m-8`):** Espaçamento entre grandes blocos de conteúdo ou seções da página.
            - **48px (`p-12`, `m-12`):** Espaçamento para margens externas de layout.
          


[STREAM_ERROR: Generation was interrupted. Please retry.]