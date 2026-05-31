import logging
from dashboard.app import app
from utils.logger import system_logger

# Disable strict werkzeug logging to keep console clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

if __name__ == "__main__":
    # Start Telegram Polling in a separate process to ensure Dashboard stability
    import subprocess
    import sys
    subprocess.Popen([sys.executable, 'telegram_daemon.py'])
    
    system_logger.info("Starting Command Center Dashboard on http://localhost:5000")
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        system_logger.error(f"Dashboard crash: {e}", exc_info=True)
