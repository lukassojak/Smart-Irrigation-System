# Configurations for the Weather API

from enum import Enum


# The time resolution for api data fetching in minutes.
# Supported values: 5, 30, 240, 1440 (ecowitt api limitations)
TEMPERATURE_TIME_RESOLUTION = 30
RAINFALL_TIME_RESOLUTION = 240
SOLAR_TIME_RESOLUTION = 30


# Maximum age of cached weather data in seconds after which it is considered expired.
# Recommended to set this to a value that is at least the same as the average irrigation time for the whole irrigation node.
# Default value is 30 minutes. (30 * 60 seconds)
MAX_DATA_AGE = 30 * 60

# Minimum count of temperature data values to calculate the average temperature.
MIN_TEMPERATURE_COUNT = 24 * 60 // TEMPERATURE_TIME_RESOLUTION // 2  # At least half a day of data


# Temperature unit identifiers for API calls.
CELSIUS = "1"
FAHRENHEIT = "2"
# Rainfall unit identifiers for API calls.
MM = "12"
INCHES = "13"
# Solar radiation unit identifiers for API calls.
LUX = "15"
WATTS_PER_SQUARE_METER = "16"

# Cycle types for the weather API.
class CycleType(Enum):
    """Enum for cycle types used in weather API calls."""
    FIVE_MINUTES = (5, "5min")
    THIRTY_MINUTES = (30, "30min")
    FOUR_HOURS = (240, "4hour")
    ONE_DAY = (1440, "1day")

    @classmethod
    def from_resolution(cls, resolution: int) -> str:
        """Returns the string representation of the cycle type based on the resolution."""
        for cycle in cls:
            if cycle.value[0] == resolution:
                return cycle.value[1]
        raise ValueError(f"Unsupported resolution: {resolution}. Supported resolutions are: {[cycle.value[0] for cycle in cls]}")
    

class ApiCallType(Enum):
    """Enum for API call types."""
    TEMPERATURE = "temperature"
    RAINFALL = "rainfall"
    SOLAR = "solar"