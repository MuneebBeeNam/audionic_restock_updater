@echo off
title Audionic Stock Notifier
cd /d "%~dp0"

echo ===================================================
echo     AUDIONIC RESTOCK MONITOR (Background Loop)
echo ===================================================
echo.

if not exist ".env" (
    echo [!] .env file not found. Creating from .env.example...
    copy .env.example .env
    echo [!] Please edit .env with your notification settings (e.g., NTFY_TOPIC).
    pause
    exit /b
)

echo [*] Checking dependencies...
python -m pip install -r requirements.txt -q

echo.
echo [*] Starting monitor in continuous loop...
echo [*] Press Ctrl+C in this window anytime to stop.
echo.

python check_stock.py --loop

pause
