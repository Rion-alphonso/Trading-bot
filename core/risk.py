from data.mt5_client import mt5_client
from data.state import state_manager
from utils.config import config
from utils.logger import error_logger

class RiskManager:
    def __init__(self):
        pass

    def calculate_lot_size(self, balance):
        """Returns compounding lot size based on risk percentage or multiplier."""
        initial_capital = config.get('trading', {}).get('initial_capital', 1110.0)
        # Using the same multiplier logic from before based on initial_capital
        multiplier = max(1, int(balance // initial_capital))
        
        # In a fully risk_percent based setup, we would calculate 
        # based on account size and SL points. But for now, 
        # we will retain the multiplier of 0.01 base logic for safety:
        lot_size = 0.01 * multiplier
        
        return round(lot_size, 2)

    def get_sl_tp_prices(self, action):
        """Calculates SL and TP absolute prices based on the flat config."""
        trading_cfg = config.get('trading', {})
        sl_points = trading_cfg.get('sl_points', 1000)
        tp_points = trading_cfg.get('tp_points', 10000)

        symbol_info = mt5_client.get_symbol_info()
        if not symbol_info:
            return None, None

        point = symbol_info['point']
        
        if action == 'BUY':
            ask = symbol_info['ask']
            sl_price = ask - (sl_points * point)
            tp_price = ask + (tp_points * point)
        else:
            bid = symbol_info['bid']
            sl_price = bid + (sl_points * point)
            tp_price = bid - (tp_points * point)
            
        return round(sl_price, symbol_info['digits']), round(tp_price, symbol_info['digits'])

risk_manager = RiskManager()
