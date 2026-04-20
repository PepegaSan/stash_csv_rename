@echo off
setlocal
cd /d "%~dp0"

title Stashmarker — build one-file Windows .exe

echo Build Stashmarker.exe (PyInstaller, one-file, no console window)
for /f "delims=" %%V in ('python -c "from app_version import APP_VERSION; print(APP_VERSION)" 2^>nul') do set "SM_VER=%%V"
if defined SM_VER echo Release version: %SM_VER%  (set in app_version.py^)
echo Spec: "%~dp0packaging\stashmarker_onefile.spec"
echo Output: "%~dp0dist\Stashmarker.exe"
echo Bundled with the exe: locales\, themes\, export_stash_files.ps1, CustomTkinter assets — Tab 5 help ^(info dialog^) uses the same locale JSON; no extra datas.
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
