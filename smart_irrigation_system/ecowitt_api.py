from datetime import datetime, timedelta
import requests
import json
import os

from smart_irrigation_system.weather_config import (
    TEMPERATURE_TIME_RESOLUTION,
    MAX_DATA_AGE,
    CELSIUS
)

def perform_api_call(url: str, params: dict) -> dict:
    """Performs an API call to fetch temperature data."""
    response = requests.get(url, params=params)

    # Check for status code -1 - indicates too frequent requests

    if response.status_code != 200:
        raise Exception(f"Failed to fetch API data: {response.status_code} - {response.text}")
    return response.json()



def temperature_api_call(fetcher, start_date: datetime, end_date: datetime) -> dict[str, str]:
    """Performs an API call to fetch temperature data."""
    params = {
        "application_key": fetcher.global_config.weather_api.application_key,
        "api_key": fetcher.global_config.weather_api.api_key,
        "mac": fetcher.global_config.weather_api.device_mac,
        "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
        "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S"),
        "cycle_type": get_cycle_type(),
        "call_back": "outdoor.temperature",
        "temp_unitid": CELSIUS,
    }

    safe_params = hide_confidential_params(params, ["api_key", "application_key", "mac"])
    url = fetcher.global_config.weather_api.history_url
    fetcher.logger.debug(f"Performing API call to {url} with params: {safe_params}")
    data = perform_api_call(url, params)
    save_json(data=data)  # Save the raw data for debugging purposes
    try:
        return data.get("data").get("outdoor").get("temperature").get("list", [])
    except KeyError as e:
        raise ValueError("Unexpected response format from temperature API.")





def hide_confidential_params(params: dict, keys_to_hide: list[str]) -> dict:
    """Returns a copy of the params dictionary with specified keys hidden."""
    safe_params = params.copy()
    for key in keys_to_hide:
        if key in safe_params:
            safe_params[key] = "***"
    return safe_params

def save_json(data: dict, filename_prefix: str = "recent_weather_data", folder: str = "debug_data") -> None:
    """Saves JSON data to a file for debugging purposes."""
    # Ensure the folder exists
    os.makedirs(folder, exist_ok=True)
    
    # Construct the full file path
    filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    file_path = os.path.join(folder, filename)
    
    # Save the JSON data to the file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def get_cycle_type() -> str:
    """Returns the data resolution in string format (e.g., '30min') for API parameters."""
    if TEMPERATURE_TIME_RESOLUTION == 5:
        return "5min"
    elif TEMPERATURE_TIME_RESOLUTION == 30:
        return "30min"
    elif TEMPERATURE_TIME_RESOLUTION == 240:
        return "4hour"
    elif TEMPERATURE_TIME_RESOLUTION == 1440:
        return "1day"
    else:
        raise ValueError("Unsupported TEMPERATURE_TIME_RESOLUTION value.")
    

def test_api_secrets_valid(fetcher, global_config) -> bool:
    """On initialization, checks if the API secrets are valid."""
    params = {
        "application_key": global_config.weather_api.application_key,
        "api_key": global_config.weather_api.api_key,
        "mac": global_config.weather_api.device_mac,
        "start_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "end_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "call_back": "outdoor.temperature",
    }


    # Attempt to fetch some data from the API to validate the secrets
    url = global_config.weather_api.history_url
    fetcher.logger.debug(f"Testing API secrets validity with URL: {url}")
    response = requests.get(url, params=params)

    if response.status_code == 200:
        # get the response data code
        try:
            data = response.json()
            if data.get("code") == 0:
                fetcher.logger.info("API secrets validated successfully.")
                return True
            elif data.get("code") == -1:
                fetcher.logger.error("Cannot validate API secrets: Too frequent requests.")
            elif data.get("code") == 40010:
                fetcher.logger.error("Invalid API secrets: Invalid application key.")
            elif data.get("code") == 40011:
                fetcher.logger.error("Invalid API secrets: Invalid API key.")
            elif data.get("code") == 40012:
                fetcher.logger.error("Invalid API secrets: Invalid device MAC address.")
            else:
                fetcher.logger.error(f"Cannot validate API secrets.")

            return False
        except Exception as e:
            fetcher.logger.error(f"Error parsing API response: {e}")
            return False
    else:
        fetcher.logger.error(f"API call failed with status code {response.status_code}: {response.text}")
        return False
    