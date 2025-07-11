from langchain.vectorstores import Chroma
from app.integrations.openai_provider import get_embeddings
from pathlib import Path
import shutil


# Envolve o Chroma para facilitar o uso pela aplicação
# Classe adaptadora para interagir com o Chroma usando embeddings OpenAI
class VectorStoreAdapter:
    """Wrapper around Chroma vector store using OpenAI embeddings."""

    # Cria o objeto definindo diretório de persistência
    def __init__(self, persist_directory: str = "chroma_db") -> None:
        # Diretório onde o Chroma irá persistir os dados
        self._persist_directory = persist_directory
        # Instancia embeddings adequados ao ambiente (interno ou público)
        self._embedding = get_embeddings()
        self._store = Chroma(
            persist_directory=persist_directory, embedding_function=self._embedding
        )

    # Insere um documento de texto no vetor
    def add_document(self, text: str, metadata: dict | None = None) -> None:
        """Adiciona um texto com metadados ao vetor."""
        self._store.add_texts([text], metadatas=[metadata or {}])

    # Persiste as alterações realizadas
    def persist(self) -> None:
        """Grava em disco o estado atual do Chroma."""
        self._store.persist()

    # Remove todos os dados e recria o armazenamento
    def clear(self) -> None:
        """Remove todos os documentos e recria o armazenamento."""
        if Path(self._persist_directory).exists():
            shutil.rmtree(self._persist_directory)
        self._store = Chroma(
            persist_directory=self._persist_directory,
            embedding_function=self._embedding,
        )
