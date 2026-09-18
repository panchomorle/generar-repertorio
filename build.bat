@echo off
echo =======================================================
echo Compilando Generador de Repertorio para Windows (.exe)
echo =======================================================

python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt

pyinstaller --noconsole --onefile --paths src --name "GeneradorRepertorio" --collect-all customtkinter --hidden-import docx --hidden-import bs4 main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================
    echo Compilacion exitosa!
    echo El ejecutable se encuentra en: dist\GeneradorRepertorio.exe
    echo =======================================================
) else (
    echo.
    echo [ERROR] Fallo la compilacion.
)
