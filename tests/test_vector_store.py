import sys
import types
from pathlib import Path

# Ajusta caminho para importar a aplicação
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Provide lightweight stubs so the adapter module can be imported without the
# real langchain dependencies.
langchain_stub = types.ModuleType("langchain")
langchain_stub.embeddings = types.ModuleType("langchain.embeddings")
langchain_stub.embeddings.OpenAIEmbeddings = object
langchain_stub.vectorstores = types.ModuleType("langchain.vectorstores")
langchain_stub.vectorstores.Chroma = object
sys.modules.setdefault("langchain", langchain_stub)
sys.modules.setdefault("langchain.embeddings", langchain_stub.embeddings)
sys.modules.setdefault("langchain.vectorstores", langchain_stub.vectorstores)

from app.storage import vector_store_adapter


# Representa um armazenamento vetorial simplificado
class DummyStore:
    def __init__(self):
        self.added = []
        self.persist_called = False

    def add_texts(self, texts, metadatas=None):
        self.added.append((texts, metadatas))

    def persist(self):
        self.persist_called = True


# Stub de embeddings usado apenas nos testes
class DummyEmbeddings:
    pass


def test_add_and_persist(monkeypatch):
    """Verifica adição de documentos e persistência."""
    dummy_store = DummyStore()

    def dummy_chroma(*args, **kwargs):
        return dummy_store

    monkeypatch.setattr(vector_store_adapter, "Chroma", dummy_chroma)
    monkeypatch.setattr(vector_store_adapter, "OpenAIEmbeddings", lambda: DummyEmbeddings())

    adapter = vector_store_adapter.VectorStoreAdapter(persist_directory="test_db")

    adapter.add_document("hello", {"foo": "bar"})
    adapter.persist()

    assert dummy_store.added == [(["hello"], [{"foo": "bar"}])]
    assert dummy_store.persist_called


def test_clear_reinitializes_store(monkeypatch, tmp_path):
    """Confere se limpar recria o armazenamento."""
    first_store = DummyStore()
    second_store = DummyStore()

    def first_chroma(*args, **kwargs):
        return first_store

    def second_chroma(*args, **kwargs):
        return second_store

    monkeypatch.setattr(vector_store_adapter, "Chroma", first_chroma)
    monkeypatch.setattr(vector_store_adapter, "OpenAIEmbeddings", lambda: DummyEmbeddings())
    adapter = vector_store_adapter.VectorStoreAdapter(persist_directory=str(tmp_path))
    assert adapter._store is first_store

    monkeypatch.setattr(vector_store_adapter, "Chroma", second_chroma)
    adapter.clear()
    assert adapter._store is second_store
