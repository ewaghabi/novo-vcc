import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import types

from app.ui import executions


# Verifica ordenação decrescente ao buscar execuções

def test_fetch_executions_sorted(monkeypatch):
    registros = [
        {"id": 1, "start_time": "2024-01-01T10:00:00"},
        {"id": 2, "start_time": "2024-02-01T10:00:00"},
    ]

    class DummyResp:
        def raise_for_status(self):
            pass
        def json(self):
            return {"executions": registros}

    def dummy_get(url, timeout=10.0):
        return DummyResp()

    monkeypatch.setattr(executions.httpx, "get", dummy_get)

    result = executions.fetch_executions()
    assert [r["id"] for r in result] == [2, 1]


# Confere retorno de detalhes de execução

def test_fetch_execution_details(monkeypatch):
    dado = {"id": 5, "status": "done"}

    class DummyResp:
        def raise_for_status(self):
            pass
        def json(self):
            return dado

    def dummy_get(url, timeout=10.0):
        assert url.endswith("/5")
        return DummyResp()

    monkeypatch.setattr(executions.httpx, "get", dummy_get)

    result = executions.fetch_execution_details(5)
    assert result == dado
