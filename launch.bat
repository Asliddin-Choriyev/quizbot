@echo off
TITLE Telegram Quiz Bot - Production Engine
COLOR 0A

echo ========================================================
echo         TELEGRAM QUIZ BOT - STARTUP LAUNCHER
echo ========================================================
echo.

:: 1. Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10 or higher from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found! Creating from .env.example...
    copy ".env.example" ".env" >nul
    echo.
    echo [ACTION REQUIRED] Please edit .env file and set your BOT_TOKEN and ADMIN_IDS.
    echo.
    notepad .env
    echo After saving your token in .env, press any key to continue...
    pause >nul
)

:: 3. Verify packages
echo [INFO] Verifying dependencies...
python -c "import aiogram, aiosqlite, pandas, openpyxl, dotenv" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing required dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)

:: 4. Launch Bot
echo [INFO] Starting QuizBot...
echo.
python main.py

echo.
echo [INFO] Bot stopped.
pause
