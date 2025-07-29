@echo off
echo Starting Brevo API Integration Application...
echo.

echo Starting Backend (Flask)...
start "Backend" cmd /k "cd backend && venv\Scripts\activate && python app.py"

timeout /t 3 /nobreak > nul

echo Starting Frontend (React)...
start "Frontend" cmd /k "cd frontend && npm start"

echo.
echo Both services are starting...
echo Backend will be available at: http://127.0.0.1:5000
echo Frontend will be available at: http://localhost:3000
echo.
echo Press any key to exit...
pause > nul