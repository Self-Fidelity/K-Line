@echo off
echo ==========================================
echo    K-Line System Stopper
echo ==========================================
echo.

echo Stopping backend (Python)...
taskkill /F /IM python.exe 2>nul

echo Stopping frontend (Node)...
taskkill /F /IM node.exe 2>nul

echo.
echo ==========================================
echo  All K-Line processes stopped
echo ==========================================
pause
