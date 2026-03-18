"""
Aplicação Streamlit para interface web do DATASUS AI Search.
"""

import os
import logging
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from data_manager import DataManager
from ai_engine import AIEngine

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="DATASUS AI Search",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos customizados
st.markdown(
    """
    <style>
    .main-title {
        color: #1f77b4;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .subtitle {
        color: #666;
        font-size: 1.1em;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_session_state():
    """Inicializa o estado da sessão."""
    if "data_manager" not in st.session_state:
        st.session_state.data_manager = None
    if "ai_engine" not in st.session_state:
        st.session_state.ai_engine = None
    if "db_initialized" not in st.session_state:
        st.session_state.db_initialized = False


def main():
    """Função principal da aplicação."""
    initialize_session_state()

    # Sidebar
    with st.sidebar:
        st.markdown("# ⚙️ Configurações")

        # Seção de API Key
        st.markdown("## 🔑 Configuração da API")
        api_key = st.text_input(
            "Chave da API do LLM",
            type="password",
            help="Cole sua chave de API (OpenAI, Anthropic, etc.)",
        )

        api_base = st.text_input(
            "URL Base da API (opcional)",
            help="Deixe em branco para usar OpenAI padrão",
            value="",
        )

        model = st.selectbox(
            "Modelo de LLM",
            ["gpt-4.1-mini", "gpt-4.1-nano", "gemini-2.5-flash"],
            help="Selecione o modelo de linguagem a usar",
        )

        # Seção de Banco de Dados
        st.markdown("## 📊 Banco de Dados")

        db_path = st.text_input(
            "Caminho do banco de dados",
            value="data/datasus.db",
            help="Caminho onde o banco DuckDB será armazenado",
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Inicializar BD", use_container_width=True):
                with st.spinner("Inicializando banco de dados..."):
                    try:
                        dm = DataManager(db_path)
                        dm.initialize_database()
                        st.session_state.data_manager = dm
                        st.session_state.db_initialized = True
                        st.success("✓ Banco de dados inicializado!")
                    except Exception as e:
                        st.error(f"Erro ao inicializar banco: {str(e)}")

        with col2:
            if st.button("ℹ️ Ver Esquema", use_container_width=True):
                if st.session_state.data_manager:
                    with st.spinner("Obtendo esquema..."):
                        schema = st.session_state.data_manager.get_schema_info()
                        st.text_area("Esquema do Banco", value=schema, height=300)
                else:
                    st.warning("Inicialize o banco primeiro")

        # Informações
        st.markdown("---")
        st.markdown("### 📖 Sobre")
        st.info(
            """
            **DATASUS AI Search** permite consultar dados epidemiológicos do DATASUS
            usando linguagem natural. Basta fazer uma pergunta e a IA gerará a consulta!
            """
        )

    # Conteúdo principal
    st.markdown('<div class="main-title">🏥 DATASUS AI Search</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Consulte dados epidemiológicos do DATASUS usando linguagem natural</div>',
        unsafe_allow_html=True,
    )

    # Verificar se está tudo configurado
    if not api_key:
        st.warning("⚠️ Configure sua chave de API no painel lateral para começar")
        return

    if not st.session_state.db_initialized:
        st.warning("⚠️ Inicialize o banco de dados no painel lateral")
        return

    # Criar engine de IA
    try:
        if st.session_state.ai_engine is None:
            st.session_state.ai_engine = AIEngine(
                api_key=api_key,
                api_base=api_base if api_base else None,
                model=model,
                db_path=db_path,
            )
    except Exception as e:
        st.error(f"Erro ao inicializar engine de IA: {str(e)}")
        return

    # Seção de consulta
    st.markdown("## 🔍 Faça sua pergunta")

    # Exemplos de perguntas
    with st.expander("📝 Ver exemplos de perguntas"):
        st.markdown(
            """
            - Qual o número de internações por doenças cardiovasculares em São Paulo em 2020?
            - Qual foi a prevalência de tuberculose em São Paulo em 2018?
            - Quantos óbitos por COVID-19 ocorreram no Brasil em 2021?
            - Qual é a taxa de mortalidade infantil por estado em 2022?
            - Quantos procedimentos ambulatoriais foram realizados em Minas Gerais em 2021?
            """
        )

    # Input da pergunta
    user_question = st.text_area(
        "Digite sua pergunta sobre dados epidemiológicos:",
        placeholder="Ex: Qual o número de internações por doenças cardiovasculares em São Paulo em 2020?",
        height=100,
    )

    # Botão de busca
    if st.button("🚀 Buscar", use_container_width=True):
        if not user_question.strip():
            st.warning("Por favor, digite uma pergunta")
        else:
            with st.spinner("Processando sua pergunta..."):
                try:
                    question, sql_query, response = st.session_state.ai_engine.answer_question(
                        user_question
                    )

                    # Exibir resultados
                    st.markdown("---")
                    st.markdown("## 📊 Resultados")

                    # Resposta formatada
                    st.markdown("### Resposta")
                    st.success(response)

                    # Detalhes técnicos
                    with st.expander("🔧 Ver detalhes técnicos"):
                        st.markdown("#### Consulta SQL gerada:")
                        st.code(sql_query, language="sql")

                except Exception as e:
                    st.error(f"Erro ao processar pergunta: {str(e)}")
                    logger.exception("Erro ao processar pergunta")

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #999; font-size: 0.9em;">
        <p>DATASUS AI Search v0.1.0 | Desenvolvido com ❤️ para análise epidemiológica</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
