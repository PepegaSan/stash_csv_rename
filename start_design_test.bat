@echo off
setlocal
cd /d "%~dp0"

echo Stashmarker - Design test GUI (visual only)
echo This launcher starts a mockup without real functionality.

title Stashmarker - Design Test

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

python "%~dp0gui_file_tools_design_test.py"
if errorlevel 1 pause
exit /b %ERRORLEVEL%
