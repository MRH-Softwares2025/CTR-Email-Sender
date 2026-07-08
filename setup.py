#!/usr/bin/env python3
"""
Quick setup script for Email Automation Bot
Helps verify configuration and test SMTP connection
"""

import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_smtp_connection():
    """Test SMTP connection with provided credentials"""
    load_dotenv()
    
    gmail_email = os.getenv('GMAIL_EMAIL')
    app_password = os.getenv('GMAIL_APP_PASSWORD')
    recipient_email = os.getenv('RECIPIENT_EMAIL')
    
    print("=== Email Automation Bot Setup Test ===\n")
    
    # Check if environment variables are set
    if not gmail_email:
        print("❌ GMAIL_EMAIL not set in .env file")
        return False
    else:
        print(f"✓ GMAIL_EMAIL: {gmail_email}")
    
    if not app_password:
        print("❌ GMAIL_APP_PASSWORD not set in .env file")
        return False
    else:
        print(f"✓ GMAIL_APP_PASSWORD: {'*' * 16} (length: {len(app_password)})")
    
    if not recipient_email:
        print("❌ RECIPIENT_EMAIL not set in .env file")
        return False
    else:
        print(f"✓ RECIPIENT_EMAIL: {recipient_email}")
    
    print("\nTesting SMTP connection...")
    
    try:
        # Connect to Gmail SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(gmail_email, app_password)
            print("✓ SMTP connection successful")
            print("✓ Authentication successful")
            return True
    
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed")
        print("  Possible causes:")
        print("  - Incorrect app password")
        print("  - 2-Factor Authentication not enabled")
        print("  - App password not generated correctly")
        return False
    
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def send_test_email():
    """Send a test email to verify everything works"""
    load_dotenv()
    
    gmail_email = os.getenv('GMAIL_EMAIL')
    app_password = os.getenv('GMAIL_APP_PASSWORD')
    recipient_email = os.getenv('RECIPIENT_EMAIL')
    
    print("\n=== Send Test Email ===\n")
    
    confirm = input(f"Send test email to {recipient_email}? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Test email cancelled.")
        return
    
    try:
        # Create test email
        msg = MIMEMultipart()
        msg['From'] = gmail_email
        msg['To'] = recipient_email
        msg['Subject'] = "Email Automation Bot - Test Email"
        
        body = """
This is a test email from the Email Automation Bot.

If you received this email, your SMTP configuration is working correctly!

Time sent: {timestamp}
        """.format(timestamp=__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(gmail_email, app_password)
            server.send_message(msg)
        
        print("✓ Test email sent successfully!")
        print(f"  Check {recipient_email} inbox (and spam folder)")
    
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")


def main():
    """Main setup function"""
    print("\n" + "="*50)
    print("  Email Automation Bot - Setup Assistant")
    print("="*50 + "\n")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print(".env file not found!")
        print("Please copy .env.example to .env and fill in your configuration:")
        print("  cp .env.example .env")
        print("  Then edit .env with your credentials")
        return
    
    # Test connection
    if test_smtp_connection():
        print("\n" + "="*50)
        print("Configuration test PASSED ✓")
        print("="*50 + "\n")
        
        # Offer to send test email
        send_test_email()
        
        print("\n" + "="*50)
        print("Setup complete! You can now run:")
        print("  python email_automation.py")
        print("="*50 + "\n")
    else:
        print("\n" + "="*50)
        print("Configuration test FAILED ❌")
        print("="*50 + "\n")
        print("Please fix the issues above and try again.")


if __name__ == "__main__":
    main()
