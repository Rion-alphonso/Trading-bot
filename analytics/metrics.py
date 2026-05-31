from data.state import state_manager
from utils.logger import system_logger

class MetricsEngine:
    def update_streaks(self, profit):
        """Updates win/loss streaks based on the latest trade."""
        win_streak = state_manager.get_state('current_win_streak') or 0
        loss_streak = state_manager.get_state('current_loss_streak') or 0
        longest_win = state_manager.get_state('longest_win_streak') or 0
        longest_loss = state_manager.get_state('longest_loss_streak') or 0
        total_trades = state_manager.get_state('total_trades') or 0
        
        state_manager.set_state('total_trades', total_trades + 1)
        
        if profit > 0:
            win_streak += 1
            loss_streak = 0
            if win_streak > longest_win:
                state_manager.set_state('longest_win_streak', win_streak)
        else:
            loss_streak += 1
            win_streak = 0
            if loss_streak > longest_loss:
                state_manager.set_state('longest_loss_streak', loss_streak)
                
        state_manager.set_state('current_win_streak', win_streak)
        state_manager.set_state('current_loss_streak', loss_streak)

metrics_engine = MetricsEngine()
