@echo off
echo Starting Cursor AI Auto-Paste Monitor...
echo.
echo Make sure Cursor AI is open before running this script.
echo Press Ctrl+C to stop the monitor.
echo.

REM Activate virtual environment
call ..\venv\Scripts\activate.bat

REM Run the copychat.py script
python copychat.py

pause
