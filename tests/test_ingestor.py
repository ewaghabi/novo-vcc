import os
from datetime import datetime
from pathlib import Path

import fitz
from docx import Document as DocxDocument
import pytest
import sys
import types

# Ensure repository root is in sys.path for package resolution
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


class DummyVectorStore:
    def __init__(self):
        self.added = []
        self.persist_called = False

    def add_document(self, text, metadata=None):
        self.added.append((text, metadata))

    def persist(self):
        self.persist_called = True


class DummyRelationalDB:
    def __init__(self):
        self.contracts = []

    def add_contract(self, name, path, ingestion_date=None):
        self.contracts.append((name, path, ingestion_date))


def create_sample_pdf(path: Path, text: str):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def create_sample_docx(path: Path, text: str):
    doc = DocxDocument()
    doc.add_paragraph(text)
    doc.save(path)


def test_extract_pdf_and_docx(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    docx_path = tmp_path / "sample.docx"

    create_sample_pdf(pdf_path, "Hello PDF")
    create_sample_docx(docx_path, "Hello DOCX")

    ingestor = ContractIngestor(tmp_path, DummyVectorStore(), DummyRelationalDB())

    assert "Hello PDF" in ingestor._extract_pdf(pdf_path)
    assert "Hello DOCX" in ingestor._extract_docx(docx_path)


def test_ingest_processes_files(monkeypatch, tmp_path):
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
    names = sorted(c[0] for c in db.contracts)
    assert names == ["file1.pdf", "file2.docx"]
    assert all(isinstance(c[2], datetime) for c in db.contracts)
