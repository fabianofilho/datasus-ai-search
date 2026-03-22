"""
Script para inicializar o banco de dados DATASUS localmente.
Executa: python scripts/init_local.py
"""
import os
import sys
import time
from pathlib import Path

# Garante que o src/ está no path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

DB_PATH = str(Path(__file__).parent.parent / "data" / "datasus.db")


def main():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  DATASUS AI Search — Inicialização Local do Banco de Dados")
    print("=" * 60)
    print(f"\nArquivo: {DB_PATH}")
    print("\nDatasets disponíveis:")
    print("  1. sim_do   — Mortalidade (SIM/DO)")
    print("  2. sih_rd   — Internações (SIH/RD)")
    print("  3. sia_pa   — Ambulatorial (SIA/PA)")
    print("  4. ibge_pop — População (IBGE)")
    print("  5. auxiliar — Tabelas auxiliares")
    print("  0. Todos (pode demorar bastante e ocupar vários GB)\n")

    escolha = input("Quais datasets importar? (ex: 1,4 ou 0 para todos): ").strip()

    mapa = {
        "1": "sim_do",
        "2": "sih_rd",
        "3": "sia_pa",
        "4": "ibge_pop",
        "5": "auxiliar",
    }

    if escolha == "0":
        datasets = list(mapa.values())
    else:
        datasets = [mapa[c.strip()] for c in escolha.split(",") if c.strip() in mapa]

    if not datasets:
        print("Nenhum dataset selecionado.")
        sys.exit(1)

    print(f"\nImportando: {', '.join(datasets)}")
    print("Isso pode demorar alguns minutos...\n")

    try:
        import datasus_db
    except ImportError:
        print("Erro: datasus-db não está instalado.")
        print("Execute: pip install datasus-db")
        sys.exit(1)

    import duckdb

    for dataset in datasets:
        print(f"⏳ Importando {dataset}...", end="", flush=True)
        t0 = time.time()
        try:
            if dataset == "sim_do":
                datasus_db.import_sim_do(db_file=DB_PATH)
            elif dataset == "sih_rd":
                datasus_db.import_sih_rd(db_file=DB_PATH)
            elif dataset == "sia_pa":
                datasus_db.import_sia_pa(db_file=DB_PATH)
            elif dataset == "ibge_pop":
                datasus_db.import_ibge_pop(db_file=DB_PATH)
            elif dataset == "auxiliar":
                datasus_db.import_auxiliar_tables(db_file=DB_PATH)
            elapsed = time.time() - t0
            print(f" ✓ ({elapsed:.0f}s)")
        except Exception as e:
            print(f" ✗ Erro: {e}")

    # Mostra tamanho do arquivo gerado
    size_mb = Path(DB_PATH).stat().st_size / (1024 * 1024)
    print(f"\n✅ Banco de dados criado: {DB_PATH} ({size_mb:.1f} MB)")

    # Verifica tabelas
    conn = duckdb.connect(DB_PATH, read_only=True)
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
    ).fetchall()
    conn.close()
    print(f"   Tabelas: {', '.join(t[0] for t in tables)}")
    print("\nPróximo passo: execute python scripts/upload_to_railway.py")


if __name__ == "__main__":
    main()
