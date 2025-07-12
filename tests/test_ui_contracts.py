import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ui import contracts


# Verifica recuperação de contratos paginados
def test_fetch_contracts(monkeypatch):
    dados = {"contracts": [{"contrato": "C1"}], "total": 10}

    class DummyResp:
        def raise_for_status(self):
            pass
        def json(self):
            return dados

    def dummy_get(url, timeout=10.0):
        assert "page=1" in url
        assert "page_size=20" in url
        return DummyResp()

    monkeypatch.setattr(contracts.httpx, "get", dummy_get)
    contratos, total = contracts.fetch_contracts(1, 20)
    assert total == 10
    assert contratos == dados["contracts"]


# Checa retorno do relatório de contrato
def test_fetch_contract_report(monkeypatch):
    class DummyResp:
        def raise_for_status(self):
            pass
        def json(self):
            return {"report": "ok"}

    def dummy_get(url, timeout=10.0):
        assert url.endswith("/C1/report")
        return DummyResp()

    monkeypatch.setattr(contracts.httpx, "get", dummy_get)
    rel = contracts.fetch_contract_report("C1")
    assert rel == "ok"

