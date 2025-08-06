

def calculate_avg_temperature(temperatures: list[float]) -> float:
    """Calculates the average temperature from a list of temperatures."""
    if not temperatures:
        raise ValueError("No temperatures available to calculate average.")
    return sum(temperatures) / len(temperatures)

def calculate_total_rainfall(rainfall_data: list[float]) -> float:
    """Calculates the total rainfall from a list of rainfall data."""
    return sum(rainfall_data)

def calculate_avg_daily_sunlight(sunlight_data: list[float], interval_days: int) -> float:
    """Calculates the average daily sunlight hours."""
    if interval_days <= 0:
        raise ValueError("Interval days must be greater than zero.")
    return sum(sunlight_data) / interval_days