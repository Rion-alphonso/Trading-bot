import time
import schedule
from data.mt5_client import mt5_client
from data.database import db, AccountSnapshot
from data.recovery import recovery_manager
from core.strategy import strategy_engine
from analytics.excel_report import excel_generator
from utils.logger import system_logger, error_logger
from utils.notifications import notifier

def daily_job():
    """Scheduled job to generate report and send email at the end of day."""
    system_logger.info("Running daily scheduled tasks...")
    excel_generator.generate_report()
    # The EOD HTML email is now dispatched automatically by Auditor

def hourly_job():
    from utils.config import config
    from data.state import state_manager
    try:
        info = mt5_client.get_account_info()
        if not info: return
        
        session = db.get_session()
        from data.database import Trade
        from datetime import datetime, timedelta
        
        open_trades = session.query(Trade).filter(Trade.status == 'OPEN').all()
        floating_pnl = 0.0
        if open_trades:
            mt5_open = mt5_client.get_open_positions()
            for db_t in open_trades:
                for p in mt5_open:
                    if str(p.ticket) == str(db_t.ticket):
                        floating_pnl += p.profit
                        break
                        
        session.close()
        
        pnl_color = "#10b981" if floating_pnl >= 0 else "#ef4444"
        pnl_str = f"${floating_pnl:.2f}"
        if floating_pnl > 0: pnl_str = "+" + pnl_str
        
        data = {
            'open_positions': len(open_trades),
            'floating_pnl': pnl_str,
            'pnl_color': pnl_color,
            'state': state_manager.get_state('trading_state', 'NORMAL'),
            'balance': f"{info['balance']:.2f}",
            'equity': f"{info['equity']:.2f}"
        }
        notifier.send_hourly_report(data)
    except Exception as e:
        error_logger.error(f"Hourly job error: {e}")

def monthly_job():
    from datetime import datetime, timedelta
    import calendar
    from utils.config import config
    
    now = datetime.now()
    last_day = calendar.monthrange(now.year, now.month)[1]
    if now.day != last_day:
        return
        
    try:
        session = db.get_session()
        from data.database import Trade
        
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_trades = session.query(Trade).filter(Trade.close_time >= start_of_month).all()
        session.close()
        
        total = len(month_trades)
        net_profit = sum(t.net_profit for t in month_trades if t.net_profit)
        wins = sum(1 for t in month_trades if t.net_profit and t.net_profit > 0)
        
        win_rate = f"{(wins/total*100):.1f}%" if total > 0 else "0.0%"
        profit_color = "#10b981" if net_profit >= 0 else "#ef4444"
        profit_str = f"${net_profit:.2f}"
        if net_profit > 0: profit_str = "+" + profit_str
        
        info = mt5_client.get_account_info()
        balance = info['balance'] if info else 0.0
        
        data = {
            'month_name': now.strftime("%B %Y").upper(),
            'net_profit': profit_str,
            'profit_color': profit_color,
            'total_trades': total,
            'win_rate': win_rate,
            'end_balance': f"{balance:.2f}"
        }
        notifier.send_monthly_report(data)
    except Exception as e:
        error_logger.error(f"Monthly job error: {e}")

def record_account_snapshot():
    """Fetches MT5 account info and records a snapshot to the database."""
    try:
        info = mt5_client.get_account_info()
        if info:
            session = db.get_session()
            snapshot = AccountSnapshot(
                balance=info['balance'],
                equity=info['equity'],
                margin=info['margin'],
                free_margin=info['free_margin']
            )
            session.add(snapshot)
            session.commit()
            session.close()
            
            # Also update current_balance in state for risk calculations
            from data.state import state_manager
            state_manager.set_state('current_balance', info['balance'])
            system_logger.info(f"Account snapshot recorded: Balance=${info['balance']:.2f}, Equity=${info['equity']:.2f}")
    except Exception as e:
        error_logger.error(f"Failed to record account snapshot: {e}")

def main():
    system_logger.info("Starting XAUUSD Trading Bot...")

    # 1. Initialize MT5
    if not mt5_client.initialize():
        error_logger.critical("Failed to initialize MT5. Exiting.")
        return

    # 2. Reconcile State
    recovery_manager.reconcile_state()

    # Record initial snapshot on startup
    record_account_snapshot()
    
    # 2.5 Send Startup Email
    try:
        from utils.config import config
        info = mt5_client.get_account_info()
        if info:
            startup_data = {
                'symbol': config.get('trading', {}).get('symbol', 'XAUUSD.m'),
                'timeframe': config.get('trading', {}).get('timeframe', 'M5'),
                'risk': config.get('trading', {}).get('risk_percent', 1.0),
                'balance': f"{info['balance']:.2f}",
                'equity': f"{info['equity']:.2f}"
            }
            notifier.send_startup_email(startup_data)
    except Exception as e:
        error_logger.error(f"Failed to fetch startup data for email: {e}")

    # 3. Schedule Jobs
    schedule.every().day.at("23:30").do(daily_job)
    schedule.every().hour.at(":00").do(hourly_job)
    schedule.every().day.at("23:50").do(monthly_job)
    
    # Start Continuous Auditor
    from core.auditor import auditor
    from utils.config import config
    if config.get('system', {}).get('auditor_enabled', False):
        auditor.start()
        
    # Telegram polling is handled exclusively by telegram_daemon.py

    # 4. Main Loop
    try:
        last_snapshot_time = 0
        while True:
            strategy_engine.execute_tick()
            schedule.run_pending()
            
            # Record snapshot every 60 seconds
            current_time = time.time()
            if current_time - last_snapshot_time >= 60:
                record_account_snapshot()
                last_snapshot_time = current_time
                
            # Sleep briefly to avoid maxing out CPU
            time.sleep(1)
            
    except KeyboardInterrupt:
        system_logger.info("Keyboard interrupt received. Shutting down...")
    except Exception as e:
        error_logger.critical(f"Fatal error in main loop: {e}", exc_info=True)
        notifier.send_alert("FATAL ERROR", str(e))
    finally:
        mt5_client.shutdown()
        notifier.send_alert("SHUTDOWN", "Trading Bot has been stopped.")

if __name__ == "__main__":
    main()
