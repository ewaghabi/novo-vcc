from fastapi import APIRouter, Body
from datetime import datetime

from app.ingestion.ingestor import ContractIngestor, ContractStructuredDataIngestor
from app.storage.vector_store_adapter import VectorStoreAdapter
from app.storage.relational_db_adapter import RelationalDBAdapter, Contract
from app.chat.chatbot import ContractChatbot

router = APIRouter()

# Initialize shared components
_vector_store = VectorStoreAdapter()
_relational_db = RelationalDBAdapter()
_ingestor = ContractIngestor("data", _vector_store, _relational_db)
_chatbot = ContractChatbot(_vector_store)


# Rota para realizar ingestão básica de arquivos
@router.post("/ingest")
def ingest() -> dict:
    """Trigger ingestion of contract files."""
    _ingestor.ingest()
    return {"status": "ok"}


# Rota responsável pela carga de metadados estruturados
@router.post("/ingest-structured")
def ingest_structured(csv_path: str = Body(..., embed=True)) -> dict:
    """Carrega metadados de contratos a partir de um CSV.

    Recebe o caminho do arquivo como parâmetro e devolve o id da execução
    registrada.
    """
    ingestor = ContractStructuredDataIngestor(csv_path, _relational_db)
    exec_id = ingestor.ingest()
    return {"status": "ok", "id": exec_id}


# Rota para enviar perguntas ao chatbot
@router.post("/chat")
def chat(question: str = Body(..., embed=True)) -> dict:
    """Ask a question about contracts."""
    answer, sources = _chatbot.ask(question)
    return {"answer": answer, "sources": sources}


# Lista todos os contratos armazenados
@router.get("/contracts")
def list_contracts() -> dict:
    """Return a simple list of stored contracts."""
    session = _relational_db._Session()
    rows = session.query(Contract).all()
    # Monta lista de dicionários a partir dos objetos
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


# Consulta execuções registradas filtrando por status e período
@router.get("/executions")
def list_executions(status: str | None = None, start: str | None = None, end: str | None = None) -> dict:
    start_dt = datetime.fromisoformat(start) if start else None
    end_dt = datetime.fromisoformat(end) if end else None
    rows = _relational_db.list_executions(status=status, start=start_dt, end=end_dt)
    # Converte objetos de execução em dicionários
    executions = [
        {
            "id": r.id,
            "task_name": r.task_name,
            "class_name": r.class_name,
            "start_time": r.start_time.isoformat() if r.start_time else None,
            "end_time": r.end_time.isoformat() if r.end_time else None,
            "status": r.status,
            "progress": r.progress,
            "message": r.message,
        }
        for r in rows
    ]
    return {"executions": executions}


# Consulta detalhes de uma execução específica
@router.get("/executions/{exec_id}")
def get_execution(exec_id: int) -> dict:
    """Retorna informações de uma execução pelo id."""
    row = _relational_db.get_execution(exec_id)
    if not row:
        return {}
    return {
        "id": row.id,
        "task_name": row.task_name,
        "class_name": row.class_name,
        "start_time": row.start_time.isoformat() if row.start_time else None,
        "end_time": row.end_time.isoformat() if row.end_time else None,
        "status": row.status,
        "progress": row.progress,
        "message": row.message,
    }
