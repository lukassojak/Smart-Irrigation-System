from datetime import datetime
import requests
import json

def temperature_api_call(url: str, params: dict) -> dict:
    """Performs an API call to fetch temperature data."""
    response = requests.get(url, params=params)

    # Check for status code -1 - indicates too frequent requests

    if response.status_code != 200:
        raise Exception(f"Failed to fetch temperature data: {response.status_code} - {response.text}")
    return response.json()

def rainfall_api_call(url: str, params: dict) -> dict:
    pass

def sunlight_api_call(url: str, params: dict) -> dict:
    pass


def hide_confidential_params(params: dict, keys_to_hide: list[str]) -> dict:
    """Returns a copy of the params dictionary with specified keys hidden."""
    safe_params = params.copy()
    for key in keys_to_hide:
        if key in safe_params:
            safe_params[key] = "***"
    return safe_params

def save_json(data: dict, filename_prefix: str = "recent_weather_data") -> None:
    """Saves JSON data to a file for debugging purposes."""
    filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)