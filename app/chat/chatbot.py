from __future__ import annotations

from typing import List, Tuple

from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

from app.storage.vector_store_adapter import VectorStoreAdapter


class ContractChatbot:
    """Simple RAG chatbot over ingested contracts."""

    def __init__(self, vector_store: VectorStoreAdapter, model: str = "gpt-3.5-turbo") -> None:
        self._vector_store = vector_store
        self._llm = ChatOpenAI(model=model)
        # Create retrieval QA chain using the underlying Chroma store
        self._chain = RetrievalQA.from_chain_type(
            llm=self._llm,
            chain_type="stuff",
            retriever=self._vector_store._store.as_retriever(),
        )

    def ask(self, question: str, top_k: int = 3) -> Tuple[str, List[str]]:
        """Return answer and list of source contract paths."""
        # Run the chain to get the final answer
        result = self._chain({"query": question})
        answer = result.get("result", "")

        # Retrieve the most relevant documents
        docs = self._vector_store._store.similarity_search(question, k=top_k)
        sources = [d.metadata.get("source", "") for d in docs]
        return answer, sources
