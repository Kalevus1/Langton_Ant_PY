@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
  ".venv\Scripts\pythonw.exe" "hormiga_langton.py"
) else if exist "..\.venv_face\Scripts\pythonw.exe" (
  "..\.venv_face\Scripts\pythonw.exe" "hormiga_langton.py"
) else (
  echo No se encontro el entorno de Python. Ejecuta "instalar.bat".
  pause
)
