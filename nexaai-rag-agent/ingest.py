"""
ingest.py

Script responsável pela ETAPA DE INDEXAÇÃO do RAG da NexaAI.

Executar separadamente da aplicação (python ingest.py) sempre que os
documentos em data/ forem adicionados, removidos ou atualizados.

Pipeline:
    1. Localiza os PDFs em data/
    2. Extrai o texto de cada página com pypdf
    3. Divide o texto em chunks menores (RecursiveCharacterTextSplitter)
    4. Gera embeddings para cada chunk (Google Gemini)
    5. Persiste os vetores + metadados no ChromaDB (chroma_db/)

Metadados preservados por chunk:
    - source: nome do arquivo PDF de origem
    - page: número da página (base 1) de onde o chunk foi extraído
    - chunk_id: índice sequencial do chunk dentro da página
"""

from __future__ import annotations

import sys
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

import config


def find_pdfs(data_dir: Path) -> list[Path]:
    """Localiza todos os arquivos PDF dentro do diretório de dados."""
    pdfs = sorted(data_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(
            f"Nenhum PDF encontrado em '{data_dir}'. "
            "Adicione os documentos da NexaAI nessa pasta antes de indexar."
        )
    return pdfs


def load_pdf_as_documents(pdf_path: Path) -> list[Document]:
    """Extrai o texto de cada página de um PDF e retorna Documents do LangChain.

    Cada página vira um Document independente, com metadados de origem e
    número de página, para que essas informações sobrevivam ao chunking
    e possam ser exibidas como "fonte" na interface.
    """
    reader = PdfReader(str(pdf_path))
    documents: list[Document] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if not text:
            # Página sem texto extraível (ex.: apenas imagem) é ignorada.
            continue
        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": pdf_path.name,
                    "page": page_number,
                },
            )
        )
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    """Divide os documentos (por página) em chunks menores para o RAG."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)

    # Adiciona um índice de chunk por página, útil para depuração e para
    # evitar IDs duplicados no ChromaDB.
    counters: dict[tuple[str, int], int] = {}
    for chunk in chunks:
        key = (chunk.metadata["source"], chunk.metadata["page"])
        counters[key] = counters.get(key, 0) + 1
        chunk.metadata["chunk_id"] = counters[key]

    return chunks


def build_vector_store(chunks: list[Document]) -> None:
    """Gera embeddings para os chunks e persiste no ChromaDB."""
    embeddings = GoogleGenerativeAIEmbeddings(
        model=config.GEMINI_EMBEDDING_MODEL,
        google_api_key=config.GOOGLE_API_KEY,
    )

    # `persist_directory` grava o índice em disco, para não recalcular
    # embeddings a cada execução da aplicação.
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=config.COLLECTION_NAME,
        persist_directory=str(config.CHROMA_DIR),
    )


def main() -> None:
    print("NexaAI — Indexação da base de conhecimento")
    print("=" * 50)

    config.validate_api_key()

    print(f"Procurando PDFs em: {config.DATA_DIR}")
    pdfs = find_pdfs(config.DATA_DIR)
    print(f"{len(pdfs)} arquivo(s) encontrado(s):")
    for pdf in pdfs:
        print(f"  - {pdf.name}")

    print("\nExtraindo texto das páginas...")
    all_documents: list[Document] = []
    for pdf in pdfs:
        page_documents = load_pdf_as_documents(pdf)
        print(f"  - {pdf.name}: {len(page_documents)} página(s) com texto")
        all_documents.extend(page_documents)

    if not all_documents:
        print("Nenhum texto pôde ser extraído dos PDFs. Abortando.")
        sys.exit(1)

    print("\nDividindo documentos em chunks...")
    chunks = split_documents(all_documents)
    print(f"Total de chunks gerados: {len(chunks)}")

    print("\nGerando embeddings e indexando no ChromaDB...")
    print(f"Diretório do índice: {config.CHROMA_DIR}")
    build_vector_store(chunks)

    print("\nIndexação concluída com sucesso.")
    print(f"Coleção: {config.COLLECTION_NAME}")


if __name__ == "__main__":
    main()
