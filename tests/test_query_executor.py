"""
Testes unitários para o QueryExecutor.
"""

import pytest
import duckdb
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from query_executor import QueryExecutor


@pytest.fixture
def temp_db(tmp_path):
    """Cria um banco de dados DuckDB temporário para testes."""
    db_path = str(tmp_path / "test.db")
    conn = duckdb.connect(db_path)

    # Criar tabela de teste
    conn.execute("""
        CREATE TABLE sim_do (
            DTOBITO DATE,
            CODMUNRES VARCHAR,
            CAUSABAS VARCHAR,
            IDADE INTEGER,
            SEXO VARCHAR
        )
    """)

    # Inserir dados de teste
    conn.execute("""
        INSERT INTO sim_do VALUES
        ('2020-03-15', '355030', 'Tuberculose pulmonar', 45, 'M'),
        ('2020-06-20', '355030', 'Tuberculose pulmonar', 62, 'F'),
        ('2020-09-10', '330455', 'Infarto agudo do miocardio', 70, 'M'),
        ('2021-01-05', '355030', 'COVID-19', 55, 'F'),
        ('2021-02-18', '330455', 'COVID-19', 80, 'M')
    """)
    conn.close()

    return db_path


def test_list_tables(temp_db):
    executor = QueryExecutor(temp_db)
    tables = executor.list_tables()
    assert "sim_do" in tables
    executor.close()


def test_execute_simple_query(temp_db):
    executor = QueryExecutor(temp_db)
    result = executor.execute("SELECT COUNT(*) as total FROM sim_do")
    assert isinstance(result, pd.DataFrame)
    assert result["total"].iloc[0] == 5
    executor.close()


def test_execute_filtered_query(temp_db):
    executor = QueryExecutor(temp_db)
    result = executor.execute(
        "SELECT COUNT(*) as total FROM sim_do WHERE YEAR(DTOBITO) = 2020"
    )
    assert result["total"].iloc[0] == 3
    executor.close()


def test_get_table_schema(temp_db):
    executor = QueryExecutor(temp_db)
    schema = executor.get_table_schema("sim_do")
    assert "DTOBITO" in schema
    assert "CAUSABAS" in schema
    executor.close()


def test_validate_valid_query(temp_db):
    executor = QueryExecutor(temp_db)
    assert executor.validate_query("SELECT * FROM sim_do LIMIT 10") is True
    executor.close()


def test_validate_invalid_query(temp_db):
    executor = QueryExecutor(temp_db)
    assert executor.validate_query("SELECT * FROM tabela_inexistente") is False
    executor.close()


def test_get_sample_data(temp_db):
    executor = QueryExecutor(temp_db)
    sample = executor.get_sample_data("sim_do", limit=2)
    assert len(sample) == 2
    executor.close()


def test_context_manager(temp_db):
    with QueryExecutor(temp_db) as executor:
        result = executor.execute("SELECT COUNT(*) as total FROM sim_do")
        assert result["total"].iloc[0] == 5
