none Rules
          
Project: AcademiaGenius

          
            Version 1.0
            Status: Approved
            Confidential
          
      
      
        
    
## Guia de Configuração para o Assistente de Código AI

    
        Como Engenheiro de Experiência do Desenvolvedor de IA, entendo a importância de um assistente de código bem configurado.
        Este guia fornecerá um arquivo de regras essencial para o seu assistente de IA, garantindo que ele compreenda profundamente o contexto do seu projeto, a stack tecnológica e os objetivos.
        Ao configurar estas regras, você otimizará a relevância e a precisão das sugestões de código, refatorações e respostas, acelerando significativamente o seu fluxo de trabalho.
    



    
### O Arquivo de Regras (`.cursorrules` ou similar)

    
        Copie o conteúdo abaixo e salve-o em um arquivo chamado `.cursorrules` (ou o nome de arquivo de regras equivalente para o seu editor/assistente de IA) na raiz do seu projeto.
        Este arquivo servirá como o "cérebro" do seu assistente, orientando-o sobre as especificidades do seu projeto de geração de conteúdo científico.
    
    # Contexto do Projeto: Gerador de Conteúdo Científico
Este projeto visa desenvolver uma aplicação para gerar Trabalhos de Conclusão de Curso (TCC), Estudos de Caso e Artigos Científicos a partir de um tema informado pelo usuário.

## Funcionalidades Principais:
1.  **Pesquisa Avançada:** Buscar os 10 artigos, estudos de caso ou documentos mais relevantes, recentes e influentes relacionados ao tema. A pesquisa deve priorizar fontes acadêmicas e científicas.
2.  **Construção de Memória:** A partir dos documentos encontrados, criar uma base de conhecimento (memória) estruturada e contextualizada sobre o assunto. Esta memória deve ser robusta o suficiente para servir de base para a geração de conteúdo autoral.
3.  **Geração de Conteúdo Autoral:** Utilizar a memória construída para gerar um conteúdo original, sem viés de IA, e em um formato padrão científico (ex: ABNT, APA, Vancouver, a ser definido pelo usuário ou configurado). O conteúdo deve ser coeso, bem fundamentado e com referências claras.

## Stack Tecnológica:

### Frontend (Interface do Usuário)
*   **Framework:** React
*   **Bundler:** Vite (para desenvolvimento rápido e builds otimizados)
*   **Gerenciamento de Estado:** Zustand ou Redux Toolkit (escolha baseada na complexidade do estado global)
*   **Estilização:** Tailwind CSS (para utilitários CSS rápidos e responsivos) ou CSS Modules (para escopo de estilos)
*   **Roteamento:** React Router v6+
*   **Princípios:** Componentes reutilizáveis, performance otimizada, experiência do usuário (UX) intuitiva e responsiva.

### Backend (Lógica de Negócio e APIs)
*   **Linguagem:** Python
*   **Framework Web:** FastAPI (preferencialmente, para APIs assíncronas de alta performance e documentação automática) ou Django REST Framework (para projetos com mais complexidade de ORM e admin).
*   **Validação de Dados:** Pydantic (para validação e serialização de dados robusta)
*   **ORM:** SQLAlchemy (para FastAPI, oferecendo flexibilidade e controle sobre o banco de dados) ou Django ORM (para Django REST Framework).
*   **Autenticação:** python-jose para JWT (JSON Web Tokens) para autenticação segura de usuários.
*   **Princípios:** APIs RESTful, código limpo e testável, segurança (validação de entrada, proteção contra ataques comuns), escalabilidade.

### Banco de Dados
*   **Plataforma:** Supabase (oferecendo PostgreSQL como base de dados relacional)
*   **Base:** PostgreSQL
*   **Recursos Utilizados:**
    *   Supabase Auth para gerenciamento de usuários e autenticação.
    *   RLS Policies (Row Level Security) para controle de acesso granular aos dados.
    *   Edge Functions (para lógica de backend sem servidor, escrita em TypeScript/JavaScript, ou para orquestrar chamadas a funções Python).
    *   Realtime subscriptions para atualizações de dados em tempo real (se aplicável para feedback ao usuário).
    *   Supabase CLI para gerenciamento de migrações e schema do banco de dados.
*   **Princípios:** Segurança dos dados, integridade referencial, escalabilidade, facilidade de uso e integração com o backend.

### Infraestrutura e Deploy
*   **Plataforma:** Vercel
*   **Recursos Utilizados:**
    *   Serverless Functions (Python para o backend FastAPI/DRF, ou Node.js para Edge Functions específicas).
    *   Edge Middleware para lógica de autenticação, roteamento e manipulação de requisições na borda da rede.
    *   Variáveis de ambiente gerenciadas de forma segura pelo dashboard da Vercel.
*   **Princípios:** Deploy contínuo (CI/CD), escalabilidade automática, performance global (CDN), simplicidade de configuração e manutenção.

## Diretrizes para o Assistente de IA:
*   Ao gerar código ou sugestões, priorize as tecnologias e padrões da stack definida acima.
*   Foque em soluções que promovam a originalidade e a ausência de viés de IA no conteúdo gerado, com ênfase na curadoria de fontes.
*   Considere a segurança e a performance em todas as camadas da aplicação, desde o frontend até o banco de dados.
*   Sugira implementações que facilitem a busca, o processamento e a indexação de grandes volumes de dados textuais de forma eficiente.
*   Ajude a estruturar o projeto de forma modular, escalável e de fácil manutenção.
*   Lembre-se do objetivo final: gerar conteúdo científico de alta qualidade, autoral e em formato padrão.
*   Priorize a clareza, a legibilidade e as boas práticas de engenharia de software.




    
### Melhores Práticas para Interagir com o Assistente de IA

    

        
            **Seja Específico e Contextual:** Ao pedir ajuda, forneça o máximo de contexto possível. Mencione a camada (frontend, backend, banco de dados), as tecnologias específicas envolvidas e o objetivo da funcionalidade. Por exemplo, em vez de "Como faço isso?", pergunte "Como posso criar um endpoint FastAPI para buscar os 10 artigos mais recentes do Supabase, utilizando Pydantic para validação de entrada?".
        
        
            **Priorize a Stack Definida:** Sempre que possível, peça ao assistente para gerar soluções que se alinhem estritamente com React, Python (FastAPI/DRF), Supabase e Vercel, utilizando as ferramentas e padrões mencionados no arquivo de regras. Isso garante que as sugestões sejam diretamente aplicáveis ao seu projeto.
        
        
            **Valide e Adapte o Código Gerado:** O código fornecido pela IA é uma sugestão inteligente. Sempre revise, teste e adapte-o para garantir que ele se integre perfeitamente ao seu projeto, siga suas convenções de código, atenda aos requisitos de segurança e performance e, crucialmente, reflita a autoria e o rigor científico que seu projeto exige.