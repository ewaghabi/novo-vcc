from __future__ import annotations

import asyncio
from datetime import datetime

from app.integrations.openai_provider import get_chat_model
from app.storage.vector_store_adapter import VectorStoreAdapter
from app.storage.relational_db_adapter import (
    RelationalDBAdapter,
    Contract,
)
from app.models.contrato import Contrato


# Classe responsável por executar prompts em todos os contratos
class ExhaustiveProcessor:
    """Executa prompts cadastrados ou ad-hoc sobre todos os contratos."""

    def __init__(
        self,
        vector_store: VectorStoreAdapter,
        relational_db: RelationalDBAdapter,
        *,
        model: str = "gpt-3.5-turbo",
        max_concurrent: int = 3,
    ) -> None:
        # Armazena dependências para acesso posterior
        self._vector_store = vector_store
        self._db = relational_db
        self._llm = get_chat_model(model=model)
        self._max_concurrent = max_concurrent

    async def run(self, prompt: str | None = None) -> list[int]:
        """Dispara a execução e retorna ids das execuções criadas."""
        # Recupera todos os contratos disponíveis
        session = self._db._Session()
        contracts = session.query(Contract).order_by(Contract.id).all()
        session.close()

        # Determina os prompts a executar: único ad-hoc ou todos cadastrados
        if prompt is not None:
            prompts: list[tuple[int | None, str]] = [(None, prompt)]
        else:
            prompts = [(p.id, p.texto) for p in self._db.list_prompts()]

        exec_ids: list[int] = []
        for pid, text in prompts:
            tipo = "adhoc" if pid is None else "registrado"
            exec_id = self._db.create_execution(
                "prompt_execution",
                self.__class__.__name__,
                tipo=tipo,
                prompt_id=pid,
                prompt_text=text,
            )
            exec_ids.append(exec_id)
            await self._run_single(exec_id, text, contracts)
        return exec_ids

    async def _run_single(
        self, exec_id: int, prompt_text: str, contracts: list[Contract]
    ) -> None:
        """Executa um prompt sobre todos os contratos."""
        total = len(contracts)
        processed = 0
        lock = asyncio.Lock()
        sem = asyncio.Semaphore(self._max_concurrent)

        async def handle(contract: Contract) -> None:
            nonlocal processed
            async with sem:
                # Monta o texto completo a ser enviado ao modelo
                contrato = Contrato.from_orm(contract)
                texto = f"{prompt_text}\n\n{contrato.relatorio()}"
                # Chamada assíncrona ao modelo de linguagem
                if hasattr(self._llm, "ainvoke"):
                    resposta = await self._llm.ainvoke(texto)
                else:
                    resposta = await asyncio.to_thread(self._llm.predict, texto)
                simples = resposta.strip().split("\n", 1)[0] if resposta else None
                self._db.add_execution_result(
                    exec_id,
                    contract.id,
                    resposta_completa=resposta,
                    resposta_simples=simples,
                )
                # Atualiza progresso de forma sincronizada
                async with lock:
                    processed += 1
                    progress = processed / total * 100
                    self._db.update_execution(exec_id, progress=progress)

        # Dispara processamento paralelo leve
        await asyncio.gather(*(handle(c) for c in contracts))
        # Finaliza registro da execução
        self._db.update_execution(
            exec_id,
            status="success",
            end_time=datetime.utcnow(),
            progress=100.0,
        )
