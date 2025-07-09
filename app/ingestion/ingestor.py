from __future__ import annotations

from datetime import datetime
from pathlib import Path
from datetime import date
import csv
import json

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


class ContractStructuredDataIngestor:
    """Load structured contract data from a CSV file."""

    def __init__(self, csv_path: str | Path, relational_db: RelationalDBAdapter) -> None:
        self.csv_path = Path(csv_path)
        self.relational_db = relational_db

    def ingest(self, full_load: bool = False) -> None:
        if full_load:
            self.relational_db.clear_contracts()

        contracts: dict[str, dict] = {}
        with open(self.csv_path, encoding="utf8") as f:
            header: list[str] | None = None
            for line in f:
                line = line.strip()
                if not line or not line.startswith('"'):
                    continue
                line = line[1:]
                if line.endswith('"'):
                    line = line[:-1]
                line = line.rstrip(';')
                line = line.replace('""', '"')
                row = next(csv.reader([line], delimiter=',', quotechar='"'))
                if header is None:
                    header = row
                    continue
                if len(row) != 20:
                    continue
                (
                    contrato,
                    inicio,
                    fim,
                    empresa,
                    icj,
                    valor_original,
                    moeda,
                    taxa_cambio,
                    gerente,
                    modalidade,
                    texto_modalidade,
                    reajuste,
                    fornecedor,
                    nome_fornecedor,
                    tipo_contrato,
                    objeto_contrato,
                    item_pedido,
                    descricao_item,
                    numero_externo,
                    descricao_item2,
                ) = row

                service = {
                    "ItemPedido": item_pedido,
                    "DescricaoItem": descricao_item,
                    "NumeroExterno": numero_externo,
                    "DescriçãoItem": descricao_item2,
                }

                if contrato not in contracts:
                    contracts[contrato] = {
                        "name": contrato,
                        "path": contrato,
                        "contrato": contrato,
                        "ingestion_date": datetime.utcnow(),
                        "last_processed": datetime.utcnow(),
                        "inicioPrazo": self._parse_date(inicio),
                        "fimPrazo": self._parse_date(fim),
                        "empresa": empresa,
                        "icj": icj,
                        "valorContratoOriginal": self._parse_float(valor_original),
                        "moeda": moeda,
                        "taxaCambio": self._parse_float(taxa_cambio),
                        "gerenteContrato": gerente,
                        "modalidade": modalidade,
                        "textoModalidade": texto_modalidade,
                        "reajuste": reajuste,
                        "fornecedor": fornecedor,
                        "nomeFornecedor": nome_fornecedor,
                        "tipoContrato": tipo_contrato,
                        "objetoContrato": objeto_contrato,
                        "linhasServico": [service],
                    }
                else:
                    contracts[contrato]["linhasServico"].append(service)

        for data in contracts.values():
            if self.relational_db.get_contract_by_contrato(data["contrato"]):
                continue
            data["linhasServico"] = json.dumps(data["linhasServico"], ensure_ascii=False)
            self.relational_db.add_contract_structured(**data)

    def _parse_date(self, value: str) -> date | None:
        try:
            return datetime.strptime(value, "%Y%m%d").date()
        except Exception:
            return None

    def _parse_float(self, value: str) -> float | None:
        try:
            return float(value)
        except Exception:
            return None
