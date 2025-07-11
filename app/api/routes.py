from fastapi import APIRouter, Body
from datetime import datetime

from app.ingestion.ingestor import ContractIngestor, ContractStructuredDataIngestor
from app.storage.vector_store_adapter import VectorStoreAdapter
from app.storage.relational_db_adapter import (
    RelationalDBAdapter,
    Contract,
    Prompt,
)
from app.chat.chatbot import ContractChatbot
from app.processing.execution import ExhaustiveProcessor

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
def chat(
    question: str = Body(..., embed=True),
    model: str | None = Body(None, embed=True),
) -> dict:
    """Envie uma pergunta ao chatbot utilizando o modelo informado."""
    # Usa o chatbot global por padrão, mas permite especificar outro modelo
    bot = _chatbot if model is None else ContractChatbot(_vector_store, model=model)
    answer, sources = bot.ask(question)
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


# Recupera detalhes de um contrato específico pelo número
@router.get("/contract/{contract_id}")
def get_contract(contract_id: str) -> dict:
    """Retorna os dados completos de um contrato pelo campo 'contrato'."""
    # Busca no banco utilizando o valor do campo 'contrato'
    row = _relational_db.get_contract_by_contrato(contract_id)
    if not row:
        return {}
    return {
        "id": row.id,
        "name": row.name,
        "path": row.path,
        "ingestion_date": row.ingestion_date.isoformat() if row.ingestion_date else None,
        "last_processed": row.last_processed.isoformat() if row.last_processed else None,
        "contrato": row.contrato,
        "inicioPrazo": row.inicioPrazo.isoformat() if row.inicioPrazo else None,
        "fimPrazo": row.fimPrazo.isoformat() if row.fimPrazo else None,
        "empresa": row.empresa,
        "icj": row.icj,
        "valorContratoOriginal": str(row.valorContratoOriginal) if row.valorContratoOriginal else None,
        "moeda": row.moeda,
        "taxaCambio": row.taxaCambio,
        "gerenteContrato": row.gerenteContrato,
        "nomeGerenteContrato": row.nomeGerenteContrato,
        "lotacaoGerenteContrato": row.lotacaoGerenteContrato,
        "areaContrato": row.areaContrato,
        "modalidade": row.modalidade,
        "textoModalidade": row.textoModalidade,
        "reajuste": row.reajuste,
        "fornecedor": row.fornecedor,
        "nomeFornecedor": row.nomeFornecedor,
        "tipoContrato": row.tipoContrato,
        "objetoContrato": row.objetoContrato,
        "linhasServico": row.linhasServico,
    }


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


# ------------------------------------------------------------
# Endpoints relacionados aos prompts cadastrados

@router.post("/prompts")
def create_prompt(
    nome: str = Body(..., embed=True),
    texto: str = Body(..., embed=True),
    periodicidade: str | None = Body(None, embed=True),
) -> dict:
    """Cadastra um novo prompt no banco."""
    pid = _relational_db.add_prompt(nome=nome, texto=texto, periodicidade=periodicidade)
    return {"id": pid}


@router.get("/prompts")
def list_prompts() -> dict:
    """Lista todos os prompts cadastrados."""
    rows = _relational_db.list_prompts()
    prompts = [
        {"id": p.id, "nome": p.nome, "texto": p.texto, "periodicidade": p.periodicidade}
        for p in rows
    ]
    return {"prompts": prompts}


@router.get("/prompts/{prompt_id}")
def get_prompt(prompt_id: int) -> dict:
    """Retorna um único prompt pelo id."""
    row = _relational_db.get_prompt(prompt_id)
    if not row:
        return {}
    return {"id": row.id, "nome": row.nome, "texto": row.texto, "periodicidade": row.periodicidade}


@router.put("/prompts/{prompt_id}")
def update_prompt(
    prompt_id: int,
    nome: str | None = Body(None, embed=True),
    texto: str | None = Body(None, embed=True),
    periodicidade: str | None = Body(None, embed=True),
) -> dict:
    """Atualiza os campos de um prompt existente."""
    fields = {}
    if nome is not None:
        fields["nome"] = nome
    if texto is not None:
        fields["texto"] = texto
    if periodicidade is not None:
        fields["periodicidade"] = periodicidade
    _relational_db.update_prompt(prompt_id, **fields)
    return {"status": "ok"}


@router.delete("/prompts/{prompt_id}")
def delete_prompt(prompt_id: int) -> dict:
    """Remove um prompt do banco."""
    _relational_db.delete_prompt(prompt_id)
    return {"status": "ok"}


# ------------------------------------------------------------
# Endpoint para execução exaustiva de prompts

@router.post("/execute")
async def execute_prompts(prompt: str | None = Body(None, embed=True)) -> dict:
    """Dispara processamento dos contratos com prompts."""
    processor = ExhaustiveProcessor(_vector_store, _relational_db)
    ids = await processor.run(prompt=prompt)
    return {"ids": ids}

