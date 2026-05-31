import datetime
import yaml
import os
from analytics.backtest_engine import BacktestEngine

def load_base_config():
    """Load trading config from config.yaml if available."""
    try:
        with open('config.yaml', 'r') as f:
            cfg = yaml.safe_load(f)
        trading = cfg.get('trading', {})
        levels = trading.get('levels', {})
        tf = trading.get('timeframe_minutes', 5)
        tf_str = f"M{tf}" if isinstance(tf, int) else tf
        return {
            'symbol': trading.get('symbol', 'XAUUSDm'),
            'timeframe': tf_str,
            'capital': trading.get('initial_capital', 1110.0),
            'l1_risk': levels.get('1', {}).get('risk_percent', 1.0),
            'l1_tp':   levels.get('1', {}).get('tp_points', 2000),
            'l1_sl':   levels.get('1', {}).get('sl_points', 20000),
            'l2_risk': levels.get('2', {}).get('risk_percent', 10.0),
            'l2_tp':   levels.get('2', {}).get('tp_points', 2400),
            'l2_sl':   levels.get('2', {}).get('sl_points', 20000),
            'l3_risk': levels.get('3', {}).get('risk_percent', 100.0),
            'l3_tp':   levels.get('3', {}).get('tp_points', 3000),
            'l3_sl':   levels.get('3', {}).get('sl_points', 20000),
        }
    except Exception as e:
        print(f"Warning: Could not load config.yaml ({e}). Using built-in defaults.")
        return {}

def run_interactive():
    print("=======================================")
    print(" XAUUSD Backtesting Engine")
    print("=======================================\n")
    
    choice = input("Do you want to use default options? (y/n): ").strip().lower()
    
    base = load_base_config()
    days_back = 30

    if choice == 'n':
        print("\n--- Setup Custom Options ---")
        base['symbol']   = input(f"Symbol (default {base.get('symbol', 'XAUUSDm')}): ").strip() or base.get('symbol', 'XAUUSDm')
        tf_input = input(f"Timeframe (M1, M5, M15, H1, D1) [default {base.get('timeframe', 'M5')}]: ").strip().upper()
        base['timeframe'] = tf_input or base.get('timeframe', 'M5')
        base['capital']  = float(input(f"Initial Capital (default {base.get('capital', 1110.0)}): ").strip() or base.get('capital', 1110.0))
        
        print("\n[Level 1 Parameters]")
        base['l1_risk'] = float(input(f"Risk % (default {base.get('l1_risk', 1.0)}): ").strip() or base.get('l1_risk', 1.0))
        base['l1_tp']   = int(input(f"Take Profit in points (default {base.get('l1_tp', 2000)}): ").strip() or base.get('l1_tp', 2000))
        base['l1_sl']   = int(input(f"Stop Loss in points (default {base.get('l1_sl', 20000)}): ").strip() or base.get('l1_sl', 20000))

        print("\n[Level 2 Parameters]")
        base['l2_risk'] = float(input(f"Risk % (default {base.get('l2_risk', 10.0)}): ").strip() or base.get('l2_risk', 10.0))
        base['l2_tp']   = int(input(f"Take Profit in points (default {base.get('l2_tp', 2400)}): ").strip() or base.get('l2_tp', 2400))
        base['l2_sl']   = int(input(f"Stop Loss in points (default {base.get('l2_sl', 20000)}): ").strip() or base.get('l2_sl', 20000))

        print("\n[Level 3 Parameters]")
        base['l3_risk'] = float(input(f"Risk % (default {base.get('l3_risk', 100.0)}): ").strip() or base.get('l3_risk', 100.0))
        base['l3_tp']   = int(input(f"Take Profit in points (default {base.get('l3_tp', 3000)}): ").strip() or base.get('l3_tp', 3000))
        base['l3_sl']   = int(input(f"Stop Loss in points (default {base.get('l3_sl', 20000)}): ").strip() or base.get('l3_sl', 20000))
        
        days_back = int(input("\nHow many days of history to test? (default 30): ").strip() or "30")
    else:
        sym  = base.get('symbol', 'XAUUSDm')
        cap  = base.get('capital', 1110.0)
        tf   = base.get('timeframe', 'M5')
        print(f"\nUsing defaults from config.yaml: Symbol={sym}, Timeframe={tf}, Capital={cap}")
        
    end_date   = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=days_back)
    
    engine = BacktestEngine(base)
    engine.run(start_date, end_date)

if __name__ == "__main__":
    run_interactive()
