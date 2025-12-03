# smart_irrigation_system/node/core/controller/controller_core.py

import os, atexit, sys, signal, threading

import smart_irrigation_system.node.config.config_loader as config_loader

from smart_irrigation_system.node.utils.logger import get_logger

from smart_irrigation_system.node.config.global_config import GlobalConfig
from smart_irrigation_system.node.core.circuit_state_manager import CircuitStateManager
from smart_irrigation_system.node.core.enums import ControllerState
from smart_irrigation_system.node.core.irrigation_circuit import IrrigationCircuit
from smart_irrigation_system.node.core.status_models import CircuitSnapshot

from smart_irrigation_system.node.core.controller.batch_strategy import SimpleBatchStrategy
from smart_irrigation_system.node.core.controller.irrigation_executor import IrrigationExecutor
from smart_irrigation_system.node.core.controller.status_aggregator import StatusAggregator
from smart_irrigation_system.node.core.controller.task_scheduler import TaskScheduler
from smart_irrigation_system.node.core.controller.task_planner import TaskPlanner
from smart_irrigation_system.node.core.controller.thread_manager import ThreadManager

from smart_irrigation_system.node.weather.recent_weather_fetcher import RecentWeatherFetcher
from smart_irrigation_system.node.weather.weather_simulator import WeatherSimulator


# Seed for the weather simulator to ensure reproducibility in tests
WEATHER_SIMULATOR_SEED = 42

# Determine the base directory of the project
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)

# Paths to configuration and data files
CONFIG_SECRETS_PATH = os.path.join(BASE_DIR, "runtime/node/config/config_secrets.json")
CONFIG_GLOBAL_PATH = os.path.join(BASE_DIR, "runtime/node/config/config_global.json")
CONFIG_ZONES_PATH = os.path.join(BASE_DIR, "runtime/node/config/zones_config.json")
ZONE_STATE_PATH = os.path.join(BASE_DIR, "runtime/node/data/zones_state.json")
IRRIGATION_LOG_PATH = os.path.join(BASE_DIR, "runtime/node/data/irrigation_log.json")


class ControllerCore:
    """
    Full replacement for (old) IrrigationController class.
    Combines components responsible for configuration, weather featching, scheduling, planning, and execution.
    """

    def __init__(self, global_config_path: str = CONFIG_GLOBAL_PATH,
                    config_zones_path: str = CONFIG_ZONES_PATH):
        self.logger = get_logger(self.__class__.__name__)

        # Load configurations
        self.global_config: GlobalConfig = self._load_global_config(global_config_path)
        self.circuits: dict[int, IrrigationCircuit] = self._load_zones_config(config_zones_path)

        # Initialize components
        self.conditions_provider: RecentWeatherFetcher | WeatherSimulator = \
            self._init_global_conditions_provider()
        self.state_manager = CircuitStateManager(ZONE_STATE_PATH,
                                                 IRRIGATION_LOG_PATH)
        self.thread_manager = ThreadManager()
        self.task_scheduler = TaskScheduler(self.thread_manager)
        self.batch_strategy = SimpleBatchStrategy()
        self.task_planner = TaskPlanner(self.batch_strategy)
        self.irrigation_executor = IrrigationExecutor(
            circuits=self.circuits,
            state_manager=self.state_manager,
            thread_manager=self.thread_manager
        )
        self.agg: StatusAggregator = StatusAggregator(
            circuits=self.circuits,
            state_manager=self.state_manager
        )

        self._state_lock = threading.Lock()
        self._controller_state = ControllerState.IDLE
        self._register_signal_handlers()
        self.logger.info("ControllerCore initialized successfully.")


    # ==================================================================================================================
    # Public API - Status and State retrieval
    # ==================================================================================================================

    @property
    def controller_state(self) -> ControllerState:
        """Get the current state of the irrigation controller."""
        with self._state_lock:
            return self._controller_state


    # ==================================================================================================================
    # Public API - Irrigation control
    # ==================================================================================================================
    
    def start_auto_cycle(self) -> None:
        """Start the automatic irrigation cycle immediately."""

        self.task_planner.plan(list(self.circuits.keys()))
        self.irrigation_executor.execute_plan(
            planner=self.task_planner,
            global_config = self.global_config,
            conditions_provider = self.conditions_provider
        )
        

    def start_manual_irrigation(self, circuit_id: int, volume_liters: float) -> None:
        """Start manual irrigation for a specific circuit with the given volume in liters."""
        pass

    def stop_all_irrigation(self, timeout: float = 10.0) -> None:
        """Stop all ongoing irrigation tasks."""
        pass

    def stop_circuit_irrigation(self, circuit_id: int, timeout: float = 10.0) -> None:
        """Stop irrigation for a specific circuit."""
        pass


    # ==================================================================================================================
    # Public API - Configuration management
    # ==================================================================================================================

    def enable_auto_irrigation(self) -> None:
        """Enable automatic irrigation scheduling."""
        pass

    def disable_auto_irrigation(self) -> None:
        """Disable automatic irrigation scheduling."""
        pass

    def reload_config(self, global_config_path: str = CONFIG_GLOBAL_PATH) -> None:
        """
        Reload global and zones configuration from the specified paths.
        Modifies the current configuration in place.
        """
        pass

    # ==================================================================================================================
    # Public API - Shutdown & Restart
    # ==================================================================================================================

    def shutdown(self) -> None:
        """Perform clean shutdown of the controller."""
        pass

    def restart(self) -> None:
        """Restart the controller."""
        pass

    # ==================================================================================================================
    # Public API (deprecated methods from IrrigationController)
    # ==================================================================================================================

    # ----------------- MQTT -----------------------

    def get_status_message(self) -> str:
        """Returns a brief status message of the irrigation controller for mqtt publishing."""

        status = self.get_status()
        status_msg = f"Controller State: {status['controller_state']}, Auto Enabled: {not status['auto_stopped']}, Auto Paused: {status['auto_paused']}, Currently Irrigating Zones: {self.get_currently_irrigating_zones()}"
        return status_msg


    def get_currently_irrigating_zones(self) -> list[int]:
        """Returns a list of IDs of currently irrigating zones."""

        irrigating_zones = []
        for circuit in self.circuits.values():
            if circuit.is_currently_irrigating:
                irrigating_zones.append(circuit.id)
        return irrigating_zones
    

    # ----------------- CLI -----------------------

    def get_circuit_snapshot(self, circuit_id: int) -> CircuitSnapshot:
        """Returns the persistent snapshot state of a given circuit."""

        if circuit_id not in self.circuits.keys():
            raise ValueError(f"Circuit ID {circuit_id} does not exist.")
        
        snapshot = self.state_manager.get_circuit_snapshot(circuit_id)
        return snapshot


    def get_status(self) -> dict:
        """Returns comprehensive snapshot of the irrigation controller's status."""

        # Fetch global conditions
        cached_conditions_str = self.conditions_provider.get_conditions_str()

        # Prepare zones status
        zones_status = []
        for circuit in self.circuits.values():
            zones_status.append({
                'id': circuit.id,
                'name': circuit.name,
                'state': circuit.state.name,
                'pin': circuit.valve.pin,
            })

        scheduled_time = f"{self.global_config.automation.scheduled_hour:02}:{self.global_config.automation.scheduled_minute:02}"
        status = {
            'auto_enabled': self.global_config.automation.enabled,
            'auto_paused': False,                               # Temporary placeholder until pause functionality is implemented
            'auto_stopped': True,                               # Temporary placeholder until auto functionality is implemented
            'scheduled_time': scheduled_time,
            'sequential': self.global_config.automation.sequential,
            'controller_state': self._controller_state.name,
            'cache_update': self.conditions_provider.last_cache_update,
            'cached_global_conditions': cached_conditions_str.split(", Timestamp:")[0],
            'zones': zones_status,
            'current_consumption': self.get_current_consumption(),
            'input_flow_capacity': self.global_config.irrigation_limits.main_valve_max_flow,
        }

        return status
    
    def get_circuit_progress(self, circuit_number: int) -> tuple[float, float]:
        """Returns the current progress and target water amount for a given circuit."""
        from smart_irrigation_system.node.core.enums import IrrigationState
        from smart_irrigation_system.node.core.status_models import CircuitRuntimeStatus

        if circuit_number not in self.circuits:
            raise ValueError(f"Circuit number {circuit_number} does not exist.")
        
        circuit = self.circuits[circuit_number]
        if circuit.state != IrrigationState.IRRIGATING:
            return 0.0, 0.0
        try:
            runtime_status: CircuitRuntimeStatus = circuit.runtime_status
            target_water_amount = runtime_status.target_volume if runtime_status.target_volume is not None else 0.0
            current_water_amount = runtime_status.current_volume if runtime_status.current_volume is not None else 0.0
        except Exception as e:
            self.logger.error(f"Error getting runtime status for circuit {circuit_number}: {e}")
            return 0.0, 0.0
        return target_water_amount, current_water_amount
        
    
    def get_daily_irrigation_time(self):
        import time
        """Returns the daily irrigation time based on the global configuration"""
        return time.struct_time((0, 0, 0, self.global_config.automation.scheduled_hour, self.global_config.automation.scheduled_minute, 0, 0, 0, -1))
    
    def get_circuit(self, circuit_number):
        """Returns the circuit object for a given circuit number"""

        if circuit_number in self.circuits.keys():
            return self.circuits[circuit_number]
        else:
            raise ValueError(f"Circuit number {circuit_number} does not exist.")
    
    def get_state(self) -> ControllerState:
        """Returns the current state of the irrigation controller"""
        return self._controller_state
        
    def get_current_consumption(self) -> float:
        """Returns the total consumption of all irrigating circuits in liters per hour"""
        total_consumption = 0.0
        for circuit in self.circuits.values():
            if circuit.is_currently_irrigating:
                total_consumption += circuit.circuit_consumption
        return total_consumption
    
    # ----------------- Deprecated Main Loop Methods -----------------------

    def start_main_loop(self):
        """Starts the main loop for automatic irrigation management. Only one instance of the main loop can run at a time."""
        
        self.logger.warning("start_main_loop is deprecated and not supported in ControllerCore.")


    def stop_main_loop(self):
        """Stops the main loop for automatic irrigation management"""
        
        self.logger.warning("stop_main_loop is deprecated and not supported in ControllerCore.")
    
    def pause_main_loop(self):
        """Pauses the main loop for the next irrigation check"""
        
        self.logger.warning("pause_main_loop is deprecated and not supported in ControllerCore.")
    
    def resume_main_loop(self):
        """Resumes the main loop after pausing"""
        
        self.logger.warning("resume_main_loop is deprecated and not supported in ControllerCore.")
    

    # ==================================================================================================================
    # Private initialization helpers
    # ==================================================================================================================

    def _load_global_config(self, path: str) -> GlobalConfig:
        """Load global configuration from the specified path."""
        # TODO: Handle exceptions and validation
        return config_loader.load_global_config(path, CONFIG_SECRETS_PATH)

    def _load_zones_config(self, path: str) -> dict[int, IrrigationCircuit]:
        """Load zones configuration and initialize circuits."""
        # TODO: Handle exceptions and validation
        circuit_list: list[IrrigationCircuit] = config_loader.load_zones_config(path)
        return {circuit.id: circuit for circuit in circuit_list}
    
    def _init_global_conditions_provider(self) -> RecentWeatherFetcher | WeatherSimulator:
        """Initialize the global weather conditions provider based on configuration."""
        if self.global_config.use_weathersimulator:
            self.logger.info("Using Weather Simulator as conditions provider.")
            return WeatherSimulator(seed=WEATHER_SIMULATOR_SEED)
        else:
            self.logger.info("Using Recent Weather Fetcher as conditions provider.")
            max_interval_days = max((circuit.interval_days for circuit in self.circuits.values()), default=1)
            return RecentWeatherFetcher(self.global_config, max_interval_days)
        
    def _register_signal_handlers(self):
        def shutdown_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, performing clean shutdown...")
            sys.exit(0)
        
        # Common termination signals
        signal.signal(signal.SIGTERM, shutdown_handler)  # Termination signal
        signal.signal(signal.SIGINT, shutdown_handler)   # Ctrl+C
        # SIGKILL cannot be caught - when received and the irrigation is running, the valves may remain open until the next startup

    
    # ==================================================================================================================
    # Private methods - State management
    # ==================================================================================================================

    def _set_state(self, new_state: ControllerState):
        """Set the controller to the specified state"""
        with self._state_lock:
            if self._controller_state == ControllerState.ERROR:
                self.logger.warning(f"Attempted to change state: ERROR → {new_state.name}, ignoring.")
                return
            if self._controller_state != new_state:
                prev_name: str = self._controller_state.name
                self._controller_state = new_state
                self.logger.debug(f"Controller state changed: {prev_name} → {new_state.name}.")

    def _set_error_state(self, reason: str):
        """Set the controller to ERROR state"""
        self._controller_state = ControllerState.ERROR
        self.logger.error(f"Controller entered ERROR state: {reason}")
        # Stop all irrigation tasks
        self.stop_all_irrigation()

    def _on_irrigation_start(self):
        """Callback for when irrigation starts."""
        self._set_state(ControllerState.IRRIGATING)

    def _on_irrigation_finish(self):
        self._set_state(ControllerState.IDLE)

    def _on_irrigation_stop_request(self):
        self._set_state(ControllerState.STOPPING)

    def _on_executor_error(self, circuit_id: int, exception: Exception):
        self._set_error_state(f"IrrigationExecutor error on circuit {circuit_id}: {exception}")

