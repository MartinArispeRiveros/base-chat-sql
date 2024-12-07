import os
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load YAML configuration
def load_config():
    with open("app/utils/config.yaml", "r") as file:
        raw_config = yaml.safe_load(file)
        # Resolve environment variables in the YAML file
        resolved_config = resolve_env_variables(raw_config)
        return resolved_config

def resolve_env_variables(config):
    if isinstance(config, dict):
        return {key: resolve_env_variables(value) for key, value in config.items()}
    elif isinstance(config, list):
        return [resolve_env_variables(item) for item in config]
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        env_var = config[2:-1]  # Strip ${ and }
        return os.getenv(env_var, "")  # Default to an empty string if not set
    return config
