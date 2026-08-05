@echo off
REM ── TAOS Launcher: create a Desktop shortcut ────────────────────────
REM Double-click me once. Creates "TAOS Launcher" on your Desktop that
REM points at the launcher on the TAOS drive - so you always run the
REM current version, never a stale local copy.

setlocal
set "EXE=Q:\Shared drives\TAOS\pipeline\launcher\dist\TAOS_Launcher.exe"
if defined TAOSDRIVE set "EXE=%TAOSDRIVE%\pipeline\launcher\dist\TAOS_Launcher.exe"

if not exist "%EXE%" (
    echo.
    echo Could not find the TAOS Launcher at:
    echo   %EXE%
    echo.
    echo Is the TAOS Google Drive mounted as Q:?  If your drive uses a
    echo different letter, ask in the pipeline channel.
    echo.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\TAOS Launcher.lnk');" ^
  "$s.TargetPath='%EXE%';" ^
  "$s.WorkingDirectory=(Split-Path '%EXE%');" ^
  "$s.IconLocation='%EXE%,0';" ^
  "$s.Description='TAOS Launcher - The Alchemy of a Storm pipeline';" ^
  "$s.Save()"

if errorlevel 1 (
    echo Something went wrong creating the shortcut.
    pause
    exit /b 1
)

echo.
echo Done - "TAOS Launcher" is now on your Desktop.
echo.
pause
