"""Prueba la copia en una base temporal propia y comprueba que no sobrescribe datos."""
import os
import subprocess
import sys
import uuid
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from database_tools import ROOT, connection, inventory

def main():
    source = connection()
    name = 'kotosh_restore_check_' + uuid.uuid4().hex[:16]
    target = {**source, 'dbname': name}
    url = make_url(os.getenv('DATABASE_URL') or __import__('dotenv').dotenv_values(ROOT/'backend/.env')['DATABASE_URL']).set(database=name)
    env = {**os.environ, 'DATABASE_URL': url.render_as_string(hide_password=False)}
    try:
        result = subprocess.run([sys.executable, str(ROOT/'scripts/restore_database.py')], env=env, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr)
        print(result.stdout.strip())
        with psycopg.connect(**target) as conn:
            invalid = conn.execute("SELECT count(*) FROM runs WHERE abs((result->'metrics'->>'balance_error')::double precision)>1e-8").fetchone()[0]
            if invalid:
                raise RuntimeError('Hay réplicas con balance inconsistente.')
        refused = subprocess.run([sys.executable, str(ROOT/'scripts/restore_database.py')], env=env, cwd=ROOT, capture_output=True, text=True)
        assert refused.returncode != 0 and 'La base destino contiene objetos' in refused.stderr
        print('Segunda restauración rechazada; datos existentes conservados.')
        smoke = subprocess.run([sys.executable, '-c', "from fastapi.testclient import TestClient; from app.api import app; c=TestClient(app); assert c.get('/api/health').status_code==200; o=c.get('/api/overview'); assert o.status_code==200; print('API sobre copia restaurada:',o.json())"], env=env, cwd=ROOT/'backend', capture_output=True, text=True)
        if smoke.returncode:
            raise RuntimeError(smoke.stderr)
        print(smoke.stdout.strip())
        print('Inventario verificado:', inventory(target)['rows'])
    finally:
        # Solo la base de nombre único creada por esta comprobación.
        with psycopg.connect(**{**source, 'dbname':'postgres'}, autocommit=True) as conn:
            conn.execute(sql.SQL('DROP DATABASE IF EXISTS {}').format(sql.Identifier(name)))

if __name__ == '__main__':
    main()
