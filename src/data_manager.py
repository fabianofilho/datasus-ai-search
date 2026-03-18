"""
Módulo para gerenciar download e atualização de dados do DATASUS.
"""

import os
import logging
from pathlib import Path
from typing import Optional
import duckdb

logger = logging.getLogger(__name__)


class DataManager:
    """
    Gerencia o download e armazenamento de dados do DATASUS em um banco DuckDB.
    """

    def __init__(self, db_path: str = "data/datasus.db"):
        """
        Inicializa o gerenciador de dados.

        Args:
            db_path: Caminho para o arquivo do banco de dados DuckDB.
        """
        self.db_path = db_path
        self._ensure_db_dir()
        self.conn = None

    def _ensure_db_dir(self):
        """Garante que o diretório do banco de dados existe."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> duckdb.DuckDBPyConnection:
        """
        Conecta ao banco de dados DuckDB.

        Returns:
            Conexão com o DuckDB.
        """
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path)
        return self.conn

    def initialize_database(self, datasets: Optional[list] = None):
        """
        Inicializa o banco de dados com dados do DATASUS.

        Args:
            datasets: Lista de datasets a importar. Se None, importa os principais.
                     Opções: 'sim_do', 'sih_rd', 'sia_pa', 'ibge_pop'
        """
        if datasets is None:
            datasets = ["sim_do", "sih_rd", "sia_pa", "ibge_pop"]

        logger.info(f"Iniciando importação de datasets: {datasets}")

        try:
            import datasus_db

            for dataset in datasets:
                logger.info(f"Importando {dataset}...")
                if dataset == "sim_do":
                    datasus_db.import_sim_do(db_file=self.db_path)
                elif dataset == "sih_rd":
                    datasus_db.import_sih_rd(db_file=self.db_path)
                elif dataset == "sia_pa":
                    datasus_db.import_sia_pa(db_file=self.db_path)
                elif dataset == "ibge_pop":
                    datasus_db.import_ibge_pop(db_file=self.db_path)
                elif dataset == "auxiliar":
                    datasus_db.import_auxiliar_tables(db_file=self.db_path)
                logger.info(f"✓ {dataset} importado com sucesso")

            logger.info("Banco de dados inicializado com sucesso!")

        except ImportError:
            logger.error(
                "datasus-db não está instalado. Execute: pip install datasus-db"
            )
            raise
        except Exception as e:
            logger.error(f"Erro ao importar dados: {e}")
            raise

    def get_schema_info(self) -> str:
        """
        Retorna informações sobre o esquema do banco de dados.

        Returns:
            String com descrição das tabelas e colunas disponíveis.
        """
        conn = self.connect()

        try:
            # Obter lista de tabelas
            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()

            schema_info = "# Esquema do Banco de Dados DATASUS\n\n"

            for (table_name,) in tables:
                schema_info += f"## Tabela: {table_name}\n"

                # Obter colunas da tabela
                columns = conn.execute(
                    f"PRAGMA table_info({table_name})"
                ).fetchall()

                schema_info += "| Coluna | Tipo | Descrição |\n"
                schema_info += "|--------|------|-------------|\n"

                for col_name, col_type, _, _, _, _ in columns:
                    schema_info += f"| {col_name} | {col_type} | - |\n"

                schema_info += "\n"

            return schema_info

        except Exception as e:
            logger.error(f"Erro ao obter informações do esquema: {e}")
            return ""

    def execute_query(self, query: str):
        """
        Executa uma consulta no banco de dados.

        Args:
            query: Consulta SQL a executar.

        Returns:
            Resultados da consulta.
        """
        conn = self.connect()
        try:
            result = conn.execute(query).fetchall()
            return result
        except Exception as e:
            logger.error(f"Erro ao executar consulta: {e}")
            raise

    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
