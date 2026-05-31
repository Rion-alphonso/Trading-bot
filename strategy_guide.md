# XAUUSD Trading Bot: Strategy & Mechanics Guide

This document provides a deep dive into the underlying trading strategy, risk management mechanics, and software architecture of the MetaTrader 5 XAUUSD Bot. 

## 1. Core Strategy Rules

The bot is designed to trade Gold against the US Dollar (**XAUUSD**) on a **5-minute (M5)** timeframe. It relies on a mechanical, alternating directional strategy coupled with an aggressive Martingale recovery system.

### Trading Sessions (IST)
The bot only operates during specific high-liquidity windows:
*   **Morning Session**: 10:00 AM to 5:30 PM (IST)
*   **Evening Session**: 8:00 PM to 10:30 PM (IST)

If the bot is started in the middle of an active session, it will not trade immediately. It waits for the **next fresh 5-minute candle** to form before executing, ensuring trades are placed precisely at the open of a new M5 period. Only **one trade** is allowed per candle.

### Alternating Direction Logic
Unlike indicator-based strategies (e.g., moving averages, RSI), this system operates on a strict mechanical sequence:
**BUY → SELL → BUY → SELL → BUY ...**

This direction alternates continuously after every closed trade, **regardless of whether the previous trade was a win or a loss**. 

---

## 2. Risk & Martingale Management

The defining characteristic of this strategy is its 3-tier Martingale progression. The strategy aggressively attempts to recover losses by increasing risk, but is capped at a maximum of 3 levels.

### Level 1 (Base Level)
*   **Risk**: 1% of the current account balance (approx 10 units for a 1110 balance).
*   **Take Profit (TP)**: 100 points (1 unit gain on scaled lot).
*   **Stop Loss (SL)**: 1000 points (10 units loss on scaled lot).

### Level 2 (Recovery Level 1)
If the Level 1 trade hits its Stop Loss, the bot escalates to Level 2.
*   **Risk**: 10% of the current account balance (approx 100 units for a 1110 balance).
*   **Take Profit (TP)**: 120 points (12 units gain on scaled lot).
*   **Stop Loss (SL)**: 1000 points (100 units loss on scaled lot).

### Level 3 (Final Stand)
If the Level 2 trade hits its Stop Loss, the bot escalates to the final recovery level.
*   **Risk**: 100% of the remaining account balance (approx 1000 units for a 1110 balance).
*   **Take Profit (TP)**: 150 points (150 units gain on scaled lot).
*   **Stop Loss (SL)**: 1000 points (1000 units loss on scaled lot).

### State Transitions
*   **On ANY Win**: The system immediately resets back to Level 1.
*   **Level 3 Loss**: If the Level 3 trade hits Stop Loss, the strategy is deemed to have failed. The system goes into a `STOPPED` state, sends a critical alert, and halts all trading to prevent further action.

**Dynamic Compounding**: Lot sizes are calculated dynamically based on the *current* balance, meaning the 1% risk grows as the account grows (compounding).

---

## 3. How the Bot Works (Under the Hood)

The software is modular, meaning different "managers" handle specific tasks.

1.  **Command Center UI & Subprocesses**: The system starts with `run_dashboard.py`, which hosts a local web dashboard. From there, it spawns `main.py` (the trading engine) and `telegram_daemon.py` (the remote control) as fully isolated processes.
2.  **The Tick Cycle**: Every second, the `main.py` loop calls the `StrategyEngine`.
3.  **State Reconciliation**: The `RecoveryManager` checks MT5 for open trades. Using SQLite's **Write-Ahead Logging (WAL)** mode, it locks and synchronizes state (`data/state.py`) across all background processes seamlessly.
4.  **Position Check & Detection**: When an open MT5 position disappears, the bot fetches the history to see if it won or lost. It passes the profit to the `MartingaleManager` to calculate the next level, and updates the SQLite database and Excel Reports.
5.  **Entry Conditions**: If no trade is open, it checks the `SessionManager` (is it between 10:00-17:30 or 20:00-22:30 IST?) and the `CandleDetector` (has a new M5 candle just started?).
6.  **Runtime Overrides**: Before execution, the engine queries the `StateManager` for any Telegram overrides. You can force the session on/off, force the next direction to BUY/SELL, or dynamically alter the Level 1 risk percentage in real-time.
7.  **Execution**: If all conditions are met, the `RiskManager` calculates the exact lot size based on the Exness contract specifications, and the `MT5Client` sends the market order.

All critical data (current level, next direction, streaks) is saved instantly to the SQLite database (`trading_bot.sqlite`). Because it uses WAL mode, you can view live trades on the Dashboard, pause the bot via Telegram, or execute an emergency `/closeall` panic exit without causing database locks or halting the trading engine.

---

## 4. Historical Backtesting Module

To ensure the strategy remains effective across different market conditions, a robust backtesting engine is included. This module operates completely independently of the live trading bot to prevent any accidental live order execution.

### How Backtesting Works
The backtester (`backtest.py`) connects to MT5 to download exact historical M5 candles for XAUUSD (e.g., the past year). It then runs the exact same mechanical sequence—alternating BUY/SELL and escalating Martingale levels—against this historical data. 

**Candle-by-Candle Simulation:**
When simulating a trade, the engine checks every historical candle's High and Low prices. If the Take Profit price falls within the candle's bounds before the Stop Loss price, it counts as a win. If the Stop Loss is hit, it triggers the Martingale escalation for the next trade.

### The Interactive Interface
Running `python backtest.py` gives you an interactive command-line interface. You can run the standard configuration, or you can tweak the parameters to research new strategy variations:
*   **Timeframe**: Test on H1 or M15 instead of M5.
*   **Initial Capital**: See how the strategy performs with $500 vs $5000.
*   **Custom Risk Levels**: Change the TP to 2000 points, or lower Level 3 risk to 50% instead of 100%.

### Analytics & Reporting
Upon completion, the engine generates `Backtest_Results.xlsx`. This provides a complete dashboard of the simulated performance, including Win Rate, Total Profit, and exactly how many times Level 2 or Level 3 were activated during the historical period, allowing you to fine-tune the parameters before deploying live.
