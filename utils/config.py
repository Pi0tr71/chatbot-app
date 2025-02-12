import json
import os

CONFIG_PATH = "json_files/config.json"

# Funkcje do zapisu i odczytu konfiguracji
def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {"api_keys": {"openai": "", "nebius": "", "sambanova": "" }, "model": "gpt-4o"}