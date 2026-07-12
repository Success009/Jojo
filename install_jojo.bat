@echo off
title Jojo One-Click Installer & Updater
cls

echo =======================================================
echo          JOJO AI COMPANION INSTALLER & UPDATER
echo =======================================================
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

:: 3. Git Pull Update detection
if exist ".git" (
    echo [SYSTEM] Git repository detected. Checking for updates from remote repository...
    git --version >nul 2>&1
    if %errorlevel% equ 0 (
        git pull
        if %errorlevel% neq 0 (
            echo [WARNING] Failed to pull updates automatically. Continuing...
        ) else (
            echo [SUCCESS] Files successfully synced with GitHub!
        )
    ) else (
        echo [WARNING] Git CLI is not installed or not in PATH. Skipping git pull...
    )
)

:: 4. Create or update Virtual Environment
if not exist "venv" (
    echo [SYSTEM] Creating isolated Python environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create python virtual environment.
        pause
        exit /b
    )
) else (
    echo [SYSTEM] Existing Python environment found. Re-using virtual environment.
)

:: 5. Install requirements (Upgrades changed files)
echo [SYSTEM] Activating environment and updating Python requirements...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt --upgrade
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.txt dependencies.
    pause
    exit /b
)

:: 6. Install Playwright browser
echo [SYSTEM] Verifying Playwright browser files are up-to-date...
playwright install chromium
if %errorlevel% neq 0 (
    echo [ERROR] Failed to verify Playwright browser.
    pause
    exit /b
)

:: 7. Register Global CLI Command with NPM
echo [SYSTEM] Registering or updating 'jojo' global command...
npm install -g .
if %errorlevel% neq 0 (
    echo [ERROR] Global registry failed. Retrying with npm link...
    npm link
)

echo.
echo =======================================================
echo          JOJO SYSTEM HAS BEEN SUCCESSFULLY UPDATED!
echo =======================================================
echo.
echo Jojo is registered and ready globally!
echo Open any CMD/PowerShell window and type:
echo.
echo   jojo
echo.
echo to start your updated AI assistant.
echo.
pause
