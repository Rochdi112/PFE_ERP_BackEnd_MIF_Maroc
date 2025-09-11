@echo off
REM Production deployment script for ERP MIF Maroc (Windows)
REM This script builds and deploys the full stack (backend + frontend)

echo 🚀 Starting production deployment for ERP MIF Maroc...

REM Check if we're in the backend directory
if not exist "docker-compose.prod.yml" (
    echo Error: Please run this script from the backend directory (PFE_ERP_BackEnd_MIF_Maroc)
    pause
    exit /b 1
)

REM Check if frontend directory exists
if not exist "..\VITE-FRONTEND-ERP-MIF-MAROC" (
    echo Error: Frontend directory not found at ..\VITE-FRONTEND-ERP-MIF-MAROC
    pause
    exit /b 1
)

echo Building frontend for production...
cd ..\VITE-FRONTEND-ERP-MIF-MAROC
call npm ci
call npm run build

if %errorlevel% neq 0 (
    echo Error: Frontend build failed
    cd ..\PFE_ERP_BackEnd_MIF_Maroc
    pause
    exit /b 1
)

echo Frontend built successfully!

cd ..\PFE_ERP_BackEnd_MIF_Maroc

echo Starting production services...
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up --build -d

if %errorlevel% neq 0 (
    echo Error: Failed to start services
    pause
    exit /b 1
)

echo Production deployment completed!
echo Services should be available at:
echo   - Frontend: http://localhost
echo   - API: http://localhost/api/v1/
echo   - API Docs: http://localhost/docs
echo   - Health Check: http://localhost/health
echo.
echo To check service status:
echo   docker-compose -f docker-compose.prod.yml ps
echo   docker-compose -f docker-compose.prod.yml logs [service_name]

pause
