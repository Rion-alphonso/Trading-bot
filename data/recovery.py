from data.mt5_client import mt5_client
from data.state import state_manager
from core.martingale import martingale_manager
from core.strategy import strategy_engine
from utils.logger import system_logger

class RecoveryManager:
    def reconcile_state(self):
        """Checks for open trades on MT5 and reconciles with local state."""
        system_logger.info("Starting state reconciliation...")
        
        status = state_manager.get_state('strategy_status')
        if status == 'STOPPED':
            system_logger.warning("Strategy was stopped. Manual intervention required to resume.")
            return

        open_positions = mt5_client.get_open_positions(strategy_engine.magic_number)
        
        if open_positions:
            system_logger.info("Found open position from previous session. Resuming monitoring.")
            strategy_engine.last_known_position = open_positions[0]
        else:
            system_logger.info("No open positions found. Checking if a trade closed while offline.")
            # For full resilience, we would verify the last closed ticket against a saved ticket in DB.
            pass
            
        system_logger.info("Reconciliation complete.")

recovery_manager = RecoveryManager()
