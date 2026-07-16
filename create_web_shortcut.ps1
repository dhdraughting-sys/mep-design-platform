# Creates a Desktop shortcut to the MEP Design Platform web app, using
# the D3D icon and your actual live URL already filled in - run this
# ONCE. Uses explorer.exe as the actual shortcut target (with the URL
# as an argument) rather than trying to point a .lnk directly at a web
# address - this is the reliable, well-established way to do this on
# Windows, since a plain .url Internet Shortcut can have flaky icon
# caching (which is what didn't work last time).
#
# If double-clicking this file doesn't work because of PowerShell's
# script execution policy, right-click it -> "Run with PowerShell", or
# open a terminal in this folder and run:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\create_web_shortcut.ps1

$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "MEP Design Platform.lnk"
$appUrl = "https://mep-design-platform.streamlit.app/"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "$env:WINDIR\explorer.exe"
$shortcut.Arguments = $appUrl
$shortcut.IconLocation = Join-Path $here "mep_icon.ico"
$shortcut.Description = "MEP Design Platform (Web App)"
$shortcut.Save()

Write-Host ""
Write-Host "Done! A shortcut called 'MEP Design Platform' is now on your Desktop." -ForegroundColor Green
Write-Host "Double-click it any time to open the app in your browser." -ForegroundColor Green
Write-Host ""
Write-Host "If the icon still looks generic rather than your logo, that's usually" -ForegroundColor Yellow
Write-Host "just Windows' icon cache being stale - try signing out and back in," -ForegroundColor Yellow
Write-Host "or restarting Windows Explorer (Task Manager -> Windows Explorer -> Restart)." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to close this window"
