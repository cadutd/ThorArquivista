from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_BAT_NAME = "executar_thor_arquivista.bat"
DEFAULT_SHORTCUT_NAME = "Thor Arquivista.lnk"
ICON_PATH = ROOT_DIR / "icons" / "favicon.ico"


BAT_TEMPLATE = r"""@echo off
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
"""


def write_bat(path: Path) -> None:
    path.write_text(BAT_TEMPLATE, encoding="utf-8", newline="\r\n")


def write_shortcut(shortcut_path: Path, bat_path: Path) -> None:
    if not ICON_PATH.exists():
        raise FileNotFoundError(f"Icone nao encontrado: {ICON_PATH}")

    powershell = f"""
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut('{shortcut_path}')
$Shortcut.TargetPath = '{bat_path}'
$Shortcut.WorkingDirectory = '{ROOT_DIR}'
$Shortcut.IconLocation = '{ICON_PATH}'
$Shortcut.Save()
"""

    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", powershell],
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera um arquivo .bat para executar o Thor Arquivista no Windows."
    )
    parser.add_argument(
        "--bat",
        default=DEFAULT_BAT_NAME,
        help=f"Nome do arquivo .bat gerado. Padrao: {DEFAULT_BAT_NAME}",
    )
    parser.add_argument(
        "--atalho",
        default=DEFAULT_SHORTCUT_NAME,
        help=f"Nome do atalho .lnk com icone. Padrao: {DEFAULT_SHORTCUT_NAME}",
    )
    parser.add_argument(
        "--sem-atalho",
        action="store_true",
        help="Gera somente o .bat, sem criar o atalho com icone.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bat_path = ROOT_DIR / args.bat
    shortcut_path = ROOT_DIR / args.atalho

    write_bat(bat_path)
    print(f"BAT gerado: {bat_path}")

    if args.sem_atalho:
        return

    write_shortcut(shortcut_path, bat_path)
    print(f"Atalho com icone gerado: {shortcut_path}")
    print(f"Icone usado: {ICON_PATH}")


if __name__ == "__main__":
    main()
