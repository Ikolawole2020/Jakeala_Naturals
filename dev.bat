@echo off
REM ---------------------------------------------------------------
REM Jakeala Naturals - start backend (Django) + frontend (Next.js)
REM Usage: double-click this file, or run  dev.bat  from the repo root.
REM ---------------------------------------------------------------
setlocal

set ROOT=%~dp0

echo ============================================
echo   Jakeala Naturals - development servers
echo ============================================
echo.

if not exist "%ROOT%backend\manage.py" (
  echo [ERROR] backend\manage.py not found. Run this from the repo root.
  pause
  exit /b 1
)

if not exist "%ROOT%frontend\package.json" (
  echo [ERROR] frontend\package.json not found. Run this from the repo root.
  pause
  exit /b 1
)

echo Starting Django backend on http://localhost:8000 ...
start "Jakeala backend (Django)" cmd /k "cd /d "%ROOT%backend" && python manage.py migrate && python manage.py seed && python manage.py runserver 8000"

echo Starting Next.js frontend on http://localhost:3000 ...
start "Jakeala frontend (Next.js)" cmd /k "cd /d "%ROOT%frontend" && npm run dev"

echo.
echo   Shop      : http://localhost:3000
echo   Admin     : http://localhost:3000/admin
echo   Django    : http://localhost:8000/admin
echo   Login     : admin / jakeala2026
echo.
echo Two windows opened. Close them to stop the servers.
endlocal
