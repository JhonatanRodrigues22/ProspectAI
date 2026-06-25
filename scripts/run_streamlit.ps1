$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

& ".\.venv\Scripts\python.exe" -m streamlit run "ui\streamlit_app.py"
