import pandas as pd

class DummyEngine:
    def __init__(self):
        self.sl_price = 1999.0
        self.tp_price = 2010.0
        self.direction = 'BUY'
        
    def _check_trade_closure(self, high, low):
        if self.direction == 'BUY':
            if low <= self.sl_price: return 'SL'
            if high >= self.tp_price: return 'TP'
        return None

engine = DummyEngine()
print(engine._check_trade_closure(high=2000.0, low=1600.0))
