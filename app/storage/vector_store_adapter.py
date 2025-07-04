from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from pathlib import Path
import shutil


class VectorStoreAdapter:
    """Wrapper around Chroma vector store using OpenAI embeddings."""

    def __init__(self, persist_directory: str = "chroma_db") -> None:
        self._persist_directory = persist_directory
        self._embedding = OpenAIEmbeddings()
        self._store = Chroma(
            persist_directory=persist_directory, embedding_function=self._embedding
        )

    def add_document(self, text: str, metadata: dict | None = None) -> None:
        """Add a single text document with optional metadata to the store."""
        self._store.add_texts([text], metadatas=[metadata or {}])

    def persist(self) -> None:
        """Persist the underlying Chroma store to disk."""
        self._store.persist()

    def clear(self) -> None:
        """Remove all documents from the store and reset it."""
        if Path(self._persist_directory).exists():
            shutil.rmtree(self._persist_directory)
        self._store = Chroma(
            persist_directory=self._persist_directory,
            embedding_function=self._embedding,
        )
