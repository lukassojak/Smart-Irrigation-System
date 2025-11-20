# smart_irrigation_system/node/core/irrigation_circuit.py

from datetime import datetime, timedelta
import time, threading
from typing import Optional

from smart_irrigation_system.node.core.relay_valve import RelayValve
from smart_irrigation_system.node.core.enums import IrrigationState, RelayValveState, IrrigationOutcome
from smart_irrigation_system.node.core.drippers import Drippers
from smart_irrigation_system.node.core.correction_factors import CorrectionFactors
from smart_irrigation_system.node.config.global_config import GlobalConfig
from smart_irrigation_system.node.weather.global_conditions import GlobalConditions
from smart_irrigation_system.node.core.circuit_state_manager import CircuitStateManager
from smart_irrigation_system.node.utils.logger import get_logger
from smart_irrigation_system.node.core.irrigation_result import IrrigationResult
from smart_irrigation_system.node.core.circuit_state_machine import is_allowed
from smart_irrigation_system.node.core.status_models import CircuitRuntimeStatus
from smart_irrigation_system.node.core.irrigation_models import weather_irrigation_model

import smart_irrigation_system.node.utils.result_factory as result_factory
import smart_irrigation_system.node.utils.time_utils as time_utils


PROGRESS_UPDATE_INTERVAL = 0.1  # seconds


class IrrigationStoppedException(Exception):
    """Custom exception raised when irrigation is stopped by the user."""
    pass


class IrrigationCircuit:
    def __init__(self, name: str, circuit_id: int, relay_pin: int,
                 enabled: bool, even_area_mode: bool, target_mm: float,
                 zone_area_m2: float, liters_per_minimum_dripper: float,
                 interval_days: int, drippers: Drippers,
                 correction_factors: CorrectionFactors, calculation_model=None):
        self.logger = get_logger(f"IrrigationCircuit-{circuit_id}")
        self.id: int = circuit_id
        self.name: str = name
        self.valve = RelayValve(relay_pin)
        self.enabled: bool = enabled
        self.even_area_mode: bool = even_area_mode
        self.target_mm: float = target_mm
        self.zone_area_m2: float = zone_area_m2
        self.liters_per_minimum_dripper: float = liters_per_minimum_dripper    # Base watering volume in liters per minimum dripper
        self.interval_days: int = interval_days
        self.drippers: Drippers = drippers
        self.local_correction_factors: CorrectionFactors = correction_factors

        # Calculation model for weather adjustments
        self.calculation_model = calculation_model or weather_irrigation_model

        # Runtime state
        self._state: IrrigationState = IrrigationState.IDLE if self.enabled else IrrigationState.DISABLED
        self._irrigating_lock: threading.Lock = threading.Lock()

        # Runtime time & water metrics
        self._start_time: Optional[datetime] = None      # Start time of the current irrigation
        self._target_duration: Optional[float] = None    # Target duration of irrigation in seconds
        self._target_volume: Optional[float] = None      # Target water volume in liters

        self.logger.info(f"Irrigation Circuit {self.id} initialized with state {self._state.name}.")


    # ============================================================================================================
    # Public irrigation methods
    # ============================================================================================================

    def irrigate_auto(self, 
                      global_config: GlobalConfig,
                      global_conditions: GlobalConditions,
                      stop_event: threading.Event) -> IrrigationResult:
        """Starts the automatic irrigation process based on weather conditions using the configured calculation model."""
        base_target_volume = self.base_target_volume
        self.logger.debug(f"Base target water amount is {base_target_volume} liters (even area mode: {self.even_area_mode}).")

        # Compute adjusted water amount using weather model
        model_result: weather_irrigation_model.WeatherModelResult = self.calculation_model.compute_weather_adjusted_volume(
            base_volume=base_target_volume,
            global_config=global_config,
            global_conditions=global_conditions,
            local_factors=self.local_correction_factors
        )

        if model_result.should_skip:
            result = result_factory.create_skipped_due_to_conditions(
                circuit_id=self.id,
                start_time=time_utils.now(),
                target_duration=0,
                target_water_amount=0.0
            )
            return result
        
        duration = self._volume_to_duration(model_result.final_volume)
        return self._irrigate(duration, stop_event)
        

    def irrigate_man(self, target_volume: float, stop_event: threading.Event) -> IrrigationResult:
        """
        Starts the manual irrigation process for a specified water amount.
        Returns the duration of irrigation in seconds, or None if irrigation was stopped.
        """
        target_duration = self._volume_to_duration(target_volume)
        
        if target_volume <= 0:
            self.logger.warning(f"Target water amount must be greater than 0. Received: {target_volume} liters. No irrigation will be performed.")
            result = result_factory.create_failure_invalid_water_amount(
                circuit_id=self.id,
                start_time=time_utils.now(),
                target_duration=0,
                target_water_amount=target_volume
            )
            return result
        
        return self._irrigate(target_duration, stop_event, target_volume)
    

    def flow_overload_timeout_triggered(self, start_time: datetime) -> IrrigationResult:
        result = result_factory.create_flow_overload(
            circuit_id=self.id,
            start_time=start_time,
            target_duration=0,
            target_water_amount=0.0
        )
        
        return result
    

    # ============================================================================================================
    # Public check methods
    # ============================================================================================================

    def is_irrigation_allowed(self, state_manager: CircuitStateManager) -> bool:
        """Checks if irrigation is needed based on global conditions and circuit settings."""
        if self.state != IrrigationState.IDLE:
            self.logger.warning(f"Irrigation not allowed: Circuit is not in IDLE state. Current state: {self.state.name}.")
            return False
        circuit_snapshot = state_manager.get_circuit_snapshot(self.id)
        last_irrigation_time = circuit_snapshot.last_irrigation
        if not self._interval_days_passed(last_irrigation_time):
            self.logger.debug(f"Irrigation not allowed: Interval days have not passed since the last irrigation. Last irrigation time: {last_irrigation_time}.")
            return False
        if not self.enabled:
            self.logger.warning(f"Irrigation not allowed: Circuit {self.id} is disabled.")
            return False
        return True
    

    # ============================================================================================================
    # Runtime status properties
    # ============================================================================================================
    
    @property
    def runtime_status(self) -> CircuitRuntimeStatus:
        """Return a structured runtime status of the circuit."""
        # State
        state = self._state
        is_irrigating = (state == IrrigationState.IRRIGATING)

        # Duration
        current_duration: Optional[int] = int(self.current_duration) if self.current_duration is not None else None
        target_duration: Optional[int] = int(self._target_duration) if self._target_duration is not None else None

        # Water metrics
        current_volume: Optional[float] = self.current_volume
        target_volume: Optional[float] = self._target_volume

        # Progress percentage
        if not is_irrigating or target_duration is None or target_duration == 0:
            progress_percentage: Optional[float] = None
        else:
            progress_percentage = round((current_duration / target_duration) * 100.0, 2)
        
        return CircuitRuntimeStatus(
            state=state,
            is_irrigating=is_irrigating,
            current_duration=current_duration,
            target_duration=target_duration,
            current_volume=current_volume,
            target_volume=target_volume,
            progress_percentage=progress_percentage,
            timestamp=time_utils.now()
        )

    # ============================================================================================================
    # Public properties
    # ============================================================================================================

    @property
    def circuit_consumption(self) -> float:
        """Returns the total consumption of all drippers in liters per hour."""
        return self.drippers.get_consumption()

    @property
    def base_target_volume(self) -> float:
        """Calculates the target water amount for irrigation based on global configuration and conditions."""
        if self.even_area_mode:
            # Calculate the target water amount based on the target mm and zone area
            base_target_volume = self.target_mm * self.zone_area_m2    # in mm * m^2 = liters
        else:
            # Calculate the target water amount based on the liters per minimum dripper
            duration = self.liters_per_minimum_dripper / self.drippers.get_minimum_dripper_flow() 
            base_target_volume = self.circuit_consumption * duration  # in liters per hour * hours = liters
        
        return round(base_target_volume, 3)

    @property
    def is_currently_irrigating(self) -> bool:
            return self._state == IrrigationState.IRRIGATING
    
    @property
    def current_duration(self) -> Optional[float]:
        """Returns the current duration of irrigation in seconds."""
        if self.state != IrrigationState.IRRIGATING:
            return None
        return (time_utils.now() - self._start_time).total_seconds()

    @property
    def current_volume(self) -> Optional[float]:
        """Returns the current volume of water used in liters."""
        if self.state != IrrigationState.IRRIGATING:
            return None
        return self._duration_to_volume(self.current_duration)
    
    @property
    def state(self) -> IrrigationState:
        """Returns the current state of the irrigation circuit."""
        with self._irrigating_lock:
            return self._state


    # ============================================================================================================
    # State management
    # ============================================================================================================

    @state.setter
    def state(self, new_state: IrrigationState):
        """Sets the current state of the irrigation circuit."""
        self._transition_state(new_state)
        # callback to controller can be added here in the future


    def _transition_state(self, new_state: IrrigationState, reason: Optional[str] = None):
        """Transitions the circuit state to a new state if allowed. Validates, logs and updates the state."""
        with self._irrigating_lock:
            old_state = self._state
            # for testing, temporary allow all transitions
            if not is_allowed(self._state, new_state):
                self.logger.warning(f"State transition from {self._state.name} to {new_state.name} not allowed, allowing temporarily.")
            
            self._state = new_state

            if reason:
                self.logger.info(f"State changed: {old_state.name} -> {self._state.name}. Reason: {reason}")
            else:
                self.logger.info(f"State changed: {old_state.name} -> {self._state.name}.")


    # ============================================================================================================
    # Private irrigation methods
    # ============================================================================================================

    def _irrigate(self, target_duration: float, stop_event: threading.Event, target_volume: Optional[float] = None) -> IrrigationResult:
        # --- INIT PHASE ---
        init_result = self._irrigation_init(target_duration, target_volume)
        if init_result is not None:
            return init_result      # early exit on init failure
        
        # --- EXECUTION PHASE ---
        elapsed_time, outcome, error = self._irrigation_execute(target_duration, stop_event)

        # --- FINALIZATION PHASE ---
        return self._irrigation_finalize(elapsed_time, outcome, error)
        

    def _irrigation_init(self, target_duration: float, target_volume: Optional[float]) -> Optional[IrrigationResult]:
        """Prepares circuit for irrigation. Returns IrrigationResult on failure, or None on success."""
        # If target_volume is provided by the caller, use it; otherwise, calculate it from target_duration
        target_volume = self._duration_to_volume(target_duration) if target_volume is None else target_volume
        # Guard: must be IDLE
        if self.state != IrrigationState.IDLE:
            self.logger.warning(
                f"Circuit {self.id} is not IDLE (state={self.state.name}). Cannot start irrigation."
            )
            result = result_factory.create_failure_circuit_not_idle(
                circuit_id=self.id,
                start_time=time_utils.now(),
                target_duration=int(target_duration),
                target_water_amount=target_volume
            )
            return result

        # Setup
        self.logger.debug(f"Starting irrigation for {int(target_duration)} seconds.")
        self.state = IrrigationState.IRRIGATING
        self._start_time = time_utils.now()
        self._target_duration = target_duration
        self._target_volume = target_volume
        return None


    def _irrigation_execute(self, duration: float, stop_event: threading.Event) -> tuple[float, IrrigationOutcome, Optional[str]]:
        """Executes the irrigation process. Returns a tuple of (elapsed_time, outcome, error)."""
        elapsed_time: float = 0.0
        error: Optional[str] = None
        outcome: Optional[IrrigationOutcome] = None
        try:
            self.valve.state = RelayValveState.OPEN

            # Main loop
            elapsed_time = 0.0
            while elapsed_time < duration:
                if stop_event.is_set():
                    outcome = IrrigationOutcome.STOPPED
                    error = f"Irrigation stopped by user after {int(elapsed_time)} seconds."
                    break
            
                time.sleep(PROGRESS_UPDATE_INTERVAL)
                elapsed_time = (time_utils.now() - self._start_time).total_seconds()

            if outcome is None:
                # successful end
                outcome = IrrigationOutcome.SUCCESS
                self.logger.debug(
                    f"Irrigation finished successfully after {int(elapsed_time)} seconds."
                )
        
        except KeyboardInterrupt:
            error = "Received KeyboardInterrupt"
            outcome = IrrigationOutcome.INTERRUPTED
            self.logger.info(f"Irrigation interrupted at {int(elapsed_time)} seconds (KeyboardInterrupt).")

        except SystemExit:
            error = "Received SystemExit"
            outcome = IrrigationOutcome.INTERRUPTED
            self.logger.info(f"Irrigation interrupted at {int(elapsed_time)} seconds (SystemExit).")

        except Exception as e:
            error = str(e)
            outcome = IrrigationOutcome.FAILED
            self.logger.error(f"Error during irrigation: {e}")

        return elapsed_time, outcome, error
    

    def _irrigation_finalize(self, elapsed_time: float, outcome: IrrigationOutcome, error: Optional[str]) -> IrrigationResult:
        """Finalizes the irrigation process and returns the IrrigationResult."""
        self.valve.state = RelayValveState.CLOSED
        
        result = result_factory.create_general(
            circuit_id=self.id,
            start_time=self._start_time,
            completed_duration=int(elapsed_time),
            target_duration=int(self._target_duration),
            actual_water_amount=self._target_volume if outcome == IrrigationOutcome.SUCCESS else self._duration_to_volume(elapsed_time, precision=3),
            target_water_amount=self._target_volume,
            success=outcome == IrrigationOutcome.SUCCESS,
            outcome=outcome,
            error=error,
        )

        # Reset state and runtime attributes
        self.state = IrrigationState.IDLE
        self._start_time = None
        self._target_duration = None
        self._target_volume = None

        return result
    

    # ============================================================================================================
    # Private water amount and duration calculations
    # ============================================================================================================

    def _volume_to_duration(self, target_volume: float, precision: int = 3) -> float:
        """Calculates the target duration of irrigation based on the target water amount and global conditions."""
        total_consumption = self.circuit_consumption
        if total_consumption <= 0:
            self.logger.warning(f"Circuit consumption is zero or negative ({total_consumption} L/h). Cannot calculate duration.")
            return 0.0
        duration_hours = target_volume / total_consumption  # in hours (liters / liters per hour = hours)
        duration_seconds = duration_hours * 60 * 60
        return round(duration_seconds, precision)
    

    def _duration_to_volume(self, duration_seconds: float, precision: int = 3) -> float:
        """Converts a duration in seconds to a water volume in liters based on the circuit consumption."""
        total_consumption = self.circuit_consumption
        duration_hours = duration_seconds / 3600.0
        volume = total_consumption * duration_hours
        return round(volume, precision)


    # ============================================================================================================
    # Private helpers
    # ============================================================================================================
    
    def _interval_days_passed(self, last_irrigation_time: Optional[datetime]) -> bool:
        """Checks if the interval days have passed since the last irrigation."""

        if last_irrigation_time is None:
            return True
        
        # Calculate the time difference from the last irrigation
        # Measured in whole days, ignoring the time part
        time_difference = time_utils.now().date() - last_irrigation_time.date()
        # Check if the interval days have passed
        return time_difference >= timedelta(days=self.interval_days)