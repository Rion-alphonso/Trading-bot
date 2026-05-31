import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

mt5.initialize()

rates = mt5.copy_rates_from_pos("XAUUSDm", mt5.TIMEFRAME_M1, 0, 1)
if rates is not None and len(rates) > 0:
    t = pd.to_datetime(rates[0]['time'], unit='s')
    print("MT5 latest candle time (naive):", t)
    print("System local time:", datetime.now())
    print("System UTC time:", datetime.utcnow())
else:
    print("No rates found.")

mt5.shutdown()
