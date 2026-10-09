"""Genera una copia PostgreSQL portable y su inventario, sin exportar roles."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from database_tools import ROOT, connection, inventory, run_pg

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=Path, default=ROOT / 'database/simulador_avicola.backup')
    args = parser.parse_args()
    config = connection()
    import psycopg
    with psycopg.connect(**config) as conn:
        if conn.execute("SELECT count(*) FROM experiments WHERE status IN ('pendiente','en ejecución')").fetchone()[0]:
            raise RuntimeError('Espera a que terminen o cancela los experimentos antes de generar una copia.')
        source_major = int(conn.execute('SHOW server_version_num').fetchone()[0]) // 10000
    args.file.parent.mkdir(parents=True, exist_ok=True)
    run_pg('pg_dump', config, ['--format=custom', '--no-owner', '--no-acl', '--file', str(args.file)])
    metadata = {'created_utc': datetime.now(timezone.utc).isoformat(), 'format': 'PostgreSQL custom', 'postgresql_source_major': source_major, 'model_version': '1.0.0', **inventory(config), 'sha256': hashlib.sha256(args.file.read_bytes()).hexdigest(), 'bytes': args.file.stat().st_size}
    args.file.with_suffix('.manifest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Copia lista:', args.file.name, '-', metadata['bytes'], 'bytes; inventario y SHA-256 guardados.')

if __name__ == '__main__':
    main()
