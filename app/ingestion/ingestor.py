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
from app.storage.execution_tracker import ExecutionTracker
from app.processing.employees import EmployeeResolver


# Classe para realizar a ingestão de contratos em PDF ou DOCX
class ContractIngestor:
    """Ingests PDF and DOCX contracts from a directory."""

    # Configura caminhos e dependências para a ingestão
    def __init__(
        self,
        directory: str | Path,
        vector_store: VectorStoreAdapter,
        relational_db: RelationalDBAdapter,
    ) -> None:
        # Caminho contendo os contratos a serem processados
        self.directory = Path(directory)
        self.vector_store = vector_store
        self.relational_db = relational_db

    # Percorre os arquivos da pasta realizando a ingestão
    def ingest(self, reprocess_all: bool = False) -> None:
        """Percorre os arquivos e envia texto para o vetor e banco"""
        if reprocess_all:
            # Solicita limpeza total do vetor quando indicado
            self.vector_store.clear()  # remove documentos existentes

        # Itera sobre todos os arquivos encontrados na pasta
        for file_path in self.directory.iterdir():  # loop sobre cada arquivo na pasta
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
            self.vector_store.add_document(text, metadata)  # armazena texto no Chroma
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
        self.vector_store.persist()  # garante que as alterações sejam salvas

    def _extract_pdf(self, path: Path) -> str:
        """Lê o texto de um arquivo PDF"""
        doc = fitz.open(path)
        # Concatena o texto de todas as páginas
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return text

    def _extract_docx(self, path: Path) -> str:
        """Lê o texto de um documento DOCX"""
        doc = DocxDocument(path)
        # Junta todas as linhas do documento
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        return text


# Classe dedicada a carregar metadados estruturados a partir de CSV
class ContractStructuredDataIngestor:
    """Load structured contract data from a CSV file."""

    # Recebe caminho do CSV e dependências de banco
    def __init__(self, csv_path: str | Path, relational_db: RelationalDBAdapter) -> None:
        # Caminho do arquivo CSV com dados estruturados
        self.csv_path = Path(csv_path)
        self.relational_db = relational_db
        self.progress = 0.0
        self._resolver = EmployeeResolver()

    # Carrega os contratos definidos no CSV
    def ingest(self, full_load: bool = False) -> None:
        """Realiza a carga dos contratos listados no CSV"""
        tracker = ExecutionTracker(
            self.relational_db, "structured_ingest", self.__class__.__name__
        )
        tracker.start()
        # Bloco protegido para registrar falhas na execução
        try:
            if full_load:
                self.relational_db.clear_contracts()

            self.progress = 0.0

            contracts: dict[str, dict] = {}
            with open(self.csv_path, encoding="utf8") as f:
                # Leitura linha a linha do CSV
                header: list[str] | None = None
                for line in f:  # percorre cada linha do arquivo
                    line = line.strip()
                    if not line or not line.startswith('"'):
                        continue
                    line = line[1:]
                    if line.endswith('"'):
                        line = line[:-1]
                    line = line.rstrip(';')
                    line = line.replace('""', '"')
                    row = next(csv.reader([line], delimiter=",", quotechar='"'))
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

            total = len(contracts)
            processed = 0
            for data in contracts.values():  # percorre cada contrato carregado
                if self.relational_db.get_contract_by_contrato(data["contrato"]):
                    processed += 1
                    self.progress = processed / total * 100
                    tracker.update(progress=self.progress)
                    continue
                emp = self._resolver.resolve(data["gerenteContrato"])
                data["nomeGerenteContrato"] = emp["nome"]
                data["lotacaoGerenteContrato"] = emp["lotacao"]
                data["linhasServico"] = json.dumps(
                    data["linhasServico"], ensure_ascii=False
                )
                self.relational_db.add_contract_structured(**data)
                processed += 1
                self.progress = processed / total * 100
                tracker.update(progress=self.progress)

            tracker.finish()
        except Exception:
            # Em caso de erro marca a execução como falha
            tracker.finish(status="failed")
            raise

    def _parse_date(self, value: str) -> date | None:
        """Converte string de data para objeto date"""
        # Tentativa de conversão para data
        try:
            return datetime.strptime(value, "%Y%m%d").date()
        except Exception:
            return None

    def _parse_float(self, value: str) -> float | None:
        """Converte número em texto para float"""
        # Converte para float quando possível
        try:
            return float(value)
        except Exception:
            return None
