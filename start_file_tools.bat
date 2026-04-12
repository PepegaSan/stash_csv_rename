@echo off
setlocal
cd /d "%~dp0"

echo Stashmarker — file list and rename (Stash_csv_rename)
echo First launch may take a while while Python loads libraries.

title Stashmarker - File tools

python -c "import customtkinter" 2>nul
if errorlevel 1 (
  echo Installing dependencies...
  pip install -r "%~dp0requirements.txt"
  if errorlevel 1 (
    echo pip install failed. Check Python and PATH.
    pause
    exit /b 1
  )
)

python "%~dp0gui_file_tools.py"
if errorlevel 1 pause
exit /b %ERRORLEVEL%
