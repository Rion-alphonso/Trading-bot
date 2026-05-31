import MetaTrader5 as mt5
from datetime import datetime, timezone
import pandas as pd

if not mt5.initialize():
    print("MT5 initialization failed.")
    quit()

symbol = "XAUUSDm"
timeframe = mt5.TIMEFRAME_M5

rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 5)
if rates is not None:
    df = pd.DataFrame(rates)
    df['time_dt'] = pd.to_datetime(df['time'], unit='s')
    print("Last 5 candles:")
    print(df[['time', 'time_dt', 'open', 'close']])
    print(f"Current UTC time: {datetime.now(timezone.utc)}")
    print(f"Current Local time: {datetime.now()}")
else:
    print("Failed to get rates")

mt5.shutdown()
