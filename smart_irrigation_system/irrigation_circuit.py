from smart_irrigation_system.relay_valve import RelayValve
from deprecated.soil_moisture_sensor import SoilMoistureSensorPair
from smart_irrigation_system.enums import IrrigationState, RelayValveState
from smart_irrigation_system.drippers import Drippers
from smart_irrigation_system.correction_factors import CorrectionFactors
from smart_irrigation_system.global_config import GlobalConfig
from smart_irrigation_system.global_conditions import GlobalConditions
from smart_irrigation_system.circuit_state_manager import CircuitStateManager
from datetime import datetime, timedelta
import time
from typing import Optional, Dict
from smart_irrigation_system.logger import get_logger

import threading


class IrrigationCircuit:
    def __init__(self, name: str, circuit_id: int, relay_pin: int,
                 enabled: bool, even_area_mode: bool, target_mm: float,
                 zone_area_m2: float, liters_per_minimum_dripper: float,
                 interval_days: int, drippers: Drippers,
                 correction_factors: CorrectionFactors, sensor_pins=None):
        self.logger = get_logger(f"IrrigationCircuit-{circuit_id}")
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
        self.last_irrigation_time: Optional[datetime] = None
        self.sensors = [SoilMoistureSensorPair(pin1, pin2) for pin1, pin2 in sensor_pins] if sensor_pins else []

        self.drippers = drippers                                        # Instance of Drippers to manage dripper flow rates
        self.local_correction_factors = correction_factors                    # Instance of CorrectionFactors for local adjustments

        self._state = IrrigationState.IDLE                               # Initial state of the irrigation circuit
        self._irrigating_lock = threading.Lock()

        # Real-time metrics
        self._target_duration: Optional[int] = None  # Target duration of irrigation in seconds
        self._current_duration: Optional[int] = 0  # Current duration of irrigation in seconds

        self.logger.info(f"Irrigation Circuit {self.id} initialized with state {self._state.name}.")


    # ============================================================================================================
    # Properties and state management
    # ============================================================================================================
    
    @property
    def is_currently_irrigating(self):
            return self._state == IrrigationState.IRRIGATING
        
    @property
    def state(self) -> IrrigationState:
        """Returns the current state of the irrigation circuit."""
        with self._irrigating_lock:
            return self._state
        
    @property
    def get_progress(self) -> tuple[float, int, int, float, float]:
        """Returns the current irrigation progress as a tuple of (percentage, target duration, current duration, target water amount, current water amount)."""
        
        # Calculate the percentage of irrigation completed
        percentage = (self._current_duration / self._target_duration) * 100.0 if self._target_duration is not None else 0.0
        
        # Calculate the target water amount based on the target duration and consumption
        target_water_amount = self._target_duration * self.get_circuit_consumption() / 3600.0 if self._target_duration is not None else 0.0
        
        # Calculate the current water amount based on the current duration and consumption
        current_water_amount = (self.get_circuit_consumption() * (self._current_duration / 3600))

        current_duration = self._current_duration if self._current_duration is not None else 0
        target_duration = self._target_duration if self._target_duration is not None else 0
        
        return (percentage, target_duration, current_duration, target_water_amount, current_water_amount)
    
    @property
    def last_irrigation_time(self) -> Optional[datetime]:
        """Returns the last irrigation time."""
        return self._last_irrigation_time

    # state setter
    @state.setter
    def state(self, new_state: IrrigationState):
        """Sets the current state of the irrigation circuit."""
        with self._irrigating_lock:
            self._state = new_state
            self.logger.debug(f"State changed to {self._state.name}.")
    
    @last_irrigation_time.setter
    def last_irrigation_time(self, new_time: Optional[datetime]):
        """Sets the last irrigation time."""
        self._last_irrigation_time = new_time
        self.logger.debug(f"Last irrigation time set to {self._last_irrigation_time}.")
    
    def init_last_irrigation_time(self, circuit_state_manager: CircuitStateManager):
        """Initializes the last irrigation time from the circuit state manager."""
        self._last_irrigation_time = circuit_state_manager.get_last_irrigation_time(self)
        if self._last_irrigation_time is None:
            self.logger.debug("Last irrigation time is not set. It will be set to None.")
        else:
            self.logger.debug(f"Last irrigation time initialized to {self._last_irrigation_time}.")


    def get_status_summary(self) -> Dict[str, str]:
        """Returns a summary of the irrigation circuit status."""
        return {
            "id": str(self.id),
            "name": self.name,
            "state": self.state.name,
            "enabled": str(self.enabled),
            "even_area_mode": str(self.even_area_mode),
            "target_mm": str(self.target_mm),
            "zone_area_m2": str(self.zone_area_m2),
            "liters_per_minimum_dripper": str(self.liters_per_minimum_dripper),
            "interval_days": str(self.interval_days),
            "drippers_count": str(len(self.drippers)),
        }

    def get_circuit_consumption(self):
        """Returns the total consumption of all drippers in liters per hour."""
        return self.drippers.get_consumption()


    # ============================================================================================================
    # Water amount and duration calculations
    # ============================================================================================================

    def _get_base_target_water_amount(self) -> float:
        """Calculates the target water amount for irrigation based on global configuration and conditions."""
        if self.even_area_mode:
            # Calculate the target water amount based on the target mm and zone area
            base_target_water_amount = self.target_mm * self.zone_area_m2    # in mm * m^2 = liters
            self.logger.debug(f"Base target water amount is {base_target_water_amount} liters (even area mode).")
        else:
            # Calculate the target water amount based on the liters per minimum dripper
            duration = self.liters_per_minimum_dripper / self.drippers.get_minimum_dripper_flow()   # in hours (liters per minimum dripper / liters per hour = hours)
            base_target_water_amount = self.get_circuit_consumption() * duration  # in liters per hour * hours = liters
            self.logger.debug(f"Base target water amount is {base_target_water_amount} liters (non-even area mode).")
        
        return round(base_target_water_amount, 3)   # Round to 3 decimal places for precision

    def _get_target_duration_seconds(self, target_water_amount: float) -> float:
        """Calculates the target duration of irrigation based on the target water amount and global conditions."""
        total_consumption = self.get_circuit_consumption()
        duration_hours = target_water_amount / total_consumption  # in hours (liters / liters per hour = hours)
        duration_seconds = duration_hours * 60 * 60
        return round(duration_seconds)


    # ============================================================================================================
    # Irrigation methods
    # ============================================================================================================

    def irrigate_automatic(self, global_config: GlobalConfig, global_conditions: GlobalConditions, stop_event) -> float:
        """Starts the automatic irrigation process depending on global conditions. Returns the duration of irrigation in seconds, or None if irrigation was stopped."""
        base_target_water_amount = self._get_base_target_water_amount()

        standard_conditions = global_config.standard_conditions
        # if there was more solar energy, rain, or temperature than the standard conditions, the delta will be POSITIVE
        delta_solar = global_conditions.solar_total - standard_conditions.solar_total
        delta_rain = global_conditions.rain_mm - standard_conditions.rain_mm
        delta_temperature = global_conditions.temperature - standard_conditions.temperature_celsius

        g_c = global_config.correction_factors
        l_c = self.local_correction_factors

        total_adjustment = (
            (delta_solar * (g_c.solar + l_c.factors.get('solar', 0.0))) +
            (delta_rain * (g_c.rain + l_c.factors.get('rain', 0.0))) +
            (delta_temperature * (g_c.temperature + l_c.factors.get('temperature', 0.0)))
        )

        self.logger.debug(f"Adjustments: Solar: {delta_solar * (g_c.solar + l_c.factors.get('solar', 0.0))}, "
                            f"Rain: {delta_rain * (g_c.rain + l_c.factors.get('rain', 0.0))}, "
                            f"Temperature: {delta_temperature * (g_c.temperature + l_c.factors.get('temperature', 0.0))}. "
        )

        # Adjust the target water amount based on the total adjustment
        adjusted_water_amount = base_target_water_amount * (1 + total_adjustment)
        adjusted_water_amount = round(adjusted_water_amount, 3)  # Round to 3 decimal places for precision
        self.logger.debug(f"Adjusted water amount is {adjusted_water_amount} liters. Total adjustment is {round(total_adjustment, 2)}.")

        # If total adjustment is -1 or less, no irrigation is needed
        if total_adjustment <= -1:
            self.logger.info(f"No irrigation needed. Total adjustment is {total_adjustment}.")
            return

        # Check bounds for the total adjusted water amount
        min_water_amount = global_config.irrigation_limits.min_percent / 100.0 * base_target_water_amount
        max_water_amount = global_config.irrigation_limits.max_percent / 100.0 * base_target_water_amount
        if not (min_water_amount <= adjusted_water_amount <= max_water_amount):
            self.logger.info(f"Adjusted water amount {adjusted_water_amount} is out of bounds ({min_water_amount}, {max_water_amount}).")
            adjusted_water_amount = max(min_water_amount, min(adjusted_water_amount, max_water_amount))
        
        duration = self._get_target_duration_seconds(adjusted_water_amount)
        return self._irrigate(duration, stop_event)
        
    def irrigate_manual(self, target_water_amount, stop_event):
        """Starts the manual irrigation process for a specified water amount. Returns the duration of irrigation in seconds, or None if irrigation was stopped."""
        if target_water_amount <= 0:
            self.logger.warning(f"Target water amount must be greater than 0. Received: {target_water_amount} liters. No irrigation will be performed.")
            return
        
        # Calculate the target duration of irrigation based on the target water amount and global conditions
        target_duration = self._get_target_duration_seconds(target_water_amount)

        return self._irrigate(target_duration, stop_event)

    def _irrigate(self, duration: int, stop_event) -> Optional[int]:
        """Private method to handle the irrigation process. Starts the irrigation for a specified duration and updates the state accordingly."""
        def update_progress(elapsed):
            """Updates the real-time metrics during irrigation."""
            self._current_duration = elapsed

        def wait_for_irrigation_completion():
            """Waits for the irrigation to complete or be stopped and updates progress."""
            nonlocal elapsed_time
            while time.time() - start_time < duration:
                elapsed_time = time.time() - start_time
                update_progress(elapsed_time)
                if stop_event.is_set():
                    self.logger.info(f"Irrigation stopped by user after {int(elapsed_time)} seconds.")
                    self.state = IrrigationState.STOPPED
                    return None
                time.sleep(0.05)

        if self.state != IrrigationState.IDLE:
            self.logger.warning(f"Circuit {self.id} is not in IDLE state. Current state: {self.state.name}. Cannot start irrigation.")
            return None
        
        self.logger.info(f"Starting irrigation for {duration} seconds.")
        self.state = IrrigationState.IRRIGATING
        self.last_irrigation_time = datetime.now()
        self._target_duration = duration
        elapsed_time = 0
        start_time = time.time()  # Record the start time of irrigation

        try:
            self.valve.state = RelayValveState.OPEN  # Open the valve to start irrigation
            wait_for_irrigation_completion()
            self.valve.state = RelayValveState.CLOSED  # Close the valve after irrigation
            return int(elapsed_time)  # Return the total elapsed time in seconds
        
        except Exception as e:
            self.state = IrrigationState.ERROR
            self.logger.error(f"Error during irrigation: {e}")
            raise e
        
        finally:
            if self.state != IrrigationState.ERROR and not stop_event.is_set():
                self.state = IrrigationState.FINISHED
                self.logger.info(f"Irrigation finished successfully after {int(elapsed_time)} seconds.")

    # deprecated method for opening the valve for a specific duration
    def _irrigate_deprecated(self, duration: int, stop_event) -> Optional[int]:
        """Starts the irrigation process for a specified duration. Returns the duration of irrigation in seconds, or None if irrigation was stopped."""
        def update_progress(elapsed):
            """Updates the real-time metrics during irrigation."""
            self._current_duration = elapsed

        self.logger.info(f"Starting irrigation for {duration} seconds.")
        # Should check if the circuit is already irrigating
        self.state = IrrigationState.IRRIGATING
        self.last_irrigation_time = datetime.now()  # Update the last irrigation time
        try:
            self._target_duration = duration
            elapsed_time = self.valve.open(duration, stop_event, progress_callback=update_progress)
            return elapsed_time
        except Exception as e:
            # NOTE: elapsed time won't be set in this case. This should be solved in future (the circuit state manager does not have a way to handle this yet)
            self.state = IrrigationState.ERROR
            self.logger.error(f"Error during irrigation: {e}")
            raise e  # Re-raise the exception to indicate failure
        finally:
            if stop_event.is_set() and self.state == IrrigationState.IRRIGATING:
                self.state = IrrigationState.STOPPED
                self.logger.info(f"Irrigation stopped by user.")
            elif self.state != IrrigationState.ERROR:
                self.state = IrrigationState.FINISHED
                self.logger.info(f"Irrigation finished successfully.")
    

    # ============================================================================================================
    # Interval and state checks
    # ============================================================================================================
    
    def _interval_days_passed(self, last_irrigation_time: Optional[datetime]) -> bool:
        """Checks if the interval days have passed since the last irrigation."""

        if last_irrigation_time is None:
            return True
        
        # Calculate the time difference from the last irrigation
        # Measured in whole days, ignoring the time part
        time_difference = datetime.now().date() - last_irrigation_time.date()
        # Check if the interval days have passed
        return time_difference >= timedelta(days=self.interval_days)


    def is_irrigation_allowed(self, state_manager: CircuitStateManager) -> bool:
        """Checks if irrigation is needed based on global conditions and circuit settings."""
        if self.state != IrrigationState.IDLE:
            self.logger.warning(f"Circuit is not in IDLE state. Current state: {self.state.name}. Cannot irrigate.")
            return False
        if not self._interval_days_passed(state_manager.get_last_irrigation_time(self)):
            self.logger.debug(f"Interval days have not passed since the last irrigation. Last irrigation time: {state_manager.get_last_irrigation_time(self)}.")
            return False
        if not self.enabled:
            self.logger.warning(f"Circuit {self.id} is disabled. Cannot irrigate.")
            return False
        return True
    

    # ===========================================================================================================
    # Debugging and testing methods
    # ===========================================================================================================

    def open_valve(self):
        """Opens the valve for debugging purposes."""
        self.valve.control(RelayValveState.OPEN)
        self.logger.info(f"Valve opened for circuit {self.id}.")

    def close_valve(self):
        """Closes the valve for debugging purposes."""
        self.valve.control(RelayValveState.CLOSED)
        self.logger.info(f"Valve closed for circuit {self.id}.")
        