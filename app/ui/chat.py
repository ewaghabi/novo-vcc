# Interface de usuário baseada em Streamlit
import streamlit as st
import httpx

from app.config import API_BASE_URL
from .prompts import render as render_prompts_tab
# Nova aba para visualizar execuções
from .executions import render as render_executions_tab
# Nova aba para listar contratos
from .contracts import render as render_contracts_tab

# Endpoint da API de chat
_CHAT_ENDPOINT = f"{API_BASE_URL.rstrip('/')}/chat"


def _chat_tab() -> None:
    """Renderiza os controles da aba de chat."""

    st.markdown("## Chat sobre contratos")

    pergunta = st.text_input("Faça sua pergunta sobre os contratos:")
    if pergunta:
        try:
            resp = httpx.post(_CHAT_ENDPOINT, json={"question": pergunta}, timeout=30.0)
            resp.raise_for_status()
            dados = resp.json()
            resposta = dados.get("answer", "")
            fontes = dados.get("sources", [])
        except Exception as exc:  # Trata falhas ao chamar a API
            st.error(f"Erro ao consultar a API: {exc}")
            return

        st.markdown("### Resposta")
        st.write(resposta)

        if fontes:
            st.markdown("### Contratos relevantes")
            for src in fontes:
                st.write(src)


def main() -> None:
    """Renderiza a aplicação com abas Chat, Prompts, Execuções e Contratos."""

    st.set_page_config(page_title="Novo VCC", layout="centered")

    with st.sidebar:
        st.markdown("# Novo VCC")
        st.markdown("Utilize as abas acima")

    aba_chat, aba_prompts, aba_exec, aba_contracts = st.tabs(
        ["Chat", "Prompts", "Execuções", "Contratos"]
    )

    with aba_chat:
        _chat_tab()

    with aba_prompts:
        render_prompts_tab()

    with aba_exec:
        render_executions_tab()

    with aba_contracts:
        render_contracts_tab()


# Inicia a aplicação quando executado diretamente
if __name__ == "__main__":
    main()
