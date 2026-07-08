@echo off
echo ========================================
echo Email Automation Bot - Build Script
echo ========================================
echo.

REM Install PyInstaller if not already installed
echo [1/4] Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

REM Install dependencies
echo [2/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Build the executable
echo [3/4] Building executable...
pyinstaller --clean email_automation_gui.spec
if errorlevel 1 (
    echo ERROR: Failed to build executable
    pause
    exit /b 1
)

REM Create distribution folder
echo [4/4] Creating distribution package...
if not exist "dist\EmailAutomationBot" mkdir "dist\EmailAutomationBot"
copy "dist\EmailAutomationBot.exe" "dist\EmailAutomationBot\" >nul
copy ".env.example" "dist\EmailAutomationBot\" >nul
copy "README.md" "dist\EmailAutomationBot\" >nul

REM Create setup instructions
echo # Email Automation Bot - Setup Instructions > "dist\EmailAutomationBot\SETUP.txt"
echo. >> "dist\EmailAutomationBot\SETUP.txt"
echo 1. Copy this entire folder to your computer >> "dist\EmailAutomationBot\SETUP.txt"
echo 2. Rename .env.example to .env >> "dist\EmailAutomationBot\SETUP.txt"
echo 3. Edit .env with your Gmail credentials: >> "dist\EmailAutomationBot\SETUP.txt"
echo    - GMAIL_EMAIL=your@gmail.com >> "dist\EmailAutomationBot\SETUP.txt"
echo    - GMAIL_APP_PASSWORD=your_16_char_app_password >> "dist\EmailAutomationBot\SETUP.txt"
echo    - RECIPIENT_EMAIL=recipient@example.com >> "dist\EmailAutomationBot\SETUP.txt"
echo    - EMAIL_SUBJECT=Your Subject >> "dist\EmailAutomationBot\SETUP.txt"
echo    - EMAIL_BODY=Your Message >> "dist\EmailAutomationBot\SETUP.txt"
echo. >> "dist\EmailAutomationBot\SETUP.txt"
echo 4. Double-click EmailAutomationBot.exe to run >> "dist\EmailAutomationBot\SETUP.txt"
echo. >> "dist\EmailAutomationBot\SETUP.txt"
echo For detailed instructions, see README.md >> "dist\EmailAutomationBot\SETUP.txt"

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Distribution package created at: dist\EmailAutomationBot\
echo.
echo To distribute:
echo 1. Zip the dist\EmailAutomationBot folder
echo 2. Share the zip file with users
echo 3. Users extract and run EmailAutomationBot.exe
echo.
pause
