import json
import os

CONFIG_PATH = "json_files/config.json"

# Functions for writing and reading configuration
def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)




def load_config() -> Settings:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {"api_keys": {"openai": "", "nebius": "", "sambanova": "" }, "model": "gpt-4o-mini"}


readme.md
.gitignre
pyprojct.toml
src
    app.py
    providers
       asdfasd
    ui
       index.html
    costs.py
    history.py
    config.py
