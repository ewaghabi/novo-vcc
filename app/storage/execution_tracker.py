from __future__ import annotations

from datetime import datetime

from .relational_db_adapter import RelationalDBAdapter


class ExecutionTracker:
    """Facilita registro de execuções de tarefas."""

    def __init__(self, db: RelationalDBAdapter, task_name: str, class_name: str) -> None:
        self._db = db
        self.task_name = task_name
        self.class_name = class_name
        self.execution_id: int | None = None

    def start(self) -> int:
        """Cria o registro inicial e retorna o id gerado."""
        self.execution_id = self._db.create_execution(self.task_name, self.class_name)
        return self.execution_id

    def update(self, progress: float | None = None, status: str | None = None, message: str | None = None) -> None:
        """Atualiza informações da execução."""
        if self.execution_id is None:
            return
        self._db.update_execution(self.execution_id, progress=progress, status=status, message=message)

    def finish(self, status: str = "success") -> None:
        """Marca finalização da execução."""
        if self.execution_id is None:
            return
        self._db.update_execution(
            self.execution_id,
            status=status,
            end_time=datetime.utcnow(),
        )
