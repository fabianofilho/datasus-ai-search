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

# Configuração de toda conexão de leitura do DuckDB: sem acesso a arquivos,
# rede ou extensões externas (bloqueia read_csv, glob, COPY TO, ATTACH, INSTALL)
# e com a configuração travada para que um SET não reative nada.
SAFE_DUCKDB_CONFIG = {"enable_external_access": False, "lock_configuration": True}


def connect_read_only(db_path: str) -> duckdb.DuckDBPyConnection:
    """
    Abre uma conexão somente leitura com SAFE_DUCKDB_CONFIG.

    O DuckDB reaproveita a instância já aberta no processo para o mesmo arquivo
    e, nesse caso, ignora a config pedida. Por isso a configuração efetiva é
    conferida e a conexão é recusada se vier sem as restrições.
    """
    conn = duckdb.connect(db_path, read_only=True, config=dict(SAFE_DUCKDB_CONFIG))
    try:
        external_access, locked = conn.execute(
            "SELECT current_setting('enable_external_access'), "
            "current_setting('lock_configuration')"
        ).fetchone()
    except Exception:
        conn.close()
        raise
    if external_access or not locked:
        conn.close()
        raise RuntimeError(
            "Conexao DuckDB sem as restricoes de seguranca: ja existe no processo "
            "uma conexao com outra configuracao para este arquivo."
        )
    return conn


def count_statements(query: str) -> int:
    """
    Conta as instruções SQL da string usando o tokenizador do DuckDB.

    O tokenizador devolve a posição de cada token em bytes UTF-8, não em
    caracteres. Com acento antes do ponto e vírgula ('São Paulo', 'óbito'),
    indexar a str desloca a posição, então a comparação é feita nos bytes.
    """
    encoded = query.encode("utf-8")
    count = 0
    pending = False
    for start, token_type in duckdb.tokenize(query):
        if token_type == duckdb.token_type.operator and encoded[start:start + 1] == b";":
            if pending:
                count += 1
            pending = False
        else:
            pending = True
    return count + (1 if pending else 0)


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
            self.conn = connect_read_only(self.db_path)
        return self.conn

    # Segunda barreira, depois da config da conexão. Palavras inteiras, para
    # pegar variações com tab ou quebra de linha e não bloquear OFFSET.
    BLOCKED_PATTERNS = [
        r"\bread_\w+", r"\bglob\b", r"\bhttpfs\b", r"\bcopy\b", r"\battach\b",
        r"\binstall\b", r"\bload\b", r"\bcreate\b", r"\bdrop\b", r"\balter\b",
        r"\binsert\b", r"\bupdate\b", r"\bdelete\b", r"\bpragma\b", r"\bexport\b",
        r"\bimport\b", r"\bcall\b", r"\bset\b", r"\breset\b", r"\bexecute\b",
    ]

    def _validate_safe(self, query: str) -> None:
        normalized = query.strip().lower()
        if not normalized.startswith("select") and not normalized.startswith("with"):
            raise PermissionError("Apenas consultas SELECT sao permitidas.")
        if count_statements(query) != 1:
            raise PermissionError("Apenas uma instrucao SQL por consulta e permitida.")
        for pattern in self.BLOCKED_PATTERNS:
            match = re.search(pattern, normalized)
            if match:
                raise PermissionError(f"Operacao bloqueada: {match.group(0)}")

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
        # A guarda vem antes do EXPLAIN: numa string com várias instruções,
        # o DuckDB executa todas as anteriores à última.
        try:
            self._validate_safe(query)
        except PermissionError as e:
            logger.warning(f"Query bloqueada: {e}")
            return False

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
