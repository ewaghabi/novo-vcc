# Aba de visualização de contratos no Streamlit
#
# Este módulo define funções auxiliares para buscar contratos via API
# e renderizar uma aba da interface com paginação.
import streamlit as st
import httpx

from app.config import API_BASE_URL

# Endpoints para contratos
_CONTRACTS_ENDPOINT = f"{API_BASE_URL.rstrip('/')}/contracts"
_CONTRACT_ENDPOINT = f"{API_BASE_URL.rstrip('/')}/contract"


def fetch_contracts(page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
    """Recupera contratos paginados da API."""
    url = f"{_CONTRACTS_ENDPOINT}?page={page}&page_size={page_size}"
    resp = httpx.get(url, timeout=10.0)
    resp.raise_for_status()
    data = resp.json()
    return data.get("contracts", []), data.get("total", 0)


def fetch_contract_report(contrato: str) -> str:
    """Obtém o relatório textual de um contrato."""
    url = f"{_CONTRACT_ENDPOINT}/{contrato}/report"
    resp = httpx.get(url, timeout=10.0)
    resp.raise_for_status()
    return resp.json().get("report", "")


def _format_currency(valor: float | None, moeda: str | None) -> str:
    """Formata valor monetário no padrão brasileiro."""
    if valor is None or moeda is None:
        return ""
    simbolos = {"BRL": "R$", "USD": "US$"}
    simbolo = simbolos.get(moeda, f"{moeda} ")
    formatted = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{simbolo} {formatted}"


def render() -> None:
    """Renderiza a aba de contratos com paginação."""
    st.markdown("## Contratos")

    page = st.session_state.get("contract_page", 1)
    page_size = 10

    try:
        contratos, total = fetch_contracts(page, page_size)
    except Exception as exc:
        st.error(f"Erro ao carregar contratos: {exc}")
        return

    # Cabeçalhos da tabela
    header = ["Contrato", "Área", "Valor"]
    cols = st.columns(len(header))
    for col, texto in zip(cols, header):
        col.markdown(f"**{texto}**")

    for c in contratos:
        cols = st.columns(len(header))
        if cols[0].button(c.get("contrato"), key=f"c_{c['contrato']}"):
            st.session_state["selected_contrato"] = c["contrato"]
            try:
                st.session_state["contract_report"] = fetch_contract_report(c["contrato"])
            except Exception as exc:
                st.error(f"Erro ao obter relatório: {exc}")
                st.session_state["contract_report"] = ""
        cols[1].write(c.get("lotacaoGerenteContrato") or "")
        # Formata a combinação de moeda e valor no padrão nacional
        cols[2].write(
            _format_currency(
                c.get("valorContratoOriginal"), c.get("moeda")
            )
        )

    total_pages = max(1, (total + page_size - 1) // page_size)
    col_prev, col_next = st.columns(2)
    if col_prev.button("Anterior", disabled=page <= 1):
        st.session_state["contract_page"] = page - 1
        st.experimental_rerun()
    if col_next.button("Próxima", disabled=page >= total_pages):
        st.session_state["contract_page"] = page + 1
        st.experimental_rerun()

    if "contract_report" in st.session_state:
        st.markdown("---")
        st.markdown(f"### Relatório do contrato {st.session_state.get('selected_contrato')}")
        st.text(st.session_state.get("contract_report", ""))
