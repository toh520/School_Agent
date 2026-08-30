. (Join-Path $PSScriptRoot 'Common.ps1')

$repositoryRoot = Get-RepositoryRoot
$processFile = Assert-SafeRuntimePath (Join-Path $repositoryRoot 'tmp\dev-processes.json')
if (Test-Path -LiteralPath $processFile -PathType Leaf) {
    $processIds = Get-Content -LiteralPath $processFile -Raw | ConvertFrom-Json
    foreach ($processId in @($processIds.coreService, $processIds.agentService, $processIds.web)) {
        if ($processId -and (Get-Process -Id $processId -ErrorAction SilentlyContinue)) {
            Stop-Process -Id $processId
        }
    }
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

Write-Host '[OK] Local M01 services are stopped.'
