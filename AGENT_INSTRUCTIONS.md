# System Guide for AI Agents (Antigravity & Others)

Welcome to the XAUUSD Trading Bot. If you are an AI agent analyzing or debugging this codebase, read these critical instructions to understand the architecture and prevent causing system failures.

## 1. The Multi-Process Architecture
This bot relies on **three entirely separated processes**. DO NOT combine them into a single event loop.
1. **`run_dashboard.py`**: The entry point. It runs a Flask server on `localhost:5000` and automatically spawns `telegram_daemon.py` as a detached subprocess.
2. **`main.py`**: The actual trading engine (tick cycle). This is NOT started automatically. It is spawned by `dashboard/app.py` when the user clicks the "Start Strategy" button on the web interface, or when they send `/start` via Telegram.
3. **`telegram_daemon.py`**: A long-polling loop that listens to Telegram commands and pushes messages. It is designed to restart automatically if it crashes.

## 2. State & Concurrency (CRITICAL)
Because `main.py`, the Dashboard, and the Telegram Daemon run concurrently, they **MUST NOT** communicate directly via memory.
- **`data/state.py` (StateManager)**: This is the single source of truth. All cross-process communication happens by setting key-value pairs in the `BotState` SQLite table.
- **WAL Mode**: The SQLite database (`trading_bot.sqlite`) is initialized with `check_same_thread=False` and uses **Write-Ahead Logging (WAL)**. If you modify database queries, ensure sessions are strictly closed (`session.close()`) immediately after use to prevent `database is locked` errors.

## 3. Telegram Networking Workaround
- **DO NOT USE `requests` OR `urllib` FOR TELEGRAM CALLS**. On the user's specific Windows environment, Python's SSL C-extension segfaults under continuous long-polling. 
- Look at `utils/telegram_bot.py`: All interactions with the Telegram API (`sendMessage`, `sendPhoto`, `getUpdates`) are executed using `subprocess.run(['curl', ...])`. This is an intentional stability workaround.

## 4. MT5 Client Safety
- The MT5 interface is NOT thread-safe for parallel execution. Only `main.py` handles trading logic.
- If the Telegram bot (`/closeall`) needs to close a trade, it sets a `force_close=True` flag in the SQLite database. The `main.py` tick loop detects this flag and securely executes the close order. Do not instantiate concurrent MT5 trading commands from the Telegram daemon process.
