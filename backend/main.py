import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging
import re
import shutil
import threading
import secrets
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from ai_engine import AIEngine
from query_executor import QueryExecutor, connect_read_only
from data_manager import DataManager

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DATASUS AI Search API",
    description="API para pesquisa de dados de saúde do DATASUS com IA",
    version="1.0.0"
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")


def require_admin(authorization: Optional[str] = Header(None)):
    if not ADMIN_TOKEN:
        raise HTTPException(status_code=503, detail="Admin token not configured")
    if authorization != f"Bearer {ADMIN_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

DB_PATH = os.getenv("DB_PATH", "data/datasus.db")

# URLs base de LLM que o cliente pode escolher em /search. A chave do servidor
# (OPENAI_API_KEY) nunca é enviada para uma URL base vinda da requisição.
# Configurável por LLM_API_BASE_ALLOWLIST (lista separada por vírgula; vazio
# desliga a escolha de URL base pelo cliente).
DEFAULT_LLM_API_BASE_ALLOWLIST = [
    "https://api.groq.com/openai/v1",
    "https://api.openai.com/v1",
    "https://generativelanguage.googleapis.com/v1beta/openai/",
    "https://api.anthropic.com/v1/",
]


def _parse_api_base_allowlist(raw: Optional[str]) -> List[str]:
    if raw is None:
        return list(DEFAULT_LLM_API_BASE_ALLOWLIST)
    return [item.strip() for item in raw.split(",") if item.strip()]


LLM_API_BASE_ALLOWLIST = _parse_api_base_allowlist(os.getenv("LLM_API_BASE_ALLOWLIST"))


def _normalize_api_base(url: str) -> str:
    return url.strip().rstrip("/").lower()


def resolve_llm_credentials(req_api_key: Optional[str], req_api_base: Optional[str]):
    """Define chave e URL base do LLM para uma requisição de /search.

    Se o cliente enviar api_base, exige a api_key da própria requisição e só
    aceita URLs da allowlist. Sem api_base do cliente, usa a configuração do
    servidor (LLM_API_BASE, OPENAI_API_KEY) ou detecta o provedor pela chave.
    """
    if req_api_base:
        if not req_api_key:
            raise HTTPException(
                status_code=400,
                detail="Ao informar api_base, envie também a api_key do provedor.",
            )
        wanted = _normalize_api_base(req_api_base)
        for allowed in LLM_API_BASE_ALLOWLIST:
            if _normalize_api_base(allowed) == wanted:
                return req_api_key, allowed
        raise HTTPException(
            status_code=400,
            detail="api_base não permitido. Use um dos provedores aceitos pelo servidor.",
        )

    api_key = req_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key não fornecida. Configure nas configurações.")

    api_base = os.getenv("LLM_API_BASE")

    # Auto-detect provider from API key if base URL not provided
    if not api_base:
        if api_key.startswith("gsk_"):
            api_base = "https://api.groq.com/openai/v1"
        elif api_key.startswith("AIza"):
            api_base = "https://generativelanguage.googleapis.com/v1beta/openai/"
        elif api_key.startswith("sk-ant-"):
            api_base = "https://api.anthropic.com/v1/"

    return api_key, api_base


# Mapeamento de datasets para tabelas e palavras-chave
DATASET_TABLES = {
    "sim_do": ["sim_do"],
    "sih_rd": ["sih_rd"],
    "sia_pa": ["sia_pa"],
    "ibge_pop": ["ibge_pop"],
}

DATASET_KEYWORDS = {
    "sim_do": ["mort", "óbito", "obito", "morte", "falec", "sim", "causa", "bito"],
    "sih_rd": ["internaç", "internac", "hospital", "sih", "aih", "leito", "cirurgia", "alta"],
    "sia_pa": ["ambulat", "consulta", "procedimento", "sia", "atenção básica", "atencao basica"],
    "ibge_pop": ["populaç", "populac", "ibge", "habitant", "censo", "demográf", "demograf"],
}


def detect_datasets_from_question(question: str) -> list:
    """Detecta quais datasets são necessários para responder a pergunta."""
    q = question.lower()
    needed = []
    for dataset, keywords in DATASET_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            needed.append(dataset)
    return needed or ["sim_do"]  # default para mortalidade se não detectar


def detect_years_from_question(question: str) -> list:
    """Extrai anos mencionados na pergunta (ex: 2019, 2020)."""
    import re
    years = re.findall(r'\b(19[89]\d|20[012]\d)\b', question)
    return [int(y) for y in years] if years else ["*"]


UFS = {"AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS",
       "MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC",
       "SP","SE","TO"}


def detect_states_from_question(question: str) -> list:
    """Extrai siglas de estados mencionados na pergunta."""
    found = re.findall(r'\b([A-Z]{2})\b', question.upper())
    matched = [s for s in found if s in UFS]
    return matched if matched else ["*"]


def get_existing_tables(db_path: str) -> list:
    """Retorna as tabelas que existem no banco de dados."""
    from pathlib import Path
    if not Path(db_path).exists():
        return []
    try:
        # Mesma config do QueryExecutor: o DuckDB compartilha a instância do
        # arquivo no processo e a primeira conexão define a config de todas.
        conn = connect_read_only(db_path)
        tables = [r[0] for r in conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        ).fetchall()]
        conn.close()
        return tables
    except Exception:
        return []


# Limites do /init-db. O endpoint fica aberto porque o front público baixa
# dados sob demanda (DownloadBanner), então cada pedido é validado contra listas
# fechadas: datasets conhecidos, UFs, anos entre INIT_DB_ANO_MIN e o ano atual,
# sem '*' e com no máximo INIT_DB_MAX_UF_ANO combinações de UF x ano.
INIT_DB_DATASETS = ["sim_do", "sih_rd", "sia_pa", "ibge_pop"]
INIT_DB_DATASETS_POR_UF = {"sim_do", "sih_rd", "sia_pa"}  # ibge_pop é nacional
INIT_DB_ANO_MIN = 1996  # SIM com CID-10 começa em 1996; SIH e SIA, em 2008
# Padrão 9: uma região inteira (o Nordeste tem 9 UFs) em um ano.
INIT_DB_MAX_UF_ANO = int(os.getenv("INIT_DB_MAX_UF_ANO", "9"))


# Estado global da inicialização do banco
_init_state = {
    "status": "idle",       # idle | running | done | error
    "current": "",          # dataset atual
    "completed": [],        # datasets concluídos
    "error": "",
}
_init_lock = threading.Lock()


def _run_init(datasets: List[str], years=None, states=None):
    global _init_state
    import datasus_db

    y = years or ["*"]
    s = states or ["*"]

    with _init_lock:
        _init_state.update({"status": "running", "completed": [], "error": "", "years": y, "states": s})

    try:
        for dataset in datasets:
            with _init_lock:
                _init_state["current"] = dataset
            logger.info(f"Importando {dataset} anos={y} estados={s}...")
            if dataset == "sim_do":
                datasus_db.import_sim_do(db_file=DB_PATH, years=y, states=s)
            elif dataset == "sih_rd":
                datasus_db.import_sih_rd(db_file=DB_PATH, years=y, states=s)
            elif dataset == "sia_pa":
                datasus_db.import_sia_pa(db_file=DB_PATH, years=y, states=s)
            elif dataset == "ibge_pop":
                datasus_db.import_ibge_pop(db_file=DB_PATH, years=y)
            elif dataset == "auxiliar":
                datasus_db.import_auxiliar_tables(db_file=DB_PATH)
            with _init_lock:
                _init_state["completed"].append(dataset)
            logger.info(f"✓ {dataset} importado")

        with _init_lock:
            _init_state.update({"status": "done", "current": ""})
    except Exception as e:
        logger.error(f"Erro ao inicializar DB: {e}")
        with _init_lock:
            _init_state.update({"status": "error", "error": str(e), "current": ""})


class SearchRequest(BaseModel):
    question: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: str = "llama-3.3-70b-versatile"


class InitDBRequest(BaseModel):
    datasets: Optional[List[str]] = None
    years: Optional[List] = None
    states: Optional[List[str]] = None


def validate_init_request(req: InitDBRequest):
    """Valida datasets, anos e UFs do /init-db e devolve as listas normalizadas.

    Recusa '*' e listas vazias, valores fora das listas fechadas e pedidos com
    mais de INIT_DB_MAX_UF_ANO combinações de UF x ano.
    """
    def recusar(mensagem: str):
        raise HTTPException(status_code=400, detail=mensagem)

    if not req.datasets:
        recusar(f"Informe os datasets: {', '.join(INIT_DB_DATASETS)}.")
    datasets = []
    for item in req.datasets:
        nome = item.strip().lower()
        if nome not in INIT_DB_DATASETS:
            recusar(f"Dataset não permitido: {item}. Use: {', '.join(INIT_DB_DATASETS)}.")
        if nome not in datasets:
            datasets.append(nome)

    ano_max = datetime.now(timezone.utc).year
    if not req.years or "*" in req.years:
        recusar("Informe os anos explicitamente; '*' (todos os anos) não é aceito.")
    anos = []
    for item in req.years:
        if isinstance(item, bool) or not (
            isinstance(item, int) or (isinstance(item, str) and re.fullmatch(r"[0-9]{4}", item.strip()))
        ):
            recusar(f"Ano inválido: {item}.")
        ano = int(item)
        if not INIT_DB_ANO_MIN <= ano <= ano_max:
            recusar(f"Ano fora do intervalo {INIT_DB_ANO_MIN} a {ano_max}: {item}.")
        if ano not in anos:
            anos.append(ano)

    ufs = []
    if any(d in INIT_DB_DATASETS_POR_UF for d in datasets):
        if not req.states or "*" in req.states:
            recusar("Informe as UFs explicitamente; '*' (todos os estados) não é aceito.")
        for item in req.states:
            uf = item.strip().upper()
            if uf not in UFS:
                recusar(f"UF inválida: {item}.")
            if uf not in ufs:
                ufs.append(uf)

    combinacoes = len(anos) * max(len(ufs), 1)
    if combinacoes > INIT_DB_MAX_UF_ANO:
        recusar(
            f"Pedido grande demais: {combinacoes} combinações de UF x ano; "
            f"o máximo por pedido é {INIT_DB_MAX_UF_ANO}."
        )
    return datasets, anos, ufs


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/search")
async def search(req: SearchRequest):
    try:
        api_key, api_base = resolve_llm_credentials(req.api_key, req.api_base)

        # Verificar se os datasets necessários estão disponíveis
        needed = detect_datasets_from_question(req.question)
        years = detect_years_from_question(req.question)
        states = detect_states_from_question(req.question)
        # O datasus-db cria as tabelas em maiúsculas (SIM_DO, SIH_RD...), então
        # a comparação ignora a caixa, como o próprio DuckDB faz no SQL.
        existing = {t.lower() for t in get_existing_tables(DB_PATH)}
        missing = [d for d in needed if d.lower() not in existing]
        if missing:
            raise HTTPException(
                status_code=422,
                detail={
                    "needs_init": True,
                    "missing_datasets": missing,
                    "years": years,
                    "states": states,
                    "message": f"Dados necessários não encontrados: {', '.join(missing)}",
                }
            )

        with AIEngine(
            api_key=api_key,
            api_base=api_base,
            model=req.model,
            db_path=DB_PATH,
        ) as engine:
            question, sql, answer = engine.answer_question(req.question)

            data = []
            columns = []
            row_count = 0
            try:
                with QueryExecutor(DB_PATH) as executor:
                    df = executor.execute(sql)
                    data = df.head(100).to_dict(orient="records")
                    columns = list(df.columns)
                    row_count = len(df)
            except Exception as e:
                logger.warning(f"Erro ao obter dados brutos: {e}")

            return {
                "question": question,
                "sql": sql,
                "answer": answer,
                "data": data,
                "columns": columns,
                "row_count": row_count,
            }

    except HTTPException:
        raise
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar a consulta.")


@app.get("/tables")
async def list_tables():
    try:
        with QueryExecutor(DB_PATH) as executor:
            tables = executor.list_tables()
            schemas = {}
            for table in tables:
                schemas[table] = executor.get_table_schema(table)
            return {"tables": tables, "schemas": schemas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/init-db")
async def init_database(req: InitDBRequest):
    """Baixa dados do DATASUS sob demanda, dentro dos limites INIT_DB_*.

    Não exige token de admin porque o front público usa este endpoint; por isso
    datasets, anos e UFs são obrigatórios e validados em validate_init_request.
    """
    with _init_lock:
        if _init_state["status"] == "running":
            return {"status": "running", "message": "Inicialização já em andamento"}

    datasets, years, states = validate_init_request(req)
    from pathlib import Path
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    t = threading.Thread(target=_run_init, args=(datasets, years, states), daemon=True)
    t.start()
    return {"status": "started", "message": f"Inicialização iniciada para: {', '.join(datasets)}"}


@app.get("/init-db/status")
async def init_db_status():
    with _init_lock:
        state = dict(_init_state)
    return state


@app.post("/upload-db")
async def upload_database(file: UploadFile = File(...), _=Depends(require_admin)):
    """Recebe um arquivo datasus.db e substitui o banco de dados atual."""
    try:
        import os
        from pathlib import Path
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        tmp_path = DB_PATH + ".tmp"
        with open(tmp_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)
        os.replace(tmp_path, DB_PATH)
        size_mb = Path(DB_PATH).stat().st_size / (1024 * 1024)
        return {"status": "ok", "size_mb": round(size_mb, 1), "message": "Banco de dados atualizado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
