from datetime import datetime
import sys
from pathlib import Path

# Ensure repository root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.storage.relational_db_adapter import Contract, RelationalDBAdapter


def test_contract_model_attributes():
    dt = datetime(2020, 1, 1)
    c = Contract(name="test", path="/tmp/file", ingestion_date=dt)
    assert c.name == "test"
    assert c.path == "/tmp/file"
    assert c.ingestion_date == dt
    assert Contract.__tablename__ == "contracts"


def test_add_contract_inserts_into_db():
    adapter = RelationalDBAdapter(db_url="sqlite:///:memory:")
    adapter.add_contract(name="c1", path="/tmp/c1.pdf")

    session = adapter._Session()
    row = session.query(Contract).first()
    session.close()

    assert row.name == "c1"
    assert row.path == "/tmp/c1.pdf"
    assert isinstance(row.ingestion_date, datetime)
