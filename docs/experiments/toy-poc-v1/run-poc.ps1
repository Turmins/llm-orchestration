# PowerShell 5.1 / 7; ASCII source; no ExecutionPolicy/auth/config changes.
[CmdletBinding()]
param(
    [string]$CodexExe = 'codex.exe',
    [string]$PythonExe = '',
    [switch]$Run,
    [switch]$AcceptUnverifiedModelAndIsolation,
    [switch]$ForcedHandoffOnly
)
$ErrorActionPreference = 'Stop'
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
$pythonArgs += @('-X', 'utf8', $runner, '--codex', $CodexExe)
if ($Run) { $pythonArgs += '--run' }
if ($AcceptUnverifiedModelAndIsolation) { $pythonArgs += '--accept-limitations' }
if ($ForcedHandoffOnly) { $pythonArgs += '--forced-handoff-only' }
# Python passes prompt bytes directly to stdin and captures raw byte streams.
# No PowerShell native pipeline, Out-File, locale conversion or shell interpolation.
& $PythonExe @pythonArgs
if ($LASTEXITCODE -ne 0) { throw "PoC controller stopped (exit $LASTEXITCODE). See its run directory." }
