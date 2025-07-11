import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.storage.relational_db_adapter import RelationalDBAdapter, Contract
from app.models.contrato import Contrato


# Verifica criação do objeto a partir do ORM
def test_contrato_from_orm_and_report():
    db = RelationalDBAdapter(db_url="sqlite:///:memory:")
    dados = {
        "contrato": "C1",
        "linhasServico": json.dumps([
            {"Item": "1", "Desc": "X", "Num": "10", "Outra": "Y"}
        ]),
        "vetor_embedding": json.dumps([0.1, 0.2]),
        "texto_completo": "Texto exemplo",
    }
    db.add_contract_structured(**dados)
    session = db._Session()
    row = session.query(Contract).first()
    session.close()

    contrato = Contrato.from_orm(row)
    assert contrato.contrato == "C1"
    assert contrato.vetor_embedding == [0.1, 0.2]
    assert contrato.texto_completo == "Texto exemplo"
    report = contrato.relatorio()
    assert "contrato: C1" in report
    assert "Item" in report

