# -*- coding: utf-8 -*-
"""Objeto de domínio para representar e manipular contratos.

Este módulo define a classe :class:`Contrato`, que corresponde a um registro da
tabela ``contracts`` do banco relacional. A ideia é facilitar a manipulação de
dados do contrato em memória, bem como fornecer utilidades para geração de
relatórios em texto.
"""

from __future__ import annotations

# Utilizamos dataclasses para simplificar a definição do objeto de domínio
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
import json
from typing import Any

# Importação absoluta do ORM de contratos para evitar problemas de path
from app.storage.relational_db_adapter import Contract


@dataclass
class Contrato:
    """Representa um contrato carregado do banco relacional."""

    # ------------------------------------------------------------------
    # Campos que mapeiam diretamente as colunas da tabela ``contracts``
    # ------------------------------------------------------------------

    id: int | None
    name: str
    path: str
    ingestion_date: datetime | None = None
    last_processed: datetime | None = None
    contrato: str | None = None
    inicioPrazo: date | None = None
    fimPrazo: date | None = None
    empresa: str | None = None
    icj: str | None = None
    valorContratoOriginal: float | None = None
    moeda: str | None = None
    taxaCambio: float | None = None
    gerenteContrato: str | None = None
    nomeGerenteContrato: str | None = None
    lotacaoGerenteContrato: str | None = None
    areaContrato: str | None = None
    modalidade: str | None = None
    textoModalidade: str | None = None
    reajuste: str | None = None
    fornecedor: str | None = None
    nomeFornecedor: str | None = None
    tipoContrato: str | None = None
    objetoContrato: str | None = None

    # Linhas de serviço armazenadas em formato JSON
    linhasServico: list[dict[str, Any]] | None = field(default=None)

    # Vetor de embedding gerado pelo modelo e o texto completo do contrato
    vetor_embedding: list[float] | None = field(default=None)
    texto_completo: str | None = None

    # ------------------------------------------------------------------
    # Métodos auxiliares de construção e conversão
    # ------------------------------------------------------------------
    @classmethod
    def from_orm(cls, row: Contract) -> "Contrato":
        """Cria instância a partir de um registro ORM."""

        # Decodifica o JSON armazenado nas colunas ``linhasServico`` e
        # ``vetor_embedding`` caso existam. Isso facilita o uso em código
        # Python, evitando que cada chamada precise fazer ``json.loads``.
        linhas = (
            json.loads(row.linhasServico)
            if getattr(row, "linhasServico", None)
            else None
        )
        vetor = (
            json.loads(row.vetor_embedding)
            if getattr(row, "vetor_embedding", None)
            else None
        )
        return cls(
            id=row.id,
            name=row.name,
            path=row.path,
            ingestion_date=row.ingestion_date,
            last_processed=row.last_processed,
            contrato=row.contrato,
            inicioPrazo=row.inicioPrazo,
            fimPrazo=row.fimPrazo,
            empresa=row.empresa,
            icj=row.icj,
            valorContratoOriginal=float(row.valorContratoOriginal)
            if row.valorContratoOriginal is not None
            else None,
            moeda=row.moeda,
            taxaCambio=row.taxaCambio,
            gerenteContrato=row.gerenteContrato,
            nomeGerenteContrato=row.nomeGerenteContrato,
            lotacaoGerenteContrato=row.lotacaoGerenteContrato,
            areaContrato=row.areaContrato,
            modalidade=row.modalidade,
            textoModalidade=row.textoModalidade,
            reajuste=row.reajuste,
            fornecedor=row.fornecedor,
            nomeFornecedor=row.nomeFornecedor,
            tipoContrato=row.tipoContrato,
            objetoContrato=row.objetoContrato,
            linhasServico=linhas,
            vetor_embedding=vetor,
            texto_completo=row.texto_completo,
        )

    def to_dict(self) -> dict:
        """Converte o contrato para ``dict`` padrão do Python.

        Essa função facilita a serialização do objeto, seja para testes
        ou para construção de relatórios em texto.
        """
        data = asdict(self)
        return data

    # Utilizamos __str__ para gerar representação legível
    def __str__(self) -> str:  # pragma: no cover - delega para relatorio
        return self.relatorio()

    # ------------------------------------------------------------------
    # Geração de relatório em formato de texto
    # ------------------------------------------------------------------
    def relatorio(self) -> str:
        """Retorna relatório formatado com os dados do contrato.

        Cada campo é apresentado no formato ``nome: valor`` e as linhas de
        serviço, quando presentes, são exibidas em formato de tabela simples.
        """
        linhas = []
        for field_name, value in self.to_dict().items():
            # Tratamento especial para as linhas de serviço, que formam uma
            # pequena tabela textual. Cada item da lista representa uma linha
            # contendo as colunas originais do JSON.
            if field_name == "linhasServico":
                linhas.append("linhasServico:")
                if value:
                    cabecalho = list(value[0].keys())
                    linhas.append(" | ".join(cabecalho))
                    linhas.append("-" * (len(" | ".join(cabecalho))))
                    for item in value:
                        linhas.append(
                            " | ".join(str(item.get(h, "")) for h in cabecalho)
                        )
                else:
                    linhas.append("<vazio>")
                continue
            # Demais campos apenas concatenam nome e valor
            linhas.append(f"{field_name}: {value}")
        return "\n".join(linhas)
