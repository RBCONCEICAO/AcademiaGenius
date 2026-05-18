# 🚀 Guia de Publicação Sem Custo (Render) — AcademiaGenius

Este guia orienta você no processo passo a passo para enviar o código do seu projeto para o seu GitHub e publicar o seu backend de forma **100% gratuita** na plataforma **Render**, aproveitando o `Dockerfile` otimizado que criamos.

---

## 📂 Etapa 1: Enviar o Código para o seu GitHub

Como já inicializei o repositório git local e fiz o primeiro commit seguro para você (escondendo suas senhas e credenciais automaticamente via `.gitignore`), você só precisa enviar os arquivos para a sua conta do GitHub:

1. **Crie um repositório vazio no GitHub**:
   * Vá em [github.com/new](https://github.com/new).
   * Dê o nome de `AcademiaGenius`.
   * Mantenha-o como **Público** ou **Privado** (ambos funcionam gratuitamente na Render) e **não** adicione README, .gitignore ou licença.

2. **Execute estes dois comandos no seu terminal** (dentro da pasta `AcademiaGenius`):
   ```bash
   # 1. Defina a branch principal como 'main'
   git branch -M main

   # 2. Associe ao seu repositório do GitHub (Substitua "seu-usuario" pelo seu nome no GitHub)
   git remote add origin https://github.com/seu-usuario/AcademiaGenius.git

   # 3. Envie o código para o GitHub
   git push -u origin main
   ```

---

## 🌐 Etapa 2: Publicar o Backend no Render (Grátis)

A Render permite rodar containers Docker de forma totalmente gratuita.

1. Acesse **[dashboard.render.com](https://dashboard.render.com)** e crie uma conta (você pode logar diretamente usando a sua conta do GitHub).
2. Clique no botão **New +** no canto superior direito e selecione **Web Service**.
3. Selecione a opção **Build and deploy from a Git repository** e conecte o repositório `AcademiaGenius` que você acabou de subir.
4. Preencha as configurações do serviço:
   * **Name**: `academiagenius-api`
   * **Region**: `Ohio (us-east-2)` ou `Oregon (us-west-2)`
   * **Branch**: `main`
   * **Root Directory**: `api` *(Muito importante! Isso aponta para a pasta do backend onde está o Dockerfile).*
   * **Runtime**: `Docker` *(A Render detectará o Dockerfile automaticamente).*
   * **Instance Type**: Escolha **Free** ($0/month).

5. **Adicionar suas chaves de API nas Variáveis de Ambiente**:
   * Vá até a seção **Environment Variables** (ou clique em **Advanced** > **Add Environment Variable**).
   * Adicione as variáveis abaixo para que a IA funcione de forma 100% gratuita e integrada no servidor:
     * `GEMINI_API_KEY` = `[Sua chave da API do Gemini]`
     * `OPENAI_API_KEY` = `[Opcional]`
     * `GROQ_API_KEY` = `[Opcional - recomendada para velocidade extra]`
     * `ANTHROPIC_API_KEY` = `[Opcional]`

6. Clique em **Create Web Service**. 
   * A Render compilará o Dockerfile e colocará a API no ar. Em poucos minutos você receberá um link público seguro, como `https://academiagenius-api.onrender.com`.

---

## 🔗 Etapa 3: Conectar o Frontend com o seu Novo Backend Live

Agora que seu backend está no ar, só precisamos dizer para o seu frontend buscar os dados no link da Render em vez do `localhost`:

1. Abra o arquivo [config.ts](file:///Users/robsonconceicao/Documents/PROJETOS/AcademiaGenius/web/src/lib/config.ts).
2. Mude a URL da API para o link fornecido pelo Render:
   ```typescript
   export const API_URL = 'https://academiagenius-api.onrender.com';
   ```
3. Salve o arquivo e publique o frontend atualizado no Firebase Hosting executando o comando abaixo no terminal da pasta `web`:
   ```bash
   npm run build && firebase deploy --only hosting
   ```

Pronto! Seu sistema estará 100% integrado, rodando em produção na nuvem de forma totalmente gratuita e acessível de qualquer lugar! 🎉
