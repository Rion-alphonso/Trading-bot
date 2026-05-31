import logging
import os
from utils.config import config

def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup as many loggers as you want"""
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    log_dir = config.get('logging', {}).get('log_dir', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    handler = logging.FileHandler(os.path.join(log_dir, log_file))        
    handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers if setup multiple times
    if not logger.handlers:
        logger.addHandler(handler)
        logger.addHandler(console_handler)

    return logger

# Pre-configured loggers for different components
system_logger = setup_logger('system', 'system.log')
trade_logger = setup_logger('trade', 'trade.log')
error_logger = setup_logger('error', 'error.log', level=logging.ERROR)
