import sys
import types
from pathlib import Path

# Ensure repository root is in sys.path for package resolution
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


class DummyStore:
    def __init__(self):
        self.added = []
        self.persist_called = False

    def add_texts(self, texts, metadatas=None):
        self.added.append((texts, metadatas))

    def persist(self):
        self.persist_called = True


class DummyEmbeddings:
    pass


def test_add_and_persist(monkeypatch):
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
