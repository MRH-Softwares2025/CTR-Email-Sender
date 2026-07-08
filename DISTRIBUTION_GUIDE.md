# Email Automation Bot - Distribution Guide

## For Distributors

### Building the Package

1. **Run the build script:**
   ```bash
   build.bat
   ```

2. **This creates:**
   - `dist\EmailAutomationBot\` folder with all necessary files
   - Standalone executable that doesn't require Python
   - Setup instructions for end users

3. **Create distribution zip:**
   - Navigate to `dist\` folder
   - Right-click `EmailAutomationBot` folder
   - Send to → Compressed (zipped) folder
   - Name it: `EmailAutomationBot-v1.0.zip`

4. **Distribute:**
   - Share the zip file via email, cloud storage, or download link
   - No technical knowledge required from recipients

### What Users Need

- Windows computer (Windows 7 or later)
- Gmail account with 2-Factor Authentication enabled
- Ability to generate an App Password (takes 2 minutes)
- Internet connection

### What Users DON'T Need

- Python installation
- Command line knowledge
- Technical skills
- Additional software

## For End Users

### Installation (3 Steps)

#### Step 1: Extract the Files
1. Download the zip file
2. Right-click → "Extract All"
3. Choose a location (Desktop, Documents, etc.)
4. Click "Extract"

#### Step 2: Configure Your Email
1. Open the extracted folder
2. Find `.env.example` file
3. Right-click → Rename
4. Change name to `.env` (remove the .example part)
5. Right-click `.env` → Open with → Notepad
6. Fill in your information:

```env
GMAIL_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_password
RECIPIENT_EMAIL=recipient@example.com
EMAIL_SUBJECT=Your Subject Here
EMAIL_BODY=Your message here
START_HOUR=9
END_HOUR=17
EMAILS_PER_HOUR=125
TIME_VARIATION_SECONDS=300
```

#### Step 3: Generate Gmail App Password
1. Go to https://myaccount.google.com/security
2. Enable "2-Step Verification" (if not already enabled)
3. Go to https://myaccount.google.com/apppasswords
4. Select "Mail" → "Other (Custom name)"
5. Name it: `Email Automation Bot`
6. Click "GENERATE"
7. Copy the 16-character password
8. Paste it in the `.env` file (remove spaces)
9. Save and close the file

### Running the Bot

1. Double-click `EmailAutomationBot.exe`
2. The GUI will open
3. Click "Send Single Email" to test
4. Use the GUI controls to send batches or run continuously

### Troubleshooting

**"Configuration error" message:**
- Make sure you renamed `.env.example` to `.env`
- Check that all fields in `.env` are filled in
- Verify your Gmail app password is correct

**"Authentication failed" message:**
- Ensure 2-Factor Authentication is enabled on your Google account
- Generate a new app password (old ones may have expired)
- Make sure you removed spaces from the app password

**Program won't open:**
- Right-click → Run as Administrator
- Check if your antivirus is blocking it
- Ensure you're using Windows 7 or later

### Safety Tips

- Never share your `.env` file with others
- Keep your app password secure
- Don't send spam - only email with recipient consent
- Start with small batches (10-20 emails) before scaling
- Monitor your Gmail account for any warnings

### Getting Help

If you encounter issues:
1. Check the README.md file in the folder
2. Ensure your Gmail credentials are correct
3. Verify you have internet connection
4. Try running as Administrator

## Advanced Options

### Changing Email Content

You can change the email subject and body directly in the GUI:
1. Edit the "Email Subject" field
2. Edit the "Email Body" text area
3. Click "Save Configuration" to save changes
4. Or just send - it uses current field values

### Adjusting Timing

- **Time Variation**: How much random time between emails (in seconds)
  - 300 = 5 minutes (safer)
  - 60 = 1 minute (moderate)
  - 6 = 6 seconds (aggressive, may trigger spam filters)

- **Emails Per Hour**: How many emails to send per hour
  - 125 = ~2,000/day over 16 hours
  - 200 = ~2,000/day over 10 hours
  - Don't exceed 2,000/day (Gmail limit)

### Operating Hours

- **Start Hour**: When to start sending (0-23, 24-hour format)
- **End Hour**: When to stop sending (0-23, 24-hour format)
- Example: 9-17 means 9 AM to 5 PM

## Legal and Ethical Use

**IMPORTANT:** This tool should only be used with recipient consent and for legitimate purposes.

- ✅ Sending to people who want your emails
- ✅ Automated notifications for willing recipients
- ✅ Personal projects with consent

- ❌ Spam or unsolicited emails
- ❌ Marketing without permission
- ❌ Harassment or unwanted communication

**Legal Compliance:**
- CAN-SPAM Act (US): Requires unsubscribe option
- GDPR (EU): Requires explicit consent
- Check local laws before automated sending

## Support

For technical support or questions:
- Refer to the README.md file
- Check Gmail's sending limits and policies
- Ensure your configuration is correct
