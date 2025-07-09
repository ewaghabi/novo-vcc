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
    areaContrato = Column(String, nullable=True)
    modalidade = Column(String, nullable=True)
    textoModalidade = Column(String, nullable=True)
    reajuste = Column(String, nullable=True)
    fornecedor = Column(String, nullable=True)
    nomeFornecedor = Column(String, nullable=True)
    tipoContrato = Column(String, nullable=True)
    objetoContrato = Column(String, nullable=True)
    linhasServico = Column(String, nullable=True)


class RelationalDBAdapter:
    """Simple SQLite wrapper for storing contract metadata."""

    def __init__(self, db_url: str = "sqlite:///data/contracts.db") -> None:
        self._engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine)

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

    def get_contract_by_path(self, path: str) -> Contract | None:
        session = self._Session()
        contract = session.query(Contract).filter_by(path=path).first()
        session.close()
        return contract

    def update_processing_date(
        self, path: str, processing_date: datetime | None = None
    ) -> None:
        session = self._Session()
        contract = session.query(Contract).filter_by(path=path).first()
        if contract:
            contract.last_processed = processing_date or datetime.utcnow()
            session.commit()
        session.close()

    def add_contract_structured(self, **fields) -> None:
        """Insert a contract with structured metadata."""
        session = self._Session()
        fields.setdefault("name", fields.get("contrato"))
        fields.setdefault("path", fields.get("contrato"))
        fields.setdefault("ingestion_date", datetime.utcnow())
        fields.setdefault("last_processed", datetime.utcnow())
        contract = Contract(**fields)
        session.add(contract)
        session.commit()
        session.close()

    def get_contract_by_contrato(self, contrato: str) -> Contract | None:
        """Return contract by its contrato identifier if present."""
        session = self._Session()
        contract = session.query(Contract).filter_by(contrato=contrato).first()
        session.close()
        return contract

    def clear_contracts(self) -> None:
        """Remove all contract rows."""
        session = self._Session()
        session.query(Contract).delete()
        session.commit()
        session.close()
