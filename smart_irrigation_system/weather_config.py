# Configurations for the Weather API


# The time resolution for temperature data fetching in minutes.
# Supported values: 5, 30, 240, 1440 
TEMPERATURE_TIME_RESOLUTION = 30

# Maximum age of cached weather data in seconds after which it is considered expired.
# Recommended to set this to a value that is at least the same as the average irrigation time for the whole irrigation node.
# Default value is 30 minutes. (30 * 60 seconds)
MAX_DATA_AGE = 90

# Temperature unit identifiers for API calls.
CELSIUS = "1"
FAHRENHEIT = "2"