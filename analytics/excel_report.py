import pandas as pd
import os
from datetime import datetime
from data.database import db, Trade, AccountSnapshot
from utils.logger import error_logger, system_logger

class ExcelReportGenerator:
    def __init__(self):
        self.filename = "TradingBot.xlsx"

    def generate_report(self):
        """Generates or updates the Excel report with real-time data."""
        try:
            session = db.get_session()
            
            # 1. Fetch data
            trades_df = pd.read_sql(session.query(Trade).statement, session.bind)
            snapshot_df = pd.read_sql(session.query(AccountSnapshot).statement, session.bind)
            session.close()

            with pd.ExcelWriter(self.filename, engine='openpyxl') as writer:
                # Dashboard
                self._create_dashboard(writer, trades_df, snapshot_df)
                
                # Trades
                trades_df.to_excel(writer, sheet_name='Trades', index=False)
                
                # We can add Daily, Weekly, Monthly Summary sheets here by grouping trades_df
                if not trades_df.empty and 'close_time' in trades_df.columns:
                    trades_df['close_time'] = pd.to_datetime(trades_df['close_time'])
                    trades_df.set_index('close_time', inplace=True)
                    
                    # Daily Summary
                    daily = trades_df.resample('D')['profit'].sum().reset_index()
                    daily.to_excel(writer, sheet_name='Daily Summary', index=False)
            
            system_logger.info(f"Excel report updated: {self.filename}")
        except Exception as e:
            error_logger.error(f"Failed to generate Excel report: {e}")

    def _create_dashboard(self, writer, trades, snapshots):
        """Creates the Dashboard KPIs sheet."""
        if trades.empty:
            df = pd.DataFrame([{"Message": "No trades yet"}])
            df.to_excel(writer, sheet_name='Dashboard', index=False)
            return

        total_trades = len(trades)
        wins = len(trades[trades['profit'] > 0])
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
        total_profit = trades['profit'].sum()

        data = {
            "Metric": ["Total Trades", "Win Rate (%)", "Total Profit", "Last Updated"],
            "Value": [total_trades, round(win_rate, 2), round(total_profit, 2), datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        }
        
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='Dashboard', index=False)

excel_generator = ExcelReportGenerator()
