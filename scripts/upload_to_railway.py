"""
Script para enviar o banco de dados local para o Railway.
Executa: python scripts/upload_to_railway.py
"""
import sys
import os
from pathlib import Path

RAILWAY_URL = "https://datasus-ai-search-production.up.railway.app"
DB_PATH = str(Path(__file__).parent.parent / "data" / "datasus.db")


def main():
    if not Path(DB_PATH).exists():
        print(f"Arquivo não encontrado: {DB_PATH}")
        print("Execute primeiro: python scripts/init_local.py")
        sys.exit(1)

    size_mb = Path(DB_PATH).stat().st_size / (1024 * 1024)
    print(f"Enviando {DB_PATH} ({size_mb:.1f} MB) para {RAILWAY_URL}...")
    print("Isso pode demorar conforme o tamanho do arquivo.\n")

    try:
        import requests
    except ImportError:
        print("Erro: requests não está instalado. Execute: pip install requests")
        sys.exit(1)

    with open(DB_PATH, "rb") as f:
        resp = requests.post(
            f"{RAILWAY_URL}/upload-db",
            files={"file": ("datasus.db", f, "application/octet-stream")},
            timeout=600,
            stream=True,
        )

    if resp.status_code == 200:
        print("✅ Banco de dados enviado com sucesso!")
        print(resp.json())
    else:
        print(f"✗ Erro {resp.status_code}: {resp.text}")
        sys.exit(1)


if __name__ == "__main__":
    main()
