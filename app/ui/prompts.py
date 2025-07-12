# Página de gerenciamento de prompts via Streamlit
import streamlit as st
import httpx

from app.config import API_BASE_URL

# Endpoints da API para CRUD de prompts
_PROMPTS_ENDPOINT = f"{API_BASE_URL.rstrip('/')}/prompts"


def render() -> None:
    """Exibe a aba de prompts com operações de CRUD."""

    # Tenta carregar lista de prompts existentes
    try:
        resp = httpx.get(_PROMPTS_ENDPOINT, timeout=10.0)
        resp.raise_for_status()
        prompts = resp.json().get("prompts", [])
    except Exception as exc:  # Caso ocorra erro na requisição
        st.error(f"Erro ao carregar prompts: {exc}")
        prompts = []

    st.markdown("## Prompts cadastrados")

    # Tabela simples com os dados retornados
    if prompts:
        st.table(prompts)
    else:
        st.info("Nenhum prompt encontrado.")

    st.markdown("---")
    st.markdown("### Incluir novo prompt")
    with st.form("add_prompt"):
        nome = st.text_input("Nome")
        texto = st.text_area("Texto")
        periodicidade = st.text_input("Periodicidade (opcional)")
        submitted = st.form_submit_button("Cadastrar")
        if submitted:
            try:
                httpx.post(
                    _PROMPTS_ENDPOINT,
                    json={
                        "nome": nome,
                        "texto": texto,
                        "periodicidade": periodicidade or None,
                    },
                    timeout=10.0,
                ).raise_for_status()
                st.success("Prompt cadastrado com sucesso!")
                st.experimental_rerun()
            except Exception as exc:
                st.error(f"Erro ao cadastrar prompt: {exc}")

    st.markdown("---")
    st.markdown("### Alterar ou excluir")

    if prompts:
        # Seleção do prompt existente
        options = {f"{p['id']} - {p['nome']}": p for p in prompts}
        chave = st.selectbox("Escolha o prompt", list(options.keys()))
        selected = options[chave]
        with st.form("edit_prompt"):
            nome_e = st.text_input("Nome", value=selected["nome"])
            texto_e = st.text_area("Texto", value=selected["texto"])
            periodicidade_e = st.text_input(
                "Periodicidade (opcional)", value=selected["periodicidade"] or ""
            )
            col1, col2 = st.columns(2)
            atualizar = col1.form_submit_button("Atualizar")
            excluir = col2.form_submit_button("Excluir")
            if atualizar:
                try:
                    httpx.put(
                        f"{_PROMPTS_ENDPOINT}/{selected['id']}",
                        json={
                            "nome": nome_e,
                            "texto": texto_e,
                            "periodicidade": periodicidade_e or None,
                        },
                        timeout=10.0,
                    ).raise_for_status()
                    st.success("Prompt atualizado!")
                    st.experimental_rerun()
                except Exception as exc:
                    st.error(f"Erro ao atualizar: {exc}")
            if excluir:
                try:
                    httpx.delete(
                        f"{_PROMPTS_ENDPOINT}/{selected['id']}", timeout=10.0
                    ).raise_for_status()
                    st.success("Prompt removido!")
                    st.experimental_rerun()
                except Exception as exc:
                    st.error(f"Erro ao excluir: {exc}")
    else:
        st.info("Nenhum prompt para editar ou excluir.")
