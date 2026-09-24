"""
Testes do endpoint /search: escolha de chave e URL base do LLM (SRCH-01) e
detecção de tabelas criadas em maiúsculas pelo datasus-db (SRCH-03).

Um servidor HTTP local faz o papel do provedor de LLM e registra o cabeçalho
Authorization de cada chamada, para provar qual chave saiu do backend.
"""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import duckdb
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from backend import main

SERVER_KEY = "sk-CHAVE-DO-SERVIDOR"
CLIENT_KEY = "sk-CHAVE-DO-CLIENTE"
FAKE_SQL = "SELECT COUNT(*) AS total FROM sim_do"


class FakeLLM:
    """Servidor compatível com /chat/completions que registra as chamadas."""

    def __init__(self):
        self.calls = []
        self.sql = FAKE_SQL
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
                fake.calls.append(
                    {"path": self.path, "authorization": self.headers.get("Authorization")}
                )
                system = body.get("messages", [{}])[0].get("content", "")
                content = fake.sql if "SQL" in system else "Resposta de teste."
                payload = json.dumps({
                    "id": "chatcmpl-teste",
                    "object": "chat.completion",
                    "created": 0,
                    "model": body.get("model", "teste"),
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}/v1"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def db_maiusculas(tmp_path, monkeypatch):
    """Banco com a tabela em maiúsculas, como o datasus-db cria (MAIN_TABLE = "SIM_DO")."""
    db_path = str(tmp_path / "datasus.db")
    conn = duckdb.connect(db_path)
    conn.execute("CREATE TABLE SIM_DO (DTOBITO DATE, CODMUNRES VARCHAR, CAUSABAS VARCHAR)")
    conn.execute("""
        INSERT INTO SIM_DO VALUES
        ('2020-03-15', '355030', 'A15'),
        ('2020-06-20', '355030', 'A16')
    """)
    conn.close()
    monkeypatch.setattr(main, "DB_PATH", db_path)
    return db_path


@pytest.fixture
def fake_llm(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", SERVER_KEY)
    monkeypatch.delenv("LLM_API_BASE", raising=False)
    with FakeLLM() as fake:
        yield fake


@pytest.fixture
def client():
    return TestClient(main.app)


PERGUNTA = "Quantos óbitos em 2020?"


def test_api_base_do_cliente_sem_api_key_nao_usa_chave_do_servidor(
    client, db_maiusculas, fake_llm, monkeypatch
):
    # Mesmo com a URL na allowlist, a chave do servidor nunca vai para uma base do cliente.
    monkeypatch.setattr(main, "LLM_API_BASE_ALLOWLIST", [fake_llm.base_url])
    resp = client.post("/search", json={"question": PERGUNTA, "api_base": fake_llm.base_url})
    assert resp.status_code == 400
    assert "api_key" in resp.json()["detail"]
    assert fake_llm.calls == []


def test_api_base_fora_da_allowlist_e_recusado(client, db_maiusculas, fake_llm):
    resp = client.post(
        "/search",
        json={"question": PERGUNTA, "api_key": CLIENT_KEY, "api_base": fake_llm.base_url},
    )
    assert resp.status_code == 400
    assert "api_base" in resp.json()["detail"]
    assert fake_llm.calls == []


def test_api_base_permitido_usa_chave_do_cliente(client, db_maiusculas, fake_llm, monkeypatch):
    monkeypatch.setattr(main, "LLM_API_BASE_ALLOWLIST", [fake_llm.base_url + "/"])
    resp = client.post(
        "/search",
        json={"question": PERGUNTA, "api_key": CLIENT_KEY, "api_base": fake_llm.base_url},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] == [{"total": 2}]
    assert fake_llm.calls
    assert {c["authorization"] for c in fake_llm.calls} == {f"Bearer {CLIENT_KEY}"}
    assert all(c["path"] == "/v1/chat/completions" for c in fake_llm.calls)


def test_base_do_servidor_continua_usando_chave_do_servidor(
    client, db_maiusculas, fake_llm, monkeypatch
):
    # Sem api_base do cliente, vale a configuração do operador (LLM_API_BASE + OPENAI_API_KEY).
    monkeypatch.setenv("LLM_API_BASE", fake_llm.base_url)
    resp = client.post("/search", json={"question": PERGUNTA})
    assert resp.status_code == 200, resp.text
    assert {c["authorization"] for c in fake_llm.calls} == {f"Bearer {SERVER_KEY}"}


def test_tabela_em_maiusculas_nao_pede_init(client, db_maiusculas, fake_llm, monkeypatch):
    monkeypatch.setenv("LLM_API_BASE", fake_llm.base_url)
    resp = client.post("/search", json={"question": PERGUNTA, "api_key": CLIENT_KEY})
    assert resp.status_code == 200, resp.text
    assert resp.json()["sql"] == FAKE_SQL


def test_dataset_ausente_continua_pedindo_init(client, db_maiusculas, fake_llm, monkeypatch):
    monkeypatch.setenv("LLM_API_BASE", fake_llm.base_url)
    resp = client.post(
        "/search", json={"question": "Internações hospitalares em 2020", "api_key": CLIENT_KEY}
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["missing_datasets"] == ["sih_rd"]
    assert fake_llm.calls == []


def test_allowlist_configuravel_por_env():
    assert main._parse_api_base_allowlist(None) == main.DEFAULT_LLM_API_BASE_ALLOWLIST
    assert main._parse_api_base_allowlist("") == []
    assert main._parse_api_base_allowlist(" https://a/v1 , ,https://b/v1") == [
        "https://a/v1",
        "https://b/v1",
    ]


def test_sql_malicioso_do_llm_nao_grava_arquivo(
    client, db_maiusculas, fake_llm, monkeypatch, tmp_path
):
    # SRCH-02: prompt injection que faz o LLM devolver várias instruções.
    alvo = tmp_path / "pwn.csv"
    fake_llm.sql = f"SELECT 1; COPY (SELECT 42) TO '{alvo}'"
    monkeypatch.setenv("LLM_API_BASE", fake_llm.base_url)
    resp = client.post("/search", json={"question": PERGUNTA, "api_key": CLIENT_KEY})
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] == []
    assert not alvo.exists()
