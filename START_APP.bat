@echo off
setlocal
cd /d "%~dp0"
title Resume Screening and Ranking System
echo ==========================================
echo   Resume Screening and Ranking System
echo ==========================================
if not exist ".venv\Scripts\python.exe" (
    echo Creating a project-specific Python environment...
    where py >nul 2>nul
    if %errorlevel%==0 (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
)
if not exist ".venv\Scripts\python.exe" (
    echo Could not create .venv.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
start "" http://127.0.0.1:5000
".venv\Scripts\python.exe" app.py
if errorlevel 1 goto error
goto end
:error
echo.
echo Setup or launch failed. Check the error above and your internet connection.
pause
exit /b 1
:end
endlocal
