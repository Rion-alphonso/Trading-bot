import yaml
from analytics.backtest_engine import BacktestEngine

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

custom_params = {
    'direction': 'BOTH',
    'days_mode': '24_5',
    'risk': 0.1,
    'tp': 10000,
    'sl': 1000,
    'sessions': '10:00-17:30,20:00-22:30'
}

engine = BacktestEngine(config)
engine.strategy = 'default'
engine.custom_params = custom_params
engine.symbol = 'XAUUSDm'
engine.timeframe_str = 'M5'

from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=365)
res = engine.run(start_date=start_date, end_date=end_date, num_candles=None)

for t in engine.trades:
    if abs(t['profit']) > 100:
        print(f"Massive trade found: {t}")
        
if engine.trades:
    print(f"Total trades: {len(engine.trades)}")
    print(f"Last trade: {engine.trades[-1]}")
