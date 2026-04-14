@echo off
setlocal
cd /d "%~dp0"

title Stashmarker — build Windows .exe

echo Build Stashmarker.exe (PyInstaller, one-file GUI)
echo Repository: %~dp0
echo Tip: use a fresh venv if your global Python has extra packages — that keeps the .exe smaller.
echo.

python --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python not found. Install Python 3.10+ and add it to PATH, then run this script again.
  pause
  exit /b 1
)

echo Installing runtime + build dependencies...
python -m pip install --upgrade pip
if errorlevel 1 goto :fail

python -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 goto :fail

python -m pip install -r "%~dp0requirements-build.txt"
if errorlevel 1 goto :fail

echo.
echo Running PyInstaller (stashmarker.spec^)...
python -m PyInstaller --noconfirm --clean "%~dp0stashmarker.spec"
if errorlevel 1 goto :fail

echo.
echo DONE.
echo Output: "%~dp0dist\Stashmarker.exe"
echo You can copy that file anywhere; settings and CSVs are created next to the .exe.
echo.
pause
exit /b 0

:fail
echo.
echo ERROR: Build failed. Check the messages above.
pause
exit /b 1
