"""
Interface de linha de comando (CLI) para o DATASUS AI Search.
Permite consultas sem necessidade de interface web.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

from data_manager import DataManager
from ai_engine import AIEngine

load_dotenv()

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="DATASUS AI Search — Consulte dados epidemiológicos usando linguagem natural.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python cli.py --init
  python cli.py "Qual o número de internações por doenças cardiovasculares em SP em 2020?"
  python cli.py --api-key sk-xxx "Quantos óbitos por tuberculose em 2018?"
        """,
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="Pergunta em linguagem natural sobre dados epidemiológicos.",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Inicializa o banco de dados com dados do DATASUS.",
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=["sim_do", "sih_rd", "sia_pa", "ibge_pop"],
        choices=["sim_do", "sih_rd", "sia_pa", "ibge_pop"],
        help="Datasets a importar durante a inicialização.",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("OPENAI_API_KEY"),
        help="Chave da API do LLM (padrão: variável OPENAI_API_KEY).",
    )
    parser.add_argument(
        "--api-base",
        default=os.getenv("LLM_API_BASE"),
        help="URL base da API (opcional, para LLMs alternativos).",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("LLM_MODEL", "gpt-4.1-mini"),
        help="Modelo de LLM a usar (padrão: gpt-4.1-mini).",
    )
    parser.add_argument(
        "--db-path",
        default=os.getenv("DB_PATH", "data/datasus.db"),
        help="Caminho para o banco de dados DuckDB.",
    )
    parser.add_argument(
        "--show-sql",
        action="store_true",
        help="Exibe a consulta SQL gerada.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Ativa logs detalhados.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # ── Inicializar banco de dados
    if args.init:
        print(f"🔄 Inicializando banco de dados em '{args.db_path}'...")
        print(f"   Datasets: {', '.join(args.datasets)}")
        try:
            dm = DataManager(args.db_path)
            dm.initialize_database(args.datasets)
            print("✅ Banco de dados inicializado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao inicializar banco: {e}")
            sys.exit(1)
        return

    # ── Responder pergunta
    if not args.question:
        print("❌ Forneça uma pergunta ou use --init para inicializar o banco.")
        print("   Use --help para mais informações.")
        sys.exit(1)

    if not args.api_key:
        print("❌ Chave de API não encontrada. Use --api-key ou defina OPENAI_API_KEY.")
        sys.exit(1)

    if not Path(args.db_path).exists():
        print(f"❌ Banco de dados não encontrado em '{args.db_path}'.")
        print("   Execute primeiro: python cli.py --init")
        sys.exit(1)

    print(f"\n🔍 Pergunta: {args.question}\n")
    print("⏳ Processando...\n")

    try:
        engine = AIEngine(
            api_key=args.api_key,
            api_base=args.api_base,
            model=args.model,
            db_path=args.db_path,
        )
        question, sql_query, response = engine.answer_question(args.question)

        if args.show_sql:
            print("─" * 60)
            print("📋 SQL Gerado:")
            print(sql_query)
            print("─" * 60)

        print("📊 Resposta:")
        print(response)
        print()

    except Exception as e:
        print(f"❌ Erro ao processar pergunta: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
