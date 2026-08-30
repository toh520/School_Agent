. (Join-Path $PSScriptRoot 'Common.ps1')

$repositoryRoot = Get-RepositoryRoot
& (Join-Path $PSScriptRoot 'check-env.ps1')
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$webDirectory = Join-Path $repositoryRoot 'code\apps\web'
Push-Location $webDirectory
try {
    if (Test-Path -LiteralPath (Join-Path $webDirectory 'package-lock.json')) {
        & (Require-Command 'npm') ci
    } else {
        & (Require-Command 'npm') install
    }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & (Require-Command 'npx') playwright install chromium
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

$agentDirectory = Join-Path $repositoryRoot 'code\services\agent-service'
$virtualEnvironment = Join-Path $agentDirectory '.venv'
if (-not (Test-Path -LiteralPath $virtualEnvironment)) {
    & (Require-Command 'python') -m venv $virtualEnvironment
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
$agentPython = Join-Path $virtualEnvironment 'Scripts\python.exe'
& $agentPython -m pip install --upgrade 'pip==26.2'
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $agentPython -m pip install --requirement (Join-Path $agentDirectory 'requirements.lock')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $agentPython -m pip install --no-deps --editable $agentDirectory
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$coreDirectory = Join-Path $repositoryRoot 'code\services\core-service'
Push-Location $coreDirectory
try {
    & (Require-Command 'mvn') --batch-mode dependency:go-offline
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Write-Host '[OK] Project dependencies are installed.'
