import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from app.agents.orchestrator import run_research_pipeline
from app.services.llm import generate
from app.services.docx_exporter import generate_docx
from app.services.notebook_service import (
    chat_with_research,
    generate_study_guide,
    generate_faq,
    generate_timeline,
    generate_audio_script,
)

def resolve_api_key(user_key: Optional[str], provider: str) -> str:
    """
    Resolve a API Key: retorna a chave inserida pelo usuário se presente,
    ou busca a chave correspondente configurada nas variáveis de ambiente do servidor (.env).
    """
    if user_key and user_key.strip():
        return user_key.strip()
    
    env_var_map = {
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "groq": "GROQ_API_KEY",
        "mistral": "MISTRAL_API_KEY"
    }
    
    env_var = env_var_map.get(provider.lower())
    if env_var:
        server_key = os.environ.get(env_var)
        if server_key and server_key.strip():
            return server_key.strip()
            
    raise HTTPException(
        status_code=401, 
        detail=f"Chave de API não fornecida para o provedor {provider} e nenhuma chave correspondente ativa no servidor. Configure a chave para continuar."
    )

app = FastAPI(title="AcademiaGenius API", version="1.0.0")

# ============================================================
# CORS - Permite que o frontend converse com a API
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Health Check
# ============================================================
class HealthCheck(BaseModel):
    status: str
    message: str

@app.get("/health", response_model=HealthCheck)
def health_check():
    return {"status": "ok", "message": "AcademiaGenius API is running"}


# ============================================================
# Endpoint de Geração de Conteúdo (Legado — geração simples)
# ============================================================
# ============================================================
class GenerateRequest(BaseModel):
    theme: str
    doc_type: str       # 'tcc', 'artigo', 'estudo'
    llm_provider: str   # 'openai', 'anthropic', 'gemini', 'groq', 'mistral'
    llm_model: str
    api_key: Optional[str] = ""


class GenerateResponse(BaseModel):
    content: str
    status: str

@app.post("/api/v1/generate", response_model=GenerateResponse)
async def generate_content(request: GenerateRequest):
    if not request.theme or len(request.theme) < 5:
        raise HTTPException(status_code=422, detail="O tema deve ter pelo menos 5 caracteres.")

    # Resolve a API Key de forma flexível (grátis se tiver no servidor)
    api_key = resolve_api_key(request.api_key, request.llm_provider)

    try:
        generated_text = generate(
            provider=request.llm_provider,
            model=request.llm_model,
            api_key=api_key,
            theme=request.theme,
            doc_type=request.doc_type,
        )
        return GenerateResponse(content=generated_text, status="success")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar conteúdo: {str(e)}")


# ============================================================
# Endpoint do Pipeline de Agentes (Pesquisa Real)
# ============================================================
class ResearchRequest(BaseModel):
    theme: str
    doc_type: str                            # 'tcc', 'artigo', 'estudo'
    llm_provider: str                        # 'gemini', 'openai', 'anthropic', 'groq', 'mistral'
    llm_model: str
    api_key: Optional[str] = ""
    norm: Optional[str] = "ABNT"
    paper_limit: Optional[int] = 8
    # Busca multi-fonte
    query_en: Optional[str] = None
    include_universities: Optional[bool] = True
    semantic_scholar_key: Optional[str] = None
    pubmed_key: Optional[str] = None
    core_key: Optional[str] = None
    # Modo Pipeline Multi-LLM
    fast_provider: Optional[str] = None     # ex: 'groq' para extração rápida
    fast_model: Optional[str] = None        # ex: 'llama-3.3-70b-versatile'
    fast_key: Optional[str] = None          # chave do provedor rápido (groq/mistral)
    groq_key: Optional[str] = None          # alias: se groq_key informado, fast_provider='groq'
    mistral_key: Optional[str] = None       # alias: se mistral_key informado e sem fast_key
    existing_document: Optional[str] = None
    clarifications: Optional[dict] = None   # Perguntas de refinamento respondidas


class ClarifyRequest(BaseModel):
    theme: str
    llm_provider: str
    llm_model: str
    api_key: Optional[str] = ""


class ResearchResponse(BaseModel):
    document: str
    papers: list
    stats: dict
    steps_log: list
    status: str

# ============================================================
# Endpoint para Extração de Texto (Upload de Arquivos)
# ============================================================
from fastapi import UploadFile, File
import PyPDF2
import io

@app.post("/api/v1/extract_text")
async def extract_text_from_files(files: list[UploadFile] = File(...)):
    extracted_texts = []
    for file in files:
        content = await file.read()
        filename = file.filename.lower()
        
        try:
            if filename.endswith(".pdf"):
                reader = PyPDF2.PdfReader(io.BytesIO(content))
                text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
                extracted_texts.append(f"--- Documento: {file.filename} ---\n{text}\n")
            elif filename.endswith(".docx"):
                import docx
                doc = docx.Document(io.BytesIO(content))
                text = "\n".join(para.text for para in doc.paragraphs)
                extracted_texts.append(f"--- Documento: {file.filename} ---\n{text}\n")
            elif filename.endswith(".doc"):
                import tempfile
                import subprocess
                import os
                with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tmp:
                    tmp.write(content)
                    tmp_name = tmp.name
                try:
                    result = subprocess.run(
                        ["textutil", "-convert", "txt", tmp_name, "-stdout"],
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=10
                    )
                    text = result.stdout
                    extracted_texts.append(f"--- Documento: {file.filename} ---\n{text}\n")
                except Exception as textutil_err:
                    raise RuntimeError(f"A extração de arquivos .doc legado requer o utilitário 'textutil' do macOS. Erro: {str(textutil_err)}")
                finally:
                    if os.path.exists(tmp_name):
                        os.remove(tmp_name)
            else:
                # Assume texto plano (.txt, .md, .csv)
                extracted_texts.append(f"--- Documento: {file.filename} ---\n{content.decode('utf-8')}\n")
        except Exception as e:
            extracted_texts.append(f"--- Documento: {file.filename} (Erro ao extrair: {str(e)}) ---\n")
            
    return {"text": "\n".join(extracted_texts)}

@app.post("/api/v1/research/clarify")
async def research_clarify(request: ClarifyRequest):
    if not request.theme or len(request.theme) < 5:
        raise HTTPException(status_code=422, detail="O tema deve ter pelo menos 5 caracteres.")
    
    # Resolve a API Key de forma flexível
    api_key = resolve_api_key(request.api_key, request.llm_provider)
    
    try:
        from app.agents.clarify_agent import generate_clarifying_questions
        questions = generate_clarifying_questions(
            theme=request.theme,
            provider=request.llm_provider,
            model=request.llm_model,
            api_key=api_key
        )
        return {"status": "success", **questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/research", response_model=ResearchResponse)
async def run_research(request: ResearchRequest):
    if not request.theme or len(request.theme) < 5:
        raise HTTPException(status_code=422, detail="O tema deve ter pelo menos 5 caracteres.")

    # Resolve a API Key principal de forma flexível
    api_key = resolve_api_key(request.api_key, request.llm_provider)

    try:
        # Resolve pipeline mode
        fast_provider = request.fast_provider
        fast_model    = request.fast_model
        fast_key      = request.fast_key

        if not fast_provider and request.groq_key:
            fast_provider = "groq"
            fast_model    = fast_model or "llama-3.3-70b-versatile"
            fast_key      = request.groq_key
        elif not fast_provider and request.mistral_key:
            fast_provider = "mistral"
            fast_model    = fast_model or "mistral-small-latest"
            fast_key      = request.mistral_key

        # Se houver um provedor rápido configurado mas nenhuma chave fornecida pelo usuário,
        # tenta resolver a chave a partir das variáveis de ambiente do servidor.
        if fast_provider and not fast_key:
            try:
                fast_key = resolve_api_key(None, fast_provider)
            except Exception:
                pass

        result = run_research_pipeline(
            theme=request.theme,
            doc_type=request.doc_type,
            provider=request.llm_provider,
            model=request.llm_model,
            api_key=api_key,
            norm=request.norm or "ABNT",
            paper_limit=request.paper_limit or 8,
            query_en=request.query_en,
            include_universities=request.include_universities if request.include_universities is not None else True,
            semantic_scholar_key=request.semantic_scholar_key,
            pubmed_key=request.pubmed_key,
            core_key=request.core_key,
            fast_provider=fast_provider,
            fast_model=fast_model,
            fast_key=fast_key,
            existing_document=request.existing_document,
            clarifications=request.clarifications,
        )

        return ResearchResponse(
            document=result["document"],
            papers=result["papers"],
            stats=result["stats"],
            steps_log=result["steps_log"],
            status="success",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Endpoint de Export DOCX
# ============================================================
class ExportDocxRequest(BaseModel):
    title: str
    document: str
    norm: Optional[str] = "ABNT"


@app.post("/api/v1/export/docx")
async def export_docx_endpoint(request: ExportDocxRequest):
    if not request.document:
        raise HTTPException(status_code=422, detail="Documento vazio.")

    try:
        docx_bytes = generate_docx(
            title=request.title,
            content=request.document,
            norm=request.norm or "ABNT",
        )

        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in request.title)[:60]
        filename = f"{safe_title}.docx"

        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar DOCX: {str(e)}")


# ============================================================
# Endpoints do Módulo Notebook (NotebookLM-style)
# ============================================================

class NotebookBase(BaseModel):
    """Base compartilhada por todas as requisições do Notebook."""
    theme: str
    document: str
    papers: list
    api_key: Optional[str] = ""
    llm_model: Optional[str] = "gemini-2.0-flash"
    llm_provider: Optional[str] = "gemini"


class ChatRequest(NotebookBase):
    question: str
    history: Optional[list] = None  # [{role: "user"|"assistant", content: "..."}]


class AudioScriptRequest(NotebookBase):
    duration_minutes: Optional[int] = 5


@app.post("/api/v1/notebook/chat")
async def notebook_chat(request: ChatRequest):
    """Chat com a pesquisa usando RAG sobre os papers e o documento."""
    api_key = resolve_api_key(request.api_key, request.llm_provider)
    try:
        result = chat_with_research(
            question=request.question,
            papers=request.papers,
            document=request.document,
            api_key=api_key,
            model=request.llm_model or "gemini-2.0-flash",
            provider=request.llm_provider or "gemini",
            history=request.history,
        )
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/notebook/study-guide")
async def notebook_study_guide(request: NotebookBase):
    """Gera um Guia de Estudo estruturado a partir das fontes."""
    api_key = resolve_api_key(request.api_key, request.llm_provider)
    try:
        result = generate_study_guide(
            theme=request.theme,
            papers=request.papers,
            document=request.document,
            api_key=api_key,
            model=request.llm_model or "gemini-2.0-flash",
            provider=request.llm_provider or "gemini",
        )
        return {"status": "success", "guide": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/notebook/faq")
async def notebook_faq(request: NotebookBase):
    """Gera FAQ automático com base nas fontes da pesquisa."""
    api_key = resolve_api_key(request.api_key, request.llm_provider)
    try:
        result = generate_faq(
            theme=request.theme,
            papers=request.papers,
            document=request.document,
            api_key=api_key,
            model=request.llm_model or "gemini-2.0-flash",
            provider=request.llm_provider or "gemini",
        )
        return {"status": "success", "faq": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/notebook/timeline")
async def notebook_timeline(request: NotebookBase):
    """Extrai linha do tempo dos marcos da área de pesquisa."""
    api_key = resolve_api_key(request.api_key, request.llm_provider)
    try:
        result = generate_timeline(
            theme=request.theme,
            papers=request.papers,
            document=request.document,
            api_key=api_key,
            model=request.llm_model or "gemini-2.0-flash",
            provider=request.llm_provider or "gemini",
        )
        return {"status": "success", "timeline": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/notebook/audio-script")
async def notebook_audio_script(request: AudioScriptRequest):
    """Gera roteiro dialógico estilo podcast (Audio Overview)."""
    api_key = resolve_api_key(request.api_key, request.llm_provider)
    try:
        result = generate_audio_script(
            theme=request.theme,
            papers=request.papers,
            document=request.document,
            api_key=api_key,
            model=request.llm_model or "gemini-2.0-flash",
            provider=request.llm_provider or "gemini",
            duration_minutes=request.duration_minutes or 5,
        )
        return {"status": "success", "script": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/config/status")
def get_config_status():
    """Retorna quais provedores possuem chaves ativas configuradas no servidor."""
    return {
        "gemini": bool(os.environ.get("GEMINI_API_KEY")),
        "openai": bool(os.environ.get("OPENAI_API_KEY")),
        "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "groq": bool(os.environ.get("GROQ_API_KEY")),
        "mistral": bool(os.environ.get("MISTRAL_API_KEY")),
    }
