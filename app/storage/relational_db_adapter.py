from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Float,
    Numeric,
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


# Modelo ORM representando os contratos armazenados
class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    ingestion_date = Column(DateTime, default=datetime.utcnow)
    last_processed = Column(DateTime, default=datetime.utcnow)

    # Additional optional metadata fields
    contrato = Column(String, nullable=True)
    inicioPrazo = Column(Date, nullable=True)
    fimPrazo = Column(Date, nullable=True)
    empresa = Column(String, nullable=True)
    icj = Column(String, nullable=True)
    valorContratoOriginal = Column(Numeric, nullable=True)
    moeda = Column(String, nullable=True)
    taxaCambio = Column(Float, nullable=True)
    gerenteContrato = Column(String, nullable=True)
    nomeGerenteContrato = Column(String, nullable=True)
    lotacaoGerenteContrato = Column(String, nullable=True)
    areaContrato = Column(String, nullable=True)
    modalidade = Column(String, nullable=True)
    textoModalidade = Column(String, nullable=True)
    reajuste = Column(String, nullable=True)
    fornecedor = Column(String, nullable=True)
    nomeFornecedor = Column(String, nullable=True)
    tipoContrato = Column(String, nullable=True)
    objetoContrato = Column(String, nullable=True)
    linhasServico = Column(String, nullable=True)


# Modelo ORM representando as execuções de tarefas
class Execution(Base):
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True)
    task_name = Column(String, nullable=False)
    class_name = Column(String, nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="running")
    progress = Column(Float, default=0.0)
    message = Column(String, nullable=True)


# Adaptador simples para persistência usando SQLite
class RelationalDBAdapter:
    """Simple SQLite wrapper for storing contract metadata."""

    # Inicializa conexões e cria tabelas no banco SQLite
    def __init__(self, db_url: str = "sqlite:///data/contracts.db") -> None:
        """Cria engine e classe de sessão."""
        self._engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine)

    # Insere um contrato simples na tabela
    def add_contract(
        self,
        name: str,
        path: str,
        ingestion_date: datetime | None = None,
        last_processed: datetime | None = None,
    ) -> None:
        session = self._Session()
        now = datetime.utcnow()
        contract = Contract(
            name=name,
            path=path,
            ingestion_date=ingestion_date or now,
            last_processed=last_processed or now,
        )
        session.add(contract)
        session.commit()
        session.close()

    # Retorna contrato a partir do caminho do arquivo
    def get_contract_by_path(self, path: str) -> Contract | None:
        """Retorna contrato pelo caminho do arquivo."""
        session = self._Session()
        contract = session.query(Contract).filter_by(path=path).first()
        session.close()
        return contract

    # Atualiza a data de processamento de um contrato
    def update_processing_date(
        self, path: str, processing_date: datetime | None = None
    ) -> None:
        """Atualiza a data de processamento do contrato."""
        session = self._Session()
        contract = session.query(Contract).filter_by(path=path).first()
        if contract:
            contract.last_processed = processing_date or datetime.utcnow()
            session.commit()
        session.close()

    # Insere contrato com metadados mais completos
    def add_contract_structured(self, **fields) -> None:
        """Insere contrato com metadados estruturados."""
        session = self._Session()
        fields.setdefault("name", fields.get("contrato"))
        fields.setdefault("path", fields.get("contrato"))
        fields.setdefault("ingestion_date", datetime.utcnow())
        fields.setdefault("last_processed", datetime.utcnow())
        contract = Contract(**fields)
        session.add(contract)
        session.commit()
        session.close()

    # Obtém contrato pelo identificador "contrato"
    def get_contract_by_contrato(self, contrato: str) -> Contract | None:
        """Busca contrato pelo identificador do campo contrato."""
        session = self._Session()
        contract = session.query(Contract).filter_by(contrato=contrato).first()
        session.close()
        return contract


    # Remove todos os contratos cadastrados
    def clear_contracts(self) -> None:
        """Remove todos os registros da tabela."""
        session = self._Session()
        session.query(Contract).delete()
        session.commit()
        session.close()

    # ------------------------------------------------------------------
    # Operações relacionadas à tabela de execuções de tarefas

    # Cria registro inicial de uma execução de tarefa
    def create_execution(self, task_name: str, class_name: str) -> int:
        """Insere registro de início de execução."""
        session = self._Session()
        exec_row = Execution(task_name=task_name, class_name=class_name)
        session.add(exec_row)
        session.commit()
        exec_id = exec_row.id
        session.close()
        return exec_id

    # Busca uma execução específica pelo ID
    def get_execution(self, exec_id: int) -> Execution | None:
        """Busca execução pelo identificador."""
        session = self._Session()
        row = session.query(Execution).filter_by(id=exec_id).first()
        session.close()
        return row

    # Atualiza campos de uma execução existente
    def update_execution(
        self,
        exec_id: int,
        *,
        progress: float | None = None,
        status: str | None = None,
        end_time: datetime | None = None,
        message: str | None = None,
    ) -> None:
        """Atualiza campos da execução."""
        session = self._Session()
        row = session.query(Execution).filter_by(id=exec_id).first()
        if row:
            if progress is not None:
                row.progress = progress
            if status is not None:
                row.status = status
            if end_time is not None:
                row.end_time = end_time
            if message is not None:
                row.message = message
            session.commit()
        session.close()

    # Remove todos os registros de execuções
    def clear_executions(self) -> None:
        """Remove todas as execuções."""
        session = self._Session()
        session.query(Execution).delete()
        session.commit()
        session.close()

    # Lista execuções filtrando por status e período
    def list_executions(
        self,
        *,
        status: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Execution]:
        """Retorna execuções filtrando por status e período."""
        session = self._Session()
        query = session.query(Execution)
        if status is not None:
            query = query.filter(Execution.status == status)
        if start is not None:
            query = query.filter(Execution.start_time >= start)
        if end is not None:
            query = query.filter(Execution.start_time <= end)
        rows = query.order_by(Execution.start_time).all()
        session.close()
        return rows
