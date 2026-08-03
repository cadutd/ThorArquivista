@echo off
setlocal

set "APP_DIR=%~dp0"
set "ICON_PATH=%APP_DIR%icons\favicon.ico"
cd /d "%APP_DIR%"

title Thor Arquivista

if exist "%APP_DIR%.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%APP_DIR%.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

if not exist "%APP_DIR%app.py" (
    echo Nao foi possivel encontrar app.py em "%APP_DIR%".
    pause
    exit /b 1
)

if not exist "%ICON_PATH%" (
    echo Aviso: icone nao encontrado em "%ICON_PATH%".
)

"%PYTHON_EXE%" "%APP_DIR%app.py"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo A aplicacao foi encerrada com erro: %EXIT_CODE%
    pause
)

exit /b %EXIT_CODE%
