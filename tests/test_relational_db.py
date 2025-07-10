from datetime import datetime
import sys
from pathlib import Path

# Permite importar módulos da aplicação durante os testes
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.storage.relational_db_adapter import (
    Contract,
    Execution,
    RelationalDBAdapter,
)


def test_contract_model_attributes():
    """Confere campos padrão do modelo Contract."""
    dt = datetime(2020, 1, 1)
    c = Contract(
        name="test",
        path="/tmp/file",
        ingestion_date=dt,
        last_processed=dt,
    )
    assert c.name == "test"
    assert c.path == "/tmp/file"
    assert c.ingestion_date == dt
    assert c.last_processed == dt
    assert Contract.__tablename__ == "contracts"
    # new optional fields should default to None
    assert c.contrato is None
    assert c.inicioPrazo is None
    assert c.fimPrazo is None
    assert c.empresa is None
    assert c.icj is None
    assert c.valorContratoOriginal is None
    assert c.moeda is None
    assert c.taxaCambio is None
    assert c.gerenteContrato is None
    assert c.nomeGerenteContrato is None
    assert c.lotacaoGerenteContrato is None
    assert c.areaContrato is None
    assert c.modalidade is None
    assert c.textoModalidade is None
    assert c.reajuste is None
    assert c.fornecedor is None
    assert c.nomeFornecedor is None
    assert c.tipoContrato is None
    assert c.objetoContrato is None
    assert c.linhasServico is None


def test_add_contract_inserts_into_db():
    """Insere contrato simples e valida campos."""
    adapter = RelationalDBAdapter(db_url="sqlite:///:memory:")
    adapter.add_contract(name="c1", path="/tmp/c1.pdf")

    session = adapter._Session()
    row = session.query(Contract).first()
    session.close()

    assert row.name == "c1"
    assert row.path == "/tmp/c1.pdf"
    assert isinstance(row.ingestion_date, datetime)
    assert isinstance(row.last_processed, datetime)
    assert row.contrato is None
    assert row.inicioPrazo is None
    assert row.fimPrazo is None
    assert row.empresa is None
    assert row.icj is None
    assert row.valorContratoOriginal is None
    assert row.moeda is None
    assert row.taxaCambio is None
    assert row.gerenteContrato is None
    assert row.nomeGerenteContrato is None
    assert row.lotacaoGerenteContrato is None
    assert row.areaContrato is None
    assert row.modalidade is None
    assert row.textoModalidade is None
    assert row.reajuste is None
    assert row.fornecedor is None
    assert row.nomeFornecedor is None
    assert row.tipoContrato is None
    assert row.objetoContrato is None
    assert row.linhasServico is None


def test_update_processing_date():
    """Atualiza data de processamento corretamente."""
    adapter = RelationalDBAdapter(db_url="sqlite:///:memory:")
    adapter.add_contract(name="c1", path="/tmp/c1.pdf")
    adapter.update_processing_date("/tmp/c1.pdf", datetime(2021, 1, 1))

    session = adapter._Session()
    row = session.query(Contract).first()
    session.close()

    assert row.last_processed == datetime(2021, 1, 1)


def test_execution_crud_operations():
    """Verifica criação e atualização de execuções."""
    db = RelationalDBAdapter(db_url="sqlite:///:memory:")

    exec_id = db.create_execution("tarefa", "Classe")
    db.update_execution(exec_id, progress=25.0)
    db.update_execution(exec_id, status="running")

    db.update_execution(exec_id, end_time=datetime(2021, 1, 2), status="done")

    session = db._Session()
    row = session.query(Execution).first()
    session.close()

    assert row.id == exec_id
    assert row.task_name == "tarefa"
    assert row.class_name == "Classe"
    assert row.progress == 25.0
    assert row.status == "done"
    assert row.end_time == datetime(2021, 1, 2)

    db.clear_executions()
    session = db._Session()
    count = session.query(Execution).count()
    session.close()
    assert count == 0
