from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from pathlib import Path
import shutil


# Envolve o Chroma para facilitar o uso pela aplicação
class VectorStoreAdapter:
    """Wrapper around Chroma vector store using OpenAI embeddings."""

    def __init__(self, persist_directory: str = "chroma_db") -> None:
        # Diretório onde o Chroma irá persistir os dados
        self._persist_directory = persist_directory
        self._embedding = OpenAIEmbeddings()
        self._store = Chroma(
            persist_directory=persist_directory, embedding_function=self._embedding
        )

    def add_document(self, text: str, metadata: dict | None = None) -> None:
        """Adiciona um texto com metadados ao vetor."""
        self._store.add_texts([text], metadatas=[metadata or {}])

    def persist(self) -> None:
        """Grava em disco o estado atual do Chroma."""
        self._store.persist()

    def clear(self) -> None:
        """Remove todos os documentos e recria o armazenamento."""
        if Path(self._persist_directory).exists():
            shutil.rmtree(self._persist_directory)
        self._store = Chroma(
            persist_directory=self._persist_directory,
            embedding_function=self._embedding,
        )
