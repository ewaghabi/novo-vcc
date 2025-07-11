import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.storage.relational_db_adapter import (
    RelationalDBAdapter,
    Contract,
    Execution,
    ExecutionResult,
)
import app.processing.execution as execution_mod
from app.processing.execution import ExhaustiveProcessor


class DummyLLM:
    def __init__(self):
        self.prompts = []

    def predict(self, text: str) -> str:
        self.prompts.append(text)
        return "resp"


def test_run_adhoc(monkeypatch):
    db = RelationalDBAdapter(db_url="sqlite:///:memory:")
    db.add_contract_structured(contrato="C1")
    db.add_contract_structured(contrato="C2")

    llm = DummyLLM()
    monkeypatch.setattr(execution_mod, "get_chat_model", lambda model="x": llm)

    proc = ExhaustiveProcessor(object(), db)
    ids = asyncio.run(proc.run(prompt="Oi?"))

    assert ids == [1]
    session = db._Session()
    exec_row = session.query(Execution).first()
    results = session.query(ExecutionResult).all()
    session.close()

    assert exec_row.tipo == "adhoc"
    assert exec_row.prompt_text == "Oi?"
    assert exec_row.progress == 100.0
    assert len(results) == 2
    assert all(r.execution_id == exec_row.id for r in results)
    assert len(llm.prompts) == 2


def test_run_registered(monkeypatch):
    db = RelationalDBAdapter(db_url="sqlite:///:memory:")
    db.add_contract_structured(contrato="C1")
    p1 = db.add_prompt(nome="p1", texto="T1")
    p2 = db.add_prompt(nome="p2", texto="T2")

    llm = DummyLLM()
    monkeypatch.setattr(execution_mod, "get_chat_model", lambda model="x": llm)

    proc = ExhaustiveProcessor(object(), db)
    ids = asyncio.run(proc.run())

    assert len(ids) == 2
    session = db._Session()
    execs = session.query(Execution).order_by(Execution.id).all()
    results = session.query(ExecutionResult).all()
    session.close()

    assert {e.prompt_id for e in execs} == {p1, p2}
    assert all(e.tipo == "registrado" for e in execs)
    assert len(results) == 2
    assert len(llm.prompts) == 2

