. (Join-Path $PSScriptRoot 'Common.ps1')

$repositoryRoot = Get-RepositoryRoot
$processFile = Assert-SafeRuntimePath (Join-Path $repositoryRoot 'tmp\dev-processes.json')
$processIdsToStop = [System.Collections.Generic.HashSet[int]]::new()

if (Test-Path -LiteralPath $processFile -PathType Leaf) {
    $processIds = Get-Content -LiteralPath $processFile -Raw | ConvertFrom-Json
    foreach ($processId in @($processIds.coreService, $processIds.agentService, $processIds.web)) {
        if ($processId) {
            [void]$processIdsToStop.Add([int]$processId)
        }
    }
}

# Conda and Windows launchers can exit after creating the actual listener. Only
# collect a replacement PID when both its command line and repository path prove
# that the listener belongs to this checkout.
$listeners = @(
    @{ Port = 8080; Marker = 'core-service-0.1.0.jar' },
    @{ Port = 8000; Marker = 'agent_service.main:app' },
    @{ Port = 5173; Marker = 'node_modules\vite' }
)
foreach ($listener in $listeners) {
    $connection = Get-NetTCPConnection -LocalPort $listener.Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $connection) {
        continue
    }
    $owner = Get-CimInstance Win32_Process -Filter "ProcessId=$($connection.OwningProcess)" -ErrorAction SilentlyContinue
    $commandLine = [string]$owner.CommandLine
    if ($commandLine -and
        $commandLine.IndexOf($repositoryRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0 -and
        $commandLine.IndexOf([string]$listener.Marker, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
        [void]$processIdsToStop.Add([int]$connection.OwningProcess)
    }
}

foreach ($processId in $processIdsToStop) {
    if (Get-Process -Id $processId -ErrorAction SilentlyContinue) {
        # A launcher can exit between the existence check and this call.
        Stop-Process -Id $processId -ErrorAction SilentlyContinue
    }
}
if (Test-Path -LiteralPath $processFile -PathType Leaf) {
    Remove-Item -LiteralPath $processFile -Force
}

$dataDirectory = Assert-SafeRuntimePath (Join-Path $repositoryRoot 'tmp\postgres-data')
if (Test-Path -LiteralPath (Join-Path $dataDirectory 'PG_VERSION')) {
    $pgCtl = Require-Command 'pg_ctl'
    & $pgCtl -D $dataDirectory status 2>$null
    if ($LASTEXITCODE -eq 0) {
        & $pgCtl -D $dataDirectory -m fast stop
    }
}

Write-Host '[OK] Local School Agent services are stopped.'
