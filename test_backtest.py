import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Add current dir to path to import analytics
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analytics.backtest_engine import BacktestEngine

config = {
    'symbol': 'XAUUSDm',
    'timeframe': 'M5',
    'capital': 1110.0,
    'spread': 10.0,
    'comm': 0.0,
    'strategy': 'buy_back',
    'custom_params': {},
    'l1_risk': 1.0, 'l1_tp': 10000, 'l1_sl': 1000,
    'l2_risk': 10.0, 'l2_tp': 10000, 'l2_sl': 1000,
    'l3_risk': 100.0, 'l3_tp': 10000, 'l3_sl': 1000,
}

engine = BacktestEngine(config)
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

print("Running backtest...")
success = engine.run(start_date, end_date)

if success:
    trades = engine.trades
    print(f"Total trades executed: {len(trades)}")
    
    # Analyze hours
    hours = [datetime.strptime(t['ENTRY TIME'], "%Y-%m-%d %H:%M:%S").hour for t in trades]
    hour_counts = pd.Series(hours).value_counts().sort_index()
    print("\nTrades per hour:")
    print(hour_counts)
else:
    print("Backtest failed.")
