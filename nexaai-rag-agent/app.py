"""
app.py

Interface Streamlit do NexaAI — Assistente Corporativo.

Permite que o usuário faça perguntas em linguagem natural sobre os
documentos internos da NexaAI e visualize a resposta gerada via RAG,
junto com as fontes utilizadas.
"""

import streamlit as st

import config
from rag import NexaAIRag

st.set_page_config(
    page_title="NexaAI — Assistente Corporativo",
    page_icon="🤖",
    layout="centered",
)


@st.cache_resource(show_spinner=False)
def load_agent() -> NexaAIRag:
    """Carrega o agente RAG uma única vez por sessão do servidor Streamlit."""
    return NexaAIRag()


def render_header() -> None:
    st.title("🤖 NexaAI — Assistente Corporativo")
    st.caption("Faça perguntas sobre os documentos internos da empresa.")


def render_sources(sources: list) -> None:
    if not sources:
        return
    with st.expander("📎 Fontes utilizadas"):
        for source in sources:
            st.markdown(f"**{source.document}** — página {source.page}")
            st.caption(source.snippet)


def main() -> None:
    render_header()

    if "history" not in st.session_state:
        st.session_state.history = []

    # --- Carregamento do agente com tratamento de erro ---
    try:
        agent = load_agent()
    except RuntimeError as exc:
        st.error(str(exc))
        st.info(
            "Configure a variável GOOGLE_API_KEY no arquivo .env "
            "(veja .env.example) e reinicie a aplicação."
        )
        st.stop()
    except Exception as exc:  # falha inesperada ao inicializar o Chroma/Gemini
        st.error(f"Erro ao inicializar o agente: {exc}")
        st.stop()

    if not agent.has_indexed_documents():
        st.warning(
            "A base de conhecimento ainda não foi indexada. "
            "Execute `python ingest.py` antes de usar o assistente."
        )
        st.stop()

    # --- Formulário de pergunta ---
    with st.form("pergunta_form", clear_on_submit=False):
        question = st.text_input(
            "Digite sua pergunta:",
            placeholder="Ex.: Qual é o preço do plano Business?",
        )
        submitted = st.form_submit_button("Perguntar")

    if submitted and question.strip():
        with st.spinner("Consultando a base de conhecimento..."):
            try:
                result = agent.ask(question)
            except Exception as exc:
                st.error(f"Ocorreu um erro ao consultar o agente: {exc}")
                result = None

        if result is not None:
            st.session_state.history.insert(0, result)

    # --- Histórico da sessão (mais recente primeiro) ---
    if st.session_state.history:
        st.divider()
        st.subheader("Histórico da sessão")
        for item in st.session_state.history:
            st.markdown(f"**Pergunta:** {item.question}")
            st.markdown(f"**Resposta:** {item.answer}")
            render_sources(item.sources)
            st.divider()
    else:
        st.info(
            "Nenhuma pergunta feita ainda. Experimente perguntar, por exemplo: "
            "\"Como faço para criar um projeto?\" ou "
            "\"Quais informações a NexaAI coleta?\""
        )


if __name__ == "__main__":
    main()
