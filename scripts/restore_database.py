"""Restaura exclusivamente en una base vacía configurada por el usuario."""
import argparse
import hashlib
import json
from pathlib import Path
from database_tools import ROOT, connection, prepare, assert_empty, inventory, run_pg

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=Path, default=ROOT / 'database/simulador_avicola.backup')
    args = parser.parse_args()
    if not args.file.is_file():
        raise RuntimeError('No existe la copia indicada.')
    manifest_file = args.file.with_suffix('.manifest.json')
    expected = json.loads(manifest_file.read_text(encoding='utf-8')) if manifest_file.is_file() else None
    if expected and hashlib.sha256(args.file.read_bytes()).hexdigest() != expected['sha256']:
        raise RuntimeError('La copia no coincide con su SHA-256. Descárgala nuevamente.')
    config = connection()
    prepare(config)
    assert_empty(config)
    run_pg('pg_restore', config, ['--no-owner', '--no-acl', '--single-transaction', '--exit-on-error', str(args.file)])
    restored = inventory(config)
    if expected and (restored['rows'] != expected['rows'] or restored['revision'] != expected['revision']):
        raise RuntimeError('El inventario restaurado no coincide con la copia. Revisa la restauración antes de iniciar.')
    print('Restauración comprobada. Revisión:', restored['revision'], '- réplicas:', restored['rows']['runs'])

if __name__ == '__main__':
    main()
