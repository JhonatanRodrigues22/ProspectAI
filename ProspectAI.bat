@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Preparando o ambiente pela primeira vez...
    powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\setup.ps1"
    if errorlevel 1 (
        echo.
        echo Nao foi possivel preparar o ambiente.
        pause
        exit /b 1
    )
)

".venv\Scripts\python.exe" -m launcher
if errorlevel 1 pause
