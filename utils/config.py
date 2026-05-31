import logging
import os
import yaml

def load_config(config_path="config.yaml"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

config = load_config()
