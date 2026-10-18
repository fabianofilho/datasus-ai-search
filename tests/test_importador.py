"""
O download do DATASUS roda em processo separado sobre uma cópia do banco e troca o
arquivo no fim. Antes ele abria o DuckDB para escrita numa thread do servidor, e as
buscas, que abrem o mesmo arquivo em modo seguro, passavam a falhar com "Can't open
a connection to same database file with a different configuration" (visto em
produção no /tables). O processo filho grava por um SQL de teste, sem rede.
"""

import sys
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

import importador
from query_executor import connect_read_only


@pytest.fixture
def banco(tmp_path):
    caminho = tmp_path / "datasus.db"
    conn = duckdb.connect(str(caminho))
    conn.execute("CREATE TABLE sim_do AS SELECT 1 AS x")
    conn.close()
    return caminho


def test_importa_com_busca_aberta_e_publica_por_troca(banco, monkeypatch):
    monkeypatch.setenv("IMPORTADOR_SQL_DE_TESTE", "CREATE TABLE sih_rd AS SELECT 42 AS y")
    leitura = connect_read_only(str(banco))  # como uma busca em andamento
    importador.importar(str(banco), {"sih_rd": {"years": [2020], "states": ["SP"]}})
    assert leitura.execute("SELECT count(*) FROM sim_do").fetchone() == (1,)
    leitura.close()
    nova = connect_read_only(str(banco))
    tabelas = {r[0] for r in nova.execute("SELECT table_name FROM information_schema.tables").fetchall()}
    nova.close()
    assert tabelas == {"sim_do", "sih_rd"}
    assert not (banco.parent / "datasus.db.importando").exists()


def test_falha_mantem_o_banco_antigo(banco, monkeypatch):
    monkeypatch.setenv("IMPORTADOR_SQL_DE_TESTE", "ISSO NAO E SQL")
    with pytest.raises(RuntimeError, match="importação falhou"):
        importador.importar(str(banco), {"sim_do": {}})
    conn = connect_read_only(str(banco))
    assert conn.execute("SELECT count(*) FROM sim_do").fetchone() == (1,)
    conn.close()
    assert not (banco.parent / "datasus.db.importando").exists()


def test_dataset_desconhecido_e_recusado(tmp_path, monkeypatch):
    monkeypatch.delenv("IMPORTADOR_SQL_DE_TESTE", raising=False)
    with pytest.raises(ValueError):
        importador.importar_no_arquivo(str(tmp_path / "x.db"), {"outra_coisa": {}})
