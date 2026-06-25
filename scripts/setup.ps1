$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements-dev.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

Write-Host "Ambiente preparado."
Write-Host "Execute: .\.venv\Scripts\python.exe -m launcher"
Write-Host "Ou dê duplo clique em ProspectAI.bat."
