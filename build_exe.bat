@echo off
setlocal
cd /d "%~dp0"

title Stashmarker — build one-file Windows .exe

echo Build Stashmarker.exe (PyInstaller, one-file, no console window)
echo Spec: "%~dp0packaging\stashmarker_onefile.spec"
echo Output: "%~dp0dist\Stashmarker.exe"
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
echo Running PyInstaller (one-file, windowed^)...
python -m PyInstaller --noconfirm --clean "%~dp0packaging\stashmarker_onefile.spec"
if errorlevel 1 goto :fail

echo.
echo DONE.
echo You can copy "dist\Stashmarker.exe" anywhere; settings and CSVs are created next to the .exe.
echo.
pause
exit /b 0

:fail
echo.
echo ERROR: Build failed. Check the messages above.
pause
exit /b 1
