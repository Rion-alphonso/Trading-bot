import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from utils.config import config
from utils.logger import system_logger, error_logger
import os
from utils.telegram_bot import telegram_bot

class NotificationManager:
    def __init__(self):
        email_config = config.get('notifications', {}).get('email', {})
        self.enabled = email_config.get('enabled', False)
        self.smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = email_config.get('smtp_port', 587)
        self.sender = email_config.get('sender', '')
        self.password = email_config.get('password', '')
        self.recipient = email_config.get('recipient', '')

    def send_alert(self, subject, message):
        """Logs the message and optionally sends an email alert."""
        system_logger.info(f"ALERT [{subject}]: {message}")
        if self.enabled:
            self._send_email(subject, message)
        # Send to Telegram
        telegram_bot.send_message(f"🔔 <b>{subject}</b>\n\n{message}")

    def _send_email(self, subject, body, attachment_path=None, html_body=None):
        if not self.sender or not self.password or not self.recipient:
            error_logger.error("Email credentials not fully configured.")
            return

        try:
            msg = MIMEMultipart('alternative') if html_body else MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = self.recipient
            msg['Subject'] = f"[MT5 XAUUSD Bot] {subject}"

            msg.attach(MIMEText(body, 'plain'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))

            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                    msg.attach(part)

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender, self.password)
            server.send_message(msg)
            server.quit()
            system_logger.info(f"Email sent successfully: {subject}")
        except Exception as e:
            error_logger.error(f"Failed to send email: {e}")

    def send_trade_opened_alert(self, data):
        subject = f"TRADE OPENED: {data['action']} #{data['ticket']}"
        telegram_msg = (
            f"🔵 <b>TRADE OPENED</b>\n\n"
            f"Action: {data['action']}\n"
            f"Level: {data['level']}\n"
            f"Size: {data['size']}\n"
            f"Entry: {data['entry_price']}\n"
            f"SL: {data['sl']}\n"
            f"TP: {data['tp']}"
        )
        telegram_bot.send_message(telegram_msg)
        system_logger.info(f"ALERT [{subject}]: {telegram_msg}")
        
        if self.enabled:
            html_body = ""
            try:
                template_path = os.path.join(os.path.dirname(__file__), 'templates', 'trade_opened.html')
                with open(template_path, 'r') as f:
                    html_template = f.read()
                color = "#10b981" if data['action'] == "BUY" else "#ef4444"
                html_body = html_template.format(**data, color=color)
            except Exception as e:
                error_logger.error(f"Failed to generate HTML email: {e}")
            self._send_email(subject, telegram_msg, html_body=html_body)

    def send_trade_closed_alert(self, data):
        subject = f"TRADE CLOSED: {data['action']} #{data['ticket']}"
        emoji = "🟢" if float(data['net_profit']) > 0 else "🔴"
        telegram_msg = (
            f"{emoji} <b>TRADE CLOSED</b>\n\n"
            f"Ticket: {data['ticket']}\n"
            f"Net Profit: ${data['net_profit']}\n"
            f"Close Price: {data['close_price']}\n"
            f"Duration: {data['duration']}\n"
            f"New Balance: ${data['new_balance']}\n"
            f"System Action: {data['next_step']}"
        )
        telegram_bot.send_message(telegram_msg)
        system_logger.info(f"ALERT [{subject}]: {telegram_msg}")
        
        if self.enabled:
            html_body = ""
            try:
                template_path = os.path.join(os.path.dirname(__file__), 'templates', 'trade_closed.html')
                with open(template_path, 'r') as f:
                    html_template = f.read()
                profit_color = "#10b981" if float(data['net_profit']) > 0 else "#ef4444"
                html_body = html_template.format(**data, profit_color=profit_color)
            except Exception as e:
                error_logger.error(f"Failed to generate HTML email: {e}")
            self._send_email(subject, telegram_msg, html_body=html_body)

    def send_startup_email(self, data):
        subject = "SYSTEM STARTUP"
        if not self.enabled: return
        try:
            template_path = os.path.join(os.path.dirname(__file__), 'templates', 'startup.html')
            with open(template_path, 'r') as f:
                html_template = f.read()
            html_body = html_template.format(**data)
            self._send_email(subject, "Trading Bot has started.", html_body=html_body)
        except Exception as e:
            error_logger.error(f"Failed to generate startup email: {e}")

    def send_hourly_report(self, data):
        subject = "HOURLY SNAPSHOT"
        if not self.enabled: return
        try:
            template_path = os.path.join(os.path.dirname(__file__), 'templates', 'hourly_report.html')
            with open(template_path, 'r') as f:
                html_template = f.read()
            html_body = html_template.format(**data)
            self._send_email(subject, "Hourly Report", html_body=html_body)
        except Exception as e:
            error_logger.error(f"Failed to generate hourly email: {e}")

    def send_daily_report(self, data):
        subject = f"DAILY AUDIT REPORT - {data.get('date_str', '')}"
        email_cfg = config.get('notifications', {}).get('email', {})
        if not email_cfg.get('enabled', False): return
        
        # Determine override recipient for reports
        report_recipient = email_cfg.get('report_recipient', email_cfg.get('recipient'))
        old_recipient = self.recipient
        self.recipient = report_recipient
        
        try:
            template_path = os.path.join(os.path.dirname(__file__), 'templates', 'daily_report.html')
            with open(template_path, 'r') as f:
                html_template = f.read()
            html_body = html_template.format(**data)
            self._send_email(subject, "Daily Report", html_body=html_body)
        except Exception as e:
            error_logger.error(f"Failed to generate daily email: {e}")
        finally:
            self.recipient = old_recipient

    def send_monthly_report(self, data):
        subject = f"MONTHLY SUMMARY - {data.get('month_name', '')}"
        email_cfg = config.get('notifications', {}).get('email', {})
        if not email_cfg.get('enabled', False): return
        
        report_recipient = email_cfg.get('report_recipient', email_cfg.get('recipient'))
        old_recipient = self.recipient
        self.recipient = report_recipient
        
        try:
            template_path = os.path.join(os.path.dirname(__file__), 'templates', 'monthly_report.html')
            with open(template_path, 'r') as f:
                html_template = f.read()
            html_body = html_template.format(**data)
            self._send_email(subject, "Monthly Report", html_body=html_body)
        except Exception as e:
            error_logger.error(f"Failed to generate monthly email: {e}")
        finally:
            self.recipient = old_recipient

notifier = NotificationManager()
