import MetaTrader5 as mt5
from utils.config import config
from utils.logger import system_logger
from datetime import datetime

class CandleDetector:
    def __init__(self):
        self.symbol = config.get('trading', {}).get('symbol', 'XAUUSD')
        self.timeframe = mt5.TIMEFRAME_M5
        self.last_candle_time = None

    def is_new_candle(self):
        """Detects if a new M5 candle has formed."""
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 1)
        if rates is None or len(rates) == 0:
            return False

        current_candle_time = rates[0]['time']
        
        if self.last_candle_time is None:
            # First run, just record the current candle but DO NOT trigger mid-candle
            # This ensures we always wait for the NEXT candle to close before trading
            self.last_candle_time = current_candle_time
            return False
            
        if current_candle_time > self.last_candle_time:
            self.last_candle_time = current_candle_time
            return True
            
        return False

candle_detector = CandleDetector()
