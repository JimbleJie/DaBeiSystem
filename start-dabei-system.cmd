@echo off
setlocal EnableExtensions

set "PROJECT_DIR=E:\DaBeiSystem-main\DaBeiSystem-main"
set "NODE_DIR=E:\nodejs"
set "LOG_DIR=E:\DaBeiSystem-main\DaBeiSystem-main\log"

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

call :write_runner "%BACKEND_CMD%" "DaBei Backend" "backend" "%BACKEND_LOG%"
call :write_runner "%FRONTEND_CMD%" "DaBei Frontend" "frontend" "%FRONTEND_LOG%"

start "DaBei Backend" cmd /k ""%BACKEND_CMD%""
start "DaBei Frontend" cmd /k ""%FRONTEND_CMD%""

echo.
echo DaBeiSystem is starting.
echo Backend and frontend windows have been opened.
echo Logs are saved in:
echo %LOG_DIR%
echo.
pause
goto done

:write_runner
set "RUNNER_PATH=%~1"
set "RUNNER_TITLE=%~2"
set "RUNNER_SCRIPT=%~3"
set "RUNNER_LOG=%~4"
>"%RUNNER_PATH%" echo @echo off
>>"%RUNNER_PATH%" echo title %RUNNER_TITLE%
>>"%RUNNER_PATH%" echo cd /d "%PROJECT_DIR%"
>>"%RUNNER_PATH%" echo set "Path=%NODE_DIR%;%%Path%%"
>>"%RUNNER_PATH%" echo echo %RUNNER_TITLE% log: %RUNNER_LOG%
>>"%RUNNER_PATH%" echo echo [%DATE% %TIME%] Starting %RUNNER_SCRIPT%...^>^>"%RUNNER_LOG%"
>>"%RUNNER_PATH%" echo npm.cmd run %RUNNER_SCRIPT% 1^>^>"%RUNNER_LOG%" 2^>^>^&1
>>"%RUNNER_PATH%" echo echo.
>>"%RUNNER_PATH%" echo echo %RUNNER_TITLE% stopped. Check log:
>>"%RUNNER_PATH%" echo echo %RUNNER_LOG%
>>"%RUNNER_PATH%" echo pause
exit /b 0

:missing_project
echo.
echo Project directory not found:
echo %PROJECT_DIR%
pause
goto done

:missing_node
echo.
echo Node.js directory not found:
echo %NODE_DIR%
pause
goto done

:done
endlocal
