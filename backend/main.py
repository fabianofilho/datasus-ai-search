import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging
import shutil
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from ai_engine import AIEngine
from query_executor import QueryExecutor
from data_manager import DataManager

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DATASUS AI Search API",
    description="API para pesquisa de dados de saúde do DATASUS com IA",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.getenv("DB_PATH", "data/datasus.db")


class SearchRequest(BaseModel):
    question: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: str = "gpt-4.1-mini"


class InitDBRequest(BaseModel):
    datasets: Optional[List[str]] = None


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/search")
async def search(req: SearchRequest):
    try:
        api_key = req.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=400, detail="API key não fornecida. Configure nas configurações.")

        api_base = req.api_base or os.getenv("LLM_API_BASE")

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
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    try:
        with DataManager(DB_PATH) as dm:
            dm.initialize_database(req.datasets)
            return {"status": "ok", "message": "Banco de dados inicializado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-db")
async def upload_database(file: UploadFile = File(...)):
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
