"""Conexión y utilidades PostgreSQL sin credenciales en argumentos."""
import os
import shutil
import subprocess
from pathlib import Path
from dotenv import dotenv_values
from sqlalchemy.engine import make_url
import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
TABLES = ['alembic_version', 'scenarios', 'scenario_versions', 'experiments', 'runs', 'run_details', 'datasets', 'observations', 'validation_records', 'workspace_settings']

def connection():
    value = os.getenv('DATABASE_URL') or dotenv_values(ROOT / 'backend/.env').get('DATABASE_URL')
    if not value:
        raise RuntimeError('Configura DATABASE_URL en backend/.env.')
    url = make_url(value)
    if not url.drivername.startswith('postgresql') or not url.database:
        raise RuntimeError('DATABASE_URL debe indicar una base PostgreSQL.')
    return dict(host=url.host or 'localhost', port=url.port or 5432, user=url.username, password=url.password, dbname=url.database)

def executable(name):
    found = shutil.which(name)
    if found:
        return found
    folder = os.getenv('POSTGRES_BIN')
    if folder and (Path(folder) / (name + '.exe')).is_file():
        return str(Path(folder) / (name + '.exe'))
    candidate = Path('C:/Program Files/PostgreSQL/18/bin') / (name + '.exe')
    if candidate.is_file():
        return str(candidate)
    raise RuntimeError('No se encuentra ' + name + '. Agrega PostgreSQL/bin al PATH o define POSTGRES_BIN.')

def run_pg(name, config, extra):
    env = os.environ.copy()
    if config.get('password') is not None:
        env['PGPASSWORD'] = config['password']
    args = [executable(name), '--host', config['host'], '--port', str(config['port']), '--username', config['user'], '--no-password', '--dbname', config['dbname'], *extra]
    result = subprocess.run(args, env=env, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(name + ' falló. Revisa conexión, permisos y versión PostgreSQL.\n' + result.stderr)

def inventory(config):
    with psycopg.connect(**config) as conn:
        counts = {table: conn.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table))).fetchone()[0] for table in TABLES}
        revision = conn.execute('SELECT version_num FROM alembic_version').fetchone()[0]
    return {'revision': revision, 'rows': counts}

def prepare(config):
    with psycopg.connect(**{**config, 'dbname': 'postgres'}, autocommit=True) as conn:
        if not conn.execute('SELECT 1 FROM pg_database WHERE datname=%s', (config['dbname'],)).fetchone():
            conn.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(config['dbname'])))

def assert_empty(config):
    with psycopg.connect(**config) as conn:
        existing = conn.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname NOT LIKE 'pg_toast%' AND c.relkind IN ('r','p','v','m','S','f')").fetchone()[0]
        if existing:
            raise RuntimeError('La base destino contiene objetos. Elige una base nueva y vacía en backend/.env; no se sobrescribe información.')
