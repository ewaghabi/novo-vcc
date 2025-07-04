from __future__ import annotations

from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document as DocxDocument

from app.storage.vector_store_adapter import VectorStoreAdapter
from app.storage.relational_db_adapter import RelationalDBAdapter


class ContractIngestor:
    """Ingests PDF and DOCX contracts from a directory."""

    def __init__(
        self,
        directory: str | Path,
        vector_store: VectorStoreAdapter,
        relational_db: RelationalDBAdapter,
    ) -> None:
        self.directory = Path(directory)
        self.vector_store = vector_store
        self.relational_db = relational_db

    def ingest(self, reprocess_all: bool = False) -> None:
        if reprocess_all:
            self.vector_store.clear()

        for file_path in self.directory.iterdir():
            if not file_path.is_file():
                continue
            ext = file_path.suffix.lower()
            if ext == ".pdf":
                text = self._extract_pdf(file_path)
            elif ext == ".docx":
                text = self._extract_docx(file_path)
            else:
                continue

            existing = self.relational_db.get_contract_by_path(str(file_path))
            if existing and not reprocess_all:
                continue

            metadata = {"source": str(file_path)}
            self.vector_store.add_document(text, metadata)
            if existing:
                self.relational_db.update_processing_date(str(file_path))
            else:
                now = datetime.utcnow()
                self.relational_db.add_contract(
                    name=file_path.name,
                    path=str(file_path),
                    ingestion_date=now,
                    last_processed=now,
                )
        self.vector_store.persist()

    def _extract_pdf(self, path: Path) -> str:
        doc = fitz.open(path)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return text

    def _extract_docx(self, path: Path) -> str:
        doc = DocxDocument(path)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        return text
