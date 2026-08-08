param(
    [switch]$IncludeOptional
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

foreach ($commandName in @('ffmpeg', 'ffprobe')) {
    if (-not (Get-Command $commandName -ErrorAction SilentlyContinue)) {
        throw "Required command is unavailable: $commandName"
    }
}

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$venvPath = Join-Path $projectRoot '.audio-skill-venv'
$venvPython = Join-Path $venvPath 'Scripts\python.exe'

if (-not (Test-Path -LiteralPath $venvPython)) {
    python -m venv $venvPath
}

& $venvPython -m pip install --disable-pip-version-check -r (Join-Path $PSScriptRoot 'requirements-core.txt')

if ($IncludeOptional) {
    & $venvPython -m pip install --disable-pip-version-check -r (Join-Path $PSScriptRoot 'requirements-optional.txt')
}

& $venvPython -c "import sys; print(sys.executable)"
