from fastapi import APIRouter, Body

from app.ingestion.ingestor import ContractIngestor, ContractStructuredDataIngestor
from app.storage.vector_store_adapter import VectorStoreAdapter
from app.storage.relational_db_adapter import RelationalDBAdapter, Contract
from app.chat.chatbot import ContractChatbot

router = APIRouter()

# Initialize shared components
_vector_store = VectorStoreAdapter()
_relational_db = RelationalDBAdapter()
_ingestor = ContractIngestor("data", _vector_store, _relational_db)
_structured_ingestor = ContractStructuredDataIngestor("data/contratos.csv", _relational_db)
_chatbot = ContractChatbot(_vector_store)


@router.post("/ingest")
def ingest() -> dict:
    """Trigger ingestion of contract files."""
    _ingestor.ingest()
    return {"status": "ok"}


@router.post("/ingest-structured")
def ingest_structured() -> dict:
    """Load structured contract metadata."""
    _structured_ingestor.ingest()
    return {"status": "ok", "progress": _structured_ingestor.progress}


@router.post("/chat")
def chat(question: str = Body(..., embed=True)) -> dict:
    """Ask a question about contracts."""
    answer, sources = _chatbot.ask(question)
    return {"answer": answer, "sources": sources}


@router.get("/contracts")
def list_contracts() -> dict:
    """Return a simple list of stored contracts."""
    session = _relational_db._Session()
    rows = session.query(Contract).all()
    contracts = [
        {
            "id": r.id,
            "name": r.name,
            "path": r.path,
            "ingestion_date": r.ingestion_date.isoformat() if r.ingestion_date else None,
            "last_processed": r.last_processed.isoformat() if r.last_processed else None,
        }
        for r in rows
    ]
    session.close()
    return {"contracts": contracts}
