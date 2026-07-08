#!/usr/bin/env python3
"""
Email Automation Bot using Python + SMTP with Gmail App Password
Sends multiple emails to a fixed recipient with time variations
"""

import smtplib
import time
import random
import logging
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
from template_system import EmailTemplate, create_email_body

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class EmailAutomationConfig:
    gmail_email: str
    app_password: str
    email_subject: str = 'Automated Email'
    email_body: str = 'This is an automated email.'
    start_hour: int = 9
    end_hour: int = 17
    emails_per_hour: int = 125
    time_variation_seconds: float = 300.0


class EmailAutomationBot:
    FIXED_RECIPIENT_EMAIL = 'jesusislord.fmradio@gmail.com'

    def __init__(self, config: EmailAutomationConfig):
        self.gmail_email = config.gmail_email
        self.app_password = config.app_password
        self.recipient_email = self.FIXED_RECIPIENT_EMAIL
        self.email_subject = config.email_subject
        self.email_body = config.email_body
        self.start_hour = config.start_hour
        self.end_hour = config.end_hour
        self.emails_per_hour = config.emails_per_hour
        self.time_variation_seconds = config.time_variation_seconds

        self.emails_sent_today = 0
        self.emails_sent_total = 0
        self.failed_emails = 0

        self.stop_requested = False

        self._validate_config()

    def _validate_config(self):
        missing = []
        if not self.gmail_email:
            missing.append('gmail_email')
        if not self.app_password:
            missing.append('app_password')
        if not self.recipient_email:
            missing.append('recipient_email')

        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

        logger.info('Configuration validated successfully')

    def _calculate_daily_limit(self):
        return 2000

    def _calculate_interval(self):
        base_interval = 3600 / self.emails_per_hour
        variation_seconds = random.uniform(-self.time_variation_seconds, self.time_variation_seconds)
        interval = base_interval + variation_seconds
        return max(interval, 5)

    def _create_email(self, custom_subject: Optional[str] = None, custom_body: Optional[str] = None, 
                     template_variables: Optional[Dict[str, Any]] = None, use_html: bool = True):
        msg = MIMEMultipart('alternative')
        msg['From'] = self.gmail_email
        msg['To'] = self.recipient_email
        msg['Subject'] = custom_subject or self.email_subject
        
        body = custom_body or self.email_body
        
        # Process template if variables are provided
        if template_variables:
            template = EmailTemplate(body)
            template.set_variables(template_variables)
            html_body = template.render(html=True)
            plain_body = template.render_plain_text()
        else:
            # Auto-detect formatting and convert to HTML
            template = EmailTemplate(body)
            html_body = template.render(html=True)
            plain_body = template.render_plain_text()
        
        # Attach both plain text and HTML versions
        msg.attach(MIMEText(plain_body, 'plain'))
        if use_html:
            msg.attach(MIMEText(html_body, 'html'))
        
        return msg

    def verify_credentials(self):
        try:
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as server:
                server.starttls()
                server.login(self.gmail_email, self.app_password)
            return {'success': True, 'message': 'SMTP credentials verified successfully.'}
        except smtplib.SMTPAuthenticationError:
            message = 'Authentication failed. Check your Gmail address and app password.'
            logger.error(message)
            return {'success': False, 'message': message}
        except smtplib.SMTPException as e:
            message = f'SMTP error during credential verification: {e}'
            logger.error(message)
            return {'success': False, 'message': message}
        except Exception as e:
            message = f'Credential check failed: {e}'
            logger.error(message)
            return {'success': False, 'message': message}

    def send_email(self, custom_subject: Optional[str] = None, custom_body: Optional[str] = None,
                   template_variables: Optional[Dict[str, Any]] = None, use_html: bool = True):
        daily_limit = self._calculate_daily_limit()
        if self.emails_sent_today >= daily_limit:
            message = f"Daily limit reached ({daily_limit} emails)."
            logger.warning(message)
            return {'success': False, 'message': message}

        try:
            msg = self._create_email(custom_subject, custom_body, template_variables, use_html)
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.gmail_email, self.app_password)
                server.send_message(msg)
            
            # Update counters
            self.emails_sent_today += 1
            self.emails_sent_total += 1
            logger.info(f"Email sent successfully to {self.recipient_email}")
            return {'success': True, 'message': 'Email sent successfully.'}

        except smtplib.SMTPAuthenticationError:
            message = 'Authentication failed. Check your email and app password.'
            logger.error(message)
            self.failed_emails += 1
            return {'success': False, 'message': message}
        except smtplib.SMTPException as e:
            message = f'SMTP error occurred: {e}'
            logger.error(message)
            self.failed_emails += 1
            return {'success': False, 'message': message}
        except Exception as e:
            message = f'Unexpected error: {e}'
            logger.error(message)
            self.failed_emails += 1
            return {'success': False, 'message': message}

    def send_batch(self, num_emails: int):
        logger.info(f"Starting batch of {num_emails} emails")
        for i in range(num_emails):
            if self.stop_requested:
                logger.info('Stop requested. Halting batch.')
                self.stop_requested = False
                break

            current_hour = datetime.now().hour
            if not (self.start_hour <= current_hour < self.end_hour):
                logger.info(f"Outside operating hours ({self.start_hour}:00-{self.end_hour}:00). Pausing.")
                break

            result = self.send_email()
            if not result.get('success'):
                logger.error('Failed to send email. Waiting 60 seconds before retry...')
                time.sleep(60)
                continue

            if i < num_emails - 1:
                interval = self._calculate_interval()
                logger.info(f"Waiting {interval:.1f} seconds before next email...")
                time.sleep(interval)

        return {
            'success': True,
            'message': f'Batch completed. Sent: {self.emails_sent_today}, Failed: {self.failed_emails}'
        }

    def run_continuous(self):
        daily_limit = self._calculate_daily_limit()
        logger.info(f"Starting continuous mode. Daily limit: {daily_limit} emails")
        while self.emails_sent_today < daily_limit:
            current_hour = datetime.now().hour
            if not (self.start_hour <= current_hour < self.end_hour):
                logger.info(f"Outside operating hours. Sleeping until {self.start_hour}:00...")
                now = datetime.now()
                next_start = now.replace(hour=self.start_hour, minute=0, second=0, microsecond=0)
                if now.hour >= self.end_hour:
                    next_start += timedelta(days=1)
                sleep_seconds = (next_start - now).total_seconds()
                time.sleep(min(sleep_seconds, 3600))
                continue

            result = self.send_email()
            if not result.get('success'):
                logger.error('Failed to send email. Retrying in 60 seconds...')
                time.sleep(60)
                continue

            interval = self._calculate_interval()
            logger.info(f"Waiting {interval:.1f} seconds before next email...")
            time.sleep(interval)

        return {'success': True, 'message': 'Continuous mode completed.'}

    def reset_daily_counter(self):
        self.emails_sent_today = 0
        logger.info('Daily counter reset')

    def request_stop(self):
        self.stop_requested = True
        logger.info('Stop requested')

    def get_statistics(self):
        return {
            'emails_sent_today': self.emails_sent_today,
            'emails_sent_total': self.emails_sent_total,
            'failed_emails': self.failed_emails,
            'daily_limit': self._calculate_daily_limit(),
        }


def main():
    from dotenv import load_dotenv
    load_dotenv()

    config = EmailAutomationConfig(
        gmail_email=os.getenv('GMAIL_EMAIL', ''),
        app_password=os.getenv('GMAIL_APP_PASSWORD', ''),
        email_subject=os.getenv('EMAIL_SUBJECT', 'Automated Email'),
        email_body=os.getenv('EMAIL_BODY', 'This is an automated email.'),
        start_hour=int(os.getenv('START_HOUR', '9')),
        end_hour=int(os.getenv('END_HOUR', '17')),
        emails_per_hour=int(os.getenv('EMAILS_PER_HOUR', '125')),
        time_variation_seconds=float(os.getenv('TIME_VARIATION_SECONDS', '300')),
    )

    bot = EmailAutomationBot(config)

    print("\n=== Email Automation Bot ===")
    print("1. Send a single email")
    print("2. Send a batch of emails")
    print("3. Run continuous mode")
    print("4. View statistics")
    print("5. Exit")

    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        if choice == '1':
            result = bot.send_email()
            print(result)
        elif choice == '2':
            num_emails = int(input("Enter number of emails to send: "))
            result = bot.send_batch(num_emails)
            print(result)
        elif choice == '3':
            confirm = input("Start continuous mode? (yes/no): ").strip().lower()
            if confirm == 'yes':
                result = bot.run_continuous()
                print(result)
        elif choice == '4':
            print(bot.get_statistics())
        elif choice == '5':
            break
        else:
            print("Invalid choice, try again.")


if __name__ == '__main__':
    main()
