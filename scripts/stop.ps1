$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pidFile = Join-Path $taskRoot '.local.pid'
if (Test-Path -LiteralPath $pidFile) {
    foreach ($savedPid in Get-Content -LiteralPath $pidFile) {
        $ownedProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$savedPid" -ErrorAction SilentlyContinue
        if ($ownedProcess -and $ownedProcess.CommandLine -and ($ownedProcess.CommandLine.Contains($taskRoot) -or $ownedProcess.CommandLine.Contains('app.worker') -or $ownedProcess.CommandLine.Contains('uvicorn app.api:app'))) {
            $processInventory = Get-CimInstance Win32_Process
            $ownedTree = [System.Collections.Generic.List[int]]::new()
            $ownedTree.Add([int]$savedPid)
            for ($treeIndex=0; $treeIndex -lt $ownedTree.Count; $treeIndex++) {
                foreach ($childProcess in $processInventory | Where-Object ParentProcessId -eq $ownedTree[$treeIndex]) { $ownedTree.Add([int]$childProcess.ProcessId) }
            }
            for ($treeIndex=$ownedTree.Count-1; $treeIndex -ge 0; $treeIndex--) { Stop-Process -Id $ownedTree[$treeIndex] -ErrorAction SilentlyContinue }
        }
    }
    Remove-Item -LiteralPath $pidFile
}
Write-Host 'Procesos iniciados por el script detenidos. Un trabajo interrumpido podrá reintentarse desde el historial.'
