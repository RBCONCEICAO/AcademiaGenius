QA & Testing Strategy
          
Project: AcademiaGenius

          
            Version 1.0
            Status: Approved
            Confidential
          
      
      
        
  
    
      &#x1F4DA; Estratégia da Pirâmide de Testes
    
    
      A estratégia de testes focará na pirâmide de testes clássica, priorizando a automação e a detecção precoce de falhas. Dada a natureza crítica da geração de conteúdo científico e a sensibilidade a dados e segurança, haverá uma ênfase particular em testes de integração (APIs) e validação de dados/lógica.
    

    1. Testes Unitários (Python, React)
    
      Foco na lógica de negócio granular e componentes isolados.
    
    
      
        
          Módulo/Componente
          O que testar
          Ferramentas
        
      
      
        
          Backend (FastAPI) - Módulo de Busca
          
            

              - Validação de entrada de tema (Pydantic).
              - Funções de parse de URLs para diferentes bases (Scielo, Google Scholar).
              - Lógica de filtragem e ordenação (relevância, data).
              - Extração de texto de PDFs (simulação ou mocks).
            

          
          Pytest, unittest.mock
        
        
          Backend (FastAPI) - Módulo de Geração
          
            

              - Lógica de construção do grafo de conhecimento.
              - Algoritmos de sumarização e recontextualização (sem IA generativa).
              - Formatação de citações ABNT/APA.
              - Geração de estruturas de seção (introdução, metodologia).
            

          
          Pytest, Hypothesis
        
        
          Frontend (React) - Componentes de UI
          
            

              - Renderização correta de formulários (tema, normas).
              - Estado de carregamento/erro.
              - Interação com hooks de estado (Zustand) para gerenciamento local.
              - Exibição de documentos encontrados.
            

          
          Vitest, React Testing Library
        
      
    

    2. Testes de Integração (API Backend, Supabase, Edge Functions)
    
      Validação da comunicação entre serviços e persistência de dados.
    
    
      
        
          Integração
          O que testar
          Ferramentas
        
      
      
        
          API Backend &#x2194; Supabase Auth
          
            

              - Autenticação e Autorização (JWT via `python-jose`).
              - Acesso a recursos protegidos após login.
              - Criação de usuários e gerenciamento de sessões.
            

          
          Pytest, HTTPX (ou requests)
        
        
          API Backend &#x2194; Supabase PostgreSQL (via ORM)
          
            

              - Persistência e recuperação de temas, documentos, trabalhos gerados.
              - Funcionamento das RLS Policies (ex: usuário só vê seus próprios trabalhos).
              - Transações e integridade de dados (ex: tema excluído, trabalhos associados devem ser tratados).
            

          
          Pytest, Testcontainers (PostgreSQL)
        
        
          API Backend &#x2194; Edge Functions/Serviços Externos
          
            

              - Invocações de APIs externas (Scielo, Google Scholar) com mocks para limites de taxa/erros.
              - Processamento assíncrono (ex: disparo de Edge Function para PDF parsing).
              - Tratamento de timeouts e retries.
            

          
          Pytest, HTTPX, moto (para AWS S3 se usado via Edge Function)
        
      
    

    3. Testes E2E (Frontend, Backend, Database)
    
      Simulação de jornadas completas do usuário em um ambiente o mais próximo possível da produção.
    
    
      
        
          Jornada do Usuário
          Cenário Crítico
          Ferramentas
        
      
      
        
          Geração Completa de Conteúdo
          
            

              - Login, inserção de tema, disparo da busca.
              - Monitoramento do progresso, revisão de documentos encontrados.
              - Geração do conteúdo científico e verificação de sua estrutura e citações.
              - Exportação para DOCX/PDF.
            

          
          Playwright
        
        
          Gerenciamento de Trabalhos
          
            

              - Criação, visualização, edição e exclusão de trabalhos.
              - Verificação de que apenas trabalhos do usuário logado são exibidos/acessíveis.
              - Atualizações em tempo real (Supabase Realtime) ao criar um novo trabalho em outra aba/dispositivo.
            

          
          Playwright
        
      
    
  

  
    
      &#x1F6A8; Cenários Críticos "Unhappy Paths" (Gherkin)
    
    
      Focando em falhas de sistema, concorrência e limitações externas que podem quebrar a experiência do usuário ou a integridade dos dados.
    

    
      Cenário 1: Falha na Comunicação com Base de Dados Científica Externa
      
**Funcionalidade:** Busca e Recuperação de Documentos

      
**Contexto:** O usuário solicita a busca de documentos para um tema específico.

      

        - **Dado** que o backend tenta acessar uma das bases de dados científicas (e.g., Scielo, IEEE Xplore).
        - **E** a base de dados externa retorna um erro HTTP 500 ou um timeout.
        - **Quando** o usuário submete um tema para busca.
        - **Então** o sistema deve registrar a falha na busca para aquela fonte específica.
        - **E** continuar a busca nas outras fontes disponíveis, se houver.
        - **E** notificar o usuário na interface que a busca em algumas fontes falhou, mas outras foram processadas.
        - **E** permitir que o usuário tente novamente a busca nessas fontes falhas posteriormente.
        - **E** não gerar um documento incompleto ou incorreto devido à falta de dados.
      

    

    
      Cenário 2: Condição de Corrida na Edição Concorrente de um Trabalho
      
**Funcionalidade:** Painel de Gerenciamento / Edição de Trabalhos

      
**Contexto:** Um usuário está editando os detalhes de um trabalho gerado.

      

        - **Dado** que um usuário possui um trabalho já gerado.
        - **E** ele abre a página de edição do trabalho em duas abas do navegador (ou dois dispositivos diferentes).
        - **Quando** ele faz uma alteração e salva na primeira aba.
        - **E** imediatamente depois, faz uma alteração diferente e tenta salvar na segunda aba.
        - **Então** o sistema deve detectar a condição de corrida usando controle de versão (ex: `updated_at` timestamp ou campos específicos no PostgreSQL via RLS).
        - **E** notificar o usuário da segunda aba sobre a versão mais recente do trabalho.
        - **E** permitir que o usuário da segunda aba escolha entre sobrescrever ou mesclar (se aplicável) as alterações, ou apenas visualizar a versão mais recente.
        - **E** o histórico de revisão deve manter ambas as versões (se houver histórico de versão implementado).
      

    

    
      Cenário 3: Exaustão de Recursos ou Limites de Processamento no Backend
      
**Funcionalidade:** Geração de Conteúdo Científico Estruturado

      
**Contexto:** O usuário solicita a geração de um TCC complexo a partir de muitos documentos.

      

        - **Dado** que o usuário seleciona 10 documentos de 100 páginas cada para a geração de um TCC.
        - **E** o processo de extração de conhecimento e geração de conteúdo é intensivo em CPU/memória no backend (FastAPI, Edge Functions).
        - **Quando** o sistema tenta processar a solicitação de geração do conteúdo.
        - **Então** o backend deve aplicar limites de tempo de execução ou memória (`ulimit` ou configurações de Vercel Edge Functions).
        - **E** se um limite for excedido, a operação deve ser gracefully terminada.
        - **E** o usuário deve ser notificado que a geração falhou devido à complexidade ou tamanho do conteúdo.
        - **E** o trabalho deve ser marcado como "Falha" no painel, com uma opção para tentar novamente com menos documentos ou resumindo-os.
        - **E** logs de erro detalhados devem ser gerados para análise da equipe.
      

    
  

  
    
      &#x1F512; Testes de Segurança (OWASP Top 10)
    
    
      Avaliando vulnerabilidades críticas específicas para a arquitetura Supabase/FastAPI/React e a natureza da aplicação.
    
    
      
        
          Vulnerabilidade (OWASP)
          Vetor de Ataque Específico para o App
          Como Testar
        
      
      
        
          A01: Broken Access Control (BAC)
          
            

              - **IDOR (Insecure Direct Object Reference)** em trabalhos ou documentos de outros usuários.
              - Acesso não autorizado a APIs de gerenciamento (ex: deletar trabalho de outro user).
            

          
          
            

              - Criar 2 usuários, logar com o User A, obter ID de trabalho do User B (via interceptação ou adivinhação). Tentar acessar/modificar o trabalho do User B via API.
              - Verificar RLS Policies do Supabase.
            

          
        
        
          A03: Injection (SQL, Command)
          
            

              - **SQL Injection** em campos de busca de tema ou filtros no backend FastAPI (se houver construção manual de queries).
              - **Command Injection** se o backend executa comandos de sistema (ex: para processar PDFs externos sem sanitização).
            

          
          
            

              - Inserir payloads SQL (`' OR 1=1 --`) em campos de texto enviados à API.
              - Verificar se o ORM (SQLAlchemy) está sendo usado corretamente com prepared statements.
              - Tentar `; rm -rf /` em entradas que podem invocar subprocessos.
            

          
        
        
          A05: Security Misconfiguration
          
            

              - Chaves de API expostas no frontend ou logs.
              - Permissões de RLS Policies muito permissivas no Supabase.
              - Headers de segurança (CORS, HSTS) mal configurados.
              - Exposição de endpoints de debug/admin do FastAPI em produção.
            

          
          
            

              - Inspecionar código frontend, headers de resposta HTTP.
              - Verificar políticas RLS via Supabase Studio e CLI.
              - Rodar ferramentas como OWASP ZAP ou Burp Suite passivamente.
            

          
        
        
          A07: Identification and Authentication Failures
          
            

              - Enumeração de usuários (via erro de login "usuário não encontrado").
              - Ataques de força bruta (credenciais fracas, falta de rate limiting).
              - Quebra de sessão (JWT expiração inadequada, falta de invalidação).
            

          
          
            

              - Tentar login com usuários existentes e inexistentes para diferenciar erros.
              - Usar Burp Suite Intruder para ataques de força bruta no endpoint de login.
              - Verificar validade do JWT após logout ou troca de senha.
            

          
        
        
          A10: Server-Side Request Forgery (SSRF)
          
            

              - Backend acessa URLs externas para busca de artigos; um atacante pode injetar URLs internas (ex: `http://localhost:8000/admin`) ou de metadados de cloud (AWS, GCP, Vercel).
            

          
          
            

              - Injetar URLs como `http://127.0.0.1/admin`, `http://localhost:port/`, `http://169.254.169.254/latest/meta-data/` em campos de tema/URL.
              - Verificar logs do backend para acessos indevidos.
              - Implementar lista de permissões (whitelist) para URLs externas.
            

          
        
      
    
  

  
    
      &#x1F4BB; Snippet de Script E2E Automatizado (Playwright)
    
    
      Este script Playwright simula o fluxo crítico de um usuário desde o login até o disparo da geração de um trabalho e verificação básica de seu status. Ele garante que os componentes React interagem corretamente com as APIs FastAPI e que os dados são persistidos via Supabase.
    
    
import { test, expect } from '@playwright/test';

test.describe('Fluxo Completo de Geração de TCC', () => {
  // Define um contexto para todos os testes dentro deste bloco
  test.beforeEach(async ({ page }) => {
    // Navega para a página de login
    await page.goto('/login');

    // Preenche os campos de login
    await page.fill('input[name="email"]', 'teste@example.com');
    await page.fill('input[name="password"]', 'SenhaSegura123!');

    // Clica no botão de login
    await page.click('button[type="submit"]');

    // Aguarda a navegação para o dashboard (ou página inicial pós-login)
    // Verifica se a URL mudou para o dashboard ou uma rota esperada
    await page.waitForURL('/dashboard');
    // Adiciona uma asserção para garantir que o login foi bem-sucedido
    await expect(page.locator('h1')).toHaveText(/Bem-vindo/i); // Exemplo: verifica um título de boas-vindas
  });

  test('Deve gerar um TCC completo a partir de um tema e verificar seu status', async ({ page }) => {
    // A. Navegar para a página de criação de novo trabalho
    await page.locator('button:has-text("Novo Trabalho")').click();
    await page.waitForURL('/new-work');
    await expect(page.locator('h2')).toHaveText(/Criar Novo Trabalho/i); // Verifica se está na página correta

    // B. Preencher o tema central
    const tema = `Aplicações de Blockchain em Gerenciamento da Cadeia de Suprimentos - Teste ${Date.now()}`;
    await page.fill('input[name="temaCentral"]', tema);
    // Asserção: Verifica se o campo foi preenchido corretamente
    await expect(page.locator('input[name="temaCentral"]')).toHaveValue(tema);

    // C. Selecionar o tipo de trabalho (TCC)
    await page.selectOption('select[name="tipoTrabalho"]', 'tcc');
    // Asserção: Verifica se a opção foi selecionada
    await expect(page.locator('select[name="tipoTrabalho"]')).toHaveValue('tcc');

    // D. Selecionar norma de formatação (ABNT)
    await page.selectOption('select[name="normaFormatacao"]', 'abnt');
    // Asserção: Verifica se a opção foi selecionada
    await expect(page.locator('select[name="normaFormatacao"]')).toHaveValue('abnt');

    // E. Disparar a busca e geração
    await page.click('button:has-text("Gerar Conteúdo")');

    // Asserção: Verifica se a notificação de processamento apareceu
    await expect(page.locator('text=Iniciando busca e geração...')).toBeVisible();

    // F. Esperar até que o trabalho apareça no painel e seu status mude para 'Concluído' ou 'Em Processo'
    // Aqui assumimos que, após o disparo, o usuário é redirecionado para o painel
    await page.waitForURL('/dashboard');

    // Localiza o item na tabela ou lista de trabalhos gerados
    // Pode ser necessário um seletor mais robusto, dependendo da estrutura da tabela.
    // Usamos um seletor que busca um elemento contendo o tema recém-criado.
    const workRow = page.locator(`tr:has-text("${tema}")`);
    await expect(workRow).toBeVisible(); // Asserção: O trabalho deve aparecer na lista

    // Asserção: Verifica se o status inicial é 'Em Processo' ou similar
    await expect(workRow.locator('.status-badge')).toHaveText('Em Processo');

    // G. Aguardar o processo de geração para ser concluído (timeout alto para E2E, pois é uma operação demorada)
    // Isso pode levar vários segundos ou minutos. É crucial para E2E.
    // Usaremos um loop para verificar o status ou esperar uma notificação do Realtime.
    // Para simplificar no Playwright, vamos aguardar até que o texto do status mude para "Concluído"
    await expect(workRow.locator('.status-badge')).toHaveText('Concluído', { timeout: 120000 }); // Asserção: O status final deve ser "Concluído" (2 minutos de timeout)

    // H. Clicar para visualizar o trabalho gerado
    await workRow.locator('button:has-text("Visualizar")').click();
    await page.waitForURL(/\/work\/\w+/); // Asserção: Verifica se a URL corresponde a um ID de trabalho específico

    // I. Validar elementos críticos do conteúdo gerado na página de visualização
    await expect(page.locator('h1')).toHaveText(tema); // Asserção: O título da página deve ser o tema
    await expect(page.locator('section:has-text("Introdução")')).toBeVisible(); // Asserção: Deve conter a seção de Introdução
    await expect(page.locator('section:has-text("Referências Bibliográficas")')).toBeVisible(); // Asserção: Deve conter a seção de Referências
    await expect(page.locator('p:has-text("Segundo")')).toBeVisible(); // Asserção: Verifica se há alguma citação no texto
    await expect(page.locator('div.citation-item')).toBeVisible(); // Asserção: Verifica se há itens de citação listados

    // J. Tentar exportar o documento
    await page.click('button:has-text("Exportar DOCX")');
    const [download] = await Promise.all([
      page.waitForEvent('download'), // Asserção: Espera que um download ocorra
      page.click('button:has-text("Exportar DOCX")')
    ]);
    await expect(download.suggestedFilename()).toContain('.docx'); // Asserção: Verifica o formato do arquivo baixado
  });

  test.afterEach(async ({ page }) => {
    // Limpeza: deslogar ou limpar dados, se necessário
    await page.click('button:has-text("Logout")'); // Supondo um botão de logout
    await page.waitForURL('/login');
  });
});