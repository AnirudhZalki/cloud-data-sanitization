@echo off
echo ===========================================
echo   Starting Data Sanitization Backend...
echo ===========================================
echo.

:: Check if the virtual environment exists, if not, create it
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Virtual environment not found. Checking if creation is needed...
    python -m venv venv
    call venv\Scripts\activate.bat
    python -m pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo.
echo [INFO] Running Uvicorn server on http://localhost:8000...
echo [TIP] Remember to update your .env file with AWS Credentials to upload to S3!
echo.

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
