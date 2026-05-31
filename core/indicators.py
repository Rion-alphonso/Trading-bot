import pandas as pd
from data.mt5_client import mt5_client
from utils.config import config
from utils.logger import system_logger
import MetaTrader5 as mt5

class IndicatorEngine:
    def __init__(self):
        self.tf_map = {
            1: mt5.TIMEFRAME_M1, 5: mt5.TIMEFRAME_M5, 15: mt5.TIMEFRAME_M15,
            60: mt5.TIMEFRAME_H1, 1440: mt5.TIMEFRAME_D1
        }
        
    def evaluate_ema_crossover(self):
        """
        Evaluates EMA crossover for the current state.
        Returns: 'BUY', 'SELL', 'WAITING', or 'NONE' (if disabled)
        """
        indicators_cfg = config.get('trading', {}).get('indicators', {})
        if not indicators_cfg.get('ema_enabled', False):
            return 'NONE'
            
        fast_period = indicators_cfg.get('ema_fast', 9)
        slow_period = indicators_cfg.get('ema_slow', 21)
        timeframe_minutes = config.get('trading', {}).get('timeframe_minutes', 5)
        timeframe = self.tf_map.get(timeframe_minutes, mt5.TIMEFRAME_M5)
        
        rates = mt5_client.get_recent_candles(timeframe, max(slow_period * 3, 100))
        if len(rates) < slow_period:
            system_logger.warning("IndicatorEngine: Not enough candles for EMA calculation.")
            return 'WAITING'
            
        df = pd.DataFrame(rates)
        df['ema_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()
        
        # Look at the last two fully closed candles
        # rates[-1] is the forming candle, rates[-2] is the last closed, rates[-3] is prev closed
        latest = df.iloc[-2]
        prev = df.iloc[-3]
        
        # Check crossover
        if prev['ema_fast'] <= prev['ema_slow'] and latest['ema_fast'] > latest['ema_slow']:
            return 'BUY'
        elif prev['ema_fast'] >= prev['ema_slow'] and latest['ema_fast'] < latest['ema_slow']:
            return 'SELL'
            
        # If no explicit crossover just happened, return WAITING
        return 'WAITING'

indicator_engine = IndicatorEngine()
