# Email Automation Bot

A Python-based email automation tool that sends multiple emails to a single recipient with time variations. It supports per-user Gmail OAuth (recommended) and Gmail SMTP app-password fallback.

## Features

- Send single emails or batches with time variations
- Continuous mode for all-day sending
- Configurable operating hours
- Random time intervals between emails to avoid detection patterns
- Daily limit enforcement (Gmail free account: 2,000 emails/day)
- Comprehensive logging and statistics
- Error handling and retry logic
- Environment-based configuration

## Prerequisites

- Python 3.7 or higher
- Google Cloud OAuth credentials (recommended for multi-user/public deployments)
- Optional: Gmail App Password enabled (fallback mode)
- Recipient consent for automated emails

## Google OAuth Setup (Per User, Recommended)

1. Open Google Cloud Console and select your project.
2. Enable APIs:
  - Gmail API
  - Google OAuth2 API
3. Configure OAuth consent screen.
4. Create OAuth 2.0 Client ID (Web application).
5. Add Authorized redirect URI:
  - https://YOUR-RENDER-SERVICE.onrender.com/api/oauth/google/callback
6. Add these environment variables:
  - GOOGLE_OAUTH_CLIENT_ID
  - GOOGLE_OAUTH_CLIENT_SECRET
  - GOOGLE_OAUTH_REDIRECT_URI (optional if it matches the default callback path)

After deployment, each logged-in user can connect their own Gmail from the Send page by clicking Connect Gmail.

## Setup Instructions

### 0. Create and activate a virtual environment

Windows PowerShell:
```powershell
cd "f:\Cursor AI\JILR EMAIL Sender - Improved"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:
```cmd
cd "f:\Cursor AI\JILR EMAIL Sender - Improved"
python -m venv .venv
.\.venv\Scripts\activate.bat
```

Then use `python` and `pip` from the activated environment.

### 1. Enable Gmail App Password

1. Go to [Google Account Settings](https://myaccount.google.com/security)
2. Enable 2-Factor Authentication (if not already enabled)
3. Go to Security → 2-Step Verification → App passwords
4. Create a new app password (name it "Email Automation Bot")
5. Copy the 16-character password (you won't see it again)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and fill in your configuration:
```env
GMAIL_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
RECIPIENT_EMAIL=jesusislord.fmradio@gmail.com
EMAIL_SUBJECT=Your Subject Here
EMAIL_BODY=Your email body content here
START_HOUR=9
END_HOUR=17
EMAILS_PER_HOUR=125
TIME_VARIATION_SECONDS=300
MPESA_CONSUMER_KEY=your_mpesa_consumer_key
MPESA_CONSUMER_SECRET=your_mpesa_consumer_secret
MPESA_SHORTCODE=123456
MPESA_PASSKEY=your_mpesa_passkey
MPESA_CALLBACK_URL=http://localhost:8001/api/subscription/confirm
SUBSCRIPTION_AMOUNT=80
SUBSCRIPTION_DAYS=30
PORT=8001
LOG_LEVEL=INFO
```

### Configuration Explained

- **GMAIL_EMAIL**: Your Gmail address
- **GMAIL_APP_PASSWORD**: The 16-character app password from step 1
- **RECIPIENT_EMAIL**: Fixed recipient email; the app always sends to `jesusislord.fmradio@gmail.com`
- **EMAIL_SUBJECT**: Default subject line for emails
- **EMAIL_BODY**: Default body content for emails
  - Raw multiline text in `.env` is supported by this app and will be parsed correctly.
  - If you prefer a single-line value, use `\n` escapes for newlines.
- **START_HOUR**: Hour to start sending (24-hour format, e.g., 9 for 9 AM)
- **END_HOUR**: Hour to stop sending (24-hour format, e.g., 17 for 5 PM)
- **EMAILS_PER_HOUR**: Target emails per hour (125 = ~2,000/day over 16 hours)
- **TIME_VARIATION_SECONDS**: Random variation in seconds between sends (300 = 5 minutes)
- **MPESA_CONSUMER_KEY**: Daraja consumer key for MPESA integration
- **MPESA_CONSUMER_SECRET**: Daraja consumer secret for MPESA integration
- **MPESA_SHORTCODE**: MPESA paybill or shortcode for STK Push requests
- **MPESA_PASSKEY**: MPESA passkey used by your Daraja account
- **MPESA_CALLBACK_URL**: Local or remote callback endpoint for payment confirmation
- **SUBSCRIPTION_AMOUNT**: Default monthly subscription price
- **SUBSCRIPTION_DAYS**: Number of days the subscription remains active after payment
- **LOG_LEVEL**: Logging level (DEBUG, INFO, WARNING, ERROR)

## Usage

### Run the Bot

You have two options:

#### Option 1: Command Line Interface (CLI)
```bash
python email_automation.py
```

#### Option 2: Graphical User Interface (GUI)
```bash
python email_automation_gui.py
```

The GUI provides:
- Visual configuration display
- Editable email subject, body, and time variation
- One-click buttons for all operations
- Real-time statistics
- Activity log
- Start/Stop controls
- Save configuration to .env file

#### Option 3: Mobile Web Interface
Activate the virtual environment first, then run the server.

Windows PowerShell:
```powershell
cd "f:\Cursor AI\JILR EMAIL Sender - Improved"
.\.venv\Scripts\Activate.ps1
python server.py
```

Windows Command Prompt:
```cmd
cd "f:\Cursor AI\JILR EMAIL Sender - Improved"
.\.venv\Scripts\activate.bat
python server.py
```

Then open a browser on your phone or computer at:
```
http://localhost:8001
```

The mobile web UI provides:
- MPESA subscription status and payment initiation
- Manual payment confirmation support (for local testing)
- Visible checkout request ID after payment initiation
- Sender configuration
- Send single, batch, and continuous controls
- Email statistics and activity log
- Fixed recipient enforcement to `jesusislord.fmradio@gmail.com`

## Production Deployment

For production, keep `.env` out of source control and use the values from `.env.example`.

### Using Gunicorn
Install dependencies and run:
```bash
pip install -r requirements.txt
gunicorn server:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

### Using the Procfile
If you deploy to Render, Railway, or a similar host, the included `Procfile` starts the app properly:
```text
web: gunicorn server:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8001}
```

### Using Docker
Build and run the container:
```bash
docker build -t jilr-email-sender .
docker run -p 8001:8001 --env-file .env jilr-email-sender
```

### Using Docker Compose
If you prefer Compose, use the included `docker-compose.yml`:
```bash
docker compose up --build
```

### Recommended production settings
- `APP_ENV=production`
- `DEBUG=false`
- `HTTPS_ONLY=true`
- `SESSION_SECURE=true`
- `SECRET_KEY` set to a strong random value
- `MPESA_CALLBACK_URL` set to your public HTTPS endpoint

### Health check
The app exposes a health endpoint at:
```
/health
```

### Why use a virtual environment?
- Keeps project dependencies isolated from global Python packages
- Prevents version conflicts between projects
- Makes installs repeatable and easier to manage
- Ensures the app uses the exact packages in `requirements.txt`

### When to turn it on
- Before installing dependencies: `pip install -r requirements.txt`
- Before running the app: `python server.py`, `python email_automation_gui.py`, or any Python command for this project
- Every time you open a new terminal session for this project

### Menu Options

1. **Send a single email** - Sends one email immediately
2. **Send a batch of emails** - Sends specified number with time variations
3. **Run continuous mode** - Sends emails continuously until daily limit or end hour
4. **View statistics** - Shows current sending statistics
5. **Exit** - Closes the program

### Example Usage

**Send 50 emails with time variations:**
```
Enter your choice (1-5): 2
Enter number of emails to send: 50
```

**Run continuous mode for the day:**
```
Enter your choice (1-5): 3
Start continuous mode? (yes/no): yes
```

### GUI Features

The graphical interface provides:

**Configuration Display:**
- Shows all current settings from .env file
- Displays Gmail email, recipient, subject, body
- Shows scheduling parameters (hours, rate, variation)

**Statistics Panel:**
- Emails sent today
- Total emails sent
- Failed emails count
- Daily limit status

**Control Buttons:**
- **Send Single Email** - Send one email immediately
- **Send Batch** - Specify number of emails to send
- **Start Continuous Mode** - Run until daily limit
- **Stop** - Halt any running operation
- **Refresh Stats** - Update statistics display

**Activity Log:**
- Real-time log of all operations
- Timestamps for each action
- Success/failure indicators
- Scrollable history

**Status Bar:**
- Current bot status (Ready, Running, Error)
- Operation progress

### Creating a Desktop Shortcut

To easily access the GUI from your desktop:

**Option 1: Using the provided script (Windows)**
```powershell
# Run PowerShell as administrator
cd "F:\Cursor AI\JILR EMAIL Sender"
.\create_shortcut.ps1
```
This will create a shortcut called "Email Automation Bot" on your desktop.

**Option 2: Using the batch file**
- Copy `Start_Email_Bot.bat` to your desktop
- Double-click it to launch the GUI

**Option 3: Manual shortcut creation**
1. Right-click on your desktop
2. Select "New" → "Shortcut"
3. Enter: `pythonw.exe "F:\Cursor AI\JILR EMAIL Sender\email_automation_gui.py"`
4. Name it: "Email Automation Bot"
5. Finish

## Packaging for Distribution

To create a standalone Windows executable for distribution to other users:

### Quick Build

```bash
# Run the build script
build.bat
```

This will:
1. Install PyInstaller and dependencies
2. Build a standalone executable
3. Create a distribution package in `dist\EmailAutomationBot\`
4. Include setup instructions

### Manual Build

```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
pyinstaller --clean email_automation_gui.spec

# The executable will be in dist\EmailAutomationBot.exe
```

### Distribution Package Contents

The distribution package includes:
- `EmailAutomationBot.exe` - Standalone executable (no Python required)
- `.env.example` - Configuration template
- `README.md` - Full documentation
- `SETUP.txt` - Quick setup instructions

### How to Distribute

1. Run `build.bat` to create the package
2. Zip the `dist\EmailAutomationBot` folder
3. Share the zip file with users
4. Users extract and run `EmailAutomationBot.exe`

### User Instructions for Recipients

1. Extract the zip file to any folder
2. Rename `.env.example` to `.env`
3. Edit `.env` with their Gmail credentials:
   - Generate a Gmail App Password (see README)
   - Add their email and app password
   - Set recipient email and message content
4. Double-click `EmailAutomationBot.exe` to run

### Advantages of Packaged Version

- **No Python installation required** for end users
- **Single executable** - easy to run
- **Self-contained** - includes all dependencies
- **Cross-folder compatible** - works from any location
- **Professional appearance** - looks like a native Windows app

## Important Limitations and Warnings

### Gmail Sending Limits
- **Free Gmail account**: 2,000 emails per day
- **Google Workspace trial**: 500 emails per day
- **Google Workspace paid**: 2,000 emails per day (increases after payment threshold)
- Limits are calculated over a rolling 24-hour period

### Risk Factors
- Sending multiple emails to the same recipient may trigger spam filters
- Automated patterns can be detected by email providers
- Account suspension is possible if patterns resemble spam
- Recipient may mark emails as spam, affecting your sender reputation

### Best Practices
1. **Start small**: Test with 10-20 emails before scaling
2. **Monitor delivery**: Check `email_automation.log` for errors
3. **Use time variations**: Keep TIME_VARIATION_SECONDS at 300 (5 minutes) or higher for safety
4. **Respect operating hours**: Don't send 24/7
5. **Get explicit consent**: Ensure recipient wants these emails
6. **Provide unsubscribe option**: Include unsubscribe mechanism in emails
7. **Monitor spam complaints**: Stop immediately if recipient reports spam

### Legal Compliance
- **CAN-SPAM Act (US)**: Requires unsubscribe option, valid physical address, truthful subject lines
- **GDPR (EU)**: Requires explicit consent for marketing emails
- Check local laws before sending automated emails

## Troubleshooting

### Authentication Error
```
SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
```
**Solution**: Verify your app password is correct and 2FA is enabled

### Daily Limit Reached
```
Daily limit reached (2000 emails). Stopping for today.
```
**Solution**: Wait 24 hours before sending more, or upgrade to Google Workspace

### Connection Timeout
```
timeout: timed out
```
**Solution**: Check internet connection and Gmail service status

## Files

- `email_automation.py` - Main bot script
- `requirements.txt` - Python dependencies
- `.env` - Configuration file (not in git)
- `.env.example` - Configuration template
- `email_automation.log` - Log file (created automatically)
- `README.md` - This file

## Security Notes

- **Never commit `.env` to version control**
- **Never share your app password**
- **Use app passwords, not your regular Gmail password**
- **Rotate app passwords periodically**
- **Monitor account for unauthorized access**

## Advanced Usage

### Custom Email Content

You can modify the `send_email()` method to accept dynamic content:

```python
# In your code
bot.send_email(
    custom_subject="Custom Subject",
    custom_body="Custom body content"
)
```

### Programmatic Usage

Import the bot class in your own scripts:

```python
from email_automation import EmailAutomationBot

bot = EmailAutomationBot()
bot.send_batch(100)  # Send 100 emails
```

## Support

For issues or questions:
1. Check the log file: `email_automation.log`
2. Verify your `.env` configuration
3. Ensure Gmail app password is correct
4. Check Gmail sending limits

## Disclaimer

This tool is for educational purposes and legitimate use cases with recipient consent. Misuse for spam or unsolicited emails violates terms of service of email providers and may be illegal in your jurisdiction. Use responsibly and ethically.
