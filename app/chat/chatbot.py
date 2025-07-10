from __future__ import annotations

from typing import List, Tuple

from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

from app.storage.vector_store_adapter import VectorStoreAdapter


# Classe que provê interação com contratos via modelo de linguagem
class ContractChatbot:
    """Simple RAG chatbot over ingested contracts."""

    # Inicializa com o vetor de contratos e modelo de linguagem
    def __init__(self, vector_store: VectorStoreAdapter, model: str = "gpt-3.5-turbo") -> None:
        # Guarda a referência ao repositório vetorial
        self._vector_store = vector_store
        self._llm = ChatOpenAI(model=model)
        # Cria cadeia de consulta com base no Chroma
        self._chain = RetrievalQA.from_chain_type(
            llm=self._llm,
            chain_type="stuff",
            retriever=self._vector_store._store.as_retriever(),
        )

    # Envia uma pergunta e retorna resposta e fontes
    def ask(self, question: str, top_k: int = 3) -> Tuple[str, List[str]]:
        """Return answer and list of source contract paths."""
        # Executa a cadeia para obter resposta
        result = self._chain({"query": question})
        answer = result.get("result", "")

        # Busca documentos mais relevantes
        docs = self._vector_store._store.similarity_search(question, k=top_k)
        sources = [d.metadata.get("source", "") for d in docs]
        return answer, sources
