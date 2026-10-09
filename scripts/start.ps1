$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pythonExe = Join-Path $taskRoot 'backend/.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Ejecuta primero scripts/install.ps1' }
foreach ($taskPort in @(8000,5174)) {
    if (Get-NetTCPConnection -LocalPort $taskPort -State Listen -ErrorAction SilentlyContinue) { throw "Puerto $taskPort ocupado. Comprueba si la aplicación ya está iniciada." }
}
$apiProcess = Start-Process -FilePath $pythonExe -ArgumentList '-m uvicorn app.api:app --host 127.0.0.1 --port 8000' -WorkingDirectory (Join-Path $taskRoot 'backend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskRoot 'backend/api.log') -RedirectStandardError (Join-Path $taskRoot 'backend/api-error.log')
$workerProcess = Start-Process -FilePath $pythonExe -ArgumentList '-u -m app.worker' -WorkingDirectory (Join-Path $taskRoot 'backend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskRoot 'backend/worker.log') -RedirectStandardError (Join-Path $taskRoot 'backend/worker-error.log')
$nodeExe = (Get-Command node.exe).Source
$vitePath = Join-Path $taskRoot 'frontend/node_modules/vite/bin/vite.js'
$frontendProcess = Start-Process -FilePath $nodeExe -ArgumentList @('"'+$vitePath+'"','--host','127.0.0.1') -WorkingDirectory (Join-Path $taskRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskRoot 'frontend/vite.log') -RedirectStandardError (Join-Path $taskRoot 'frontend/vite-error.log')
@($apiProcess.Id,$workerProcess.Id,$frontendProcess.Id) | Set-Content (Join-Path $taskRoot '.local.pid')
Write-Host 'Aplicación: http://127.0.0.1:5174 · API: http://127.0.0.1:8000/docs'
Write-Host 'Para detener: ./scripts/stop.ps1'
