from datetime import datetime, timedelta
import yaml
from analytics.backtest_engine import BacktestEngine

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Hardcode the TP and SL for testing the old period
config['trading']['tp_points'] = 10000
config['trading']['sl_points'] = 1000

engine = BacktestEngine(config['trading'])
end_date = datetime(2026, 5, 31)
start_date = end_date - timedelta(days=30)

engine.run(start_date, end_date)

wins = len([t for t in engine.trades if t['result'] == 'TP'])
total = len(engine.trades)
if total > 0:
    print(f'Win rate for period ending May 27: {wins/total*100:.2f}% (Wins: {wins}, Total: {total})')
else:
    print('No trades')
