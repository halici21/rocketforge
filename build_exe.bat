@echo off
REM ===========================================================================
REM  RocketForge - the canonical build.
REM
REM      build_exe.bat                 production package of the pushed master
REM      build_exe.bat --development   package of any tree, labelled development
REM
REM  Output, always and only:
REM      dist\RocketForge\RocketForge.exe         the application
REM      dist\RocketForge\rocketforge_build.json  its identity (commit, channel)
REM      dist\RocketForge\BUILD.md                the build record (SHA-256, ...)
REM
REM  Everything else - preconditions, the PySide6 pin gate, identity, icons,
REM  packaging, verification - is packaging\build_release.py. It refuses a
REM  dirty or unpushed tree and any PySide6 other than the pinned one, and a
REM  package that fails its checks is marked as an unknown build.
REM  See docs\engineering\release\BUILD_AND_LAUNCH.md.
REM ===========================================================================
setlocal
cd /d "%~dp0"

REM  The build environment: .venv-cea, with requirements.txt,
REM  requirements-thermochemistry.txt, requirements-fluids.txt and
REM  requirements-3d.txt installed. The production package ships NASA CEA,
REM  CoolProp and Qt Quick 3D (only the files the 3D view loads) inside it.
set "PY=%~dp0.venv-cea\Scripts\python.exe"
if not exist "%PY%" (
    echo [rocketforge] .venv-cea not found. Create it first:
    echo [rocketforge]   python -m venv .venv-cea
    echo [rocketforge]   .venv-cea\Scripts\python.exe -m pip install -r requirements.txt -r requirements-thermochemistry.txt -r requirements-fluids.txt -r requirements-3d.txt
    endlocal
    exit /b 1
)

"%PY%" -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [rocketforge] Installing PyInstaller...
    "%PY%" -m pip install "pyinstaller>=6.10" || goto :fail
)

"%PY%" "packaging\build_release.py" %*
if errorlevel 1 goto :fail
endlocal
exit /b 0

:fail
echo.
echo [rocketforge] ERROR: build failed. See the output above.
endlocal
exit /b 1
