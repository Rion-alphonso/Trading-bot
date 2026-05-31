import pytz
from datetime import datetime
from utils.config import config

class SessionManager:
    def __init__(self):
        self.ist_tz = pytz.timezone('Asia/Kolkata')
        self.sessions = config.get('trading', {}).get('sessions_ist', [])

    def is_active_session(self):
        """Checks if current time in IST is within active trading sessions."""
        now_ist = datetime.now(self.ist_tz)
        current_time = now_ist.time()

        for session in self.sessions:
            start_time = datetime.strptime(session['start'], '%H:%M').time()
            end_time = datetime.strptime(session['end'], '%H:%M').time()
            
            if start_time <= current_time <= end_time:
                return True
        return False

session_manager = SessionManager()
