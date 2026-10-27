@echo off
cd /d "%~dp0"
echo Installing GIS Portal dependencies (internet required for first setup)...
python -m pip install -r requirements.txt
if errorlevel 1 (
 echo Dependency installation failed. Check Python and internet connection.
 pause
 exit /b 1
)
echo Opening Philippine Land Services GIS Portal...
python launch.py
pause
