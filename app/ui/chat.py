# Interface de usuário baseada em Streamlit
import streamlit as st

import httpx

from app.config import API_BASE_URL


# Endpoint da API de chat
_CHAT_ENDPOINT = f"{API_BASE_URL.rstrip('/')}/chat"


def main() -> None:
    """Renderiza a interface principal de chat."""
    st.set_page_config(page_title="Novo VCC - Chat", layout="centered")

    # Sidebar with navigation
    with st.sidebar:
        st.markdown("# Novo VCC")
        st.markdown("[Chat](#)")
        st.markdown("[Config](#)")

    st.title("Chat sobre contratos")  # cabeçalho principal

    question = st.text_input("Faça sua pergunta sobre os contratos:")  # entrada do usuário
    if question:
        try:
            response = httpx.post(_CHAT_ENDPOINT, json={"question": question}, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            answer = data.get("answer", "")
            sources = data.get("sources", [])
        except Exception as exc:
            st.error(f"Erro ao consultar a API: {exc}")
            return

        st.markdown("## Resposta")
        st.write(answer)

        if sources:
            st.markdown("## Contratos relevantes")
            for src in sources:
                st.write(src)


if __name__ == "__main__":
    main()
