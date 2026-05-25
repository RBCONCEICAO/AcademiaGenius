# Dockerfile para FastAPI Backend do AcademiaGenius
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências básicas de compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependências
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar restante do código da API
COPY . .

# Expor a porta padrão da API
EXPOSE 8000

# Executar a aplicação com Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
