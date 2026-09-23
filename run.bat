@echo off
REM ===========================================================================
REM  RocketForge - run the development version from source.
REM
REM      run.bat
REM
REM  Uses the project virtual environment in .venv when it exists, otherwise
REM  python on PATH. For the packaged application, see build_exe.bat.
REM ===========================================================================
setlocal
cd /d "%~dp0"

set "PY=%~dp0.venv-cea\Scripts\pythonw.exe"
if not exist "%PY%" set "PY=%~dp0.venv-cea\Scripts\python.exe"
if not exist "%PY%" set "PY=%~dp0.venv\Scripts\pythonw.exe"
if not exist "%PY%" set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" main.py %*
endlocal
