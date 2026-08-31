param(
    [string]$EnvironmentFile
)

. (Join-Path $PSScriptRoot 'Common.ps1')

$repositoryRoot = Get-RepositoryRoot
if ($EnvironmentFile) {
    Import-SchoolAgentEnvironment -EnvironmentFile $EnvironmentFile
    & (Join-Path $PSScriptRoot 'init-db.ps1') -EnvironmentFile $EnvironmentFile
} else {
    Import-SchoolAgentEnvironment
    & (Join-Path $PSScriptRoot 'init-db.ps1')
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$runtimeDirectory = Assert-SafeRuntimePath (Join-Path $repositoryRoot 'tmp')
$logDirectory = Assert-SafeRuntimePath (Join-Path $repositoryRoot 'logs')
$processFile = Join-Path $runtimeDirectory 'dev-processes.json'
New-Item -ItemType Directory -Force -Path $runtimeDirectory, $logDirectory | Out-Null

$coreJar = Join-Path $repositoryRoot 'code\services\core-service\target\core-service-0.1.0.jar'
$agentPython = Join-Path $repositoryRoot 'code\services\agent-service\.venv\Scripts\python.exe'
$viteEntry = Join-Path $repositoryRoot 'code\apps\web\node_modules\vite\bin\vite.js'
foreach ($artifact in @($coreJar, $agentPython, $viteEntry)) {
    if (-not (Test-Path -LiteralPath $artifact -PathType Leaf)) {
        throw "Missing build artifact: $artifact. Run code/tools/test-all.ps1 first."
    }
}

$javaExecutable = if ($env:JAVA_HOME) { Join-Path $env:JAVA_HOME 'bin\java.exe' } else { Require-Command 'java' }
if (-not (Test-Path -LiteralPath $javaExecutable -PathType Leaf)) {
    throw "Java executable was not found: $javaExecutable"
}
$javaProcess = Start-Process -FilePath $javaExecutable `
    -ArgumentList @('-jar', $coreJar) `
    -WorkingDirectory (Split-Path $coreJar) `
    -RedirectStandardOutput (Join-Path $logDirectory 'core-service.out.log') `
    -RedirectStandardError (Join-Path $logDirectory 'core-service.err.log') `
    -WindowStyle Hidden -PassThru

$agentProcess = Start-Process -FilePath $agentPython `
    -ArgumentList @('-m', 'uvicorn', 'agent_service.main:app', '--app-dir', (Join-Path $repositoryRoot 'code\services\agent-service\src'), '--host', '127.0.0.1', '--port', $env:SCHOOL_AGENT_AGENT_PORT) `
    -WorkingDirectory (Join-Path $repositoryRoot 'code\services\agent-service') `
    -RedirectStandardOutput (Join-Path $logDirectory 'agent-service.out.log') `
    -RedirectStandardError (Join-Path $logDirectory 'agent-service.err.log') `
    -WindowStyle Hidden -PassThru

$webProcess = Start-Process -FilePath (Require-Command 'node') `
    -ArgumentList @($viteEntry, '--host', '127.0.0.1') `
    -WorkingDirectory (Join-Path $repositoryRoot 'code\apps\web') `
    -RedirectStandardOutput (Join-Path $logDirectory 'web.out.log') `
    -RedirectStandardError (Join-Path $logDirectory 'web.err.log') `
    -WindowStyle Hidden -PassThru

@{
    coreService = $javaProcess.Id
    agentService = $agentProcess.Id
    web = $webProcess.Id
} | ConvertTo-Json | Set-Content -LiteralPath $processFile

$healthUrl = "http://127.0.0.1:$($env:SCHOOL_AGENT_CORE_PORT)/api/v1/health/system"
for ($attempt = 1; $attempt -le 30; $attempt++) {
    try {
        $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
        if ($health.success -and $health.data.status -eq 'UP') {
            Write-Host "[OK] Full health chain is ready: $healthUrl"
            Write-Host 'Web: http://127.0.0.1:5173'
            exit 0
        }
    } catch {
        # Connection failures are expected while the services are starting.
    }

    # The core endpoint can respond with DOWN before the Agent is ready. Wait
    # after every unsuccessful attempt so the retry window is truly 30 seconds.
    Start-Sleep -Seconds 1
}

Write-Warning "Services did not become healthy. Inspect logs under $logDirectory."
& (Join-Path $PSScriptRoot 'stop-dev.ps1')
throw 'School Agent services failed their startup health check.'
