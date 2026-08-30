. (Join-Path $PSScriptRoot 'Common.ps1')

$repositoryRoot = Get-RepositoryRoot

Push-Location (Join-Path $repositoryRoot 'code\services\core-service')
try {
    & (Require-Command 'mvn') --batch-mode spotless:check test package
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

$agentPython = Join-Path $repositoryRoot 'code\services\agent-service\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $agentPython -PathType Leaf)) {
    throw 'Python virtual environment is missing. Run code/tools/install-dependencies.ps1 first.'
}
Push-Location (Join-Path $repositoryRoot 'code\services\agent-service')
try {
    & $agentPython -m ruff check .
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $agentPython -m ruff format --check .
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $agentPython -m pytest
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Push-Location (Join-Path $repositoryRoot 'code\apps\web')
try {
    & (Require-Command 'npm') run check
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & (Require-Command 'npm') run build
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & (Require-Command 'npm') run test:e2e
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Write-Host '[OK] Java, Python and Web M01 tests passed.'
