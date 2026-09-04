param([switch]$SkipIndex)

. (Join-Path $PSScriptRoot 'Common.ps1')
Import-SchoolAgentEnvironment
if ($env:SCHOOL_AGENT_DB_HOST -notin @('127.0.0.1', 'localhost')) {
    throw 'Demo restore is restricted to a local development database.'
}
$repositoryRoot = Get-RepositoryRoot
$agentPython = Join-Path $repositoryRoot 'code\services\agent-service\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $agentPython)) {
    throw 'Install project dependencies first.'
}
# Use the same Windows venv fallback as start-dev, without exposing connection secrets.
& $agentPython -c 'pass' 2>$null
if ($LASTEXITCODE -ne 0) {
    $agentPython = Require-Command 'python'
    $sitePackages = Join-Path $repositoryRoot 'code\services\agent-service\.venv\Lib\site-packages'
    $env:PYTHONPATH = if ($env:PYTHONPATH) { "$sitePackages;$($env:PYTHONPATH)" } else { $sitePackages }
}
if (-not $SkipIndex) {
    & $agentPython (Join-Path $PSScriptRoot 'm06-handoff-data.py') import `
        (Join-Path $repositoryRoot 'code\deploy\fixtures\m06-course-index.json.gz')
    if ($LASTEXITCODE -ne 0) { throw 'Index import failed; existing indexes are never overwritten.' }
}
$psql = Require-Command 'psql'
$previousPgPassword = $env:PGPASSWORD
try {
    $env:PGPASSWORD = $env:SCHOOL_AGENT_DB_PASSWORD
    & $psql -h $env:SCHOOL_AGENT_DB_HOST -p $env:SCHOOL_AGENT_DB_PORT `
        -U $env:SCHOOL_AGENT_DB_USERNAME -d $env:SCHOOL_AGENT_DB_NAME -v ON_ERROR_STOP=1 `
        -f (Join-Path $repositoryRoot 'code\deploy\fixtures\m06-demo.sql')
    if ($LASTEXITCODE -ne 0) { throw 'Demo SQL import failed.' }
} finally {
    $env:PGPASSWORD = $previousPgPassword
}
Write-Host '[OK] Local M06 demo data restored. Enable EXAMS/MASTERY consent in the UI as needed.'
