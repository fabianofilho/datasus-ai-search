"""
Módulo para executar consultas SQL no banco de dados DuckDB.
"""

import logging
import re
from typing import Any, Dict, List
import duckdb
import pandas as pd

_SAFE_TABLE_NAME = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

logger = logging.getLogger(__name__)


class QueryExecutor:
    """
    Executa consultas SQL no banco de dados DuckDB e retorna resultados formatados.
    """

    def __init__(self, db_path: str = "data/datasus.db"):
        """
        Inicializa o executor de consultas.

        Args:
            db_path: Caminho para o arquivo do banco de dados DuckDB.
        """
        self.db_path = db_path
        self.conn = None

    def connect(self) -> duckdb.DuckDBPyConnection:
        """
        Conecta ao banco de dados DuckDB.

        Returns:
            Conexão com o DuckDB.
        """
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path, read_only=True)
        return self.conn

    BLOCKED_PATTERNS = [
        "read_csv", "read_parquet", "read_json", "read_blob",
        "read_text", "glob(", "httpfs", "copy ", "attach ",
        "install ", "load ", "create ", "drop ", "alter ",
        "insert ", "update ", "delete ", "pragma ", "export ",
        "import ", "call ", "set ", "execute(",
    ]

    def _validate_safe(self, query: str) -> None:
        normalized = query.strip().lower()
        if not normalized.startswith("select") and not normalized.startswith("with"):
            raise PermissionError("Apenas consultas SELECT sao permitidas.")
        for pattern in self.BLOCKED_PATTERNS:
            if pattern in normalized:
                raise PermissionError(f"Operacao bloqueada: {pattern.strip()}")

    def execute(self, query: str) -> pd.DataFrame:
        """
        Executa uma consulta SQL e retorna os resultados como DataFrame.
        Apenas SELECT/WITH sao permitidos. Funcoes de acesso a filesystem sao bloqueadas.
        """
        self._validate_safe(query)
        conn = self.connect()

        try:
            logger.debug(f"Executando query: {query}")
            result = conn.execute(query).df()
            logger.debug(f"Query executada com sucesso. Linhas retornadas: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"Erro ao executar consulta: {e}")
            raise

    def validate_query(self, query: str) -> bool:
        """
        Valida se uma consulta SQL é válida sem executá-la.

        Args:
            query: Consulta SQL a validar.

        Returns:
            True se a consulta é válida, False caso contrário.
        """
        conn = self.connect()

        try:
            # Usar EXPLAIN para validar sem executar
            conn.execute(f"EXPLAIN {query}")
            logger.debug("Query validada com sucesso")
            return True

        except Exception as e:
            logger.warning(f"Query inválida: {e}")
            return False

    def get_table_schema(self, table_name: str) -> Dict[str, str]:
        """
        Obtém o esquema de uma tabela.

        Args:
            table_name: Nome da tabela.

        Returns:
            Dicionário com nomes de colunas e seus tipos.
        """
        conn = self.connect()

        try:
            if not _SAFE_TABLE_NAME.match(table_name):
                raise ValueError(f"Nome de tabela invalido: {table_name}")
            columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            schema = {col[1]: col[2] for col in columns}
            return schema

        except Exception as e:
            logger.error(f"Erro ao obter esquema da tabela {table_name}: {e}")
            return {}

    def list_tables(self) -> List[str]:
        """
        Lista todas as tabelas disponíveis no banco de dados.

        Returns:
            Lista com nomes das tabelas.
        """
        conn = self.connect()

        try:
            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()
            return [table[0] for table in tables]

        except Exception as e:
            logger.error(f"Erro ao listar tabelas: {e}")
            return []

    def get_sample_data(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """
        Obtém dados de exemplo de uma tabela.

        Args:
            table_name: Nome da tabela.
            limit: Número de linhas a retornar.

        Returns:
            DataFrame com dados de exemplo.
        """
        try:
            if not _SAFE_TABLE_NAME.match(table_name):
                raise ValueError(f"Nome de tabela invalido: {table_name}")
            limit = min(int(limit), 100)
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            return self.execute(query)

        except Exception as e:
            logger.error(f"Erro ao obter dados de exemplo: {e}")
            return pd.DataFrame()

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
