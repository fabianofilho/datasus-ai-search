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

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
