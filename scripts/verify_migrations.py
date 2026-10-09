"""Test upgrade on a new, uniquely named temporary PostgreSQL database."""
import os,sys,uuid,subprocess
from pathlib import Path
import psycopg
from psycopg import sql
from dotenv import dotenv_values
from sqlalchemy.engine import make_url
root=Path(__file__).resolve().parents[1];url=make_url(dotenv_values(root/'backend/.env')['DATABASE_URL'])
temporary='kotosh_test_migrations_'+uuid.uuid4().hex
admin=url.set(drivername='postgresql',database='postgres').render_as_string(hide_password=False)
with psycopg.connect(admin,autocommit=True) as connection:
    connection.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(temporary)))
    try:
        child_env=dict(os.environ,DATABASE_URL=url.set(database=temporary).render_as_string(hide_password=False))
        subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=root/'backend',env=child_env,check=True)
        native=url.set(drivername='postgresql',database=temporary).render_as_string(hide_password=False)
        with psycopg.connect(native) as test_connection:
            assert test_connection.execute('SELECT version_num FROM alembic_version').fetchone()[0]=='003'
            assert test_connection.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'").fetchone()[0]==10
        print('Migraciones 001, 002 y 003 verificadas en PostgreSQL vacío; 10 tablas presentes.')
    finally:
        # Only the exact database created in this invocation may be removed.
        assert temporary.startswith('kotosh_test_migrations_') and len(temporary)==55
        connection.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(temporary)))
