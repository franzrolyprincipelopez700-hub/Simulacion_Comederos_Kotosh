$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $taskRoot
& backend/.venv/Scripts/python scripts/prepare_db.py
if ($LASTEXITCODE -ne 0) { throw 'No se pudo preparar la base. Revisa backend/.env y PostgreSQL.' }
Set-Location backend
& .venv/Scripts/python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Falló la migración' }
& .venv/Scripts/python -m app.seed
Set-Location $taskRoot
