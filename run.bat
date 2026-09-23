@echo off
REM ===========================================================================
REM  RocketForge - development launcher: runs the application from this source
REM  tree, and only that. It never starts a packaged build.
REM
REM      run.bat
REM
REM  The window title reads "RocketForge [DEV <commit>]", and Settings shows
REM  "Build <commit>-dev . development . source run". For the packaged
REM  application, run dist\RocketForge\RocketForge.exe or the RocketForge
REM  desktop shortcut. See docs\engineering\release\BUILD_AND_LAUNCH.md.
REM
REM  Environment: .venv-cea (NASA CEA and CoolProp, like the package), else
REM  .venv (no providers). Never a python from PATH.
REM ===========================================================================
setlocal
cd /d "%~dp0"

set "PY=%~dp0.venv-cea\Scripts\pythonw.exe"
if not exist "%PY%" set "PY=%~dp0.venv\Scripts\pythonw.exe"
if not exist "%PY%" (
    echo [rocketforge] No project environment. Create .venv-cea as the README
    echo [rocketforge] describes under "Running"; run.bat does not use a python
    echo [rocketforge] from PATH.
    endlocal
    exit /b 1
)

echo [rocketforge] Development run from source: %PY%
"%PY%" main.py %*
endlocal
