@echo off
REM --- TAOS Launcher release -----------------------------------------
REM One command: bump the version, build the exe, deploy it to the TAOS drive.
REM
REM   release.bat 1.3.2     bump to 1.3.2, build, deploy
REM   release.bat           build + deploy the current version (no bump)
REM
REM Deploy = the exe only. Payloads, defaults.json and splash art are edited
REM directly on the drive and need no build (see HANDOFF.md).

setlocal enabledelayedexpansion
cd /d "%~dp0"

if not "%~1"=="" (
    python bump_version.py %~1 || goto :err
)
for /f "usebackq delims=" %%i in (`python bump_version.py --print`) do set "VER=%%i"
if "!VER!"=="" goto :err
echo.
echo === TAOS Launcher v!VER! ===
echo.

call build.bat
if errorlevel 1 goto :err
if not exist "dist\TAOS_Launcher.exe" goto :err

REM --- where is the TAOS drive? --------------------------------------
set "DRIVE=%TAOSDRIVE%"
if "!DRIVE!"=="" for /f "usebackq delims=" %%i in (`python drive_path.py`) do set "DRIVE=%%i"
if "!DRIVE!"=="" set /p DRIVE=TAOS drive root (e.g. Q:\Shared drives\TAOS): 
if not exist "!DRIVE!\pipeline" (
    echo.
    echo Not a TAOS drive root - no \pipeline folder under: !DRIVE!
    goto :err
)

echo.
echo Deploy targets:
echo   !DRIVE!\pipeline\launcher\dist\TAOS_Launcher.exe   ^(crew copy point^)
echo   !DRIVE!\pipeline\TAOS_Launcher.exe                 ^(desktop shortcuts target this^)
echo.
set /p GO=Copy v!VER! to the drive now? [y/N]: 
if /i not "!GO!"=="y" (
    echo Skipped deploy. Build is in dist\TAOS_Launcher.exe
    exit /b 0
)

REM Nothing may hold the drive exe open, or the copy fails.
taskkill /F /IM TAOS_Launcher.exe >NUL 2>&1

REM --- archive whatever is on the drive now ---------------------------
set "OLDVER=prev"
if exist "!DRIVE!\pipeline\launcher\dist\VERSION.txt" (
    for /f "tokens=3" %%i in ('type "!DRIVE!\pipeline\launcher\dist\VERSION.txt"') do set "OLDVER=%%i"
)
if not exist "!DRIVE!\pipeline\launcher\dist" mkdir "!DRIVE!\pipeline\launcher\dist"
if exist "!DRIVE!\pipeline\launcher\dist\TAOS_Launcher.exe" (
    if not exist "!DRIVE!\pipeline\launcher\dist\_archive" mkdir "!DRIVE!\pipeline\launcher\dist\_archive"
    move /y "!DRIVE!\pipeline\launcher\dist\TAOS_Launcher.exe" "!DRIVE!\pipeline\launcher\dist\_archive\TAOS_Launcher_!OLDVER!.exe" >NUL
    echo Archived previous build as _archive\TAOS_Launcher_!OLDVER!.exe
)

copy /y "dist\TAOS_Launcher.exe" "!DRIVE!\pipeline\launcher\dist\TAOS_Launcher.exe" >NUL || goto :copyerr
copy /y "dist\TAOS_Launcher.exe" "!DRIVE!\pipeline\TAOS_Launcher.exe" >NUL || goto :copyerr
> "!DRIVE!\pipeline\launcher\dist\VERSION.txt" echo TAOS Launcher v!VER!  built %DATE% %TIME%

REM --- verify both copies match the build -----------------------------
for %%F in ("dist\TAOS_Launcher.exe") do set "SZ=%%~zF"
for %%F in ("!DRIVE!\pipeline\launcher\dist\TAOS_Launcher.exe") do set "SZ1=%%~zF"
for %%F in ("!DRIVE!\pipeline\TAOS_Launcher.exe") do set "SZ2=%%~zF"
echo.
if "!SZ!"=="!SZ1!" if "!SZ!"=="!SZ2!" (
    echo VERIFIED: both drive copies are v!VER! ^(!SZ! bytes^).
    echo Give Google Drive a minute to sync, then tell the crew to relaunch.
    exit /b 0
)
echo MISMATCH - build !SZ! / launcher\dist !SZ1! / pipeline !SZ2!
echo Re-run the copy, or copy by hand. Do not announce this release.
exit /b 1

:copyerr
echo.
echo COPY FAILED. Usual cause: someone has the drive exe running
echo (it locks the file). Close every TAOS Launcher, then re-run.
exit /b 1

:err
echo.
echo RELEASE ABORTED - see output above. Nothing was copied to the drive.
exit /b 1
