@echo off
title Jojo One-Click Installer and Updater
cls

echo =======================================================
echo          JOJO AI COMPANION INSTALLER AND UPDATER
echo =======================================================
echo.

rem 1. Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed on this machine.
    echo Please download and install Node.js from https://nodejs.org
    pause
    exit /b
)

rem 2. Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed on this machine.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b
)

rem 3. Git Pull Update detection
if not exist ".git" goto create_venv
echo [SYSTEM] Git repository detected. Checking for updates from remote repository...
git --version >nul 2>&1
if errorlevel 1 goto create_venv
call git pull
echo [SUCCESS] Files successfully synced with GitHub!

:create_venv
rem 4. Create or update Virtual Environment
if exist "venv" goto skip_venv
echo [SYSTEM] Creating isolated Python environment (venv)...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create python virtual environment.
    pause
    exit /b
)
goto install_reqs

:skip_venv
echo [SYSTEM] Existing Python environment found. Re-using virtual environment.

:install_reqs
rem 5. Install requirements
echo [SYSTEM] Activating environment and updating Python requirements...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
call pip install -r requirements.txt --upgrade
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.txt dependencies.
    pause
    exit /b
)

rem 6. Install Playwright browser
echo [SYSTEM] Verifying Playwright browser files are up-to-date...
call playwright install chromium
if errorlevel 1 (
    echo [ERROR] Failed to verify Playwright browser.
    pause
    exit /b
)

rem 7. Register Global CLI Command with NPM
echo [SYSTEM] Registering or updating 'jojo' global command...
call npm install -g .
if errorlevel 1 (
    echo [ERROR] Global registry failed. Retrying with npm link...
    call npm link
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
