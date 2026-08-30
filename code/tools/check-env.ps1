. (Join-Path $PSScriptRoot 'Common.ps1')

$checks = @(
    @{ Name = 'Node.js'; Command = 'node'; Arguments = @('--version'); Expected = '^v24\.19\.0$' },
    @{ Name = 'npm'; Command = 'npm'; Arguments = @('--version'); Expected = '^11\.17\.0$' },
    @{ Name = 'Python'; Command = 'python'; Arguments = @('--version'); Expected = '^Python 3\.12\.' },
    @{ Name = 'Java'; Command = 'java'; Arguments = @('-version'); Expected = '21\.0\.' },
    @{ Name = 'Maven'; Command = 'mvn'; Arguments = @('--version'); Expected = 'Apache Maven 3\.9\.' },
    @{ Name = 'PostgreSQL'; Command = 'psql'; Arguments = @('--version'); Expected = 'PostgreSQL\) 16\.' }
)

$failures = @()
foreach ($check in $checks) {
    try {
        $executable = Require-Command $check.Command
        # Java reports its version on stderr; Windows PowerShell must not turn that
        # conventional output into a terminating error during the version check.
        $previousErrorPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            $output = (& $executable @($check.Arguments) 2>&1 | Out-String).Trim()
        } finally {
            $ErrorActionPreference = $previousErrorPreference
        }
        if ($output -notmatch $check.Expected) {
            $failures += "$($check.Name): unexpected version: $output"
        } else {
            Write-Host "[OK] $($check.Name): $($output.Split([Environment]::NewLine)[0])"
        }
    } catch {
        $failures += "$($check.Name): $($_.Exception.Message)"
    }
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host '[OK] M01 development toolchain is ready.'
