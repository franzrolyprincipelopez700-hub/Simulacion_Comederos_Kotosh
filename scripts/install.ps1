$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $taskRoot
if (-not (Test-Path -LiteralPath 'backend/.venv/Scripts/python.exe')) { python -m venv backend/.venv }
if (-not (Test-Path -LiteralPath 'backend/.venv/Scripts/python.exe')) { throw 'No se creó el entorno virtual. Comprueba Python y PATH.' }
& backend/.venv/Scripts/python -m pip install -r backend/requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación Python' }
if (-not (Test-Path -LiteralPath 'backend/.env')) { Copy-Item -LiteralPath 'backend/.env.example' -Destination 'backend/.env'; Write-Host 'Edita backend/.env con tu conexión PostgreSQL y ejecuta scripts/migrate.ps1' }
Set-Location frontend
npm.cmd ci
if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación Node' }
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación del frontend' }
Set-Location $taskRoot
