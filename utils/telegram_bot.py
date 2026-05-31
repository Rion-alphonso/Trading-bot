import requests
import threading
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from utils.config import config
from utils.logger import system_logger, error_logger
from data.database import db, AccountSnapshot

class TelegramManager:
    def __init__(self):
        self._load_config()
        self.last_update_id = 0
        self.polling_thread = None
        self.stop_event = threading.Event()

    def _load_config(self):
        tg_cfg = config.get('notifications', {}).get('telegram', {})
        self.enabled = tg_cfg.get('enabled', False)
        self.token = tg_cfg.get('bot_token', '')
        self.chat_id = tg_cfg.get('chat_id', '')
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, text):
        if not self.enabled or not self.token or not self.chat_id:
            return
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            import subprocess, json
            result = subprocess.run(['curl', '-s', '-X', 'POST', f"{self.base_url}/sendMessage", '-H', 'Content-Type: application/json', '-d', json.dumps(payload)], capture_output=True, text=True)
            if result.stdout:
                data = json.loads(result.stdout)
                if not data.get('ok'):
                    error_logger.error(f"Telegram Send Error: {data.get('description')}")
        except Exception as e:
            error_logger.error(f"Telegram send error: {e}")

    def start_polling(self):
        if not self.enabled or not self.token:
            return
        if self.polling_thread is None or not self.polling_thread.is_alive():
            self.stop_event.clear()
            self.polling_thread = threading.Thread(target=self._poll_updates, daemon=True)
            self.polling_thread.start()
            system_logger.info("Telegram Remote Control polling started.")

    def _poll_updates(self):
        while not self.stop_event.is_set():
            try:
                import subprocess, json
                curl_cmd = ['curl', '-s', f"{self.base_url}/getUpdates?offset={self.last_update_id + 1}&timeout=5"]
                result = subprocess.run(curl_cmd, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout:
                    data = json.loads(result.stdout)
                    if not data.get('ok'):
                        error_logger.error(f"Telegram API Error: {data.get('description')}")
                        time.sleep(5)
                        continue
                        
                    for item in data.get('result', []):
                        self.last_update_id = item['update_id']
                        msg = item.get('message', {})
                        text = msg.get('text', '')
                        chat = msg.get('chat', {})
                        if str(chat.get('id')) == str(self.chat_id):
                            system_logger.info(f"Received command: {text}")
                            try:
                                self._handle_command(text)
                            except Exception as e:
                                system_logger.error(f"Error in _handle_command: {e}", exc_info=True)
            except Exception as e:
                system_logger.error(f"Error in _poll_updates: {e}", exc_info=True)
            time.sleep(1)

    def send_photo(self, photo_path):
        if not self.enabled or not self.token or not self.chat_id: return
        import subprocess
        subprocess.run(['curl', '-s', '-X', 'POST', f"{self.base_url}/sendPhoto", '-F', f'chat_id={self.chat_id}', '-F', f'photo=@{photo_path}'], capture_output=True)

    def _handle_command(self, cmd):
        from data.state import state_manager
        from data.database import db, AccountSnapshot, Trade, PerformanceMetrics
        import psutil
        import os
        
        args = cmd.strip().lower().split(' ')
        command = args[0]
        
        if command in ['/status', '/start']:
            session = db.get_session()
            snap = session.query(AccountSnapshot).order_by(AccountSnapshot.id.desc()).first()
            session.close()
            bal = snap.balance if snap else 0
            eq = snap.equity if snap else 0
            state = state_manager.get_state('strategy_status') or 'STOPPED'
            lvl = state_manager.get_state('current_level')
            nxt = state_manager.get_state('next_direction')
            self.send_message(f"📊 <b>Bot Status</b>\nState: {state}\nBalance: ${bal:.2f}\nEquity: ${eq:.2f}\nLevel: {lvl}\nNext: {nxt}")
            
        elif command == '/report':
            session = db.get_session()
            metrics = session.query(PerformanceMetrics).order_by(PerformanceMetrics.id.desc()).first()
            session.close()
            if metrics:
                self.send_message(f"📈 <b>Daily Report</b>\nTrades: {metrics.total_trades}\nPnL: ${metrics.daily_pnl:.2f}\nWin Rate: {metrics.win_rate:.1f}%")
            else:
                self.send_message("No report available yet.")
                
        elif command == '/history':
            session = db.get_session()
            trades = session.query(Trade).filter(Trade.status == 'CLOSED').order_by(Trade.close_time.desc()).limit(5).all()
            session.close()
            msg = "🕒 <b>Recent History</b>\n"
            for t in trades:
                msg += f"#{t.ticket} {t.type} L{t.level}: ${t.profit:.2f}\n"
            self.send_message(msg if trades else "No history found.")
            
        elif command == '/open':
            session = db.get_session()
            trade = session.query(Trade).filter(Trade.status == 'OPEN').first()
            session.close()
            if trade:
                self.send_message(f"🟢 <b>Open Position</b>\nTicket: {trade.ticket}\nType: {trade.type}\nOpen: {trade.open_price}\nLevel: {trade.level}")
            else:
                self.send_message("No open positions.")
                
        elif command == '/chart':
            try:
                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                session = db.get_session()
                snaps = session.query(AccountSnapshot).order_by(AccountSnapshot.id.desc()).limit(100).all()
                session.close()
                if not snaps:
                    self.send_message("Not enough data for chart.")
                    return
                snaps.reverse()
                equities = [s.equity for s in snaps]
                plt.figure(figsize=(8,4))
                plt.plot(equities, color='blue', label='Equity')
                plt.title('Equity Curve')
                plt.grid(True)
                plt.savefig('chart.png')
                plt.close()
                self.send_photo('chart.png')
            except Exception as e:
                self.send_message(f"Chart Error: {e}")
                
        elif command == '/logs':
            try:
                with open('logs/system.log', 'r') as f:
                    lines = f.readlines()[-15:]
                log_txt = "".join(lines)
                self.send_message(f"📜 <b>Recent Logs</b>\n<pre>{log_txt[-4000:]}</pre>")
            except:
                self.send_message("Could not read logs.")

        elif command == '/pause':
            state_manager.set_state('strategy_status', 'STOPPED')
            self.send_message("🛑 <b>Bot Paused</b>\nStrategy engine halted.")
            
        elif command == '/resume':
            state_manager.set_state('strategy_status', 'RUNNING')
            self.send_message("▶️ <b>Bot Resumed</b>\nStrategy engine started.")
            
        elif command == '/closeall':
            state_manager.set_state('force_close', True)
            self.send_message("🚨 <b>EMERGENCY</b>\nSignal sent to close all positions.")
            
        elif command == '/reset':
            state_manager.set_state('current_level', 1)
            self.send_message("🔄 <b>Reset</b>\nMartingale level reset to 1.")
            
        elif command == '/setrisk':
            if len(args) > 1:
                state_manager.set_state('risk_override', args[1])
                self.send_message(f"⚠️ <b>Risk Override</b>\nLevel 1 risk set to {args[1]}%")
            else:
                self.send_message("Usage: /setrisk 2.0")
                
        elif command == '/direction':
            if len(args) > 1 and args[1] in ['buy', 'sell']:
                state_manager.set_state('direction_override', args[1].upper())
                self.send_message(f"🧭 <b>Direction Override</b>\nNext trade forced to {args[1].upper()}")
            else:
                self.send_message("Usage: /direction buy")
                
        elif command == '/session':
            if len(args) > 1 and args[1] in ['on', 'off']:
                state_manager.set_state('session_override', args[1] == 'off')
                self.send_message(f"🕒 <b>Session Override</b>\nSession limits ignored: {args[1] == 'off'}")
            else:
                self.send_message("Usage: /session off")
                
        elif command == '/config':
            risk = state_manager.get_state('risk_override') or 'Default'
            sess = state_manager.get_state('session_override')
            d_over = state_manager.get_state('direction_override') or 'None'
            self.send_message(f"⚙️ <b>Config</b>\nRisk Override: {risk}\nSession Ignore: {sess}\nDir Override: {d_over}")
            
        elif command == '/health':
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            db_path = os.path.join('data', 'trading_bot.sqlite')
            db_size = os.path.getsize(db_path) / (1024*1024) if os.path.exists(db_path) else 0.0
            self.send_message(f"🩺 <b>Health</b>\nCPU: {cpu}%\nRAM: {mem}%\nDB Size: {db_size:.2f} MB")
        else:
            self.send_message("Unknown command. Available: /status, /report, /history, /open, /chart, /logs, /pause, /resume, /closeall, /reset, /setrisk, /direction, /session, /config, /health")

telegram_bot = TelegramManager()
