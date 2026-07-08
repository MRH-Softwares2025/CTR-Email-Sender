# Email Automation App Operating Instructions

## 1. Activate the virtual environment

Open PowerShell in the project folder:

```powershell
cd "f:\Cursor AI\JILR EMAIL Sender - Improved"
.\.venv\Scripts\Activate.ps1
```

If you use Command Prompt instead:

```cmd
cd "f:\Cursor AI\JILR EMAIL Sender - Improved"
.\.venv\Scripts\activate.bat
```

After activation, your prompt should show `(.venv)`.

## 2. Install dependencies

With the venv activated, install required packages:

```powershell
pip install -r requirements.txt
```

## 3. Configure the environment

Copy the example environment file and edit `.env`:

```powershell
copy .env.example .env
```

Open `.env` and set your values. Important fields:

- `GMAIL_EMAIL`
- `GMAIL_APP_PASSWORD`
- `RECIPIENT_EMAIL` (must remain `jesusislord.fmradio@gmail.com`)
- `EMAIL_SUBJECT`
- `EMAIL_BODY`
- `START_HOUR`
- `END_HOUR`
- `EMAILS_PER_HOUR`
- `TIME_VARIATION_SECONDS`
- `MPESA_CONSUMER_KEY`
- `MPESA_CONSUMER_SECRET`
- `MPESA_SHORTCODE`
- `MPESA_PASSKEY`
- `MPESA_CALLBACK_URL`
- `SUBSCRIPTION_AMOUNT`
- `SUBSCRIPTION_DAYS`
- `PORT`
- `LOG_LEVEL`

> Note: If you do not yet have real MPESA/Daraja credentials, you can still use the app locally by leaving the MPESA fields empty and using the manual payment confirmation flow.
>
> In this mode, click `Pay with MPESA`, then use `Confirm Payment` with the generated checkout ID and enter `success` as the status.
>
You can use raw multiline text for `EMAIL_BODY` in `.env`.

## 4. Start the app

Run the server from the activated environment:

```powershell
python server.py
```

If the port is already used, set a different port in `.env`, for example:

```env
PORT=8001
```

Then open the app in a browser:

```text
http://localhost:8001/
```

## 5. Use the mobile web interface

### Subscription

- Click `Pay with MPESA` to start payment.
- Enter a phone number when prompted.
- After payment initiation, the last checkout ID appears in the UI.
- Click `Confirm Payment` and enter the checkout ID and status to activate the subscription.

### Settings

- Enter your Gmail address and app password.
- Set email subject, body, start/end hours, emails per hour, and time variation.
- Click `Save Settings`.

### Controls

- `Send Single Email`: Sends one email immediately.
- `Send Batch`: Sends a specified number of emails in one batch.
- `Start Continuous Mode`: Runs the send loop automatically based on configured hours and variation.
- `Stop`: Requests the current send process to stop.

### Status and logs

- The subscription card shows whether the subscription is active and how many days remain.
- The statistics card shows daily and total send counts and failures.
- The activity log shows recent app events.

## 6. Common troubleshooting

- If the page fails to load, verify the server is running and the correct port is set in `.env`.
- If `localhost:8001` returns `ERR_CONNECTION_REFUSED`, check the server startup output for bind errors.
- If `rsas.exe` or another service occupies the port, change `PORT` to a free value such as `8002`.
- Use Gmail App Passwords, not your main Gmail password.

## 7. Stop the server

Press `CTRL+C` in the terminal running `python server.py`.

## 8. Restart the server

If you change `.env`, restart the server so the new settings take effect.

```powershell
CTRL+C
python server.py
```
