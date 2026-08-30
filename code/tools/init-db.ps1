param(
    [string]$EnvironmentFile
)

. (Join-Path $PSScriptRoot 'Common.ps1')

$repositoryRoot = Get-RepositoryRoot
if ($EnvironmentFile) {
    Import-SchoolAgentEnvironment -EnvironmentFile $EnvironmentFile
} else {
    Import-SchoolAgentEnvironment
}

$initdb = Require-Command 'initdb'
$pgCtl = Require-Command 'pg_ctl'
$createdb = Require-Command 'createdb'
$psql = Require-Command 'psql'

$dataDirectory = Assert-SafeRuntimePath (Join-Path $repositoryRoot 'tmp\postgres-data')
$logDirectory = Assert-SafeRuntimePath (Join-Path $repositoryRoot 'logs')
$databaseLog = Join-Path $logDirectory 'postgres.log'
$passwordFile = Assert-SafeRuntimePath (Join-Path $repositoryRoot 'tmp\postgres-init-password.txt')
$databaseName = $env:SCHOOL_AGENT_DB_NAME
$databaseUser = $env:SCHOOL_AGENT_DB_USERNAME
$databasePort = $env:SCHOOL_AGENT_DB_PORT

if ($databaseName -notmatch '^[a-z][a-z0-9_]{0,62}$' -or $databaseUser -notmatch '^[a-z][a-z0-9_]{0,62}$') {
    throw 'Database name and username must use lowercase letters, digits and underscores.'
}
if ([int]$databasePort -lt 1024 -or [int]$databasePort -gt 65535) {
    throw 'Database port must be between 1024 and 65535.'
}

New-Item -ItemType Directory -Force -Path (Split-Path $dataDirectory), $logDirectory | Out-Null
if (-not (Test-Path -LiteralPath (Join-Path $dataDirectory 'PG_VERSION'))) {
    try {
        Set-Content -LiteralPath $passwordFile -Value $env:SCHOOL_AGENT_DB_PASSWORD -NoNewline
        & $initdb -D $dataDirectory -U $databaseUser --pwfile=$passwordFile --auth-local=trust --auth-host=scram-sha-256 --encoding=UTF8
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } finally {
        if (Test-Path -LiteralPath $passwordFile) {
            Remove-Item -LiteralPath $passwordFile -Force
        }
    }
}

& $pgCtl -D $dataDirectory status 2>$null
if ($LASTEXITCODE -ne 0) {
    & $pgCtl -D $dataDirectory -l $databaseLog -o "-p $databasePort -h 127.0.0.1" start
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$previousPgPassword = $env:PGPASSWORD
try {
    $env:PGPASSWORD = $env:SCHOOL_AGENT_DB_PASSWORD
    $queryOutput = & $psql -h 127.0.0.1 -p $databasePort -U $databaseUser -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$databaseName'"
    if ($LASTEXITCODE -ne 0) {
        throw 'Unable to query the local PostgreSQL instance.'
    }
    $exists = if ($null -eq $queryOutput) { '' } else { ($queryOutput | Out-String).Trim() }
    if ($exists -ne '1') {
        & $createdb -h 127.0.0.1 -p $databasePort -U $databaseUser $databaseName
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
} finally {
    $env:PGPASSWORD = $previousPgPassword
}

Write-Host "[OK] PostgreSQL is ready at 127.0.0.1:$databasePort/$databaseName."
