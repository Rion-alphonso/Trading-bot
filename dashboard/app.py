from flask import Flask, jsonify, request, render_template
import subprocess
import os
import psutil
from dashboard.strategy_manager import load_strategies, save_strategies, apply_strategy
from data.database import db, Trade, AccountSnapshot, BotState, BacktestResult
from sqlalchemy import desc

app = Flask(__name__)
PID_FILE = "bot.pid"

def get_bot_status():
    if not os.path.exists(PID_FILE):
        return "STOPPED"
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        if psutil.pid_exists(pid):
            return "RUNNING"
        else:
            os.remove(PID_FILE)
            return "STOPPED"
    except Exception:
        return "STOPPED"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    if get_bot_status() == "RUNNING":
        return jsonify({"status": "error", "message": "Bot is already running"}), 400
        
    try:
        # Run main.py in the background
        bot_process = subprocess.Popen(["python", "main.py"], cwd=os.getcwd())
        with open(PID_FILE, 'w') as f:
            f.write(str(bot_process.pid))
        return jsonify({"status": "success", "message": "Bot started"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/bot/state', methods=['GET'])
def get_bot_state_api():
    try:
        session = db.get_session()
        state_records = session.query(BotState).all()
        session.close()
        state = {r.key: r.value for r in state_records}
        return jsonify({"status": "success", "state": state})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        session = db.get_session()
        results = session.query(BacktestResult).order_by(desc(BacktestResult.total_profit)).all()
        
        data = []
        for r in results:
            data.append({
                "id": r.id,
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M") if r.timestamp else "",
                "symbol": r.symbol,
                "strategy": r.strategy,
                "duration": f"{r.duration_val} {r.duration_mode}",
                "capital": round(r.initial_capital, 2),
                "profit": round(r.total_profit, 2),
                "trades": r.total_trades,
                "win_rate": round(r.win_rate, 2),
                "blowups": r.account_blowups,
                "raw_config": r.raw_config
            })
            
        session.close()
        return jsonify({"status": "success", "leaderboard": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    if get_bot_status() != "RUNNING":
        return jsonify({"status": "error", "message": "Bot is not running"}), 400
        
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        # Gracefully terminate
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
        os.remove(PID_FILE)
        return jsonify({"status": "success", "message": "Bot stopped"})
    except Exception as e:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/state', methods=['GET'])
def get_state():
    session = db.get_session()
    
    # Get latest account snapshot
    latest_snapshot = session.query(AccountSnapshot).order_by(desc(AccountSnapshot.timestamp)).first()
    balance = latest_snapshot.balance if latest_snapshot else 0
    equity = latest_snapshot.equity if latest_snapshot else 0
    margin = latest_snapshot.margin if latest_snapshot else 0
    free_margin = latest_snapshot.free_margin if latest_snapshot else 0
    
    # Get bot state (level, direction)
    level_record = session.query(BotState).filter(BotState.key == 'current_level').first()
    direction_record = session.query(BotState).filter(BotState.key == 'next_direction').first()
    
    current_level = level_record.value if level_record else 1
    next_direction = direction_record.value if direction_record else "WAITING"
    
    # Get all closed trades for KPI calculation
    from datetime import datetime
    all_closed = session.query(Trade).filter(Trade.status == 'CLOSED').all()
    
    total_trades = len(all_closed)
    wins = [t for t in all_closed if t.profit is not None and t.profit > 0]
    losses = [t for t in all_closed if t.profit is not None and t.profit <= 0]
    
    win_count = len(wins)
    loss_count = len(losses)
    
    gross_profit = sum(t.profit for t in wins)
    gross_loss = abs(sum(t.profit for t in losses))
    net_profit = gross_profit - gross_loss
    
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.9 if gross_profit > 0 else 0)
    avg_win = (gross_profit / win_count) if win_count > 0 else 0
    avg_loss = (gross_loss / loss_count) if loss_count > 0 else 0
    
    # Drawdown calc
    peak = 0
    drawdown = 0
    running_pnl = 0
    for t in all_closed:
        if t.profit:
            running_pnl += t.profit
            if running_pnl > peak:
                peak = running_pnl
            dd = peak - running_pnl
            if dd > drawdown:
                drawdown = dd
                
    # Recovery rate
    level_2_count = len([t for t in all_closed if t.level == 2])
    level_3_count = len([t for t in all_closed if t.level == 3])
    recovery_count = level_2_count + level_3_count
    
    # Get bot state (level, direction)
    level_record = session.query(BotState).filter(BotState.key == 'current_level').first()
    direction_record = session.query(BotState).filter(BotState.key == 'next_direction').first()
    
    current_level = level_record.value if level_record else 1
    next_direction = direction_record.value if direction_record else "WAITING"
    
    # Get open trades
    open_trades = session.query(Trade).filter(Trade.status == 'OPEN').all()
    open_trades_data = []
    for t in open_trades:
        open_trades_data.append({
            "ticket": t.ticket,
            "type": t.type,
            "open_price": t.open_price,
            "volume": t.volume,
            "level": t.level
        })
        
    # Get recent trades for table
    recent_closed = sorted(all_closed, key=lambda x: x.close_time or datetime.min, reverse=True)[:50]
    closed_trades_data = []
    for t in recent_closed:
        closed_trades_data.append({
            "ticket": t.ticket,
            "type": t.type,
            "close_time": t.close_time.strftime("%Y-%m-%dT%H:%M:%SZ") if t.close_time else "",
            "profit": t.profit,
            "level": t.level
        })
        
    session.close()
    
    return jsonify({
        "status": get_bot_status(),
        "balance": balance,
        "equity": equity,
        "margin": margin,
        "free_margin": free_margin,
        "current_level": current_level,
        "next_direction": next_direction,
        "kpis": {
            "net_profit": net_profit,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "profit_factor": profit_factor,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "drawdown": drawdown,
            "recovery_count": recovery_count
        },
        "recent_trades": closed_trades_data
    })

@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    return jsonify(load_strategies())

@app.route('/api/strategies/apply', methods=['POST'])
def apply_strat():
    data = request.json
    name = data.get('name')
    if apply_strategy(name):
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Strategy not found"}), 404

@app.route('/api/strategies/save', methods=['POST'])
def save_strat():
    data = request.json
    name = data.get('name')
    config_data = data.get('config')
    
    strategies = load_strategies()
    strategies[name] = config_data
    save_strategies(strategies)
    
    return jsonify({"status": "success"})

@app.route('/api/strategies/delete', methods=['POST'])
def delete_strat():
    data = request.json
    name = data.get('name')
    strategies = load_strategies()
    if name in strategies:
        del strategies[name]
        save_strategies(strategies)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Strategy not found"}), 404

@app.route('/api/trades', methods=['GET'])
def get_trades_history():
    filter_type = request.args.get('filter', 'all')
    session = db.get_session()
    from datetime import datetime, timedelta
    query = session.query(Trade).filter(Trade.status == 'CLOSED')
    if filter_type != 'all':
        now = datetime.utcnow()
        if filter_type == 'hour':
            query = query.filter(Trade.close_time >= now - timedelta(hours=1))
        elif filter_type == 'day':
            query = query.filter(Trade.close_time >= now - timedelta(days=1))
        elif filter_type == 'week':
            query = query.filter(Trade.close_time >= now - timedelta(weeks=1))
        elif filter_type == 'month':
            query = query.filter(Trade.close_time >= now - timedelta(days=30))
    trades = query.order_by(desc(Trade.close_time)).all()
    trades_data = []
    for t in trades:
        trades_data.append({
            "ticket": t.ticket,
            "type": t.type,
            "level": t.level,
            "open_time": t.open_time.strftime("%Y-%m-%dT%H:%M:%SZ") if t.open_time else "",
            "close_time": t.close_time.strftime("%Y-%m-%dT%H:%M:%SZ") if t.close_time else "",
            "profit": t.profit
        })
    session.close()
    return jsonify(trades_data)

@app.route('/api/backtest/run', methods=['POST'])
def run_gui_backtest():
    data = request.json
    print(f"DEBUG BACKTEST PAYLOAD: {data}")
    duration_mode = data.get('duration_mode', 'days')
    duration_val = int(data.get('duration_val', 30))
    capital = float(data.get('capital', 1110.0))
    spread = float(data.get('spread', 10.0))
    comm = float(data.get('comm', 0.0))
    strategy = data.get('strategy', 'default')
    custom_params = data.get('custom_params', {})
    symbol = data.get('symbol', 'XAUUSDm')

    from analytics.backtest_engine import BacktestEngine
    import yaml
    try:
        with open('config.yaml', 'r') as f:
            base_config = yaml.safe_load(f)
    except Exception:
        base_config = {}
    tf_minutes = base_config.get('trading', {}).get('timeframe_minutes', 5)
    tf_str = data.get('timeframe', f'M{tf_minutes}' if isinstance(tf_minutes, int) else tf_minutes)
    config = {
        'symbol': symbol,
        'timeframe': tf_str,
        'capital': capital,
        'spread': spread,
        'comm': comm,
        'strategy': strategy,
        'custom_params': custom_params,
        'l1_risk': 1.0, 'l1_tp': 10000, 'l1_sl': 1000,
        'l2_risk': 10.0, 'l2_tp': 10000, 'l2_sl': 1000,
        'l3_risk': 100.0, 'l3_tp': 10000, 'l3_sl': 1000,
    }
    engine = BacktestEngine(config)
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    if duration_mode == 'candles':
        success = engine.run(end_date=end_date, num_candles=duration_val)
    elif duration_mode == 'trades':
        success = engine.run(end_date=end_date, max_trades=duration_val)
    else:
        start_date = end_date - timedelta(days=duration_val)
        success = engine.run(start_date=start_date, end_date=end_date)
        
    import MetaTrader5 as mt5
    mt5.shutdown()
    if not success:
        return jsonify({"status": "error", "message": "Backtest failed to run. Check MT5 connection."}), 500
    wins = [t for t in engine.trades if t['result'] == 'TP']
    total_trades = len(engine.trades)
    win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
    total_profit = sum([t['profit'] for t in engine.trades])
    results = {
        "status": "success",
        "kpis": {
            "initial_capital": engine.initial_balance,
            "final_capital": engine.balance,
            "total_profit": total_profit,
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "blowups": engine.account_blowups
        },
        "trades": engine.trades,
        "ohlc": getattr(engine, 'rates_data', {}).to_dict('records') if hasattr(engine.rates_data, 'to_dict') else engine.rates_data
    }
    for t in results['trades']:
        if 'entry_time' in t and not isinstance(t['entry_time'], str): t['entry_time'] = t['entry_time'].strftime("%Y-%m-%dT%H:%M:%SZ")
        if 'exit_time' in t and not isinstance(t['exit_time'], str): t['exit_time'] = t['exit_time'].strftime("%Y-%m-%dT%H:%M:%SZ")
        
    # Save to leaderboard database
    try:
        session = db.get_session()
        result_record = BacktestResult(
            symbol=symbol,
            strategy=strategy,
            duration_mode=duration_mode,
            duration_val=duration_val,
            initial_capital=engine.initial_balance,
            final_capital=engine.balance,
            total_profit=total_profit,
            total_trades=total_trades,
            win_rate=round(win_rate, 2),
            account_blowups=engine.account_blowups,
            is_optimized=False,
            raw_config=config
        )
        session.add(result_record)
        session.commit()
        session.close()
    except Exception as e:
        print(f"Error saving to leaderboard: {e}")
        
        return jsonify(results)
    except Exception as e:
        print(f"Error saving to leaderboard: {e}")
        
    return jsonify(results)

@app.route('/api/backtest/optimize', methods=['POST'])
def optimize_gui_backtest():
    data = request.json
    duration_mode = data.get('duration_mode', 'days')
    duration_val = int(data.get('duration_val', 30))
    capital = float(data.get('capital', 1110.0))
    spread = float(data.get('spread', 10.0))
    comm = float(data.get('comm', 0.0))
    strategy = data.get('strategy', 'default')
    custom_params = data.get('custom_params', {})
    symbol = data.get('symbol', 'XAUUSDm')
    
    from analytics.backtest_engine import BacktestEngine
    from datetime import datetime, timedelta
    end_date = datetime.now()
    
    import yaml
    try:
        with open('config.yaml', 'r') as f:
            base_config = yaml.safe_load(f)
    except Exception:
        base_config = {}
        
    tf_minutes = base_config.get('trading', {}).get('timeframe_minutes', 5)
    tf_str = data.get('timeframe', f'M{tf_minutes}' if isinstance(tf_minutes, int) else tf_minutes)

    def evaluate(tp_mult, sl_mult):
        config = {
            'symbol': symbol,
            'timeframe': tf_str,
            'capital': capital,
            'spread': spread,
            'comm': comm,
            'strategy': strategy,
            'custom_params': custom_params,
            'l1_risk': 1.0, 'l1_tp': int(10000 * tp_mult), 'l1_sl': int(1000 * sl_mult),
            'l2_risk': 10.0, 'l2_tp': int(10000 * tp_mult), 'l2_sl': int(1000 * sl_mult),
            'l3_risk': 100.0, 'l3_tp': int(10000 * tp_mult), 'l3_sl': int(1000 * sl_mult),
        }
        engine = BacktestEngine(config)
        
        if duration_mode == 'candles':
            success = engine.run(end_date=end_date, num_candles=duration_val)
        elif duration_mode == 'trades':
            success = engine.run(end_date=end_date, max_trades=duration_val)
        else:
            success = engine.run(start_date=end_date - timedelta(days=duration_val), end_date=end_date)
            
        return engine, success

    multipliers = [0.8, 1.0, 1.2, 1.5]
    results_list = []
    best_profit = -float('inf')
    best_trades = []
    best_ohlc = []

    for tp_m in multipliers:
        for sl_m in multipliers:
            engine, success = evaluate(tp_m, sl_m)
            if not success:
                continue
                
            wins = [t for t in engine.trades if t['result'] == 'TP']
            total_trades = len(engine.trades)
            win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
            total_profit = sum([t['profit'] for t in engine.trades])
            
            results_list.append({
                'tp_mult': tp_m,
                'sl_mult': sl_m,
                'win_rate': win_rate,
                'trades_count': total_trades,
                'profit': total_profit
            })
            
            if total_profit > best_profit:
                best_profit = total_profit
                best_trades = engine.trades
                best_ohlc = getattr(engine, 'rates_data', {}).to_dict('records') if hasattr(engine.rates_data, 'to_dict') else engine.rates_data

    import MetaTrader5 as mt5
    mt5.shutdown()
    
    if not results_list:
        return jsonify({"status": "error", "message": "Optimization failed."}), 500
        
    results_list.sort(key=lambda x: x['profit'], reverse=True)
    for t in best_trades:
        if 'entry_time' in t and not isinstance(t['entry_time'], str): t['entry_time'] = t['entry_time'].strftime("%Y-%m-%dT%H:%M:%SZ")
        if 'exit_time' in t and not isinstance(t['exit_time'], str): t['exit_time'] = t['exit_time'].strftime("%Y-%m-%dT%H:%M:%SZ")

    return jsonify({
        "status": "success",
        "results": results_list,
        "best_trades": best_trades,
        "best_ohlc": best_ohlc
    })

@app.route('/api/settings', methods=['GET'])
def get_settings():
    import yaml
    try:
        with open('config.yaml', 'r') as f:
            cfg = yaml.safe_load(f)
    except Exception:
        cfg = {}
    return jsonify({
        "sessions_ist": cfg.get('trading', {}).get('sessions_ist', []),
        "auto_on_enabled": cfg.get('system', {}).get('auto_on_enabled', False),
        "auto_off_enabled": cfg.get('system', {}).get('auto_off_enabled', False),
        "auditor_enabled": cfg.get('system', {}).get('auditor_enabled', False),
        "telegram_enabled": cfg.get('notifications', {}).get('telegram', {}).get('enabled', False),
        "telegram_bot_token": cfg.get('notifications', {}).get('telegram', {}).get('bot_token', ''),
        "telegram_chat_id": cfg.get('notifications', {}).get('telegram', {}).get('chat_id', '')
    })

@app.route('/api/settings', methods=['POST'])
def save_settings():
    import yaml
    data = request.json
    try:
        with open('config.yaml', 'r') as f:
            cfg = yaml.safe_load(f)
    except Exception:
        cfg = {}
    if 'trading' not in cfg: cfg['trading'] = {}
    if 'system' not in cfg: cfg['system'] = {}
    cfg['trading']['sessions_ist'] = data.get('sessions_ist', [])
    cfg['system']['auto_on_enabled'] = data.get('auto_on_enabled', False)
    cfg['system']['auto_off_enabled'] = data.get('auto_off_enabled', False)
    cfg['system']['auditor_enabled'] = data.get('auditor_enabled', False)
    if 'notifications' not in cfg: cfg['notifications'] = {}
    if 'telegram' not in cfg['notifications']: cfg['notifications']['telegram'] = {}
    cfg['notifications']['telegram']['enabled'] = data.get('telegram_enabled', False)
    cfg['notifications']['telegram']['bot_token'] = data.get('telegram_bot_token', '')
    cfg['notifications']['telegram']['chat_id'] = data.get('telegram_chat_id', '')
    with open('config.yaml', 'w') as f:
        yaml.dump(cfg, f, default_flow_style=False)
    try:
        from core.scheduler_manager import update_tasks
        update_tasks(cfg['trading']['sessions_ist'], cfg['system'])
    except Exception as e:
        print(f"Scheduler update failed: {e}")
    return jsonify({"status": "success"})


