@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Detecting installed Python...
  py -3.14 -m venv .venv
  if errorlevel 1 (
    echo Python 3.14 not detected. Trying any installed Python 3.10+...
    py -3 -m venv .venv
  )
  if errorlevel 1 (
    echo Unable to create environment. Install Python 3.14 from python.org and ensure py launcher is installed.
    pause
    exit /b 1
  )
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Dependency installation failed.
    pause
    exit /b 1
  )
)
".venv\Scripts\python.exe" app.py
if errorlevel 1 pause
