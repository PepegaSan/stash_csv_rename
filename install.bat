@echo off
setlocal
cd /d "%~dp0"

title Stash file tools — install

echo Stash — file list and rename
echo Installing Python dependencies from requirements.txt ...
echo.

python --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python not found. Install Python 3 and add it to PATH, then run this script again.
  pause
  exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 (
  echo WARNING: pip upgrade failed; continuing with install anyway.
)

python -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
  echo.
  echo ERROR: pip install failed. Check the messages above.
  pause
  exit /b 1
)

echo.
echo Done. You can run start_file_tools.bat or: python gui_file_tools.py
pause
exit /b 0
