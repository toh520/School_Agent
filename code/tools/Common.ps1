Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-RepositoryRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
}

function Import-SchoolAgentEnvironment {
    param(
        [string]$EnvironmentFile = (Join-Path (Get-RepositoryRoot) 'deploy\.env.local')
    )

    if (-not (Test-Path -LiteralPath $EnvironmentFile -PathType Leaf)) {
        throw "Missing environment file: $EnvironmentFile. Copy deploy/.env.example to deploy/.env.local first."
    }

    foreach ($line in Get-Content -LiteralPath $EnvironmentFile) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) {
            continue
        }

        $separator = $trimmed.IndexOf('=')
        if ($separator -lt 1) {
            throw "Invalid environment entry: $trimmed"
        }

        $name = $trimmed.Substring(0, $separator).Trim()
        $value = $trimmed.Substring($separator + 1).Trim()
        if ($name -notmatch '^SCHOOL_AGENT_[A-Z0-9_]+$') {
            throw "Unsupported environment variable: $name"
        }
        if (-not $value -or $value.StartsWith('replace_with_')) {
            throw "Environment variable $name still has an empty or placeholder value."
        }
        [Environment]::SetEnvironmentVariable($name, $value, 'Process')
    }
}

function Require-Command {
    param([Parameter(Mandatory)][string]$Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Required command '$Name' was not found. Activate the school-agent Conda environment."
    }
    return $command.Source
}

function Assert-SafeRuntimePath {
    param([Parameter(Mandatory)][string]$Path)

    $root = [IO.Path]::GetFullPath((Get-RepositoryRoot))
    $resolved = [IO.Path]::GetFullPath($Path)
    if (-not $resolved.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Runtime path must stay inside the repository: $resolved"
    }
    return $resolved
}
