@echo off
echo ==========================================
echo    K-Line System Stopper
echo ==========================================
echo.

echo Stopping backend (K-Line Backend)...
taskkill /F /FI "WINDOWTITLE eq K-Line Backend" 2>nul

echo Stopping frontend (K-Line Frontend)...
taskkill /F /FI "WINDOWTITLE eq K-Line Frontend" 2>nul

echo.
echo ==========================================
echo  All K-Line processes stopped
echo ==========================================
pause
