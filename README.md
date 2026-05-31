# 🤖 XAUUSD MetaTrader 5 Trading Bot

An automated, crash-safe algorithmic trading system and historical backtester designed for trading Gold (**XAUUSD**) on the **5-minute (M5)** timeframe using MetaTrader 5 (MT5). The system utilizes a mechanical, alternating directional logic paired with a bounded 3-tier Martingale recovery structure.

---

## 🌟 Key Features

*   **Mechanical Alternating Logic**: Employs a strict alternating trade sequence (BUY ➔ SELL ➔ BUY ➔ SELL) on a new candle open, removing emotional decision-making.
*   **Bounded Martingale Recovery**: Uses a 3-tier risk scaling model (1% ➔ 10% ➔ 100%) designed to recover losses rapidly, complete with an automatic emergency shutdown.
*   **Crash-Safe & Persistent**: Implements persistent state reconciliation with a local SQLite database (`trading_bot.sqlite`) using WAL mode for concurrent multi-process access. If the system restarts, it seamlessly detects open trades and picks up exactly where it left off.
*   **Command Center Dashboard**: Includes a sleek local web interface (`http://localhost:5000`) for starting/stopping the bot, monitoring active trades, viewing history, and launching backtests visually.
*   **Telegram Remote Control**: Integrated robust Telegram daemon that supports 15 powerful remote commands including equity curve generation (`/chart`), emergency stops (`/closeall`), runtime risk overrides (`/setrisk`), and performance reporting (`/report`).
*   **High-Fidelity Backtester**: Includes an interactive backtesting engine that downloads historical M5 candles directly from your broker to simulate and stress-test strategy parameters.
*   **Comprehensive Analytics**: Generates automated Excel spreadsheets and live web charts featuring performance metrics, win rates, and streak logs.

---

## 📈 Core Trading Strategy

The bot trades **XAUUSD** exclusively on the **M5** timeframe. It operates strictly within highly liquid market sessions to minimize spread costs and slippage.

### 🕒 Session Windows (IST)
*   **Morning Session**: 10:00 AM – 5:30 PM (IST)
*   **Evening Session**: 8:00 PM – 10:30 PM (IST)
*   *Note: Trades are executed precisely at the open of a fresh 5-minute candle. Only one trade is permitted per candle.*

### 🔄 Alternating Direction Logic
The system enforces a mechanical entry cycle:
$$\text{BUY} \longrightarrow \text{SELL} \longrightarrow \text{BUY} \longrightarrow \text{SELL} \longrightarrow \dots$$
The direction alternates after **every closed trade**, regardless of whether the previous trade resulted in a profit or loss.

### 🛡️ Risk & Martingale Mechanics
The strategy attempts to recover losses dynamically by increasing risk over a maximum of three tiers. Lot sizes are computed dynamically based on your *current* account balance (compounding).

| Tier Level | Risk (% of Balance) | Take Profit (TP) | Stop Loss (SL) | Next Action on Loss | Next Action on Win |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Level 1** | 1% (~10 Units) | 100 Points (1 Unit) | 1,000 Points (10 Units) | Escalate to Level 2 | Reset to Level 1 |
| **Level 2** | 10% (~100 Units) | 120 Points (12 Units) | 1,000 Points (100 Units) | Escalate to Level 3 | Reset to Level 1 |
| **Level 3** | 100% (~1000 Units) | 150 Points (150 Units) | 1,000 Points (1000 Units) | **Emergency Stop** | Reset to Level 1 |

*   **Emergency Stop**: If a Level 3 trade hits its Stop Loss, the bot enters a `STOPPED` state, triggers email alerts, and halts all operations to prevent capital exhaustion.

---

## ⚙️ System Architecture

The software is structured into isolated, crash-resilient processes:
1.  **Command Center (`run_dashboard.py` & `dashboard/`)**: The main entry point hosting the Flask web UI and orchestrating background processes.
2.  **Telegram Daemon (`telegram_daemon.py`)**: An isolated, self-healing process that safely polls Telegram without crashing the main application.
3.  **Tick Cycle (`main.py`)**: The central trading engine process spawned by the dashboard, driving candle checking and order orchestration.
4.  **State Reconciliation (`data/`)**: Uses SQLite WAL mode to share lock-free state across the Dashboard, Telegram, and Trading processes.
5.  **Backtesting Module (`backtest.py` & `analytics/`)**: Simulated execution sandbox using raw historical data, fully integrated into the web dashboard.

---

## 🚀 Step-by-Step Execution Plan

### 1. Broker & Account Setup
1.  **Register with Exness**: Create a personal account at [Exness.com](https://www.exness.com/).
2.  **Create a Demo MT5 Account**: Navigate to your Exness Personal Area and open an MT5 Demo account.
    *   **Leverage**: Set to `1:2000` (or similar).
    *   **Balance**: Start with `$1,110` (to perfectly align with the bot's risk configuration).
    *   *Note: Save your Account Login Number, Password, and Server Name (e.g., `Exness-MT5Trial6`).*

### 2. Configure MetaTrader 5
1.  Download and install the **MetaTrader 5 Desktop Terminal** from Exness.
2.  Log in via **File -> Login to Trade Account** using your Demo account details.
3.  Ensure your terminal has Algo Trading enabled:
    *   Go to **Tools -> Options -> Expert Advisors**.
    *   Check **"Allow algorithmic trading"**.
    *   Verify the **Algo Trading** icon in the top toolbar is green.

### 3. Install Python Dependencies
Ensure you have Python 3.9+ installed and added to your system PATH, then clone your repository and install the requirements:
```bash
# Clone the repository
git clone git@github.com:Rion-alphonso/Trading-bot.git
cd Trading-bot

# Install requirements
pip install -r requirements.txt
```

### 4. Configure Application Settings
Open `config.yaml` in your editor and update the required properties:
```yaml
notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    sender: "your_email@gmail.com"
    password: "your_app_password" # Use a Google App Password, not your raw Gmail password
    recipient: "recipient_email@gmail.com"
  telegram:
    enabled: true
    bot_token: "YOUR_BOT_TOKEN"
    chat_id: "YOUR_CHAT_ID"
```

### 5. Running the Bot Live
Ensure MetaTrader 5 is running in the background and connected to your account, then launch the dashboard:
```bash
python run_dashboard.py
```
Open your browser and navigate to **`http://localhost:5000`**. From there, you can configure your capital and click **Start Strategy** to launch the trading engine in the background.

### 6. Running a Historical Backtest
To backtest settings or explore different parameter variations against historical broker data:
```bash
python backtest.py
```
*   Select `y` to use default configuration settings or `n` to enter custom timeframes, capital parameters, and TP/SL configurations.
*   Once finished, review the generated **`Backtest_Results.xlsx`** dashboard to examine performance.

---

## ⚠️ Disclaimer

Foreign exchange and commodity trading carries a high level of risk and may not be suitable for all investors. The high degree of leverage can work against you as well as for you. Past performance of any algorithmic trading system is not necessarily indicative of future results. You should carefully consider your investment objectives, level of experience, and risk appetite before deciding to trade with real capital. Use this software at your own risk.