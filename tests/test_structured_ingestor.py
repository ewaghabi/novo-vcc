import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # inclui raiz do projeto

langchain_stub = types.ModuleType("langchain")
langchain_stub.embeddings = types.ModuleType("langchain.embeddings")
langchain_stub.embeddings.OpenAIEmbeddings = object
langchain_stub.vectorstores = types.ModuleType("langchain.vectorstores")
langchain_stub.vectorstores.Chroma = object
sys.modules.setdefault("langchain", langchain_stub)
sys.modules.setdefault("langchain.embeddings", langchain_stub.embeddings)
sys.modules.setdefault("langchain.vectorstores", langchain_stub.vectorstores)

from app.ingestion.ingestor import ContractStructuredDataIngestor
from app.storage.relational_db_adapter import RelationalDBAdapter, Contract, Execution


DATA_FILE = ROOT / "tests" / "data" / "contratos_tst.csv"


def _get_all(session):
    """Retorna todos os contratos ordenados."""
    return session.query(Contract).order_by(Contract.contrato).all()


# Valida criação de registros a partir do CSV
def test_ingest_structured_creates_records():
    """Gera registros no banco a partir do CSV."""
    db = RelationalDBAdapter(db_url="sqlite:///:memory:")
    ing = ContractStructuredDataIngestor(DATA_FILE, db)
    exec_id = ing.ingest()

    session = db._Session()
    rows = _get_all(session)
    session.close()

    assert len(rows) == 6
    c = {r.contrato: json.loads(r.linhasServico) for r in rows}
    assert len(c["4600637168"]) == 5
    first = next(r for r in rows if r.contrato == "4600308523")
    assert first.nomeGerenteContrato == "CARLOS SANTANA LIMA ALMEIDA"
    assert first.lotacaoGerenteContrato == "TI/DEVOPS"
    assert ing.progress == 100.0
    assert isinstance(exec_id, int)


# Garante que contratos repetidos não são inseridos
def test_ingest_structured_skips_existing():
    """Não duplica contratos já existentes."""
    db = RelationalDBAdapter(db_url="sqlite:///:memory:")
    db.add_contract_structured(contrato="4600326151")
    ing = ContractStructuredDataIngestor(DATA_FILE, db)
    ing.ingest()

    session = db._Session()
    rows = _get_all(session)
    session.close()
    # Should still be 6 unique contracts
    assert len(rows) == 6


# Verifica modo full_load que apaga registros anteriores
def test_ingest_structured_full_load_clears():
    """Apaga tudo quando em modo full_load."""
    db = RelationalDBAdapter(db_url="sqlite:///:memory:")
    ing = ContractStructuredDataIngestor(DATA_FILE, db)
    ing.ingest()
    # second run with full load should clear previous
    ing.ingest(full_load=True)

    session = db._Session()
    rows = _get_all(session)
    session.close()
    assert len(rows) == 6


# Confere atualização do progresso durante carga
def test_ingest_progress_tracking():
    """Acompanha a porcentagem de processamento."""
    db = RelationalDBAdapter(db_url="sqlite:///:memory:")
    ing = ContractStructuredDataIngestor(DATA_FILE, db)
    assert ing.progress == 0.0
    exec_id = ing.ingest()
    assert ing.progress == 100.0
    assert isinstance(exec_id, int)


# Checa se registro de execução é criado
def test_ingest_creates_execution_record():
    """Verifica registro de execução durante ingestão estruturada."""
    db = RelationalDBAdapter(db_url="sqlite:///:memory:")
    ing = ContractStructuredDataIngestor(DATA_FILE, db)
    exec_id = ing.ingest()

    session = db._Session()
    exec_rows = session.query(Execution).all()
    session.close()

    assert len(exec_rows) == 1
    assert exec_rows[0].status == "success"
    assert exec_rows[0].id == exec_id
