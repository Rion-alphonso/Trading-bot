import MetaTrader5 as mt5
from datetime import datetime, timedelta

if not mt5.initialize():
    quit()

end_time = datetime.now()
start_time = end_time - timedelta(days=365)

rates = mt5.copy_rates_range("XAUUSDm", mt5.TIMEFRAME_M5, start_time, end_time)
print("1 year copy_rates_range:", len(rates) if rates is not None else "None", mt5.last_error())

mt5.shutdown()
