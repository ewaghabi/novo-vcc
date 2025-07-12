# Aba de execuções para o frontend Streamlit
import streamlit as st
import httpx

from app.config import API_BASE_URL

# Endpoints da API para execuções
_EXECUTIONS_ENDPOINT = f"{API_BASE_URL.rstrip('/')}/executions"


def fetch_executions() -> list[dict]:
    """Recupera lista de execuções ordenada por data/hora decrescente."""

    resp = httpx.get(_EXECUTIONS_ENDPOINT, timeout=10.0)
    resp.raise_for_status()
    data = resp.json().get("executions", [])
    # Ordena pela data/hora de início, mais recentes primeiro
    return sorted(data, key=lambda r: r.get("start_time") or "", reverse=True)


def fetch_execution_details(exec_id: int) -> dict:
    """Consulta detalhes de uma execução específica."""

    url = f"{_EXECUTIONS_ENDPOINT}/{exec_id}"
    resp = httpx.get(url, timeout=10.0)
    resp.raise_for_status()
    return resp.json()


def render() -> None:
    """Exibe tabela de execuções e permite ver detalhes ao clicar no id."""

    try:
        executions = fetch_executions()
    except Exception as exc:  # Falha ao carregar a lista
        st.error(f"Erro ao carregar execuções: {exc}")
        return

    st.markdown("## Execuções")

    selected = st.session_state.get("selected_exec")

    if executions:
        # Cabeçalhos da tabela manual
        header = ["ID", "Tarefa", "Início", "Fim", "Status"]
        cols = st.columns(len(header))
        for col, texto in zip(cols, header):
            col.markdown(f"**{texto}**")

        for exec_row in executions:
            cols = st.columns(len(header))
            if cols[0].button(str(exec_row["id"]), key=f"exec_{exec_row['id']}"):
                st.session_state["selected_exec"] = exec_row["id"]
                selected = exec_row["id"]
            cols[1].write(exec_row.get("task_name"))
            cols[2].write(exec_row.get("start_time"))
            cols[3].write(exec_row.get("end_time"))
            cols[4].write(exec_row.get("status"))
    else:
        st.info("Nenhuma execução encontrada.")

    if selected:
        st.markdown("---")
        st.markdown(f"### Detalhes da execução {selected}")
        try:
            details = fetch_execution_details(int(selected))
            st.json(details)
        except Exception as exc:
            st.error(f"Erro ao carregar detalhes: {exc}")
