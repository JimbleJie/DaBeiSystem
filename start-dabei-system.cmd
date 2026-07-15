@echo off
setlocal EnableExtensions
title DaBeiSystem Launcher

set "PROJECT_DIR=E:\DaBeiSystem-main\DaBeiSystem-main"
set "NODE_DIR=E:\nodejs"
set "LOG_DIR=E:\DaBeiSystem-main\DaBeiSystem-main\log"

cls
echo ========================================
echo          DaBeiSystem Launcher
echo ========================================
echo.

if not exist "%PROJECT_DIR%" goto missing_project
if not exist "%NODE_DIR%" goto missing_node
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "TS=%%I"
set "BACKEND_LOG=%LOG_DIR%\backend-%TS%.log"
set "FRONTEND_LOG=%LOG_DIR%\frontend-%TS%.log"
set "START_LOG=%LOG_DIR%\start-all-%TS%.log"
set "BACKEND_CMD=%LOG_DIR%\run-backend-%TS%.cmd"
set "FRONTEND_CMD=%LOG_DIR%\run-frontend-%TS%.cmd"

echo [%DATE% %TIME%] Project directory: %PROJECT_DIR%>>"%START_LOG%"
echo [%DATE% %TIME%] Node.js directory: %NODE_DIR%>>"%START_LOG%"
echo [%DATE% %TIME%] Backend log: %BACKEND_LOG%>>"%START_LOG%"
echo [%DATE% %TIME%] Frontend log: %FRONTEND_LOG%>>"%START_LOG%"

call :write_runner "%BACKEND_CMD%" "backend" "%BACKEND_LOG%"
call :write_runner "%FRONTEND_CMD%" "frontend" "%FRONTEND_LOG%"

echo Starting backend service...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -WindowStyle Hidden -FilePath $env:ComSpec -ArgumentList '/c', '%BACKEND_CMD%'"
if errorlevel 1 goto failed

echo Starting frontend service...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -WindowStyle Hidden -FilePath $env:ComSpec -ArgumentList '/c', '%FRONTEND_CMD%'"
if errorlevel 1 goto failed

echo.
echo Services are starting in the background.
echo.
echo Frontend:
echo   http://127.0.0.1:5173/
echo Backend health:
echo   http://127.0.0.1:4000/api/health
echo.
echo Logs:
echo   %LOG_DIR%
echo.
echo This window can be closed after the services start.
echo To stop services, close node.exe processes from Task Manager.
echo.
pause
goto done

:write_runner
set "RUNNER_PATH=%~1"
set "RUNNER_SCRIPT=%~2"
set "RUNNER_LOG=%~3"
>"%RUNNER_PATH%" echo @echo off
>>"%RUNNER_PATH%" echo cd /d "%PROJECT_DIR%"
>>"%RUNNER_PATH%" echo set "Path=%NODE_DIR%;%%Path%%"
>>"%RUNNER_PATH%" echo echo [%DATE% %TIME%] Starting %RUNNER_SCRIPT%...^>^>"%RUNNER_LOG%"
>>"%RUNNER_PATH%" echo npm.cmd run %RUNNER_SCRIPT% 1^>^>"%RUNNER_LOG%" 2^>^>^&1
exit /b 0

:missing_project
echo Project directory not found:
echo %PROJECT_DIR%
echo.
pause
goto done

:missing_node
echo Node.js directory not found:
echo %NODE_DIR%
echo.
pause
goto done

:failed
echo Failed to start DaBeiSystem. Please check logs in:
echo %LOG_DIR%
echo.
pause
goto done

:done
endlocal
