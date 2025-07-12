import sys
import types
from pathlib import Path

# Adjust path to import the application
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Provide lightweight stubs for langchain modules used during import
langchain_stub = types.ModuleType("langchain")
langchain_stub.embeddings = types.ModuleType("langchain.embeddings")
class DummyEmbeddings:
    pass
langchain_stub.embeddings.OpenAIEmbeddings = DummyEmbeddings

langchain_stub.vectorstores = types.ModuleType("langchain.vectorstores")
class DummyChroma:
    def __init__(self, *args, **kwargs):
        pass
    def as_retriever(self):
        return self
    def similarity_search(self, query, k=3):
        return []
    def add_texts(self, texts, metadatas=None):
        pass
    def persist(self):
        pass
langchain_stub.vectorstores.Chroma = DummyChroma

langchain_stub.chat_models = types.ModuleType("langchain.chat_models")
class DummyChatOpenAI:
    def __init__(self, *args, **kwargs):
        pass
langchain_stub.chat_models.ChatOpenAI = DummyChatOpenAI

langchain_stub.chains = types.ModuleType("langchain.chains")
class DummyRetrievalQA:
    def __init__(self, *args, **kwargs):
        pass
    @classmethod
    def from_chain_type(cls, *args, **kwargs):
        return cls()
langchain_stub.chains.RetrievalQA = DummyRetrievalQA

sys.modules.setdefault("langchain", langchain_stub)
sys.modules.setdefault("langchain.embeddings", langchain_stub.embeddings)
sys.modules.setdefault("langchain.vectorstores", langchain_stub.vectorstores)
sys.modules.setdefault("langchain.chat_models", langchain_stub.chat_models)
sys.modules.setdefault("langchain.chains", langchain_stub.chains)

from fastapi.testclient import TestClient
from app.api import app
import app.api.routes as routes


class DummyChatbot:
    def __init__(self):
        self.questions = []
    def ask(self, question):
        self.questions.append(question)
        return "dummy answer", ["src1", "src2"]


class DummyIngestor:
    def __init__(self):
        self.called = False
    def ingest(self):
        self.called = True


# Verifica retorno estruturado da rota /chat
def test_chat_endpoint_returns_structure(monkeypatch):
    chatbot = DummyChatbot()
    monkeypatch.setattr(routes, "_chatbot", chatbot)
    client = TestClient(app)
    resp = client.post("/chat", json={"question": "hello"})
    assert resp.status_code == 200
    assert resp.json() == {"answer": "dummy answer", "sources": ["src1", "src2"]}
    assert chatbot.questions == ["hello"]


# Garante que /ingest aciona o ingestor
def test_ingest_endpoint_calls_ingestor(monkeypatch):
    ing = DummyIngestor()
    monkeypatch.setattr(routes, "_ingestor", ing)
    client = TestClient(app)
    resp = client.post("/ingest")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert ing.called


# Checa se /ingest-structured chama corretamente o ingestor
def test_ingest_structured_calls_ingestor(monkeypatch):
    class DummyStructured(DummyIngestor):
        def __init__(self, path, db):
            super().__init__()
            self.path = path
            self.db = db
        def ingest(self):
            self.called = True
            return 10

    created = {}

    def dummy_ctor(path, db):
        obj = DummyStructured(path, db)
        created["obj"] = obj
        return obj

    monkeypatch.setattr(routes, "ContractStructuredDataIngestor", dummy_ctor)
    client = TestClient(app)
    resp = client.post("/ingest-structured", json={"csv_path": "file.csv"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "id": 10}
    assert created["obj"].called
    assert created["obj"].path == "file.csv"


# Testa ingestão real via API com verificação de execuções
def test_structured_ingestion_via_api(monkeypatch, tmp_path):
    # Usa banco em memória e arquivo de testes
    data_file = ROOT / "tests" / "data" / "contratos_tst.csv"
    db_path = tmp_path / "db.sqlite"
    db = routes.RelationalDBAdapter(db_url=f"sqlite:///{db_path}")
    monkeypatch.setattr(routes, "_relational_db", db)

    client = TestClient(app)
    resp = client.post("/ingest-structured", json={"csv_path": str(data_file)})
    assert resp.status_code == 200
    exec_id = resp.json()["id"]

    # Aguarda até que a execução esteja concluída
    resp = client.get(f"/executions/{exec_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    resp = client.get("/contracts")
    assert resp.status_code == 200
    assert len(resp.json()["contracts"]) == 6

    resp = client.get("/executions", params={"status": "success"})
    assert resp.status_code == 200
    assert len(resp.json()["executions"]) == 1


# Verifica recuperação de contrato pelo campo 'contrato'
def test_get_contract_by_contrato(monkeypatch):
    class DummyDB:
        def __init__(self):
            from types import SimpleNamespace
            from datetime import datetime
            self.row = SimpleNamespace(
                id=1,
                name="c1",
                path="/tmp/c1",
                ingestion_date=datetime(2020, 1, 1),
                last_processed=datetime(2020, 1, 2),
                contrato="C1",
                inicioPrazo=None,
                fimPrazo=None,
                empresa=None,
                icj=None,
                valorContratoOriginal=None,
                moeda=None,
                taxaCambio=None,
                gerenteContrato=None,
                nomeGerenteContrato=None,
                lotacaoGerenteContrato=None,
                areaContrato=None,
                modalidade=None,
                textoModalidade=None,
                reajuste=None,
                fornecedor=None,
                nomeFornecedor=None,
                tipoContrato=None,
                objetoContrato=None,
                linhasServico=None,
                vetor_embedding=None,
                texto_completo=None,
            )

        def get_contract_by_contrato(self, contrato):
            return self.row if contrato == "C1" else None

    db = DummyDB()
    monkeypatch.setattr(routes, "_relational_db", db)
    client = TestClient(app)
    resp = client.get("/contract/C1")
    assert resp.status_code == 200
    assert resp.json()["id"] == 1
    resp = client.get("/contract/C2")
    assert resp.status_code == 200
    assert resp.json() == {}


# Verifica paginação na listagem de contratos
def test_contracts_pagination(monkeypatch, tmp_path):
    db_path = tmp_path / "db.sqlite"
    db = routes.RelationalDBAdapter(db_url=f"sqlite:///{db_path}")
    for i in range(5):
        db.add_contract_structured(
            contrato=f"C{i}",
            lotacaoGerenteContrato=f"A{i}",
            valorContratoOriginal=100 + i,
            moeda="BRL",
        )

    monkeypatch.setattr(routes, "_relational_db", db)
    client = TestClient(app)

    resp = client.get("/contracts", params={"page": 1, "page_size": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["contracts"]) == 2


# Checa geração do relatório via endpoint
def test_contract_report_endpoint(monkeypatch, tmp_path):
    db_path = tmp_path / "db.sqlite"
    db = routes.RelationalDBAdapter(db_url=f"sqlite:///{db_path}")
    db.add_contract_structured(contrato="C1", linhasServico=None)

    monkeypatch.setattr(routes, "_relational_db", db)
    client = TestClient(app)
    resp = client.get("/contract/C1/report")
    assert resp.status_code == 200
    assert "contrato: C1" in resp.json()["report"]


# Confere uso do parâmetro model na rota /chat
def test_chat_endpoint_accepts_model(monkeypatch):
    class DummyBot(DummyChatbot):
        def __init__(self, model=None, **kwargs):
            super().__init__()
            self.model = model

    created = {}

    def dummy_ctor(store, model="x"):
        bot = DummyBot(model=model)
        created["bot"] = bot
        return bot

    monkeypatch.setattr(routes, "ContractChatbot", dummy_ctor)
    monkeypatch.setattr(routes, "_chatbot", DummyChatbot())
    client = TestClient(app)
    resp = client.post("/chat", json={"question": "oi", "model": "my-model"})
    assert resp.status_code == 200
    assert created["bot"].model == "my-model"
    assert created["bot"].questions == ["oi"]


# CRUD completo de prompts via API
def test_prompts_crud_via_api(monkeypatch, tmp_path):
    db_path = tmp_path / "db.sqlite"
    db = routes.RelationalDBAdapter(db_url=f"sqlite:///{db_path}")
    monkeypatch.setattr(routes, "_relational_db", db)
    client = TestClient(app)

    resp = client.post(
        "/prompts",
        json={"nome": "Teste", "texto": "Oi?", "periodicidade": "diario"},
    )
    assert resp.status_code == 200
    pid = resp.json()["id"]

    resp = client.get("/prompts")
    assert resp.status_code == 200
    assert len(resp.json()["prompts"]) == 1

    resp = client.put(f"/prompts/{pid}", json={"nome": "Novo"})
    assert resp.status_code == 200

    resp = client.get(f"/prompts/{pid}")
    assert resp.json()["nome"] == "Novo"

    resp = client.delete(f"/prompts/{pid}")
    assert resp.status_code == 200
    resp = client.get("/prompts")
    assert resp.json()["prompts"] == []

# Verifica acionamento do ExhaustiveProcessor via API

def test_execute_endpoint_calls_processor(monkeypatch):
    class DummyProcessor:
        def __init__(self, *args, **kwargs):
            self.prompt = None
        async def run(self, prompt=None):
            self.prompt = prompt
            return [99]

    proc = DummyProcessor()
    monkeypatch.setattr(routes, "ExhaustiveProcessor", lambda *a, **k: proc)
    client = TestClient(app)
    resp = client.post("/execute", json={"prompt": "Perg?"})
    assert resp.status_code == 200
    assert resp.json() == {"ids": [99]}
    assert proc.prompt == "Perg?"

    resp = client.post("/execute", json={})
    assert resp.status_code == 200
    assert proc.prompt is None

