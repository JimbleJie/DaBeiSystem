@echo off
setlocal
set "PROJECT_DIR=E:\DaBeiSystem-main\DaBeiSystem-main"
set "NODE_DIR=E:\nodejs"
set "LOG_DIR=E:\DaBeiSystem-main\DaBeiSystem-main\log"

cd /d "%PROJECT_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_DIR%\scripts\start-all-windows.ps1" -ProjectDir "%PROJECT_DIR%" -NodeDir "%NODE_DIR%" -LogDir "%LOG_DIR%"

if errorlevel 1 (
  echo.
  echo 启动失败，请查看日志目录：%LOG_DIR%
  pause
)

endlocal
