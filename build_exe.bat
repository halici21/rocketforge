@echo off
REM ===========================================================================
REM  RocketForge - build the Windows executable.
REM
REM      build_exe.bat
REM
REM  Produces  dist\RocketForge\RocketForge.exe  together with the Qt runtime
REM  and the QML interface it needs. Run it from anywhere; it works out of its
REM  own location, so a shortcut to it is fine.
REM
REM  Prefers the project virtual environment in .venv, because that is where
REM  the PySide6 version the interface was built against lives. Falls back to
REM  whatever python is on PATH.
REM ===========================================================================
setlocal
cd /d "%~dp0"

REM  Prefers .venv-cea, the provider-enabled environment, because the official
REM  desktop build ships with the NASA CEA thermochemistry provider inside it.
REM  Falls back to .venv, which still builds - just without thermochemistry.
set "PY=%~dp0.venv-cea\Scripts\python.exe"
if not exist "%PY%" (
    echo [rocketforge] .venv-cea not found; falling back to .venv.
    echo [rocketforge] The build will NOT include the thermochemistry provider.
    set "PY=%~dp0.venv\Scripts\python.exe"
)
if not exist "%PY%" (
    echo [rocketforge] .venv not found, falling back to python on PATH.
    set "PY=python"
)

echo [rocketforge] Python: %PY%
"%PY%" --version || goto :fail

REM ---- make sure the packager is available ---------------------------------
"%PY%" -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [rocketforge] Installing PyInstaller...
    "%PY%" -m pip install "pyinstaller>=6.10" || goto :fail
)

REM ---- refresh the application icon ----------------------------------------
if exist "packaging\make_icon.py" (
    if not exist "packaging\RocketForge.ico" (
        echo [rocketforge] Rendering application icon...
        "%PY%" "packaging\make_icon.py" "packaging\RocketForge.ico" || goto :fail
    )
)

REM ---- clean the previous build --------------------------------------------
echo [rocketforge] Cleaning build\ and dist\...
if exist "build\RocketForge" rmdir /s /q "build\RocketForge"
if exist "dist\RocketForge" rmdir /s /q "dist\RocketForge"

REM ---- package --------------------------------------------------------------
echo [rocketforge] Packaging...
"%PY%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --distpath "dist" ^
    --workpath "build" ^
    "packaging\RocketForge.spec" || goto :fail

if not exist "dist\RocketForge\RocketForge.exe" goto :missing

echo.
echo [rocketforge] Build complete.
echo [rocketforge]   dist\RocketForge\RocketForge.exe
echo.
endlocal
exit /b 0

:missing
echo.
echo [rocketforge] ERROR: the packager finished but RocketForge.exe is not in dist\RocketForge.
endlocal
exit /b 1

:fail
echo.
echo [rocketforge] ERROR: build failed. See the output above.
endlocal
exit /b 1
