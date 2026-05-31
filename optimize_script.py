import MetaTrader5 as mt5
from analytics.backtest_engine import BacktestEngine
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def run_optimization():
    # Extensive Grid parameters
    sl_points = [500, 1000, 1500, 2000, 3000]
    tp_points = [1000, 2000, 5000, 8000, 10000, 15000]
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90) # 3 months test
    
    results = []
    
    print("Starting Grid Search Optimization for Gold (XAUUSDm) over last 90 days...")
    
    for sl in sl_points:
        for tp in tp_points:
            config = {
                'symbol': 'XAUUSDm',
                'timeframe': 'M5',
                'capital': 1000.0,
                'spread': 0.0,
                'comm': 0.0,
                'strategy': 'custom',
                'custom_params': {
                    'risk': 1.0, # 1% risk to see proper compounding differences
                    'sl': sl,
                    'tp': tp,
                    'direction': 'BOTH',
                    'sessions': '10:00-17:30,20:00-22:30'
                },
                'l1_risk': 1.0,
                'l1_tp': tp,
                'l1_sl': sl,
                'l2_risk': 10.0,
                'l2_tp': tp,
                'l2_sl': sl,
                'l3_risk': 100.0,
                'l3_tp': tp,
                'l3_sl': sl,
            }
            
            # Monkeypatch the engine's excel generator so it doesn't spam files
            engine = BacktestEngine(config)
            engine._generate_excel = lambda: None 
            
            success = engine.run(start_date=start_date, end_date=end_date)
            if not success or not engine.trades:
                continue
                
            profit = engine.balance - engine.initial_balance
            win_rate = len([t for t in engine.trades if t['result'] == 'TP']) / len(engine.trades) * 100
            
            results.append({
                'sl': sl, 'tp': tp, 'profit': profit, 'win_rate': win_rate, 'trades': len(engine.trades)
            })
            
    results.sort(key=lambda x: x['profit'], reverse=True)
    
    print("\n--- TOP 3 BEST COMBINATIONS ---")
    for r in results[:3]:
        print(f"SL: {r['sl']} | TP: {r['tp']} | Profit: ${r['profit']:.2f} | WinRate: {r['win_rate']:.2f}% | Trades: {r['trades']}")
        
    mt5.shutdown()

if __name__ == "__main__":
    run_optimization()
