

class Drippers:
    def __init__(self):
        self.total_consumption = 0  # in liters per hour
        self.drippers = {}  # key: liters_per_hour, value: count
    
    def add_dripper(self, liters_per_hour):
        """Adds a dripper with specified flow rate."""
        if liters_per_hour in self.drippers:
            self.drippers[liters_per_hour] += 1
        else:
            self.drippers[liters_per_hour] = 1
        self.total_consumption += liters_per_hour
    
    def remove_dripper(self, liters_per_hour):
        """Removes a dripper with specified flow rate."""
        if liters_per_hour in self.drippers and self.drippers[liters_per_hour] > 0:
            self.drippers[liters_per_hour] -= 1
            self.total_consumption -= liters_per_hour
            if self.drippers[liters_per_hour] == 0:
                del self.drippers[liters_per_hour]
    
    def get_consumption(self):
        """Returns the total consumption of all drippers in liters per hour."""
        return self.total_consumption