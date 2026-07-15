@echo off
setlocal
set "PROJECT_DIR=E:\DaBeiSystem-main\DaBeiSystem-main"
set "NODE_DIR=E:\nodejs"
set "LOG_DIR=E:\DaBeiSystem-main\DaBeiSystem-main\log"
cd /d "%PROJECT_DIR%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-all-windows.ps1" -ProjectDir "%PROJECT_DIR%" -NodeDir "%NODE_DIR%" -LogDir "%LOG_DIR%" %*
endlocal
