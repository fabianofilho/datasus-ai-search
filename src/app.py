"""
Aplicação Streamlit para interface web do DATASUS AI Search.
"""

import os
import sys
import logging
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Adicionar src ao path para importações relativas funcionarem
sys.path.insert(0, str(Path(__file__).parent))

from data_manager import DataManager
from ai_engine import AIEngine

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# ─── Configuração da Página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="DATASUS AI Search",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    .stTextArea textarea { font-size: 1.05rem; }
    .answer-box {
        background-color: #f0f7ff;
        border-left: 4px solid #1f77b4;
        padding: 1rem 1.5rem;
        border-radius: 4px;
        margin-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Estado da Sessão ──────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "db_initialized": False,
        "db_path": "data/datasus.db",
        "history": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.title("⚙️ Configurações")

        # ── API
        st.subheader("🔑 API do LLM")
        api_key = st.text_input(
            "Chave da API",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            help="Cole aqui sua chave de API (OpenAI, Anthropic, etc.)",
        )
        api_base = st.text_input(
            "URL Base (opcional)",
            value=os.getenv("LLM_API_BASE", ""),
            help="Deixe em branco para usar a OpenAI padrão. "
                 "Para Ollama local: http://localhost:11434/v1",
        )
        model = st.selectbox(
            "Modelo",
            ["gpt-4.1-mini", "gpt-4.1-nano", "gemini-2.5-flash", "gpt-4o", "gpt-3.5-turbo"],
            help="Selecione o modelo de linguagem a usar",
        )

        st.divider()

        # ── Banco de Dados
        st.subheader("📊 Banco de Dados")
        db_path = st.text_input(
            "Caminho do banco DuckDB",
            value=st.session_state.db_path,
        )
        st.session_state.db_path = db_path

        datasets_options = {
            "SIM – Mortalidade (sim_do)": "sim_do",
            "SIH – Internações (sih_rd)": "sih_rd",
            "SIA – Ambulatorial (sia_pa)": "sia_pa",
            "IBGE – População (ibge_pop)": "ibge_pop",
        }
        selected_labels = st.multiselect(
            "Datasets a importar",
            options=list(datasets_options.keys()),
            default=list(datasets_options.keys()),
        )
        selected_datasets = [datasets_options[label] for label in selected_labels]

        if st.button("🔄 Inicializar / Atualizar BD", use_container_width=True):
            if not selected_datasets:
                st.warning("Selecione ao menos um dataset.")
            else:
                with st.spinner("Baixando e importando dados do DATASUS..."):
                    try:
                        dm = DataManager(db_path)
                        dm.initialize_database(selected_datasets)
                        st.session_state.db_initialized = True
                        st.success("✅ Banco de dados pronto!")
                    except Exception as e:
                        st.error(f"Erro ao inicializar banco: {e}")

        if st.session_state.db_initialized:
            st.success("✅ Banco de dados disponível")
        else:
            st.warning("⚠️ Banco não inicializado")

        if st.button("ℹ️ Ver Esquema do BD", use_container_width=True):
            if st.session_state.db_initialized:
                dm = DataManager(db_path)
                schema = dm.get_schema_info()
                st.text_area("Esquema", value=schema, height=300)
            else:
                st.warning("Inicialize o banco primeiro.")

        st.divider()
        st.caption("DATASUS AI Search v0.1.0")

    return api_key, api_base, model


# ─── Conteúdo Principal ────────────────────────────────────────────────────────
def render_main(api_key: str, api_base: str, model: str):
    st.title("🏥 DATASUS AI Search")
    st.markdown(
        "Consulte dados epidemiológicos do DATASUS usando **linguagem natural**. "
        "A IA traduz sua pergunta em SQL, executa a consulta e retorna a resposta formatada."
    )

    # Exemplos
    with st.expander("📝 Exemplos de perguntas"):
        examples = [
            "Qual o número de internações por doenças cardiovasculares em São Paulo em 2020?",
            "Qual foi a prevalência de tuberculose em São Paulo em 2018?",
            "Quantos óbitos por COVID-19 ocorreram no Brasil em 2021?",
            "Qual é a taxa de mortalidade infantil por estado em 2022?",
            "Quantos procedimentos ambulatoriais foram realizados em Minas Gerais em 2021?",
            "Quais as 10 principais causas de morte no Brasil em 2019?",
            "Qual a média de dias de internação por diagnóstico no Rio de Janeiro em 2020?",
        ]
        for ex in examples:
            if st.button(f"↗ {ex}", key=ex):
                st.session_state["question_input"] = ex

    # Input
    question = st.text_area(
        "Digite sua pergunta:",
        value=st.session_state.get("question_input", ""),
        placeholder="Ex: Qual o número de internações por doenças cardiovasculares em São Paulo em 2020?",
        height=110,
        key="question_input",
    )

    col_btn, col_clear = st.columns([5, 1])
    with col_btn:
        search_clicked = st.button("🚀 Buscar", use_container_width=True, type="primary")
    with col_clear:
        if st.button("🗑️ Limpar", use_container_width=True):
            st.session_state["question_input"] = ""
            st.rerun()

    # Validações
    if search_clicked:
        if not api_key:
            st.error("Configure sua chave de API no painel lateral.")
            return
        if not st.session_state.db_initialized:
            st.error("Inicialize o banco de dados no painel lateral.")
            return
        if not question.strip():
            st.warning("Digite uma pergunta antes de buscar.")
            return

        with st.spinner("Processando sua pergunta com IA..."):
            try:
                engine = AIEngine(
                    api_key=api_key,
                    api_base=api_base if api_base else None,
                    model=model,
                    db_path=st.session_state.db_path,
                )
                _, sql_query, response = engine.answer_question(question)

                # Salvar no histórico
                st.session_state.history.insert(
                    0, {"question": question, "sql": sql_query, "answer": response}
                )

                # Exibir resultado
                st.markdown("---")
                st.subheader("📊 Resposta")
                st.markdown(
                    f'<div class="answer-box">{response}</div>',
                    unsafe_allow_html=True,
                )

                with st.expander("🔧 Consulta SQL gerada"):
                    st.code(sql_query, language="sql")

            except Exception as e:
                st.error(f"Erro ao processar pergunta: {e}")
                logger.exception("Erro ao processar pergunta")

    # Histórico
    if st.session_state.history:
        st.markdown("---")
        st.subheader("🕒 Histórico de Consultas")
        for i, item in enumerate(st.session_state.history[:5]):
            with st.expander(f"[{i+1}] {item['question'][:80]}..."):
                st.markdown(f"**Resposta:** {item['answer']}")
                st.code(item["sql"], language="sql")


# ─── Main ──────────────────────────────────────────────────────────────────────
def main():
    init_session()
    api_key, api_base, model = render_sidebar()
    render_main(api_key, api_base, model)


if __name__ == "__main__":
    main()
