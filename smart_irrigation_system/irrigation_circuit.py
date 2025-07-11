from smart_irrigation_system.relay_valve import RelayValve
from deprecated.soil_moisture_sensor import SoilMoistureSensorPair
from smart_irrigation_system.enums import IrrigationState
from smart_irrigation_system.drippers import Drippers
from smart_irrigation_system.correction_factors import CorrectionFactors
from smart_irrigation_system.global_config import GlobalConfig
from smart_irrigation_system.global_conditions import GlobalConditions
from datetime import datetime, timedelta
from typing import Optional

import threading


class IrrigationCircuit:
    def __init__(self, name: str, circuit_id: int, relay_pin: int,
                 enabled: bool, even_area_mode: bool, target_mm: float,
                 zone_area_m2: float, liters_per_minimum_dripper: float,
                 interval_days: int, drippers: Drippers,
                 correction_factors: CorrectionFactors, sensor_pins=None):
        self.id = circuit_id
        self.name = name
        self.valve = RelayValve(relay_pin)
        self.enabled = enabled
        self.even_area_mode = even_area_mode                            # True if the circuit uses even area mode
        self.target_mm = target_mm                                      # Base target watering depth in mm (for even area mode, otherwise None)
        self.zone_area_m2 = zone_area_m2                                # Area of the zone in square meters (for even area mode, otherwise None)
        self.liters_per_minimum_dripper = liters_per_minimum_dripper    # Base watering volume in liters per minimum dripper (for non-even area mode, otherwise None)
        # Ask Drippers for the dripper with the minimum flow rate in liters per hour in configuration

        self.interval_days = interval_days
        self.sensors = [SoilMoistureSensorPair(pin1, pin2) for pin1, pin2 in sensor_pins] if sensor_pins else []

        self.drippers = drippers                                        # Instance of Drippers to manage dripper flow rates
        self.local_correction_factors = correction_factors                    # Instance of CorrectionFactors for local adjustments

        self._state = IrrigationState.IDLE                               # Initial state of the irrigation circuit
        self._irrigating_lock = threading.Lock()

    
    @property
    def is_currently_irrigating(self):
        with self._irrigating_lock:
            # possible bug
            return self._state == IrrigationState.IRRIGATING
        
    @property
    def state(self) -> IrrigationState:
        """Returns the current state of the irrigation circuit."""
        with self._irrigating_lock:
            return self._state

    # state setter
    @state.setter
    def state(self, new_state: IrrigationState):
        """Sets the current state of the irrigation circuit."""
        with self._irrigating_lock:
            self._state = new_state
            print(f"I-Circuit {self.id}: State changed to {new_state}")


    def get_circuit_consumption(self):
        """Returns the total consumption of all drippers in liters per hour."""
        return self.drippers.get_consumption()


    def get_base_target_water_amount(self) -> float:
        """Calculates the target water amount for irrigation based on global configuration and conditions."""
        if self.even_area_mode:
            # Calculate the target water amount based on the target mm and zone area
            base_target_water_amount = self.target_mm * self.zone_area_m2    # in mm * m^2 = liters
        else:
            # Calculate the target water amount based on the liters per minimum dripper
            duration = self.liters_per_minimum_dripper / self.drippers.get_minimum_dripper_flow()   # in hours (liters per minimum dripper / liters per hour = hours)
            base_target_water_amount = self.get_circuit_consumption() * duration  # in liters per hour * hours = liters
        
        return base_target_water_amount


    def get_target_duration_seconds(self, target_water_amount: float) -> float:
        """Calculates the target duration of irrigation based on the target water amount and global conditions."""
        if self.even_area_mode:
            # Calculate the target duration based on the target water amount and the total consumption
            total_consumption = self.get_circuit_consumption()
            duration_hours = target_water_amount / total_consumption  # in hours (liters / liters per hour = hours)
        else:
            # Calculate the target duration based on the liters per minimum dripper and its flow rate
            minimum_dripper_consumption = self.drippers.get_minimum_dripper_flow()  # in liters per hour
            minimum_dripper_target_water_amount = self.liters_per_minimum_dripper   # in liters
            duration_hours = minimum_dripper_target_water_amount / minimum_dripper_consumption  # in hours (liters / liters per hour = hours)
        
        # Convert hours to seconds
        duration_seconds = duration_hours * 60 * 60  # in seconds
        return duration_seconds


    def irrigate_automatic(self, global_config: GlobalConfig, global_conditions: GlobalConditions, stop_event) -> float:
        """Starts the automatic irrigation process depending on global conditions. Returns the duration of irrigation in seconds."""
        base_target_water_amount = self.get_base_target_water_amount()

        standard_conditions = global_config.standard_conditions
        # if there was more sunlight, rain, or temperature than the standard conditions, the delta will be POSITIVE
        delta_sunlight = global_conditions.sunlight_hours - standard_conditions.sunlight_hours
        delta_rain = global_conditions.rain_mm - standard_conditions.rain_mm
        delta_temperature = global_conditions.temperature - standard_conditions.temperature_celsius

        g_c = global_config.correction_factors
        l_c = self.local_correction_factors

        total_adjustment = (
            (delta_sunlight * g_c.sunlight * l_c.factors.get('sunlight')) +
            (delta_rain * g_c.rain * l_c.factors.get('rain')) +
            (delta_temperature * g_c.temperature * l_c.factors.get('temperature'))
        )

        # If total adjustment is -1 or less, no irrigation is needed
        if total_adjustment <= -1:
            print(f"I-Circuit {self.id}: No irrigation needed due to negative adjustment.")
            return
        
        # Check bounds for the total adjustment
        min = global_config.irrigation_limits.min_percent / 100.0
        max = global_config.irrigation_limits.max_percent / 100.0
        if not (min <= total_adjustment <= max):
            print(f"I-Circuit {self.id}: Total adjustment {total_adjustment} is out of bounds ({min}, {max}). Limiting to bounds.")
            total_adjustment = max(min, min(total_adjustment, max))

        # Adjust the target water amount based on the total adjustment
        adjusted_water_amount = base_target_water_amount * (1 + total_adjustment)
        print(f"I-Circuit {self.id}: Adjusted water amount is {adjusted_water_amount} liters.")
        
        duration = self.get_target_duration_seconds(adjusted_water_amount)
        return self.irrigate(duration, stop_event)
        

    def irrigate_manual(self, target_water_amount, stop_event):
        """Starts the manual irrigation process for a specified water amount"""
        # Maybe should use mm instead of liters?
        if target_water_amount <= 0:
            print(f"I-Circuit {self.id}: Target water amount is zero or negative.")
            return
        
        # Calculate the target duration of irrigation based on the target water amount and global conditions
        target_duration = self.get_target_duration_seconds(target_water_amount)

        self.irrigate(target_duration, stop_event)


    def irrigate(self, duration, stop_event):
        """Starts the irrigation process for a specified duration"""

        print(f"I-Circuit  {self.id}: Starting irrigation")
        self.state = IrrigationState.IRRIGATING
        try:
            if not self.valve.is_open():
                self.valve.open(duration, stop_event)
            else:
                print(f"I-Circuit {self.id}: Valve is already open, skipping.")
        except Exception as e:
            self.state = IrrigationState.ERROR
            print(f"I-Circuit {self.id}: Error during irrigation - {e}")
        finally:
            if stop_event.is_set():
                self.state = IrrigationState.STOPPED
                print(f"I-Circuit {self.id}: Irrigation stopped by external event")
            elif self.state != IrrigationState.ERROR:
                self.state = IrrigationState.FINISHED
                print(f"I-Circuit {self.id}: Finished irrigation")

            self.valve.close()  # Fail-safe close the valve if it was opened
            return 0 if self.state == IrrigationState.ERROR else duration
        
    def interval_days_passed(self, last_irrigation_time: Optional[datetime]) -> bool:
        """Checks if the interval days have passed since the last irrigation."""

        if last_irrigation_time is None:
            return True
        
        # Calculate the time difference from the last irrigation
        time_difference = datetime.now() - last_irrigation_time
        # Check if the interval days have passed
        return time_difference >= timedelta(days=self.interval_days)


    def is_irrigation_allowed(self, state_manager) -> bool:
        """Checks if irrigation is needed based on global conditions and circuit settings."""
        if self.state != IrrigationState.IDLE:
            print(f"I-Circuit {self.id}: Cannot check irrigation need, circuit is not idle.")
            return False
        if not self.interval_days_passed(state_manager.get_last_irrigation_time(self)):
            print(f"I-Circuit {self.id}: Interval days have not passed since the last irrigation.")
            return False
        if not self.enabled:
            print(f"I-Circuit {self.id}: Circuit is disabled.")
            return False
        return True
        