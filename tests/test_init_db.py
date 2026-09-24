"""
Testes do endpoint /init-db (SRCH-06): aberto ao front público, mas com
datasets, anos e UFs validados contra listas fechadas, sem '*' e com limite de
combinações de UF x ano por pedido. A importação real é trocada por um espião.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from backend import main


class _ThreadSincrona:
    """Roda o alvo no start(), para o teste não depender do agendamento da thread."""

    def __init__(self, target, args=(), daemon=None):
        self._target = target
        self._args = args

    def start(self):
        self._target(*self._args)


@pytest.fixture
def importacoes(tmp_path, monkeypatch):
    """Substitui _run_init por um espião e isola o estado global."""
    chamadas = []
    monkeypatch.setattr(main, "_run_init", lambda *args: chamadas.append(args))
    monkeypatch.setattr(main, "threading", SimpleNamespace(Thread=_ThreadSincrona))
    monkeypatch.setattr(main, "DB_PATH", str(tmp_path / "datasus.db"))
    monkeypatch.setitem(main._init_state, "status", "idle")
    monkeypatch.setattr(main, "INIT_DB_MAX_UF_ANO", 9)
    return chamadas


@pytest.fixture
def client():
    return TestClient(main.app)


def _post(client, **body):
    return client.post("/init-db", json=body)


def test_pedido_valido_sem_token_de_admin(client, importacoes, monkeypatch):
    monkeypatch.setattr(main, "ADMIN_TOKEN", "segredo")
    resp = _post(client, datasets=["sim_do"], years=[2020], states=["SP"])
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "started"
    assert importacoes == [(["sim_do"], [2020], ["SP"])]


def test_normaliza_e_remove_duplicados(client, importacoes):
    resp = _post(
        client, datasets=["SIM_DO", "sim_do"], years=["2020", 2020, 2021], states=["sp", "SP", " rj "]
    )
    assert resp.status_code == 200, resp.text
    assert importacoes == [(["sim_do"], [2020, 2021], ["SP", "RJ"])]


@pytest.mark.parametrize(
    "body",
    [
        {"datasets": ["sim_do"], "years": ["*"], "states": ["SP"]},
        {"datasets": ["sim_do"], "years": [2020], "states": ["*"]},
        {"datasets": ["sim_do"], "years": [2020, "*"], "states": ["SP"]},
        {"datasets": ["sim_do"], "states": ["SP"]},
        {"datasets": ["sim_do"], "years": [2020]},
        {"datasets": ["sim_do"], "years": [], "states": ["SP"]},
        {"years": [2020], "states": ["SP"]},
        {},
    ],
)
def test_recusa_curinga_e_listas_ausentes(client, importacoes, body):
    resp = _post(client, **body)
    assert resp.status_code == 400
    assert importacoes == []


@pytest.mark.parametrize(
    "body",
    [
        {"datasets": ["auxiliar"], "years": [2020], "states": ["SP"]},
        {"datasets": ["sinan"], "years": [2020], "states": ["SP"]},
        {"datasets": ["sim_do"], "years": [2020], "states": ["XX"]},
        {"datasets": ["sim_do"], "years": [2020], "states": ["S*"]},
        {"datasets": ["sim_do"], "years": [2020], "states": ["SP/../"]},
        {"datasets": ["sim_do"], "years": [1995], "states": ["SP"]},
        {"datasets": ["sim_do"], "years": [datetime.now(timezone.utc).year + 1], "states": ["SP"]},
        {"datasets": ["sim_do"], "years": ["20*"], "states": ["SP"]},
        {"datasets": ["sim_do"], "years": ["abc"], "states": ["SP"]},
        {"datasets": ["sim_do"], "years": [True], "states": ["SP"]},
        {"datasets": ["sim_do"], "years": [2020.5], "states": ["SP"]},
    ],
)
def test_recusa_valores_fora_das_listas_fechadas(client, importacoes, body):
    resp = _post(client, **body)
    assert resp.status_code == 400
    assert importacoes == []


def test_limite_de_uf_vezes_ano(client, importacoes, monkeypatch):
    monkeypatch.setattr(main, "INIT_DB_MAX_UF_ANO", 4)
    ok = _post(client, datasets=["sih_rd"], years=[2020, 2021], states=["SP", "RJ"])
    assert ok.status_code == 200, ok.text
    monkeypatch.setitem(main._init_state, "status", "idle")
    grande = _post(client, datasets=["sih_rd"], years=[2019, 2020, 2021], states=["SP", "RJ"])
    assert grande.status_code == 400
    assert "máximo" in grande.json()["detail"]
    assert len(importacoes) == 1


def test_todas_as_ufs_em_um_ano_passa_do_limite_padrao(client, importacoes):
    resp = _post(client, datasets=["sim_do"], years=[2020], states=sorted(main.UFS))
    assert resp.status_code == 400
    assert importacoes == []


def test_ibge_pop_nao_exige_uf(client, importacoes):
    resp = _post(client, datasets=["ibge_pop"], years=[2020, 2021])
    assert resp.status_code == 200, resp.text
    assert importacoes == [(["ibge_pop"], [2020, 2021], [])]


def test_pedido_em_andamento_nao_dispara_outro(client, importacoes, monkeypatch):
    monkeypatch.setitem(main._init_state, "status", "running")
    resp = _post(client, datasets=["sim_do"], years=[2020], states=["SP"])
    assert resp.json()["status"] == "running"
    assert importacoes == []
