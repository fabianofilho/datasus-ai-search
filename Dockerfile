FROM python:3.11-slim

WORKDIR /app

# System deps for C extensions (datasus-dbc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Banco já com um recorte de demonstração. No plano gratuito do Render o disco se
# apaga a cada reinício, e sem dados prontos a primeira busca depois de o serviço
# dormir mandava baixar do FTP do DATASUS na hora. O recorte padrão (SIM de SP em
# 2020, cerca de 26 MB e 20 s de download) cobre a pergunta de exemplo de
# tuberculose; troque por build arg ou deixe '{}' para imagem vazia.
ARG PRELOAD='{"sim_do": {"years": [2020], "states": ["SP"]}}'
RUN mkdir -p /app/data \
    && python3 -c "import duckdb; duckdb.connect('/app/data/datasus.db').close()" \
    && if [ "$PRELOAD" != "{}" ]; then python3 src/importador.py /app/data/datasus.db "$PRELOAD"; fi

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
