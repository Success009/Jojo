@echo off
title Jojo AI Companion Launcher
cls

echo =======================================================
echo            INITIALIZING JOJO AI COMPANION
echo =======================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please install Python 3.8+ from python.org and try again.
    pause
    exit /b
)

:: Create Virtual Environment if it doesn't exist
if not exist "venv" (
    echo [SYSTEM] Creating Python virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b
    )
)

:: Activate Virtual Environment
echo [SYSTEM] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install Requirements
echo [SYSTEM] Installing and updating dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b
)

:: Install Playwright Chromium Browser
echo [SYSTEM] Ensuring Playwright browser binaries are installed...
playwright install chromium
if %errorlevel% neq 0 (
    echo [ERROR] Playwright browser installation failed.
    pause
    exit /b
)

echo.
echo [SUCCESS] Environment successfully prepared!
echo [SYSTEM] Starting Jojo Console Interface...
echo.

:: Run Jojo
python jojo_cli.py

:: Keep window open on exit
echo.
echo [SYSTEM] Jojo has terminated.
pause
