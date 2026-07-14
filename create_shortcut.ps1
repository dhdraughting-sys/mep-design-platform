# Creates a Desktop shortcut for the MEP Design Platform, using the
# custom icon (mep_icon.ico) and a friendly name - run this ONCE.
#
# If double-clicking this file doesn't work because of PowerShell's
# script execution policy, right-click it -> "Run with PowerShell", or
# open a terminal in this folder and run:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\create_shortcut.ps1

$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "MEP Design Platform.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $here "run.bat"
$shortcut.WorkingDirectory = $here
$shortcut.IconLocation = Join-Path $here "mep_icon.ico"
$shortcut.Description = "MEP Design Platform - HVAC & Ventilation calculations"
$shortcut.Save()

Write-Host ""
Write-Host "Done! A shortcut called 'MEP Design Platform' is now on your Desktop." -ForegroundColor Green
Write-Host "Double-click it any time to launch the app." -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to close this window"
