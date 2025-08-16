from datetime import datetime, timedelta
import requests
import json
import os
import copy

from smart_irrigation_system.weather_config import (
    TEMPERATURE_TIME_RESOLUTION,
    RAINFALL_TIME_RESOLUTION,
    SOLAR_TIME_RESOLUTION,
    MAX_DATA_AGE,
    CELSIUS,
    MM,
    WATTS_PER_SQUARE_METER,
    CycleType,
    ApiCallType
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
        "cycle_type": get_cycle_type(ApiCallType.TEMPERATURE),
        "call_back": "outdoor.temperature",
        "temp_unitid": CELSIUS,
    }

    safe_params = hide_confidential_params(params, ["api_key", "application_key", "mac"])
    url = fetcher.global_config.weather_api.history_url
    fetcher.logger.debug(f"Performing API call to {url} with params: {safe_params}")
    data = perform_api_call(url, params)

    # Make a copy of the data and replace epoch timestamps with human-readable dates for debugging
    data_to_save = copy.deepcopy(data)  # Use deepcopy to avoid modifying the original data
    try:
        temperature_list = data_to_save.get("data", {}).get("outdoor", {}).get("temperature", {}).get("list", {})
        if isinstance(temperature_list, dict):  # Ensure "list" is a dictionary
            data_to_save["data"]["outdoor"]["temperature"]["list"] = {
                datetime.fromtimestamp(int(epoch)).strftime("%Y-%m-%d %H:%M:%S"): value
                for epoch, value in temperature_list.items()
            }
        else:
            fetcher.logger.error(f"Unexpected data structure for temperature list: {temperature_list}")
    except Exception as e:
        fetcher.logger.error(f"Unexpected error while converting timestamps: {e}")
    save_json(data=data_to_save, filename_prefix="recent_temperature_data")

    try:
        return data.get("data").get("outdoor").get("temperature").get("list", [])
    except KeyError as e:
        raise ValueError("Unexpected response format from temperature API.")


def rainfall_api_call_history(fetcher, start_date: datetime, end_date: datetime) -> dict[str, str]:
    """Performs an API call to fetch rainfall data."""
    params = {
        "application_key": fetcher.global_config.weather_api.application_key,
        "api_key": fetcher.global_config.weather_api.api_key,
        "mac": fetcher.global_config.weather_api.device_mac,
        "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
        "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S"),
        "cycle_type": get_cycle_type(ApiCallType.RAINFALL),
        "call_back": "rainfall.yearly",
        "rainfall_unitid": MM,
    }

    safe_params = hide_confidential_params(params, ["api_key", "application_key", "mac"])
    url = fetcher.global_config.weather_api.history_url
    fetcher.logger.debug(f"Performing API call to {url} with params: {safe_params}")
    data = perform_api_call(url, params)

    # Make a copy of the data and replace epoch timestamps with human-readable dates for debugging
    data_to_save = copy.deepcopy(data)  # Use deepcopy to avoid modifying the original data
    try:
        rainfall_list = data_to_save.get("data", {}).get("rainfall", {}).get("yearly", {}).get("list", {})
        if isinstance(rainfall_list, dict):  # Ensure "list" is a dictionary
            data_to_save["data"]["rainfall"]["yearly"]["list"] = {
                datetime.fromtimestamp(int(epoch)).strftime("%Y-%m-%d %H:%M:%S"): value
                for epoch, value in rainfall_list.items()
            }
        else:
            fetcher.logger.error(f"Unexpected data structure for rainfall list: {rainfall_list}")
    except Exception as e:
        fetcher.logger.error(f"Unexpected error while converting timestamps: {e}")
    save_json(data=data_to_save, filename_prefix="recent_rainfall_data")

    try:
        return data.get("data").get("rainfall").get("yearly", {}).get("list", {})
    except KeyError as e:
        raise ValueError("Unexpected response format from rainfall API.")
    

def solar_api_call_history(fetcher, start_date: datetime, end_date: datetime) -> dict[str, str]:
    """Performs an API call to fetch solar energy data."""
    params = {
        "application_key": fetcher.global_config.weather_api.application_key,
        "api_key": fetcher.global_config.weather_api.api_key,
        "mac": fetcher.global_config.weather_api.device_mac,
        "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
        "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S"),
        "cycle_type": get_cycle_type(ApiCallType.SOLAR),
        "call_back": "solar_and_uvi.solar",
        "solar_irradiance_unitid": WATTS_PER_SQUARE_METER,
    }

    safe_params = hide_confidential_params(params, ["api_key", "application_key", "mac"])
    url = fetcher.global_config.weather_api.history_url
    fetcher.logger.debug(f"Performing API call to {url} with params: {safe_params}")
    data = perform_api_call(url, params)

    # Make a copy of the data and replace epoch timestamps with human-readable dates for debugging
    data_to_save = copy.deepcopy(data)  # Use deepcopy to avoid modifying the original data
    try:
        solar_list = data_to_save.get("data", {}).get("solar_and_uvi", {}).get("solar", {}).get("list", {})
        if isinstance(solar_list, dict):  # Ensure "list" is a dictionary
            data_to_save["data"]["solar_and_uvi"]["solar"]["list"] = {
                datetime.fromtimestamp(int(epoch)).strftime("%Y-%m-%d %H:%M:%S"): value
                for epoch, value in solar_list.items()
            }
        else:
            fetcher.logger.error(f"Unexpected data structure for solar list: {solar_list}")
    except Exception as e:
        fetcher.logger.error(f"Unexpected error while converting timestamps: {e}")
    save_json(data=data_to_save, filename_prefix="recent_solar_data")

    try:
        return data.get("data").get("solar_and_uvi").get("solar", {}).get("list", {})
    except KeyError as e:
        raise ValueError("Unexpected response format from solar API.")


def all_api_call_real_time(fetcher) -> dict[str, list]:
    """Performs an API call to fetch real-time data for temperature and rainfall."""
    params = {
        "application_key": fetcher.global_config.weather_api.application_key,
        "api_key": fetcher.global_config.weather_api.api_key,
        "mac": fetcher.global_config.weather_api.device_mac,
        "call_back": "outdoor.temperature,rainfall.yearly",
        "temp_unitid": CELSIUS,
        "rainfall_unitid": MM,
    }

    safe_params = hide_confidential_params(params, ["api_key", "application_key", "mac"])
    url = fetcher.global_config.weather_api.realtime_url
    fetcher.logger.debug(f"Performing API call to {url} with params: {safe_params}")
    data = perform_api_call(url, params)

    # Make a copy of the data and replace epoch timestamps with human-readable dates for debugging
    data_to_save = copy.deepcopy(data)  # Use deepcopy to avoid modifying the original data
    try:
        # Convert the "time" fields to human-readable format
        data_to_save["data"]["outdoor"]["temperature"]["time"] = datetime.fromtimestamp(
            int(data["data"]["outdoor"]["temperature"]["time"])
        ).strftime("%Y-%m-%d %H:%M:%S")
        data_to_save["data"]["rainfall"]["yearly"]["time"] = datetime.fromtimestamp(
            int(data["data"]["rainfall"]["yearly"]["time"])
        ).strftime("%Y-%m-%d %H:%M:%S")
    except KeyError as e:
        fetcher.logger.error(f"Error converting timestamps to human-readable format: {e}")
    except ValueError as e:
        fetcher.logger.error(f"Invalid timestamp value: {e}")
    except Exception as e:
        fetcher.logger.error(f"Unexpected error while converting timestamps: {e}")
    save_json(data=data_to_save, filename_prefix="real_time_weather_data")


    try:
        temperature_data = data.get("data").get("outdoor", {}).get("temperature", {}).get("value", None)
        rainfall_data = data.get("data").get("rainfall", {}).get("yearly", {}).get("value", None)
        return {
            "temperature": temperature_data,
            "rainfall": rainfall_data
        }
    except KeyError as e:
        raise ValueError("Unexpected response format from real-time API.")




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

def get_cycle_type(api_call_type: ApiCallType) -> str:
    """Returns the cycle type based on the configured time resolution."""
    if api_call_type == ApiCallType.TEMPERATURE:
        return CycleType.from_resolution(TEMPERATURE_TIME_RESOLUTION)
    elif api_call_type == ApiCallType.RAINFALL:
        return CycleType.from_resolution(RAINFALL_TIME_RESOLUTION)
    elif api_call_type == ApiCallType.SOLAR:
        return CycleType.from_resolution(SOLAR_TIME_RESOLUTION)
    else:
        raise ValueError(f"Unsupported API call type: {api_call_type}. Supported types are: {list(ApiCallType)}")
    


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
    