import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.storage.relational_db_adapter import RelationalDBAdapter, Execution
from app.storage.execution_tracker import ExecutionTracker


# Verifica ciclo completo de registro de execução
def test_execution_tracker_flow():
    """Valida ciclo completo do tracker."""
    db = RelationalDBAdapter(db_url="sqlite:///:memory:")
    tracker = ExecutionTracker(db, "tarefa", "Classe")

    tracker.start()
    tracker.update(progress=50.0)
    tracker.finish()

    session = db._Session()
    row = session.query(Execution).first()
    session.close()

    assert row.task_name == "tarefa"
    assert row.class_name == "Classe"
    assert row.progress == 50.0
    assert row.status == "success"
    assert row.end_time is not None
