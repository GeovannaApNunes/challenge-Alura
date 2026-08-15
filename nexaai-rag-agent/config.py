"""
config.py

Configurações centrais da aplicação NexaAI - Assistente Corporativo.

Todas as configurações sensíveis (como a API key do Google) são lidas
a partir de variáveis de ambiente / arquivo .env, nunca hardcoded.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (se existir) para o ambiente do processo
load_dotenv()

# --- Diretórios do projeto ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"

# --- Credenciais e modelos (Google Gemini) ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Modelo de chat (geração de respostas). Pode ser trocado via .env sem
# alterar código-fonte.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Modelo de embeddings usado tanto na indexação (ingest.py) quanto na
# consulta (rag.py). É essencial que os DOIS usem o MESMO modelo.
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")

# --- Parâmetros de RAG ---
# Tamanho (em caracteres) de cada chunk de texto extraído dos PDFs.
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))

# Sobreposição entre chunks consecutivos, para não perder contexto nas bordas.
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# Quantidade de chunks recuperados por pergunta (top-k).
RETRIEVER_K = int(os.getenv("RETRIEVER_K", "4"))

# Nome da coleção usada dentro do ChromaDB.
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "nexaai_knowledge_base")


def validate_api_key() -> None:
    """Lança um erro claro caso a API key não esteja configurada.

    Chamado nos pontos de entrada (ingest.py e app.py) para falhar cedo
    e com uma mensagem compreensível, em vez de um erro genérico da API.
    """
    if not GOOGLE_API_KEY:
        raise RuntimeError(
            "GOOGLE_API_KEY não encontrada. Configure-a no arquivo .env "
            "(veja .env.example) antes de executar a aplicação."
        )
