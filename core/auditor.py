import threading
import time
from collections import deque
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from data.database import db, Trade
from data.mt5_client import mt5_client
from utils.config import config
from utils.logger import system_logger

class Auditor:
    def __init__(self):
        self.running = False
        self.thread = None
        self.warnings = []
        
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            system_logger.info("Auditor system started.")

    def stop(self):
        self.running = False
        
    def _loop(self):
        last_check = datetime.min
        dispatched_today = False
        
        while self.running:
            now = datetime.now()
            
            # Check every 5 minutes
            if (now - last_check).total_seconds() >= 300:
                self.run_audit()
                last_check = now
                
            # Check if we should dispatch end of day email
            sessions_ist = config.get('trading', {}).get('sessions_ist', [])
            if sessions_ist:
                ends = []
                for s in sessions_ist:
                    try: ends.append(datetime.strptime(s['end'], "%H:%M").time())
                    except: pass
                if ends:
                    latest_end = max(ends)
                    # if now is after latest_end + 1 min and haven't dispatched today
                    end_time_today = datetime.combine(now.date(), latest_end)
                    if now >= end_time_today and now < end_time_today + timedelta(minutes=10):
                        if not dispatched_today:
                            self.dispatch_email()
                            dispatched_today = True
                            
            # Reset dispatch flag at midnight
            if now.hour == 0 and now.minute < 10:
                dispatched_today = False
                
            time.sleep(60)
            
    def run_audit(self):
        try:
            # 1. MT5 vs DB Consistency
            session = db.get_session()
            db_open_trades = session.query(Trade).filter(Trade.status == 'OPEN').all()
            db_tickets = set(t.ticket for t in db_open_trades)
            
            mt5_open = mt5_client.get_open_positions()
            mt5_tickets = set(p.ticket for p in mt5_open)
            
            ghost_trades = mt5_tickets - db_tickets
            missing_trades = db_tickets - mt5_tickets
            
            if ghost_trades:
                self.warnings.append(f"[{datetime.now().strftime('%H:%M')}] Ghost Trades in MT5 not in DB: {ghost_trades}")
            if missing_trades:
                self.warnings.append(f"[{datetime.now().strftime('%H:%M')}] Missing Trades in MT5 but OPEN in DB: {missing_trades}")
                
            session.close()
            
            # 2. Log Scraping
            log_dir = config.get('logging', {}).get('log_dir', 'logs')
            error_log = os.path.join(log_dir, 'error.log')
            if os.path.exists(error_log):
                with open(error_log, 'r') as f:
                    lines = deque(f, 50)
                    # Check last 50 lines for new errors
                    for line in lines[-50:]:
                        if 'ERROR' in line or 'Exception' in line:
                            if line.strip() not in self.warnings:
                                self.warnings.append(line.strip())
                                
            # 3. Database Size limit
            db_path = config.get('database', {}).get('db_path', 'trading_bot.sqlite')
            if os.path.exists(db_path):
                size_mb = os.path.getsize(db_path) / (1024 * 1024)
                if size_mb > 500:
                    self.warnings.append(f"[{datetime.now().strftime('%H:%M')}] DB Size Warning: {size_mb:.2f} MB")
                    
        except Exception as e:
            system_logger.error(f"Auditor error: {e}")

    def dispatch_email(self):
        try:
            from utils.notifications import notifier
            from data.state import state_manager
            
            # Fetch daily stats
            session = db.get_session()
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_trades = session.query(Trade).filter(Trade.close_time >= today_start).all()
            session.close()
            
            total_trades = len(today_trades)
            net_profit_val = sum(t.net_profit for t in today_trades if t.net_profit)
            
            profit_color = "#10b981" if net_profit_val >= 0 else "#ef4444"
            profit_str = f"${net_profit_val:.2f}"
            if net_profit_val > 0: profit_str = "+" + profit_str
            
            end_balance = state_manager.get_state('current_balance', 0.0)
            
            warnings_html = ""
            if not self.warnings:
                warnings_html = "<div class='no-warnings'>No issues detected today. System is healthy.</div>"
            else:
                warnings_html = "<div class='warnings'><strong>System Warnings:</strong><ul>"
                for w in set(self.warnings):
                    warnings_html += f"<li>{w}</li>"
                warnings_html += "</ul></div>"
                
            data = {
                'date_str': datetime.now().strftime('%Y-%m-%d'),
                'net_profit': profit_str,
                'profit_color': profit_color,
                'total_trades': total_trades,
                'end_balance': f"{end_balance:.2f}",
                'warnings_html': warnings_html
            }
            
            notifier.send_daily_report(data)
            self.warnings.clear()
            system_logger.info("Daily Audit Report dispatched via NotificationManager.")
        except Exception as e:
            system_logger.error(f"Failed to dispatch audit report: {e}")

auditor = Auditor()
