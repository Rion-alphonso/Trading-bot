import json
from data.database import db, BotState
from utils.logger import system_logger, error_logger

class StateManager:
    """Manages the persistence and retrieval of the bot's state."""
    
    def __init__(self):
        self._ensure_defaults()

    def _ensure_defaults(self):
        session = db.get_session()
        try:
            defaults = {
                'next_direction': 'BUY',  # Alternate: BUY -> SELL
                'current_balance': 1110.0, # Initial Capital
                'last_processed_candle_time': None,
                'strategy_status': 'ACTIVE', # ACTIVE, STOPPED
                'current_win_streak': 0,
                'current_loss_streak': 0,
                'longest_win_streak': 0,
                'longest_loss_streak': 0,
                'total_trades': 0,
                'force_close': False,
                'risk_override': None,
                'direction_override': None,
                'session_override': None
            }
            
            for key, default_val in defaults.items():
                state_record = session.query(BotState).filter_by(key=key).first()
                if not state_record:
                    new_state = BotState(key=key, value=default_val)
                    session.add(new_state)
            session.commit()
        except Exception as e:
            session.rollback()
            error_logger.error(f"Error ensuring default state: {e}")
        finally:
            session.close()

    def get_state(self, key):
        session = db.get_session()
        try:
            record = session.query(BotState).filter_by(key=key).first()
            if record:
                return record.value
            return None
        finally:
            session.close()

    def set_state(self, key, value):
        session = db.get_session()
        try:
            record = session.query(BotState).filter_by(key=key).first()
            if record:
                record.value = value
            else:
                new_state = BotState(key=key, value=value)
                session.add(new_state)
            session.commit()
            system_logger.info(f"State updated: {key} = {value}")
        except Exception as e:
            session.rollback()
            error_logger.error(f"Failed to set state {key}: {e}")
        finally:
            session.close()

# Global state manager instance
state_manager = StateManager()
