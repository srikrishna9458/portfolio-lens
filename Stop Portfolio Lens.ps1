$projectRoot = $PSScriptRoot
$runtimeFolder = Join-Path $projectRoot 'runtime'
foreach ($serviceName in @('dashboard','model')) {
    $pidFile = Join-Path $runtimeFolder ($serviceName + '.pid')
    if (Test-Path -LiteralPath $pidFile) {
        $servicePid = [int](Get-Content -LiteralPath $pidFile)
        $serviceProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$servicePid" -ErrorAction SilentlyContinue
        if ($serviceProcess -and $serviceProcess.CommandLine.Contains($projectRoot)) {
            Stop-Process -Id $servicePid -ErrorAction SilentlyContinue
        }
    }
}
