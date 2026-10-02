# PowerShell 5.1 / 7; ASCII source; no ExecutionPolicy/auth/config changes.
[CmdletBinding()]
param(
    [string]$CodexExe = 'codex.exe',
    [string]$PythonExe = '',
    [Parameter(Mandatory = $true)]
    [string]$DataDir,
    [switch]$Run,
    [switch]$RuntimeReviewed,
    [switch]$ExportOnly,
    [string]$PriorLedger = '',
    [switch]$AcceptUnverifiedModelAndIsolation
)
$ErrorActionPreference = 'Stop'
if ($CodexExe -eq 'codex.exe' -and -not (Get-Command codex.exe -ErrorAction SilentlyContinue)) {
    # Existing inspected desktop bundle only; Python pins both executable hashes.
    $bundledCli = Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\bin\de8a38d2100ae498\codex.exe'
    if (Test-Path -LiteralPath $bundledCli -PathType Leaf) { $CodexExe = $bundledCli }
}
$runner = Join-Path $PSScriptRoot 'cli_runner.py'
$pythonArgs = @()
if (-not $PythonExe) {
    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        $PythonExe = 'py.exe'
        $pythonArgs += '-3'
    } elseif (Get-Command python.exe -ErrorAction SilentlyContinue) {
        $PythonExe = 'python.exe'
    } else {
        throw 'Existing Python 3.9+ is required. Nothing has been installed or run.'
    }
}
$pythonArgs += @('-B', '-X', 'utf8', $runner, '--codex', $CodexExe, '--data-dir', $DataDir)
if ($Run) { $pythonArgs += '--run' }
if ($RuntimeReviewed) { $pythonArgs += '--runtime-reviewed' }
if ($ExportOnly) { $pythonArgs += '--export-only' }
if ($PriorLedger) { $pythonArgs += @('--prior-ledger', $PriorLedger) }
if ($AcceptUnverifiedModelAndIsolation) { $pythonArgs += '--accept-limitations' }
# Python passes prompt bytes directly to stdin and captures raw byte streams.
# No PowerShell native pipeline, Out-File, locale conversion or shell interpolation.
& $PythonExe @pythonArgs
if ($LASTEXITCODE -ne 0) { throw "PoC controller stopped (exit $LASTEXITCODE). See the private ledger and project export." }
