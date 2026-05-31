import json
import os
import yaml
from utils.logger import system_logger

STRATEGIES_FILE = "dashboard/strategies.json"
CONFIG_FILE = "config.yaml"

def load_strategies():
    if not os.path.exists(STRATEGIES_FILE):
        # Create a default one based on current config
        with open(CONFIG_FILE, 'r') as f:
            current_config = yaml.safe_load(f)
        default_strategies = {
            "Default Gold": current_config.get('trading', {})
        }
        save_strategies(default_strategies)
        return default_strategies
    
    with open(STRATEGIES_FILE, 'r') as f:
        return json.load(f)

def save_strategies(strategies):
    os.makedirs(os.path.dirname(STRATEGIES_FILE), exist_ok=True)
    with open(STRATEGIES_FILE, 'w') as f:
        json.dump(strategies, f, indent=4)

def apply_strategy(name):
    strategies = load_strategies()
    if name not in strategies:
        return False
        
    strategy_config = strategies[name]
    
    # Read current config
    with open(CONFIG_FILE, 'r') as f:
        current_config = yaml.safe_load(f)
        
    # Overwrite trading block
    current_config['trading'] = strategy_config
    
    # Save back
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(current_config, f, sort_keys=False, default_flow_style=False)
        
    system_logger.info(f"Applied strategy: {name}")
    return True
