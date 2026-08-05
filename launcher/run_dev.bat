@echo off
REM ── TAOS Launcher: dev run ─────────────────────────────────────────
REM Double-click to test the launcher without building the exe.
REM First run sets up a local Python environment (takes a minute); after
REM that it starts instantly. Nothing is installed system-wide.

setlocal
cd /d "%~dp0"

if not exist .venv (
    echo First run: setting up local environment, give it a minute...
    python -m venv .venv || goto :err
)
call .venv\Scripts\activate.bat

python -c "import PySide6" 2>NUL
if errorlevel 1 (
    echo Installing UI library...
    pip install --quiet PySide6 || goto :err
)

python main.py
exit /b 0

:err
echo.
echo Setup failed. Most likely Python is missing or too new for PySide6.
echo Ask Claude — mention what the message above says.
pause
exit /b 1
