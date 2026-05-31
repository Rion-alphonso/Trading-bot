# Beginner's Guide: Setting up MT5 & Exness for the Trading Bot

If you are new to algorithmic trading, this step-by-step guide will walk you through creating a broker account, installing MetaTrader 5, and connecting your Python bot.

---

## Step 1: Create an Exness Account
Exness is the broker that actually holds your funds and executes your trades in the real market.
1. Go to [Exness.com](https://www.exness.com/) and click **Register** or **Open Account**.
2. Fill in your country of residence, email, and choose a secure password.
3. Complete the email/phone verification process and fill out your profile.

## Step 2: Create a MT5 Trading Account (Demo Recommended)
*Never run a new trading bot on a Real money account first. Always start with a Demo account.*
1. Log into your Exness Personal Area.
2. In the "My Accounts" section, click the **Demo** tab.
3. Click **Open New Account**.
4. Choose **Standard** (or Pro, depending on your preference) and ensure the trading platform is set to **MT5**.
5. Set your Leverage (e.g., 1:2000), Starting Balance (e.g., $1110 to match the bot's design), and create an Account Password.
6. **Save these details:** You will be given a **Login Number** (e.g., 12345678) and a **Server Name** (e.g., Exness-MT5Trial6). Keep these safe along with your password.

## Step 3: Download & Install MetaTrader 5
1. In your Exness Personal Area, click the menu icon next to your new Demo account and select **Trade**.
2. Click on the link to download the **MetaTrader 5 Desktop Terminal** for Windows.
3. Run the downloaded `.exe` file and complete the standard installation process.

## Step 4: Log into MT5
1. Open the MetaTrader 5 application on your computer.
2. Go to the top menu: **File -> Login to Trade Account**.
3. Enter the details you saved in Step 2:
   * **Login**: Your Exness MT5 Account Number
   * **Password**: The password you created for that specific account
   * **Server**: Select your specific server from the dropdown (e.g., Exness-MT5Trial6)
4. Click **OK**. You should hear a chime, and the bottom right corner of the screen will show green/blue connection bars.

## Step 5: Enable Auto Trading
For the Python bot to send trades to MT5, you must grant it permission.
1. In MT5, go to the top menu: **Tools -> Options**.
2. Select the **Expert Advisors** tab.
3. Check the box that says **"Allow algorithmic trading"**.
4. Uncheck the boxes that disable it on account/profile changes if you want it to remain permanently on.
5. Click **OK**. The "Algo Trading" button on your top toolbar should now have a green play icon.

---

## Step 6: Setting up the Python Bot
Now that MT5 is ready and running in the background, you need to prepare the bot.
1. Download and install **Python** (version 3.9 or higher) from [python.org](https://www.python.org/). *Important: Check the box "Add Python to PATH" during installation.*
2. Open a Command Prompt or PowerShell window.
3. Navigate to the folder where you saved the Trading Bot files.
4. Install the required libraries by running:
   ```bash
   pip install -r requirements.txt
   ```

## Step 7: Configure the Bot
1. Open the `config.yaml` file in a text editor (like Notepad).
2. Under the `notifications` section, update the email settings with your Gmail credentials.
   * *Note: If you use Gmail, you must generate an "App Password" from your Google Account Security settings. Do not use your standard email password.*
3. To enable the **Telegram Remote Control** bot, fill out the `telegram` section with your `bot_token` (from BotFather) and `chat_id` (your personal Telegram user ID).
4. Save the file.

## Step 8: Run the Bot via the Command Center!
1. Ensure MetaTrader 5 is **OPEN** and connected to your Exness account.
# Beginner's Guide: Setting up MT5 & Exness for the Trading Bot

If you are new to algorithmic trading, this step-by-step guide will walk you through creating a broker account, installing MetaTrader 5, and connecting your Python bot.

---

## Step 1: Create an Exness Account
Exness is the broker that actually holds your funds and executes your trades in the real market.
1. Go to [Exness.com](https://www.exness.com/) and click **Register** or **Open Account**.
2. Fill in your country of residence, email, and choose a secure password.
3. Complete the email/phone verification process and fill out your profile.

## Step 2: Create a MT5 Trading Account (Demo Recommended)
*Never run a new trading bot on a Real money account first. Always start with a Demo account.*
1. Log into your Exness Personal Area.
2. In the "My Accounts" section, click the **Demo** tab.
3. Click **Open New Account**.
4. Choose **Standard** (or Pro, depending on your preference) and ensure the trading platform is set to **MT5**.
5. Set your Leverage (e.g., 1:2000), Starting Balance (e.g., $1110 to match the bot's design), and create an Account Password.
6. **Save these details:** You will be given a **Login Number** (e.g., 12345678) and a **Server Name** (e.g., Exness-MT5Trial6). Keep these safe along with your password.

## Step 3: Download & Install MetaTrader 5
1. In your Exness Personal Area, click the menu icon next to your new Demo account and select **Trade**.
2. Click on the link to download the **MetaTrader 5 Desktop Terminal** for Windows.
3. Run the downloaded `.exe` file and complete the standard installation process.

## Step 4: Log into MT5
1. Open the MetaTrader 5 application on your computer.
2. Go to the top menu: **File -> Login to Trade Account**.
3. Enter the details you saved in Step 2:
   * **Login**: Your Exness MT5 Account Number
   * **Password**: The password you created for that specific account
   * **Server**: Select your specific server from the dropdown (e.g., Exness-MT5Trial6)
4. Click **OK**. You should hear a chime, and the bottom right corner of the screen will show green/blue connection bars.

## Step 5: Enable Auto Trading
For the Python bot to send trades to MT5, you must grant it permission.
1. In MT5, go to the top menu: **Tools -> Options**.
2. Select the **Expert Advisors** tab.
3. Check the box that says **"Allow algorithmic trading"**.
4. Uncheck the boxes that disable it on account/profile changes if you want it to remain permanently on.
5. Click **OK**. The "Algo Trading" button on your top toolbar should now have a green play icon.

---

## Step 6: Setting up the Python Bot
Now that MT5 is ready and running in the background, you need to prepare the bot.
1. Download and install **Python** (version 3.9 or higher) from [python.org](https://www.python.org/). *Important: Check the box "Add Python to PATH" during installation.*
2. Open a Command Prompt or PowerShell window.
3. Navigate to the folder where you saved the Trading Bot files.
4. Install the required libraries by running:
   ```bash
   pip install -r requirements.txt
   ```

## Step 7: Configure the Bot
1. Open the `config.yaml` file in a text editor (like Notepad).
2. Under the `notifications` section, update the email settings with your Gmail credentials.
   * *Note: If you use Gmail, you must generate an "App Password" from your Google Account Security settings. Do not use your standard email password.*
3. To enable the **Telegram Remote Control** bot, fill out the `telegram` section with your `bot_token` (from BotFather) and `chat_id` (your personal Telegram user ID).
4. Save the file.

## Step 8: Run the Bot via the Command Center!
1. Ensure MetaTrader 5 is **OPEN** and connected to your Exness account.
2. In your Command Prompt (in the bot's folder), run:
   ```bash
   python run_dashboard.py
   ```
3. You will see logs stating `Starting Command Center Dashboard on http://localhost:5000`.
4. Open your web browser and navigate to **[http://localhost:5000](http://localhost:5000)**.
5. Click **"Start Strategy"** from the web interface. The bot will now monitor the time and place trades automatically on XAUUSD when the session starts!

**Telegram Remote Control:**
The Telegram integration is active. You will receive live trade alerts, and you can control the bot remotely using 15 powerful commands. Send `/status` for a quick glance, `/chart` to view a live equity curve graph, `/report` for performance metrics, `/closeall` for emergency exits, or `/setrisk` to alter trading parameters directly from your mobile phone.

---

## Step 9: Running a Historical Backtest (Optional)

If you want to test how the strategy would have performed over the past year (or with different TP/SL settings) without risking real money:

1. Keep MetaTrader 5 open and connected.
2. In your Command Prompt (in the bot's folder), run:
   ```bash
   python backtest.py
   ```
3. The script will ask you: `Do you want to use default options? (y/n)`.
4. Type `y` to run a simulation using the exact settings in your configuration, or type `n` to interactively change things like Timeframe, Risk %, or TP/SL points.
5. The backtester will download historical data directly from your broker and simulate the trades.
6. When it finishes, open the newly created **`Backtest_Results.xlsx`** file in your folder. The "Dashboard" sheet will show you the exact profit, win rate, and total trades taken over that historical period!
