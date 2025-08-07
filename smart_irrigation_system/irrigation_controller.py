
# check if threading is supported in the current environment
try:
    import threading
    THREADING_SUPPORTED = True
except ImportError:
    THREADING_SUPPORTED = False
    class DummyThread:
        def __init__(self, *args, **kwargs): pass
        def start(self): pass

    class DummyLock:
        def __enter__(self): pass
        def __exit__(self, exc_type, exc_val, exc_tb): pass

    class DummyEvent:
        def set(self): pass
        def clear(self): pass
        def is_set(self): return False
        def wait(self, timeout=None): pass

    threading = type('threading', (), {
        'Thread': DummyThread,
        'Lock': DummyLock,
        'Event': DummyEvent,
        'current_thread': lambda: "main-thread"
    })()

import time
from typing import Dict, Any
import atexit

from smart_irrigation_system.irrigation_circuit import IrrigationCircuit
from smart_irrigation_system.global_conditions import GlobalConditions
from smart_irrigation_system.weather_simulator import WeatherSimulator
from smart_irrigation_system.recent_weather_fetcher import RecentWeatherFetcher
from smart_irrigation_system.global_config import GlobalConfig
from smart_irrigation_system.config_loader import load_global_config, load_zones_config
from smart_irrigation_system.enums import IrrigationState, ControllerState
from smart_irrigation_system.circuit_state_manager import CircuitStateManager
from smart_irrigation_system.logger import get_logger

# Seed for the weather simulator to ensure reproducibility in tests
WEATHER_SIMULATOR_SEED = 42

# Paths to configuration files
CONFIG_GLOBAL_PATH = "./config/config_global.json"
CONFIG_ZONES_PATH =  "./config/zones_config.json"
ZONE_STATE_PATH = "./data/zones_state.json"

# Constants for irrigation process
MAX_WAIT_TIME = 60 * 30    # seconds, should be time long enough for most of circuits to finish irrigation, in future maybe make it configurable, or automatically adjust it based on the circuit's average irrigation time
WAIT_INTERVAL_SECONDS = 1  # seconds, how often to check the flow capacity when waiting for it to become available


class IrrigationController:
    """The main irrigation controller that manages all the irrigation circuits. Pattern: Singleton"""

    # ============================================================================================================
    # Initialization and configuration loading
    # ============================================================================================================

    def __init__(self, config_global_path=CONFIG_GLOBAL_PATH, config_zones_path=CONFIG_ZONES_PATH):
        self.logger = get_logger("IrrigationController")
        self.global_config_path = config_global_path
        self.zones_config_path = config_zones_path

        # Load configurations
        self._load_global_config()
        self._load_zones_config()

        # Initialize components
        self.global_conditions_provider = self._initialize_global_conditions_provider()
        self.state_manager = CircuitStateManager(ZONE_STATE_PATH)
        atexit.register(self.state_manager.handle_clean_shutdown)

        # Initialize threading
        self._initialize_threading()

        # Set initial controller state
        self.controller_state = ControllerState.IDLE  
        
        self.logger.info("IrrigationController initialized with %d circuits.", len(self.circuits))

    def _load_global_config(self):
        """Loads the globalconfiguration."""
        try:
            self.global_config: GlobalConfig = load_global_config(self.global_config_path)
        except FileNotFoundError as e:
            self.logger.error(f"Global configuration file not found: {e}. Exiting initialization.")
            raise e
        except ValueError as e:
            self.logger.error(f"Error loading global configuration: {e}. Exiting initialization.")
            raise e
        
    def _load_zones_config(self):
        """Loads the zones configuration and initializes circuits."""
        try:
            self.circuits_list = load_zones_config(self.zones_config_path)
            self.circuits: Dict[int, IrrigationCircuit] = {circuit.id: circuit for circuit in self.circuits_list}
            self.logger.debug("Zones configuration loaded successfully with %d circuits.", len(self.circuits))
        except FileNotFoundError as e:
            self.logger.error(f"Zones configuration file not found: {e}. Exiting initialization.")
            raise e
        except ValueError as e:
            self.logger.error(f"Error loading zones configuration: {e}. Exiting initialization.")
            raise e

    def _initialize_global_conditions_provider(self) -> WeatherSimulator | RecentWeatherFetcher:
        """Initializes the global conditions provider as WeatherSimulator if API is not available, or RecentWeatherFetcher if it is available."""
        max_interval_days = max((circuit.interval_days for circuit in self.circuits_list), default=1)
        if self.global_config.weather_api.api_enabled:
            try:
                fetcher = RecentWeatherFetcher(global_config=self.global_config, max_interval_days=max_interval_days)
                self.logger.info("Using RecentWeatherFetcher for global conditions.")
                return fetcher
            except ValueError as e:
                self.logger.error(f"Failed to initialize RecentWeatherFetcher: {e}.")
                # on error, fallback to WeatherSimulator (if environment = 'production' this should not happen)

        self.logger.info("Using WeatherSimulator for global conditions.")
        return WeatherSimulator(seed=WEATHER_SIMULATOR_SEED)
    
    def _initialize_threading(self):
        """Initializes threading-related components."""
        if THREADING_SUPPORTED:
            self.threads = []
            self.stop_event = threading.Event()
            self.threads_lock = threading.Lock()
            self.logger.info("Threading is supported in this environment.")
        else:
            self.logger.warning("Threading is not supported in this environment. Using dummy threading implementation.")
            self.threads = []
            self.stop_event = DummyEvent()
            self.threads_lock = DummyLock()

    
    # ===========================================================================================================
    # Configuration management
    # ===========================================================================================================

    def reload_config(self, config_global_path=CONFIG_GLOBAL_PATH, config_zones_path=CONFIG_ZONES_PATH):
        """ Reloads the global configuration and zones configuration in runtime. If any error occurs, it will raise an exception and the controller will not be updated. """
        pass

    # ===========================================================================================================
    # Status and information retrieval
    # ===========================================================================================================

    def get_status_summary(self) -> Dict[str, Any]:
        """Returns a summary of the current status of the irrigation controller for DisplayManager"""
        summary = {
            "global_conditions": self.global_conditions_provider.get_current_conditions().to_dict(),
            "circuits": {circuit.id: circuit.get_status_summary() for circuit in self.circuits.values()},
            "global_config": self.global_config.to_dict(),
            "circuit_states": {circuit.id: circuit.state.value for circuit in self.circuits.values()},
        }
        return summary
    
    def get_daily_irrigation_time(self) -> time.struct_time:
        """Returns the daily irrigation time based on the global configuration"""
        return time.struct_time((0, 0, 0, self.global_config.automation.scheduled_hour, self.global_config.automation.scheduled_minute, 0, 0, 0, -1))
    
    def get_circuit(self, circuit_number):
        """Returns the circuit object for a given circuit number"""

        if circuit_number in self.circuits:
            return self.circuits[circuit_number]
        else:
            raise ValueError(f"Circuit number {circuit_number} does not exist.")
    
    def get_state(self) -> ControllerState:
        """Returns the current state of the irrigation controller"""
        return self.controller_state
        
    def get_current_consumption(self) -> float:
        """Returns the total consumption of all irrigating circuits in liters per hour"""
        total_consumption = 0.0
        with self.threads_lock:
            for circuit in self.circuits.values():
                if circuit.is_currently_irrigating:
                    total_consumption += circuit.get_circuit_consumption()
        
        return total_consumption
    
    def get_irrigating_count(self) -> int:
        """Checks how many threads are currently running"""
        with self.threads_lock:
            return len(self.threads)


    # ===========================================================================================================
    # Irrigation management
    # ===========================================================================================================
    
    def perform_automatic_irrigation(self):
        """Performs automatic irrigation based on the global configuration"""
        if not self.global_config.automation.enabled:
            self.logger.warning("Automatic irrigation is not enabled in the global configuration.")
            return
        
        if self.controller_state != ControllerState.IDLE:
            self.logger.warning("Cannot start automatic irrigation while the controller is not in IDLE state.")
            return

        self.logger.info("Starting automatic irrigation process...")

        # Update global conditions before starting irrigation
        self.global_conditions_provider.update_current_conditions()
        current_conditions_str = self.global_conditions_provider.get_conditions_str()
        self.logger.info(f"Global conditions updated: {current_conditions_str}")

        self.controller_state = ControllerState.IRRIGATING

        try:
            if self.global_config.automation.sequential:
                self.logger.info("Performing sequential irrigation...")
                self.perform_irrigation_sequential()
            else:
                self.logger.info("Performing concurrent irrigation...")
                self.perform_irrigation_concurrent()
        except Exception as e:
            self.logger.error(f"Error during automatic irrigation: {e}")
            self.controller_state = ControllerState.ERROR
        else:
            self.logger.info("Automatic irrigation process completed successfully.")
            self.controller_state = ControllerState.IDLE

    def start_irrigation_circuit(self, circuit: IrrigationCircuit):
        """Starts the irrigation process for a specified circuit in a new thread"""
        def thread_target():

            try:
                self.state_manager.irrigation_started(circuit)  # Update the state manager that irrigation has started
                self.logger.info(f"Starting irrigation for circuit {circuit.id}...")
                duration = circuit.irrigate_automatic(self.global_config, self.global_conditions_provider.get_current_conditions(), self.stop_event)
                # maybe better to check the state not by the duration, but by the stop_event.is_set() or circuit.state
                if circuit.state == IrrigationState.STOPPED:
                    assert self.stop_event.is_set(), "Circuit state is STOPPED, but stop_event is not set. This should not happen."
                    self.logger.warning(f"Irrigation for circuit {circuit.id} was interrupted.")
                    self.state_manager.update_irrigation_result(circuit, "interrupted", duration)
                else:
                    self.state_manager.update_irrigation_result(circuit, "success", duration)
            except Exception as e:
                self.logger.error(f"Unexpected error during irrigation of circuit {circuit.id}: {e}")
                self.state_manager.update_irrigation_result(circuit, "error", 0)
            finally:
                # after the irrigation is done, OR after interruption, remove the thread from the list
                with self.threads_lock:
                    current = threading.current_thread()
                    try:
                        self.threads.remove(current)
                    except ValueError:
                        self.logger.warning(f"Thread {current.name} not found in the threads list. It might have already been removed.")
                
                    # Update the circuit state after irrigation
                    circuit.state = IrrigationState.IDLE if not circuit.state == IrrigationState.ERROR else IrrigationState.ERROR

        t = threading.Thread(target=thread_target)
        with self.threads_lock:
            self.threads.append(t)

        t.start()
    
    def perform_irrigation_concurrent(self):
        """Performs automatic irrigation for all circuits at once"""
        self.stop_event.clear()

        for circuit in self.circuits.values():
            # Check if the stop event is set before starting irrigation
            if self.stop_event.is_set():
                self.logger.info("Stopping irrigation due to stop event.")
                break

            if circuit.is_irrigation_allowed(self.state_manager):
                # Check the current consumption against the main valve max flow limit
                try:
                    wait_time = 0
                    # NOTE: This is a blocking call, it will wait until the flow capacity is available
                    while (self.global_config.automation.max_flow_monitoring
                            and self.get_current_consumption() + circuit.get_circuit_consumption()
                            > self.global_config.irrigation_limits.main_valve_max_flow):
                        if wait_time >= MAX_WAIT_TIME:
                            self.state_manager.update_irrigation_result(circuit, "skipped", 0)
                            raise TimeoutError(f"Timeout: Skipping circuit {circuit.id} due to persistent flow overload.")
                        
                        self.logger.debug(f"Waiting for flow capacity for circuit {circuit.id}...")
                        self.logger.info(f"Current consumption: {self.get_current_consumption()} L/h, Circuit consumption: {circuit.get_circuit_consumption()} L/h")
                        time.sleep(WAIT_INTERVAL_SECONDS)  # Wait for 1 second before checking again
                        wait_time += WAIT_INTERVAL_SECONDS

                    self.start_irrigation_circuit(circuit)
                except TimeoutError as e:
                    self.logger.warning(str(e))
                    continue
            else:
                self.logger.info(f"Circuit {circuit.id} does not need irrigation at the moment.")
                self.state_manager.update_irrigation_result(circuit, "skipped", 0)
        
        # Wait for all threads to finish
        self.logger.debug("Waiting for all irrigation threads to finish...")
        while True:
            with self.threads_lock:
                if not self.threads:
                    break
                threads_copy = list(self.threads)
            for t in threads_copy:
                t.join(timeout=1)  # prevent indefinite blocking
            time.sleep(0.1)
        self.logger.debug("All irrigation threads have completed.")

    def perform_irrigation_sequential(self):
        """Performs automatic irrigation for all circuits one by one by their IDs"""
        self.stop_event.clear()
        self.controller_state = ControllerState.IRRIGATING

        try:
            for circuit in self.circuits.values():
                # Check if the stop event is set before starting irrigation
                if self.stop_event.is_set():
                    self.logger.info("Stopping irrigation due to stop event.")
                    break

                if not circuit.is_irrigation_allowed(self.state_manager):
                    self.logger.info(f"Circuit {circuit.id} does not need irrigation at the moment.")
                    self.state_manager.update_irrigation_result(circuit, "skipped", 0)
                    continue

                # Check the current consumption against the main valve max flow limit
                if self.global_config.automation.max_flow_monitoring and \
                circuit.get_circuit_consumption() > self.global_config.irrigation_limits.main_valve_max_flow:
                    self.logger.warning(f"Circuit {circuit.id} has too high consumption ({circuit.get_circuit_consumption()} L/h) to start irrigation, skipping it.")
                    self.state_manager.update_irrigation_result(circuit, "skipped", 0)
                    continue
                try:
                    self.state_manager.irrigation_started(circuit)  # Update the state manager that irrigation has started
                    self.logger.info(f"Starting irrigation for circuit {circuit.id}...")
                    duration = circuit.irrigate_automatic(self.global_config, self.global_conditions_provider.get_current_conditions(), self.stop_event)
                    if circuit.state == IrrigationState.STOPPED:
                        assert self.stop_event.is_set(), "Circuit state is STOPPED, but stop_event is not set. This should not happen."
                        self.logger.warning(f"Irrigation for circuit {circuit.id} was interrupted.")
                        self.state_manager.update_irrigation_result(circuit, "interrupted", duration)
                    else:
                        self.state_manager.update_irrigation_result(circuit, "success", duration)
                except Exception as e:
                    self.logger.error(f"Unexpected error during irrigation of circuit {circuit.id}: {e}")
                    self.state_manager.update_irrigation_result(circuit, "error", 0)
                finally:
                    # Update the circuit state after irrigation
                    circuit.state = IrrigationState.IDLE
        except Exception as e:
            self.logger.error(f"Error during sequential irrigation: {e}")
            self.controller_state = ControllerState.ERROR
        else:
            self.logger.info("Sequential irrigation process completed successfully.")
            self.controller_state = ControllerState.IDLE

    def stop_irrigation(self):
        """Stops all irrigation processes"""
        self.logger.info("Stopping all irrigation processes...")
        self.stop_event.set()

        with self.threads_lock:
            threads_copy = self.threads.copy()
        
        for thread in threads_copy:
            thread.join()  # Wait for all threads to finish
        
        self.threads.clear()  # Clear the thread list after stopping all threads
        self.logger.info("Stopping circuits done.")


    # ===========================================================================================================
    # Cleanup and shutdown
    # ===========================================================================================================

    def cleanup(self):
        """Cleans up the resources used by the irrigation controller"""
        self.logger.info("Cleaning up resources...")
        self.stop_irrigation()
    
