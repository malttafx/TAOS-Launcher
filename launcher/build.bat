@echo off
REM --- TAOS Launcher build -------------------------------------------
REM Run from this folder on a Windows machine with Python 3.11+ installed.
REM Produces dist\TAOS_Launcher.exe (single file, Python bundled inside).
REM The version comes from launcher\__init__.py - bump it with
REM   python bump_version.py 1.3.2      (or just run release.bat 1.3.2)

setlocal
cd /d "%~dp0"

echo [1/5] Creating build venv...
if not exist .venv (python -m venv .venv || goto :err)
call .venv\Scripts\activate.bat

echo [2/5] Installing build deps...
python -m pip install --quiet PySide6 pyinstaller pillow || goto :err

echo [3/5] Converting logo to .ico...
python make_ico.py || goto :err

echo [4/5] Stamping version...
python make_version_info.py || goto :err

echo [5/5] Building exe...
pyinstaller --noconfirm --clean --onefile --noconsole ^
  --name TAOS_Launcher ^
  --icon icons\taos.ico ^
  --version-file version_info.txt ^
  --add-data "icons;icons" ^
  main.py || goto :err

echo.
echo Done: dist\TAOS_Launcher.exe
echo Deploy: run release.bat, or copy the exe by hand to BOTH
echo         ^<TAOSDRIVE^>\pipeline\launcher\dist\TAOS_Launcher.exe
echo         ^<TAOSDRIVE^>\pipeline\TAOS_Launcher.exe
exit /b 0

:err
echo BUILD FAILED - see output above.
exit /b 1
