@echo off
echo Starting Rapid Learn...
echo.

:: Change to the directory containing the batch file
cd /d "%~dp0"

:: Check if venv exists, if not create it
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate
    echo Installing requirements...
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate
)

:: Run the Flask application
echo Starting Flask server...
echo.
echo Please open your browser and go to: http://localhost:5000
echo.
python app.py

:: Keep the window open if there's an error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred. Press any key to exit.
    pause >nul
) 