@echo off
cd /d "%~dp0"

echo ==========================================
echo    K-Line System Launcher
echo ==========================================
echo.

echo [1/3] Starting backend (http://localhost:8000)...
start "K-Line Backend" cmd /k "cd /d %~dp0 && .venv\Scripts\activate.bat && set DATABASE_TYPE=sqlite && uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/3] Starting frontend (http://localhost:5173)...
start "K-Line Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo [3/3] Opening browser...
start http://localhost:5173

echo.
echo ==========================================
echo  All services started!
echo    Frontend: http://localhost:5173
echo    Backend:  http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo ==========================================
echo.
echo  To stop: run stop.bat or close the windows
echo.
pause
