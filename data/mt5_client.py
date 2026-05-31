import MetaTrader5 as mt5
from utils.logger import system_logger, error_logger
from utils.config import config
import time
from datetime import datetime

class MT5Client:
    def __init__(self):
        self.symbol = config.get('trading', {}).get('symbol', 'XAUUSD')
        self.connected = False

    def initialize(self):
        """Initializes the MT5 connection."""
        if not mt5.initialize():
            error_logger.error(f"MT5 initialize() failed, error code = {mt5.last_error()}")
            return False
        
        self.connected = True
        system_logger.info("MT5 initialized successfully.")
        
        # Ensure symbol is available
        if_selected = mt5.symbol_select(self.symbol, True)
        if not if_selected:
            error_logger.error(f"Failed to select symbol {self.symbol}")
            return False
        
        return True

    def shutdown(self):
        if self.connected:
            mt5.shutdown()
            self.connected = False
            system_logger.info("MT5 connection closed.")

    def get_symbol_info(self):
        """Retrieves symbol specifications (point, contract size, etc.)."""
        info = mt5.symbol_info(self.symbol)
        if info is None:
            error_logger.error(f"Failed to get symbol info for {self.symbol}")
            return None
        return {
            'point': info.point,
            'contract_size': info.trade_contract_size,
            'digits': info.digits,
            'ask': info.ask,
            'bid': info.bid
        }

    def get_account_info(self):
        """Retrieves current account balance, equity, and margin."""
        info = mt5.account_info()
        if info is None:
            error_logger.error("Failed to get account info")
            return None
        return {
            'balance': info.balance,
            'equity': info.equity,
            'margin': info.margin,
            'free_margin': info.margin_free
        }

    def place_order(self, action, lot_size, sl=None, tp=None, magic=123456):
        """Places a market BUY or SELL order."""
        point = self.get_symbol_info()['point']
        
        order_type = mt5.ORDER_TYPE_BUY if action == 'BUY' else mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(self.symbol).ask if action == 'BUY' else mt5.symbol_info_tick(self.symbol).bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": float(lot_size),
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": magic,
            "comment": "XAUUSD Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        if sl:
            request["sl"] = sl
        if tp:
            request["tp"] = tp

        result = mt5.order_send(request)
        
        if result is None:
            error_logger.error(f"Order failed: Connection lost or MT5 rejected request. Error: {mt5.last_error()}")
            return None
            
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_logger.error(f"Order failed: {result.retcode} - {result.comment}")
            return None
            
        system_logger.info(f"Order placed successfully: Ticket {result.order}")
        return result

    def get_open_positions(self, magic=123456):
        """Returns open positions for the specific magic number."""
        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None:
            return []
        
        bot_positions = [p for p in positions if p.magic == magic]
        return bot_positions

    def get_closed_trade_profit(self, ticket):
        """Retrieves the net profit and exact timestamps for a specific position ticket."""
        deals = mt5.history_deals_get(position=ticket)
        if deals is None or len(deals) == 0:
            return None, None, None, None
            
        # Verify the OUT deal has actually arrived to avoid race conditions
        out_deals = [d for d in deals if d.entry == mt5.DEAL_ENTRY_OUT]
        if not out_deals:
            return None, None, None, None
            
        total_profit = sum(deal.profit + deal.commission + deal.swap for deal in deals)
        
        close_price = out_deals[-1].price
        close_time = datetime.fromtimestamp(out_deals[-1].time)
        
        in_deals = [d for d in deals if d.entry == mt5.DEAL_ENTRY_IN]
        open_time = datetime.fromtimestamp(in_deals[0].time) if in_deals else datetime.utcnow()
        
        return total_profit, close_price, open_time, close_time

    def get_recent_candles(self, timeframe, count=100):
        """Retrieves recent candles for indicator calculations."""
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, count)
        if rates is None:
            error_logger.error(f"Failed to copy rates for {self.symbol}")
            return []
        return rates

mt5_client = MT5Client()
