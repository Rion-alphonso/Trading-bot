import urllib.request
import json

data = json.dumps({
    'duration_mode': 'days',
    'duration_val': 30,
    'capital': 1110.0,
    'spread': 10.0,
    'comm': 0.0,
    'strategy': 'default',
    'symbol': 'XAUUSDm',
    'timeframe': 'M5',
    'custom_params': {}
}).encode('utf-8')

req = urllib.request.Request('http://localhost:5000/api/backtest/run', data=data, headers={'Content-Type': 'application/json'})
res = json.loads(urllib.request.urlopen(req).read())

ohlc = res.get('ohlc', [])
print(f"OHLC Length: {len(ohlc)}")
if ohlc:
    print(f"First OHLC: {ohlc[0]}")
    print(f"Last OHLC: {ohlc[-1]}")
    
trades = res.get('trades', [])
print(f"Trades Length: {len(trades)}")
if trades:
    print(f"First Trade: {trades[0]}")
