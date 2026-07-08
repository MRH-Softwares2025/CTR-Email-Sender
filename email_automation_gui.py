#!/usr/bin/env python3
"""
Email Automation Bot - GUI Version
Graphical interface for managing email automation
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from email_automation import EmailAutomationBot, EmailAutomationConfig
from datetime import datetime
from notification_system import get_notification_manager


class EmailAutomationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Email Automation Bot")
        self.root.geometry("800x600")
        
        self.bot = None
        self.is_running = False
        self.stop_event = threading.Event()
        
        # Create GUI
        self.create_widgets()
        
        # Initialize bot
        self.initialize_bot()
        
        # Start notification checker
        self.notification_manager = get_notification_manager()
        self.start_notification_checker()
    
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Email Automation Bot", 
            font=('Helvetica', 16, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Configuration Section
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Configuration labels and editable fields
        self.config_labels = {}
        self.config_entries = {}
        
        # Read-only fields
        readonly_items = [
            ('GMAIL_EMAIL', 'Gmail Email'),
            ('START_HOUR', 'Start Hour'),
            ('END_HOUR', 'End Hour'),
            ('EMAILS_PER_HOUR', 'Emails Per Hour')
        ]
        
        for i, (env_var, label_text) in enumerate(readonly_items):
            ttk.Label(config_frame, text=f"{label_text}:").grid(
                row=i//2, column=(i%2)*2, sticky=tk.W, padx=(0, 5)
            )
            value_label = ttk.Label(config_frame, text="Loading...", font=('Consolas', 9))
            value_label.grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=(0, 20))
            self.config_labels[env_var] = value_label
        
        # Editable fields
        ttk.Label(config_frame, text="Recipient Email (fixed):").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        self.recipient_entry = ttk.Entry(config_frame, width=40)
        self.recipient_entry.grid(row=2, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(config_frame, text="Email Subject:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5))
        self.subject_entry = ttk.Entry(config_frame, width=40)
        self.subject_entry.grid(row=3, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(config_frame, text="Email Body:").grid(row=4, column=0, sticky=tk.NW, padx=(0, 5))
        
        # Formatting toolbar
        format_frame = ttk.Frame(config_frame)
        format_frame.grid(row=4, column=1, sticky=tk.W, padx=(0, 20))
        
        self.bold_btn = ttk.Button(format_frame, text="Bold", command=self.apply_bold, width=8)
        self.bold_btn.grid(row=0, column=0, padx=2)
        
        self.italic_btn = ttk.Button(format_frame, text="Italic", command=self.apply_italic, width=8)
        self.italic_btn.grid(row=0, column=1, padx=2)
        
        self.underline_btn = ttk.Button(format_frame, text="Underline", command=self.apply_underline, width=10)
        self.underline_btn.grid(row=0, column=2, padx=2)
        
        self.body_text = scrolledtext.ScrolledText(config_frame, height=4, width=40, font=('Consolas', 9))
        self.body_text.grid(row=5, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(config_frame, text="Time Variation (seconds):").grid(row=6, column=0, sticky=tk.W, padx=(0, 5))
        self.variation_entry = ttk.Entry(config_frame, width=10)
        self.variation_entry.grid(row=6, column=1, sticky=tk.W, padx=(0, 20))
        
        # Save configuration button
        ttk.Button(config_frame, text="Save Configuration", command=self.save_config).grid(
            row=7, column=0, columnspan=2, pady=10
        )
        
        # Statistics Section
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="10")
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.stats_labels = {}
        stat_items = [
            ('emails_sent_today', 'Emails Sent Today'),
            ('emails_sent_total', 'Total Emails Sent'),
            ('failed_emails', 'Failed Emails'),
            ('daily_limit', 'Daily Limit')
        ]
        
        for i, (stat_key, label_text) in enumerate(stat_items):
            ttk.Label(stats_frame, text=f"{label_text}:").grid(
                row=i//2, column=(i%2)*2, sticky=tk.W, padx=(0, 5)
            )
            value_label = ttk.Label(stats_frame, text="0", font=('Consolas', 10, 'bold'))
            value_label.grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=(0, 20))
            self.stats_labels[stat_key] = value_label
        
        # Control Buttons Section
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Buttons
        ttk.Button(control_frame, text="Send Single Email", command=self.send_single).grid(
            row=0, column=0, padx=5, pady=5
        )
        ttk.Button(control_frame, text="Send Batch", command=self.send_batch_dialog).grid(
            row=0, column=1, padx=5, pady=5
        )
        ttk.Button(control_frame, text="Start Continuous Mode", command=self.start_continuous).grid(
            row=0, column=2, padx=5, pady=5
        )
        ttk.Button(control_frame, text="Stop", command=self.stop_bot).grid(
            row=0, column=3, padx=5, pady=5
        )
        ttk.Button(control_frame, text="Refresh Stats", command=self.refresh_stats).grid(
            row=0, column=4, padx=5, pady=5
        )
        
        # Log Section
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Notification Section
        notification_frame = ttk.LabelFrame(main_frame, text="Notifications", padding="10")
        notification_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.notification_text = scrolledtext.ScrolledText(notification_frame, height=6, font=('Consolas', 9))
        self.notification_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        notification_frame.columnconfigure(0, weight=1)
        notification_frame.rowconfigure(0, weight=1)
        
        # Clear notifications button
        ttk.Button(notification_frame, text="Clear Notifications", command=self.clear_notifications).grid(
            row=1, column=0, pady=5
        )
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E))
    
    def initialize_bot(self):
        """Initialize the email bot"""
        try:
            import os
            from dotenv import load_dotenv

            script_dir = os.path.dirname(os.path.abspath(__file__))
            env_path = os.path.join(script_dir, '.env')
            load_dotenv(env_path)

            config = EmailAutomationConfig(
                gmail_email=os.getenv('GMAIL_EMAIL', ''),
                app_password=os.getenv('GMAIL_APP_PASSWORD', ''),
                email_subject=os.getenv('EMAIL_SUBJECT', 'Automated Email'),
                email_body=os.getenv('EMAIL_BODY', 'This is an automated email.'),
                start_hour=int(os.getenv('START_HOUR', 9)),
                end_hour=int(os.getenv('END_HOUR', 17)),
                emails_per_hour=int(os.getenv('EMAILS_PER_HOUR', 125)),
                time_variation_seconds=float(os.getenv('TIME_VARIATION_SECONDS', 300))
            )
            self.bot = EmailAutomationBot(config)
            self.update_config_display()
            self.refresh_stats()
            self.log("Bot initialized successfully")
            self.status_var.set("Ready")
        except Exception as e:
            self.log(f"Error initializing bot: {e}")
            self.status_var.set("Error - Check configuration")
            messagebox.showerror("Initialization Error", f"Failed to initialize bot:\n{e}")
    
    def update_config_display(self):
        """Update configuration display"""
        import os
        from dotenv import load_dotenv
        
        # Load from the correct path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(script_dir, '.env')
        load_dotenv(env_path)
        
        config_map = {
            'GMAIL_EMAIL': os.getenv('GMAIL_EMAIL', 'Not set'),
            'RECIPIENT_EMAIL': os.getenv('RECIPIENT_EMAIL', 'Not set'),
            'EMAIL_SUBJECT': os.getenv('EMAIL_SUBJECT', 'Not set'),
            'EMAIL_BODY': os.getenv('EMAIL_BODY', 'Not set'),
            'START_HOUR': os.getenv('START_HOUR', 'Not set'),
            'END_HOUR': os.getenv('END_HOUR', 'Not set'),
            'EMAILS_PER_HOUR': os.getenv('EMAILS_PER_HOUR', 'Not set'),
            'TIME_VARIATION_SECONDS': os.getenv('TIME_VARIATION_SECONDS', 'Not set')
        }
        
        for env_var, label in self.config_labels.items():
            value = config_map.get(env_var, 'Not set')
            # Truncate long values
            if len(str(value)) > 30:
                value = str(value)[:27] + "..."
            label.config(text=value)
        
        # Update editable fields
        self.recipient_entry.delete(0, tk.END)
        self.recipient_entry.insert(0, EmailAutomationBot.FIXED_RECIPIENT_EMAIL)
        self.recipient_entry.config(state='readonly')

        self.subject_entry.delete(0, tk.END)
        self.subject_entry.insert(0, config_map.get('EMAIL_SUBJECT', ''))
        
        self.body_text.delete(1.0, tk.END)
        self.body_text.insert(1.0, config_map.get('EMAIL_BODY', ''))
        
        self.variation_entry.delete(0, tk.END)
        self.variation_entry.insert(0, config_map.get('TIME_VARIATION_SECONDS', ''))
    
    def save_config(self):
        """Save configuration to .env file"""
        try:
            import os
            from dotenv import load_dotenv
            
            # Get script directory and .env path
            script_dir = os.path.dirname(os.path.abspath(__file__))
            env_path = os.path.join(script_dir, '.env')
            
            if not os.path.exists(env_path):
                messagebox.showerror("Error", f".env file not found at {env_path}")
                return
            
            # Read all lines
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Get new values
            new_subject = self.subject_entry.get()
            new_body = self.body_text.get(1.0, tk.END).strip()
            new_variation = self.variation_entry.get()
            
            # Update lines
            updated_lines = []
            for line in lines:
                if line.startswith('EMAIL_SUBJECT='):
                    updated_lines.append(f'EMAIL_SUBJECT={new_subject}\n')
                elif line.startswith('EMAIL_BODY='):
                    updated_lines.append(f'EMAIL_BODY={new_body}\n')
                elif line.startswith('TIME_VARIATION_SECONDS='):
                    updated_lines.append(f'TIME_VARIATION_SECONDS={new_variation}\n')
                else:
                    updated_lines.append(line)
            
            # Write back
            with open(env_path, 'w') as f:
                f.writelines(updated_lines)
            
            # Reload environment from the correct path
            load_dotenv(env_path)
            
            # Update bot configuration
            if self.bot:
                self.bot.email_subject = new_subject
                self.bot.email_body = new_body
                try:
                    self.bot.time_variation_seconds = float(new_variation)
                except ValueError:
                    pass  # Keep old value if invalid
            
            self.log("Configuration saved successfully")
            messagebox.showinfo("Success", "Configuration saved to .env file")
            
        except Exception as e:
            self.log(f"Error saving configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration:\n{e}")
    
    def refresh_stats(self):
        """Refresh statistics display"""
        if self.bot:
            stats = self.bot.get_statistics()
            for stat_key, label in self.stats_labels.items():
                label.config(text=str(stats.get(stat_key, 0)))
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def send_single(self):
        """Send a single email"""
        if not self.bot:
            messagebox.showerror("Error", "Bot not initialized")
            return
        
        # Use current values from editable fields
        custom_subject = self.subject_entry.get()
        custom_body = self.body_text.get(1.0, tk.END).strip()
        
        self.status_var.set("Sending single email...")
        self.log("Sending single email...")
        
        def send():
            try:
                success = self.bot.send_email(custom_subject, custom_body)
                
                if success:
                    self.log("✓ Email sent successfully")
                    self.refresh_stats()
                    messagebox.showinfo("Success", "Email sent successfully!")
                else:
                    self.log("✗ Failed to send email")
                    messagebox.showerror("Error", "Failed to send email")
                self.status_var.set("Ready")
            except Exception as e:
                self.log(f"✗ Error: {e}")
                messagebox.showerror("Error", f"Error sending email:\n{e}")
                self.status_var.set("Error")
        
        threading.Thread(target=send, daemon=True).start()
    
    def send_batch_dialog(self):
        """Show dialog to send batch of emails"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Send Batch")
        dialog.geometry("300x150")
        
        ttk.Label(dialog, text="Number of emails:").grid(row=0, column=0, padx=10, pady=10)
        
        num_emails_var = tk.StringVar(value="10")
        entry = ttk.Entry(dialog, textvariable=num_emails_var)
        entry.grid(row=0, column=1, padx=10, pady=10)
        
        def send_batch():
            try:
                num = int(num_emails_var.get())
                dialog.destroy()
                self.send_batch(num)
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
        
        ttk.Button(dialog, text="Send", command=send_batch).grid(row=1, column=0, columnspan=2, pady=10)
    
    def send_batch(self, num_emails):
        """Send batch of emails"""
        if not self.bot:
            messagebox.showerror("Error", "Bot not initialized")
            return
        
        # Use current values from editable fields
        custom_subject = self.subject_entry.get()
        custom_body = self.body_text.get(1.0, tk.END).strip()
        
        self.status_var.set(f"Sending batch of {num_emails} emails...")
        self.log(f"Starting batch of {num_emails} emails...")
        
        def send():
            try:
                self.bot.email_subject = custom_subject
                self.bot.email_body = custom_body
                self.bot.send_batch(num_emails)
                
                self.log(f"✓ Batch completed")
                self.refresh_stats()
                messagebox.showinfo("Success", f"Batch of {num_emails} emails completed!")
                self.status_var.set("Ready")
            except Exception as e:
                self.log(f"✗ Error: {e}")
                messagebox.showerror("Error", f"Error sending batch:\n{e}")
                self.status_var.set("Error")
        
        threading.Thread(target=send, daemon=True).start()
    
    def start_continuous(self):
        """Start continuous mode"""
        if not self.bot:
            messagebox.showerror("Error", "Bot not initialized")
            return
        
        if self.is_running:
            messagebox.showwarning("Warning", "Bot is already running")
            return
        
        confirm = messagebox.askyesno(
            "Confirm",
            "Start continuous mode? This will send emails until the daily limit is reached.\n\nPress Stop to halt."
        )
        
        if not confirm:
            return
        
        self.is_running = True
        self.stop_event.clear()
        self.status_var.set("Running continuous mode...")
        self.log("Starting continuous mode...")
        
        def run_continuous():
            try:
                while self.is_running and not self.stop_event.is_set():
                    current_hour = datetime.now().hour
                    if not (self.bot.start_hour <= current_hour < self.bot.end_hour):
                        self.log(f"Outside operating hours. Waiting...")
                        time.sleep(60)
                        continue
                    
                    success = self.bot.send_email()
                    if not success:
                        self.log("Failed to send email. Retrying in 60 seconds...")
                        time.sleep(60)
                        continue
                    
                    self.refresh_stats()
                    
                    if self.bot.emails_sent_today >= self.bot._calculate_daily_limit():
                        self.log("Daily limit reached. Stopping.")
                        break
                    
                    interval = self.bot._calculate_interval()
                    time.sleep(interval)
                
                self.is_running = False
                self.status_var.set("Ready")
                self.log("Continuous mode stopped")
                
            except Exception as e:
                self.log(f"✗ Error in continuous mode: {e}")
                self.is_running = False
                self.status_var.set("Error")
        
        threading.Thread(target=run_continuous, daemon=True).start()
    
    def stop_bot(self):
        """Stop the bot"""
        if self.is_running or (self.bot and self.bot.stop_requested == False):
            self.is_running = False
            self.stop_event.set()
            if self.bot:
                self.bot.request_stop()
            self.log("Stop signal sent...")
            self.status_var.set("Stopping...")
        else:
            messagebox.showinfo("Info", "Bot is not currently running")
    
    def apply_bold(self):
        """Apply bold formatting to selected text"""
        self._apply_formatting('**', '**')
    
    def apply_italic(self):
        """Apply italic formatting to selected text"""
        self._apply_formatting('*', '*')
    
    def apply_underline(self):
        """Apply underline formatting to selected text"""
        self._apply_formatting('__', '__')
    
    def _apply_formatting(self, prefix, suffix):
        """Apply formatting to selected text in the body text widget"""
        try:
            # Get current selection
            sel_start = self.body_text.index(tk.SEL_FIRST)
            sel_end = self.body_text.index(tk.SEL_LAST)
            
            # Get selected text
            selected_text = self.body_text.get(sel_start, sel_end)
            
            # Apply formatting
            formatted_text = f"{prefix}{selected_text}{suffix}"
            
            # Replace the selected text with formatted text
            self.body_text.delete(sel_start, sel_end)
            self.body_text.insert(sel_start, formatted_text)
            
        except tk.TclError:
            # No text selected, just insert formatting markers at cursor
            cursor_pos = self.body_text.index(tk.INSERT)
            self.body_text.insert(cursor_pos, f"{prefix}{suffix}")
            self.body_text.mark_set(tk.INSERT, f"{cursor_pos}+{len(prefix)} chars")
    
    def start_notification_checker(self):
        """Start background thread to check for notifications"""
        def check_notifications():
            while not self.stop_event.is_set():
                try:
                    self.update_notification_display()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    self.log(f"Error checking notifications: {e}")
                    time.sleep(30)
        
        thread = threading.Thread(target=check_notifications, daemon=True)
        thread.start()
    
    def update_notification_display(self):
        """Update the notification display"""
        try:
            notifications = self.notification_manager.get_active_notifications()
            if not notifications:
                self.notification_text.delete(1.0, tk.END)
                self.notification_text.insert(tk.END, "No notifications")
                return
            
            display_text = ""
            for notification in notifications:
                priority_symbol = {
                    'critical': '🔴',
                    'urgent': '🟠',
                    'warning': '🟡',
                    'info': '🔵'
                }.get(notification.priority.value, '⚪')
                
                read_status = "✓" if notification.read else "○"
                timestamp = notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
                
                display_text += f"{priority_symbol} {read_status} [{notification.priority.value.upper()}] {notification.title}\n"
                display_text += f"   {notification.message}\n"
                display_text += f"   {timestamp}\n"
                display_text += "-" * 60 + "\n"
            
            self.notification_text.delete(1.0, tk.END)
            self.notification_text.insert(tk.END, display_text)
            
        except Exception as e:
            self.log(f"Error updating notification display: {e}")
    
    def clear_notifications(self):
        """Clear all notifications"""
        self.notification_manager.dismiss_all()
        self.notification_text.delete(1.0, tk.END)
        self.notification_text.insert(tk.END, "No notifications")
        self.log("All notifications cleared")


def main():
    root = tk.Tk()
    app = EmailAutomationGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
