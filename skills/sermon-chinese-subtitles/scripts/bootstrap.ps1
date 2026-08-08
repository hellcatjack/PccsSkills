param(
    [string]$EnvironmentPath = ".subtitle-skill-venv"
)

$ErrorActionPreference = "Stop"
$skillRoot = Split-Path -Parent $PSScriptRoot
$requirements = Join-Path $PSScriptRoot "requirements-core.txt"

if (-not (Test-Path -LiteralPath $EnvironmentPath)) {
    python -m venv $EnvironmentPath
}

$python = Join-Path $EnvironmentPath "Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -r $requirements

Write-Output "SUBTITLE_SKILL_ENV_READY path=$([System.IO.Path]::GetFullPath($EnvironmentPath)) skill=$skillRoot"
