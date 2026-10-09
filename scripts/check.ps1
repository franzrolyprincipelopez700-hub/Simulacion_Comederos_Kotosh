$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location (Join-Path $taskRoot 'backend')
& .venv/Scripts/python -m alembic current
& .venv/Scripts/python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Pruebas backend fallidas' }
Set-Location (Join-Path $taskRoot 'frontend')
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Compilación frontend fallida' }
Set-Location $taskRoot
