from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    ingestion_date = Column(DateTime, default=datetime.utcnow)


class RelationalDBAdapter:
    """Simple SQLite wrapper for storing contract metadata."""

    def __init__(self, db_url: str = "sqlite:///data/contracts.db") -> None:
        self._engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine)

    def add_contract(
        self, name: str, path: str, ingestion_date: datetime | None = None
    ) -> None:
        session = self._Session()
        contract = Contract(
            name=name, path=path, ingestion_date=ingestion_date or datetime.utcnow()
        )
        session.add(contract)
        session.commit()
        session.close()
