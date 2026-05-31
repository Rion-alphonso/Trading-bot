# Changelog - Recent Updates

## 1. Web Dashboard Integration
- Created a comprehensive local web dashboard using Flask.
- Hosted at `http://localhost:5000` with UI tabs for Active Trades, Performance Metrics, and Interactive Backtesting.

## 2. Process Architecture & Concurrency
- Separated the system into isolated processes to guarantee crash-resilience:
  - `run_dashboard.py`: Hosts the Web UI.
  - `main.py`: The core Strategy Engine (Tick Loop) spawned dynamically.
  - `telegram_daemon.py`: A self-healing Telegram polling process.
- Migrated the SQLite Database to **WAL (Write-Ahead Logging)** mode. This ensures all three processes can concurrently read/write to `data.state.state_manager` without database locking.

## 3. Telegram Robustness & Native Networking
- Replaced Python's native SSL library (`requests` / `urllib`) with native OS `curl` via `subprocess` for all Telegram API calls.
- This permanently solved a Windows-specific memory segfault bug where long-polling the Telegram API caused the daemon to crash.

## 4. 15 Advanced Telegram Actions
- Implemented 15 powerful remote control commands via Telegram:
  - **Insights**: `/status`, `/report`, `/history`, `/open`, `/chart` (generates Matplotlib equity curves), `/logs`.
  - **Controls**: `/start`, `/pause`, `/resume`, `/closeall` (emergency market exit), `/reset`.
  - **Overrides**: `/setrisk`, `/direction`, `/session`, `/config`.
  - **Diagnostics**: `/health` (CPU/RAM metrics using `psutil`).

## 5. Requirements Upgraded
- Added `matplotlib` (for Telegram charting) and `psutil` (for diagnostics) to `requirements.txt`.
