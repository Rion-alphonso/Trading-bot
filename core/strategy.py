from data.mt5_client import mt5_client
from data.state import state_manager
from core.session import session_manager
from core.candle import candle_detector
from core.risk import risk_manager
from utils.logger import system_logger, trade_logger
from utils.notifications import notifier
from utils.config import config
import time
from datetime import datetime
from data.database import db, Trade

class StrategyEngine:
    def __init__(self):
        self.magic_number = 123456
        self.last_known_position = None

    def execute_tick(self):
        """Called every tick or iteration to evaluate the strategy."""
        
        # 1. Check if strategy is stopped
        status = state_manager.get_state('strategy_status')
        if status == 'STOPPED':
            return

        # 2. Reconcile Open Positions
        open_positions = mt5_client.get_open_positions(self.magic_number)
        
        # 2.5 Check Force Close Override
        if state_manager.get_state('force_close') == True:
            system_logger.warning("Force close flag detected! Emergency closing positions...")
            if open_positions:
                for pos in open_positions:
                    mt5_client.close_position(pos)
            state_manager.set_state('force_close', False)
            state_manager.set_state('strategy_status', 'STOPPED')
            notifier.send_alert("🚨 EMERGENCY HALT", "Force close triggered remotely. All positions closed and engine halted.")
            return

        if open_positions:
            # Wait for trade to close, do nothing
            self.last_known_position = open_positions[0].ticket
            return
            
        # If there were open positions previously but not now, process the close
        if self.last_known_position and not open_positions:
            self._handle_closed_position()

        # 3. Check Session & Days
        sess_override = state_manager.get_state('session_override')
        if not sess_override:
            if not session_manager.is_active_session():
                return
            
        # 4. Check Candle
        if not candle_detector.is_new_candle():
            return
            
        # 5. We are ready to place a new trade!
        self._place_new_trade()

    def _handle_closed_position(self):
        """Processes a trade that has just closed."""
        system_logger.info("Detecting closed position.")
        
        if not self.last_known_position:
            return
            
        profit, close_price, open_time, close_time = mt5_client.get_closed_trade_profit(self.last_known_position)
        if profit is not None:
            trade_logger.info(f"Trade {self.last_known_position} closed. Net Profit: {profit}")
            # Duration calculation
            duration = "N/A"
            if open_time and close_time:
                duration_td = close_time - open_time
                duration = str(duration_td).split('.')[0]
                
            next_step = "Proceeding to next trade"
            
            notifier.send_trade_closed_alert({
                'action': state_manager.get_state('next_direction') or 'BOTH',
                'ticket': self.last_known_position,
                'net_profit': f"{profit:.2f}",
                'close_price': close_price,
                'duration': duration,
                'new_balance': f"{state_manager.get_state('current_balance') or 0:.2f}",
                'next_step': next_step
            })
            
            # Update Trade in DB
            try:
                session = db.get_session()
                trade_record = session.query(Trade).filter(Trade.ticket == self.last_known_position).first()
                if trade_record:
                    trade_record.status = "CLOSED"
                    trade_record.close_time = close_time
                    trade_record.close_price = close_price
                    trade_record.profit = profit
                    session.commit()
                session.close()
            except Exception as e:
                system_logger.error(f"Failed to update trade in DB: {e}")
            
            # Update Balance
            account_info = mt5_client.get_account_info()
            if account_info:
                state_manager.set_state('current_balance', account_info['balance'])
            
            self.last_known_position = None
            
            # Toggle Direction for NEXT trade if configured to BOTH
            trading_cfg = config.get('trading', {})
            cfg_dir = trading_cfg.get('direction', 'BOTH')
            if cfg_dir == 'BOTH':
                current_direction = state_manager.get_state('next_direction')
                next_direction = 'SELL' if current_direction == 'BUY' else 'BUY'
                state_manager.set_state('next_direction', next_direction)
            else:
                state_manager.set_state('next_direction', cfg_dir)
            
            # Update Excel report in real-time
            from analytics.excel_report import excel_generator
            excel_generator.generate_report()

    def _place_new_trade(self):
        """Places a new trade according to state."""
        balance = state_manager.get_state('current_balance')
        direction = state_manager.get_state('next_direction')
        dir_override = state_manager.get_state('direction_override')
        
        # Ensure direction matches config if not BOTH and no override
        trading_cfg = config.get('trading', {})
        cfg_dir = trading_cfg.get('direction', 'BOTH')
        
        if dir_override in ['BUY', 'SELL']:
            direction = dir_override
            state_manager.set_state('direction_override', None) # Consume override
        else:
            if cfg_dir in ['BUY', 'SELL']:
                direction = cfg_dir
                state_manager.set_state('next_direction', direction)
            
            # Apply Indicator logic
            from core.indicators import indicator_engine
            ema_signal = indicator_engine.evaluate_ema_crossover()
            if ema_signal == 'WAITING':
                return
            elif ema_signal in ['BUY', 'SELL']:
                if cfg_dir == 'BOTH' or cfg_dir == ema_signal:
                    direction = ema_signal
                    state_manager.set_state('next_direction', direction)
                else:
                    return # EMA signal disagrees with forced config direction
                
        if not direction:
            direction = 'BUY' # fallback
            
        lot_size = risk_manager.calculate_lot_size(balance)
        if lot_size <= 0:
            system_logger.error("Calculated lot size is <= 0. Cannot place trade.")
            return

        sl, tp = risk_manager.get_sl_tp_prices(direction)
        if not sl or not tp:
            system_logger.error("Failed to calculate SL/TP. Cannot place trade.")
            return
            
        system_logger.info(f"Placing {direction} trade. Size: {lot_size}, SL: {sl}, TP: {tp}")
        
        result = mt5_client.place_order(
            action=direction,
            lot_size=lot_size,
            sl=sl,
            tp=tp,
            magic=self.magic_number
        )
        
        if result:
            time.sleep(0.5) # Wait for MT5 server to register position
            pos = mt5_client.get_open_positions(self.magic_number)
            pos_data = next((p for p in pos if p.ticket == result.order), None)
            
            open_price = pos_data.price_open if pos_data else result.price
            open_time_dt = datetime.fromtimestamp(pos_data.time) if pos_data else datetime.utcnow()
            
            trade_logger.info(f"Opened {direction} order {result.order}")
            
            account_info = mt5_client.get_account_info()
            bal = account_info['balance'] if account_info else 0
            eq = account_info['equity'] if account_info else 0
            
            notifier.send_trade_opened_alert({
                'action': direction,
                'ticket': result.order,
                'level': 1, # Kept for backward compatibility in alert formats
                'size': lot_size,
                'entry_price': open_price,
                'sl': sl,
                'tp': tp,
                'balance': f"{bal:.2f}",
                'equity': f"{eq:.2f}"
            })
            self.last_known_position = result.order
            
            try:
                session = db.get_session()
                new_trade = Trade(
                    ticket=result.order,
                    type=direction,
                    open_time=open_time_dt,
                    open_price=open_price,
                    sl=sl,
                    tp=tp,
                    volume=lot_size,
                    level=1,
                    status="OPEN"
                )
                session.add(new_trade)
                session.commit()
                session.close()
            except Exception as e:
                system_logger.error(f"Failed to log trade to DB: {e}")

strategy_engine = StrategyEngine()
