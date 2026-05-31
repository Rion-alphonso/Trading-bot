import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd

if not mt5.initialize():
    quit()

end = datetime.now()

# Try to get 1 candle from 10 years ago
start_10y = end - timedelta(days=365*10)
rates = mt5.copy_rates_range("XAUUSDm", mt5.TIMEFRAME_M5, start_10y, start_10y + timedelta(days=30))
if rates is not None and len(rates)>0:
    print("10 years ago returned data from:", pd.to_datetime(rates[0]['time'], unit='s'))

mt5.shutdown()
