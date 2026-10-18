"""
Importa dados do DATASUS num processo separado e publica o banco por troca atômica.

Por que processo separado: o DuckDB compartilha uma única instância por arquivo
dentro de um processo, e a primeira conexão define a configuração de todas. O
servidor abre o banco em modo seguro (somente leitura, sem acesso externo); se o
datasus-db abrisse o mesmo arquivo para escrita numa thread do servidor, as
buscas passariam a falhar com "Can't open a connection to same database file with
a different configuration". Num processo à parte, cada um tem a sua instância.

Por que cópia e troca: o processo importa numa cópia do banco e, no fim, troca o
arquivo com os.replace. As buscas continuam lendo o banco antigo durante o
download e passam a ver o novo na próxima conexão. Se a importação falhar, o
banco antigo fica intacto.

Uso, de dentro do servidor ou no build da imagem:

    python src/importador.py data/datasus.db '{"sim_do": {"years": [2020], "states": ["SP"]}}'
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

IMPORTADORES = ("sim_do", "sih_rd", "sia_pa", "ibge_pop", "auxiliar")


def importar_no_arquivo(db_file: str, pedido: dict) -> None:
    """Roda o datasus-db sobre db_file. Só deve ser chamado num processo próprio."""
    sql_de_teste = os.environ.get("IMPORTADOR_SQL_DE_TESTE")
    if sql_de_teste:
        # Só para os testes: grava sem rede, pelo mesmo caminho de processo e troca.
        import duckdb

        conn = duckdb.connect(db_file)
        conn.execute(sql_de_teste)
        conn.close()
        return

    import datasus_db

    for dataset, args in pedido.items():
        if dataset not in IMPORTADORES:
            raise ValueError(f"dataset desconhecido: {dataset}")
        anos = args.get("years") or ["*"]
        ufs = args.get("states") or ["*"]
        if dataset == "sim_do":
            datasus_db.import_sim_do(db_file=db_file, years=anos, states=ufs)
        elif dataset == "sih_rd":
            datasus_db.import_sih_rd(db_file=db_file, years=anos, states=ufs)
        elif dataset == "sia_pa":
            datasus_db.import_sia_pa(db_file=db_file, years=anos, states=ufs)
        elif dataset == "ibge_pop":
            datasus_db.import_ibge_pop(db_file=db_file, years=anos)
        elif dataset == "auxiliar":
            datasus_db.import_auxiliar_tables(db_file=db_file)


def importar(db_path: str, pedido: dict, timeout: int = 3600) -> None:
    """Importa em processo separado sobre uma cópia e publica com os.replace.

    Levanta RuntimeError com a última linha de erro do processo filho se ele falhar.
    """
    destino = Path(db_path)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_name(destino.name + ".importando")
    if temporario.exists():
        temporario.unlink()
    if destino.exists():
        shutil.copy2(destino, temporario)

    processo = subprocess.run(
        [sys.executable, __file__, str(temporario), json.dumps(pedido)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if processo.returncode != 0:
        if temporario.exists():
            temporario.unlink()
        ultima = (processo.stderr.strip().splitlines() or ["falha sem mensagem"])[-1]
        raise RuntimeError(f"importação falhou: {ultima}")
    os.replace(temporario, destino)


if __name__ == "__main__":
    importar_no_arquivo(sys.argv[1], json.loads(sys.argv[2]))
