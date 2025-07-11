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
    ForeignKey,
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
    vetor_embedding = Column(String, nullable=True)
    texto_completo = Column(String, nullable=True)


# Tabela que armazena prompts reutilizáveis para execução de análises
class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    texto = Column(String, nullable=False)
    periodicidade = Column(String, nullable=True)


# Modelo ORM representando as execuções de tarefas
class Execution(Base):
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True)
    task_name = Column(String, nullable=False)
    class_name = Column(String, nullable=False)
    # Campos adicionais para registrar o contexto do prompt executado
    tipo = Column(String, nullable=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=True)
    prompt_text = Column(String, nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="running")
    progress = Column(Float, default=0.0)
    message = Column(String, nullable=True)


# Resultado gerado após uma execução em um contrato específico
class ExecutionResult(Base):
    __tablename__ = "execution_results"

    id = Column(Integer, primary_key=True)
    execution_id = Column(Integer, ForeignKey("executions.id"), nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    resposta_completa = Column(String, nullable=True)
    resposta_simples = Column(String, nullable=True)
    confianca = Column(Float, nullable=True)


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
    # Operações para tabela de prompts

    def add_prompt(
        self,
        nome: str,
        texto: str,
        periodicidade: str | None = None,
    ) -> int:
        """Insere um novo prompt e retorna seu ID."""
        session = self._Session()
        row = Prompt(nome=nome, texto=texto, periodicidade=periodicidade)
        session.add(row)
        session.commit()
        pid = row.id
        session.close()
        return pid

    def list_prompts(self) -> list[Prompt]:
        """Lista todos os prompts cadastrados."""
        session = self._Session()
        rows = session.query(Prompt).order_by(Prompt.id).all()
        session.close()
        return rows

    def get_prompt(self, prompt_id: int) -> Prompt | None:
        """Recupera um prompt pelo id."""
        session = self._Session()
        row = session.query(Prompt).filter_by(id=prompt_id).first()
        session.close()
        return row

    def update_prompt(self, prompt_id: int, **fields) -> None:
        """Atualiza campos de um prompt existente."""
        session = self._Session()
        row = session.query(Prompt).filter_by(id=prompt_id).first()
        if row:
            for key, value in fields.items():
                setattr(row, key, value)
            session.commit()
        session.close()

    def delete_prompt(self, prompt_id: int) -> None:
        """Remove um prompt do banco."""
        session = self._Session()
        row = session.query(Prompt).filter_by(id=prompt_id).first()
        if row:
            session.delete(row)
            session.commit()
        session.close()

    # ------------------------------------------------------------------
    # Operações para resultados de execução

    def add_execution_result(
        self,
        execution_id: int,
        contract_id: int | None,
        resposta_completa: str | None,
        resposta_simples: str | None,
        confianca: float | None = None,
    ) -> int:
        """Registra resultado produzido por uma execução."""
        session = self._Session()
        row = ExecutionResult(
            execution_id=execution_id,
            contract_id=contract_id,
            resposta_completa=resposta_completa,
            resposta_simples=resposta_simples,
            confianca=confianca,
        )
        session.add(row)
        session.commit()
        rid = row.id
        session.close()
        return rid

    # ------------------------------------------------------------------
    # Operações relacionadas à tabela de execuções de tarefas

    # Cria registro inicial de uma execução de tarefa
    def create_execution(
        self,
        task_name: str,
        class_name: str,
        *,
        tipo: str | None = None,
        prompt_id: int | None = None,
        prompt_text: str | None = None,
    ) -> int:
        """Insere registro de início de execução."""
        session = self._Session()
        exec_row = Execution(
            task_name=task_name,
            class_name=class_name,
            tipo=tipo,
            prompt_id=prompt_id,
            prompt_text=prompt_text,
        )
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
