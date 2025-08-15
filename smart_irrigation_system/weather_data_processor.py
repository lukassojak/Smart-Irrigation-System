

def calculate_avg_temperature(temperatures: list[float]) -> float:
    """Calculates the average temperature from a list of temperatures."""
    if not temperatures:
        raise ValueError("No temperatures available to calculate average.")
    return sum(temperatures) / len(temperatures)

def calculate_total_rainfall(rainfall_data: dict[float]) -> float:
    """Calculates the total rainfall from a list of rainfall data."""
    if not rainfall_data:
        raise ValueError("No rainfall data available to calculate total.")
    first_value = rainfall_data[0]
    last_value = rainfall_data[-1]
    if first_value > last_value:
        raise ValueError("Rainfall data is not in chronological order.")
    return last_value - first_value

    

def calculate_avg_daily_sunlight(sunlight_data: list[float], interval_days: int) -> float:
    """Calculates the average daily sunlight hours."""
    if interval_days <= 0:
        raise ValueError("Interval days must be greater than zero.")
    return sum(sunlight_data) / interval_days