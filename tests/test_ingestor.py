import os
from datetime import datetime
from pathlib import Path

import fitz
from docx import Document as DocxDocument
import pytest
import sys
import types

# Ajusta PATH para localizar o pacote da aplicação
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Stub langchain modules so imports in the application do not require the real
# heavy dependencies during tests.
langchain_stub = types.ModuleType("langchain")
langchain_stub.embeddings = types.ModuleType("langchain.embeddings")
langchain_stub.embeddings.OpenAIEmbeddings = object
langchain_stub.vectorstores = types.ModuleType("langchain.vectorstores")
langchain_stub.vectorstores.Chroma = object
sys.modules.setdefault("langchain", langchain_stub)
sys.modules.setdefault("langchain.embeddings", langchain_stub.embeddings)
sys.modules.setdefault("langchain.vectorstores", langchain_stub.vectorstores)

from app.ingestion.ingestor import ContractIngestor


# Armazena dados de forma simplificada durante os testes
class DummyVectorStore:
    def __init__(self):
        self.added = []
        self.persist_called = False
        self.cleared = False

    def add_document(self, text, metadata=None):
        self.added.append((text, metadata))

    def persist(self):
        self.persist_called = True

    def clear(self):
        self.cleared = True


# Simula banco relacional usado pela ingestão
class DummyRelationalDB:
    def __init__(self):
        self.contracts = []

    def add_contract(
        self,
        name,
        path,
        ingestion_date=None,
        last_processed=None,
    ):
        self.contracts.append(
            {
                "name": name,
                "path": path,
                "ingestion_date": ingestion_date,
                "last_processed": last_processed,
            }
        )

    def get_contract_by_path(self, path):
        for c in self.contracts:
            if c["path"] == path:
                return c
        return None

    def update_processing_date(self, path, processing_date=None):
        c = self.get_contract_by_path(path)
        if c:
            c["last_processed"] = processing_date or datetime.utcnow()


def create_sample_pdf(path: Path, text: str):
    """Gera um PDF fictício para testes."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def create_sample_docx(path: Path, text: str):
    """Cria documento DOCX simples."""
    doc = DocxDocument()
    doc.add_paragraph(text)
    doc.save(path)


def test_extract_pdf_and_docx(tmp_path):
    """Valida extração de texto de arquivos."""
    pdf_path = tmp_path / "sample.pdf"
    docx_path = tmp_path / "sample.docx"

    create_sample_pdf(pdf_path, "Hello PDF")
    create_sample_docx(docx_path, "Hello DOCX")

    ingestor = ContractIngestor(tmp_path, DummyVectorStore(), DummyRelationalDB())

    assert "Hello PDF" in ingestor._extract_pdf(pdf_path)
    assert "Hello DOCX" in ingestor._extract_docx(docx_path)


def test_ingest_processes_files(monkeypatch, tmp_path):
    """Verifica ingestão básica de arquivos."""
    pdf_path = tmp_path / "file1.pdf"
    docx_path = tmp_path / "file2.docx"
    pdf_path.touch()
    docx_path.touch()

    vec = DummyVectorStore()
    db = DummyRelationalDB()

    ingestor = ContractIngestor(tmp_path, vec, db)

    monkeypatch.setattr(ingestor, "_extract_pdf", lambda p: "PDF TEXT")
    monkeypatch.setattr(ingestor, "_extract_docx", lambda p: "DOCX TEXT")

    ingestor.ingest()

    expected = [
        ("PDF TEXT", {"source": str(pdf_path)}),
        ("DOCX TEXT", {"source": str(docx_path)}),
    ]
    assert sorted(vec.added, key=lambda x: x[0]) == sorted(expected, key=lambda x: x[0])
    assert vec.persist_called
    names = sorted(c["name"] for c in db.contracts)
    assert names == ["file1.pdf", "file2.docx"]
    assert all(isinstance(c["ingestion_date"], datetime) for c in db.contracts)
    assert all(isinstance(c["last_processed"], datetime) for c in db.contracts)


def test_ingest_skips_already_processed_files(monkeypatch, tmp_path):
    """Garante que arquivos já processados são ignorados."""
    pdf_path = tmp_path / "file1.pdf"
    docx_path = tmp_path / "file2.docx"
    pdf_path.touch()
    docx_path.touch()

    vec = DummyVectorStore()
    db = DummyRelationalDB()
    db.add_contract(
        name="file1.pdf",
        path=str(pdf_path),
        ingestion_date=datetime(2020, 1, 1),
        last_processed=datetime(2020, 1, 1),
    )

    ingestor = ContractIngestor(tmp_path, vec, db)

    monkeypatch.setattr(ingestor, "_extract_pdf", lambda p: "PDF TEXT")
    monkeypatch.setattr(ingestor, "_extract_docx", lambda p: "DOCX TEXT")

    ingestor.ingest()

    assert ("PDF TEXT", {"source": str(pdf_path)}) not in vec.added
    assert ("DOCX TEXT", {"source": str(docx_path)}) in vec.added
    assert len(db.contracts) == 2


def test_ingest_reprocess_all_clears_and_updates(monkeypatch, tmp_path):
    """Testa opção de reprocessamento completo."""
    pdf_path = tmp_path / "file1.pdf"
    docx_path = tmp_path / "file2.docx"
    pdf_path.touch()
    docx_path.touch()

    vec = DummyVectorStore()
    db = DummyRelationalDB()
    db.add_contract(
        name="file1.pdf",
        path=str(pdf_path),
        ingestion_date=datetime(2020, 1, 1),
        last_processed=datetime(2020, 1, 1),
    )
    db.add_contract(
        name="file2.docx",
        path=str(docx_path),
        ingestion_date=datetime(2020, 1, 1),
        last_processed=datetime(2020, 1, 1),
    )

    ingestor = ContractIngestor(tmp_path, vec, db)

    monkeypatch.setattr(ingestor, "_extract_pdf", lambda p: "PDF TEXT")
    monkeypatch.setattr(ingestor, "_extract_docx", lambda p: "DOCX TEXT")

    ingestor.ingest(reprocess_all=True)

    assert vec.cleared
    assert len(vec.added) == 2
    assert all(c["last_processed"] is not None for c in db.contracts)
