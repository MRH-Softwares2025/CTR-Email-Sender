# PowerShell script to create desktop shortcut for Email Automation Bot

$WshShell = New-Object -comObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\Email Automation Bot.lnk")
$Shortcut.TargetPath = "pythonw.exe"
$Shortcut.Arguments = "`"F:\Cursor AI\JILR EMAIL Sender\email_automation_gui.py`""
$Shortcut.WorkingDirectory = "F:\Cursor AI\JILR EMAIL Sender"
$Shortcut.Description = "Email Automation Bot GUI"
$Shortcut.IconLocation = "pythonw.exe,0"
$Shortcut.Save()

Write-Host "Desktop shortcut created: Email Automation Bot.lnk" -ForegroundColor Green
Write-Host "You can now double-click the shortcut on your desktop to launch the bot." -ForegroundColor Green
