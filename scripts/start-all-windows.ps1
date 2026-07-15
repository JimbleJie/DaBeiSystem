param(
    [string]$ProjectDir = "E:\DaBeiSystem-main\DaBeiSystem-main",
    [string]$NodeDir = "E:\nodejs",
    [string]$LogDir = "E:\DaBeiSystem-main\DaBeiSystem-main\log"
)

$ErrorActionPreference = "Stop"

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackendLog = Join-Path $LogDir "backend-$Timestamp.log"
$FrontendLog = Join-Path $LogDir "frontend-$Timestamp.log"
$LauncherLog = Join-Path $LogDir "start-all-$Timestamp.log"

function Write-LauncherLog {
    param([string]$Message)
    $Line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $Line
    Add-Content -Path $LauncherLog -Value $Line -Encoding UTF8
}

if (-not (Test-Path $ProjectDir)) {
    throw "Project directory not found: $ProjectDir"
}

if (-not (Test-Path $NodeDir)) {
    throw "Node.js directory not found: $NodeDir"
}

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

$SharedPrefix = @"
`$ErrorActionPreference = 'Stop'
Set-Location '$ProjectDir'
`$env:Path = '$NodeDir;' + `$env:Path
"@

$BackendCommand = @"
$SharedPrefix
Write-Host 'Backend log: $BackendLog'
& npm.cmd run backend 2>&1 | Tee-Object -FilePath '$BackendLog' -Append
"@

$FrontendCommand = @"
$SharedPrefix
Write-Host 'Frontend log: $FrontendLog'
& npm.cmd run frontend 2>&1 | Tee-Object -FilePath '$FrontendLog' -Append
"@

Write-LauncherLog "Project directory: $ProjectDir"
Write-LauncherLog "Node.js directory: $NodeDir"
Write-LauncherLog "Log directory: $LogDir"
Write-LauncherLog "Backend log: $BackendLog"
Write-LauncherLog "Frontend log: $FrontendLog"

Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", $BackendCommand
)

Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", $FrontendCommand
)

Write-LauncherLog "Backend and frontend launch commands have been started."
