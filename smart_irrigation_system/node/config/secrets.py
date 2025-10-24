import os
import json

def get_secret(key: str, path: str) -> str:
    # First try to get the secret from environment variables
    if key in os.environ:
        return os.environ[key]
    
    # Fallback to config_secrets.json, used for development and testing
    try:
        with open(path, "r") as f:
            secrets = json.load(f)
            return secrets.get(key)
    except FileNotFoundError:
        # create empty config_secrets.json if it doesn't exist
        secrets = {"api_key": "your_api_key_here",
                   "application_key": "your_application_key_here",
                   "device_mac": "your_device_mac_here"}
        with open("config/config_secrets.json", "w") as f:
            json.dump(secrets, f, indent=4)
        
        # Raise an value error and inform the user to fill in the secrets
        raise ValueError("config_secrets.json created. Please fill in the secrets and try again.")

    raise ValueError(f"Secret '{key}' not found in environment variables or config_secrets.json.")