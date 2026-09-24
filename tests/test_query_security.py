"""
Testes de segurança do QueryExecutor (SRCH-02): conexão DuckDB sem acesso
externo e com configuração travada, uma única instrução por consulta e guarda
aplicada antes do EXPLAIN.
"""

import sys
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import query_executor
from query_executor import QueryExecutor, count_statements


@pytest.fixture
def temp_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = duckdb.connect(db_path)
    conn.execute("CREATE TABLE sim_do (DTOBITO DATE, CAUSABAS VARCHAR)")
    conn.execute("INSERT INTO sim_do VALUES ('2020-03-15', 'A15'), ('2021-01-05', 'B34')")
    conn.close()
    return db_path


@pytest.fixture
def executor(temp_db):
    ex = QueryExecutor(temp_db)
    yield ex
    ex.close()


@pytest.fixture
def secret_csv(tmp_path):
    path = tmp_path / "segredo.csv"
    path.write_text("usuario,senha\nadmin,123\n")
    return path


def test_conexao_sem_acesso_externo_e_travada(executor):
    conn = executor.connect()
    external, locked = conn.execute(
        "SELECT current_setting('enable_external_access'), current_setting('lock_configuration')"
    ).fetchone()
    assert external is False
    assert locked is True


def test_copy_to_bloqueado(executor, tmp_path):
    alvo = tmp_path / "x.csv"
    with pytest.raises(PermissionError):
        executor.execute(f"COPY (SELECT 42) TO '{alvo}'")
    with pytest.raises(PermissionError):
        executor.execute(f"SELECT 1;\nCOPY (SELECT 7) TO '{alvo}'")
    # Mesmo sem a guarda, a conexão recusa escrever arquivos.
    with pytest.raises(duckdb.Error):
        executor.connect().execute(f"COPY (SELECT 42) TO '{alvo}'")
    assert not alvo.exists()


def test_validate_query_aplica_guarda_antes_do_explain(executor, tmp_path):
    alvo = tmp_path / "y.csv"
    assert executor.validate_query(f"SELECT 1; COPY (SELECT 42) TO '{alvo}'") is False
    assert not alvo.exists()


def test_read_csv_de_arquivo_local_bloqueado(executor, secret_csv):
    with pytest.raises(PermissionError):
        executor.execute(f"SELECT * FROM read_csv_auto('{secret_csv}')")
    # Replacement scan ('arquivo.csv' como tabela) passa pela guarda textual,
    # mas a conexão sem acesso externo recusa a leitura.
    with pytest.raises(duckdb.Error):
        executor.execute(f"SELECT * FROM '{secret_csv}'")
    assert executor.validate_query(f"SELECT * FROM '{secret_csv}'") is False
    with pytest.raises(duckdb.Error):
        executor.connect().execute(f"SELECT * FROM read_csv_auto('{secret_csv}')")


def test_glob_bloqueado(executor, tmp_path):
    with pytest.raises(PermissionError):
        executor.execute(f"SELECT * FROM glob ('{tmp_path}/*')")
    with pytest.raises(PermissionError):
        executor.execute(f"SELECT * FROM glob('{tmp_path}/*')")
    with pytest.raises(duckdb.Error):
        executor.connect().execute(f"SELECT * FROM glob('{tmp_path}/*')")


def test_set_bloqueado(executor):
    with pytest.raises(PermissionError):
        executor.execute("SET enable_external_access = true")
    with pytest.raises(PermissionError):
        executor.execute("SELECT 1;\tSET enable_external_access = true")
    conn = executor.connect()
    for comando in (
        "SET enable_external_access = true",
        "SET lock_configuration = false",
        "RESET lock_configuration",
        "SET memory_limit = '10GB'",
    ):
        with pytest.raises(duckdb.Error):
            conn.execute(comando)
    assert conn.execute("SELECT current_setting('enable_external_access')").fetchone()[0] is False


def test_multiplas_instrucoes_recusadas(executor):
    with pytest.raises(PermissionError, match="uma instrucao"):
        executor.execute("SELECT 1; SELECT 2")
    assert count_statements("SELECT 1; SELECT 2") == 2
    # Ponto e vírgula dentro de literal, comentário ou no final não conta.
    assert count_statements("SELECT ';' AS x") == 1
    assert count_statements("SELECT 1 -- ; comentario") == 1
    assert count_statements("SELECT 1;") == 1
    assert executor.execute("SELECT ';' AS x")["x"].iloc[0] == ";"


def test_offset_nao_e_bloqueado(executor):
    result = executor.execute("SELECT * FROM sim_do ORDER BY DTOBITO LIMIT 10 OFFSET 1")
    assert list(result["CAUSABAS"]) == ["B34"]


def test_instancia_sem_restricoes_e_recusada(temp_db):
    # O DuckDB reaproveita a instância aberta e ignora a config da nova conexão.
    aberta = duckdb.connect(temp_db, read_only=True)
    try:
        with pytest.raises(RuntimeError):
            QueryExecutor(temp_db).connect()
    finally:
        aberta.close()
    with QueryExecutor(temp_db) as ex:
        assert ex.execute("SELECT COUNT(*) AS n FROM sim_do")["n"].iloc[0] == 2


def test_get_existing_tables_usa_conexao_segura(temp_db, monkeypatch):
    from backend import main

    chamadas = []

    def espiao(db_path):
        chamadas.append(db_path)
        return query_executor.connect_read_only(db_path)

    monkeypatch.setattr(main, "connect_read_only", espiao)
    assert main.get_existing_tables(temp_db) == ["sim_do"]
    assert chamadas == [temp_db]
