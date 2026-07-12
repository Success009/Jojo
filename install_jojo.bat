@echo off
title Jojo One-Click Installer
cls

echo =======================================================
echo          JOJO AI COMPANION GLOBAL INSTALLER
echo =======================================================
echo.
echo This installer will configure the environment, install local Python
echo and Playwright dependencies, and register the global 'jojo' command.
echo.

:: 1. Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed on this machine.
    echo Please download and install Node.js from https://nodejs.org
    pause
    exit /b
)

:: 2. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed on this machine.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b
)

:: 3. Create Virtual Environment
echo [SYSTEM] Creating isolated Python environment (venv)...
if not exist "venv" (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create python virtual environment.
        pause
        exit /b
    )
)

:: 4. Install requirements
echo [SYSTEM] Activating environment and installing Python requirements...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.txt dependencies.
    pause
    exit /b
)

:: 5. Install Playwright browser
echo [SYSTEM] Preparing Playwright browser...
playwright install chromium
if %errorlevel% neq 0 (
    echo [ERROR] Failed to download Playwright browser.
    pause
    exit /b
)

:: 6. Register Global CLI Command with NPM
echo [SYSTEM] Registering 'jojo' as a global system-wide CLI command...
npm install -g .
if %errorlevel% neq 0 (
    echo [ERROR] Global registry failed. Retrying with npm link...
    npm link
)

echo.
echo =======================================================
echo              INSTALLATION COMPLETED SUCCESS
echo =======================================================
echo.
echo Jojo is now registered as a global system command!
echo You can open any Command Prompt or PowerShell window and type:
echo.
echo   jojo
echo.
echo to start your AI system assistant from any directory.
echo.
pause
