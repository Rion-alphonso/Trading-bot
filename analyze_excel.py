import pandas as pd
import glob
import os

files = glob.glob("Backtest_Results_*.xlsx")
if "Backtest_Results.xlsx" in files:
    files.remove("Backtest_Results.xlsx") # Ignored as it might be old
    
results = []
for file in files:
    try:
        df = pd.read_excel(file, sheet_name='Trade Log')
        if df.empty:
            continue
            
        strategy = file.replace('Backtest_Results_', '').replace('.xlsx', '')
        
        print(f"Columns for {file}: {df.columns.tolist()}")
        if 'result' not in df.columns:
            continue
            
        total_trades = len(df)
        wins = len(df[df['result'] == 'TP'])
        losses = len(df[df['result'] == 'SL'])
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate Max Consecutive Losses
        max_consecutive_losses = 0
        current_losses = 0
        
        # Calculate Max Drawdown %
        # Assuming initial balance is the first balance before trade 1, but we can look at the sequence of BALANCE AFTER
        balances = df['balance_after'].tolist()
        initial_balance = 1110.0 # From config
        
        peak = initial_balance
        max_dd_pct = 0
        
        for index, row in df.iterrows():
            if row['result'] == 'SL':
                current_losses += 1
                if current_losses > max_consecutive_losses:
                    max_consecutive_losses = current_losses
            else:
                current_losses = 0
                
            bal = row['balance_after']
            if bal > peak:
                peak = bal
            
            dd_pct = (peak - bal) / peak * 100
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct
                
        final_balance = balances[-1] if balances else initial_balance
        net_profit = final_balance - initial_balance
        
        results.append({
            'Strategy': strategy,
            'Total Trades': total_trades,
            'Win Rate': f"{win_rate:.2f}%",
            'Net Profit': f"${net_profit:.2f}",
            'Final Balance': f"${final_balance:.2f}",
            'Max Cons. Losses': max_consecutive_losses,
            'Max Drawdown %': f"{max_dd_pct:.2f}%"
        })
    except Exception as e:
        print(f"Error processing {file}: {e}")

res_df = pd.DataFrame(results)
print(res_df.to_string(index=False))
