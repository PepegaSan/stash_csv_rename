@echo off
setlocal
cd /d "%~dp0"

echo Stashmarker — file list and rename (Stash_csv_rename)
for /f "delims=" %%V in ('python -c "from app_version import APP_VERSION; print(APP_VERSION)" 2^>nul') do set "SM_VER=%%V"
if defined SM_VER echo Version %SM_VER%
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
