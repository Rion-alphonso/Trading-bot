import time
import subprocess
import sys
from utils.logger import system_logger

def run_loop():
    while True:
        try:
            system_logger.info("Starting Telegram Daemon Process...")
            subprocess.run([sys.executable, "-c", "import traceback; from utils.telegram_bot import telegram_bot;\ntry:\n    telegram_bot._poll_updates()\nexcept BaseException as e:\n    print('CRASH CAUSE:', repr(e))\n    traceback.print_exc()"])
            time.sleep(2)
        except Exception as e:
            time.sleep(5)

if __name__ == '__main__':
    run_loop()
