"""
tests/test_ingest.py

Testes da etapa de processamento de documentos (não dependem de API key,
pois testam apenas leitura de PDF e chunking, que são operações locais).

Executar com:
    pytest tests/test_ingest.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from ingest import find_pdfs, load_pdf_as_documents, split_documents

EXPECTED_PDFS = {
    "01_base_conhecimento_nexaai.pdf",
    "02_faq_suporte_nexaai.pdf",
    "03_politica_privacidade_nexaai.pdf",
    "04_planos_e_precos_nexaai.pdf",
    "05_termos_de_uso_nexaai.pdf",
}


def test_find_pdfs_locates_all_documents():
    pdfs = find_pdfs(config.DATA_DIR)
    found_names = {p.name for p in pdfs}
    assert EXPECTED_PDFS.issubset(found_names)


def test_load_pdf_extracts_text_with_metadata():
    pdf_path = config.DATA_DIR / "04_planos_e_precos_nexaai.pdf"
    documents = load_pdf_as_documents(pdf_path)

    assert len(documents) >= 1
    first = documents[0]
    assert first.metadata["source"] == "04_planos_e_precos_nexaai.pdf"
    assert first.metadata["page"] == 1
    assert "Business" in first.page_content


def test_split_documents_generates_chunks_with_ids():
    pdf_path = config.DATA_DIR / "05_termos_de_uso_nexaai.pdf"
    documents = load_pdf_as_documents(pdf_path)
    chunks = split_documents(documents)

    assert len(chunks) >= 1
    for chunk in chunks:
        assert "source" in chunk.metadata
        assert "page" in chunk.metadata
        assert "chunk_id" in chunk.metadata
        assert len(chunk.page_content) <= config.CHUNK_SIZE + config.CHUNK_OVERLAP
