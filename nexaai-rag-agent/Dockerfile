# NexaAI — Assistente Corporativo
# Imagem baseada em Python slim para manter o build enxuto.

FROM python:3.12-slim

WORKDIR /app

# Instala dependências do sistema necessárias para compilar
# algumas libs nativas usadas pelo ChromaDB.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas o requirements primeiro para aproveitar o cache de camadas
# do Docker quando o código muda mas as dependências não.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# A API key e demais variáveis são fornecidas em tempo de execução
# (via --env-file .env ou docker-compose), nunca copiadas para a imagem.

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Por padrão, apenas inicia a interface. A indexação (`python ingest.py`)
# deve ser executada manualmente antes do primeiro uso — veja README.md
# e docs/deploy-oci.md.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
