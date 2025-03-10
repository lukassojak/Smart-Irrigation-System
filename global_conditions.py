import random


class GlobalConditions:
    """Gets the global conditions from the local weather station"""
    # For now, it will just use random values

    def __init__(self):
        self.temperature = 0
        self.rainfall = 0
        self.sunlight = 0

    def update(self):
        """Simulates new global conditions"""

        self.temperature = random.uniform(10, 35)   # °C in average in the last X hours
        self.rainfall = random.uniform(0, 10)       # mm in the last X hours
        self.sunlight = random.uniform(0, 100)      # % average in the last X hours

    def get_conditions(self):
        """Returns the current global conditions as a dictionary"""

        return {
            "temperature": self.temperature,
            "rainfall": self.rainfall,
            "sunlight": self.sunlight
        }