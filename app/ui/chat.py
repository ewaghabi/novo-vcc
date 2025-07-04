import streamlit as st

from app.chat import ContractChatbot
from app.storage.vector_store_adapter import VectorStoreAdapter


# Initialize vector store and chatbot
_vector_store = VectorStoreAdapter()
_chatbot = ContractChatbot(_vector_store)


def main() -> None:
    st.set_page_config(page_title="Novo VCC - Chat", layout="centered")

    # Sidebar with navigation
    with st.sidebar:
        st.markdown("# Novo VCC")
        st.markdown("[Chat](#)")
        st.markdown("[Config](#)")

    st.title("Chat sobre contratos")

    question = st.text_input("Faça sua pergunta sobre os contratos:")
    if question:
        answer, sources = _chatbot.ask(question)
        st.markdown("## Resposta")
        st.write(answer)

        if sources:
            st.markdown("## Contratos relevantes")
            for src in sources:
                st.write(src)


if __name__ == "__main__":
    main()
