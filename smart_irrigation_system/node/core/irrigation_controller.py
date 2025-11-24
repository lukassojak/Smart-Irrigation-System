import time, threading, atexit, sys, signal, os
from typing import Dict, Any
from datetime import datetime

from smart_irrigation_system.node.core.irrigation_circuit import IrrigationCircuit
from smart_irrigation_system.node.weather.global_conditions import GlobalConditions
from smart_irrigation_system.node.weather.weather_simulator import WeatherSimulator
from smart_irrigation_system.node.weather.recent_weather_fetcher import RecentWeatherFetcher
from smart_irrigation_system.node.config.global_config import GlobalConfig
from smart_irrigation_system.node.config.config_loader import load_global_config, load_zones_config
from smart_irrigation_system.node.core.enums import IrrigationState, ControllerState, IrrigationOutcome
from smart_irrigation_system.node.core.circuit_state_manager import CircuitStateManager
from smart_irrigation_system.node.utils.logger import get_logger
from smart_irrigation_system.node.core.irrigation_result import IrrigationResult
from smart_irrigation_system.node.core.status_models import CircuitStatus, CircuitSnapshot, CircuitRuntimeStatus
import smart_irrigation_system.node.utils.time_utils as time_utils

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

# Constants for irrigation process
MAX_WAIT_TIME = 500    # seconds, should be time long enough for most of circuits to finish irrigation
WAIT_INTERVAL_SECONDS = 5  # seconds, how often to check the flow capacity when waiting for it to become available

# Constants for automatic irrigation main loop
CHECK_INTERVAL = 5  # seconds, how often to check the time for irrigation
TOLERANCE = 1  # minutes, tolerance for irrigation time, if the current time is within this tolerance of the scheduled time, irrigation will be started
WEATHER_CACHE_REFRESH_INTERVAL = 1 * 60  # seconds, how often to refresh the weather cache in RecentWeatherFetcher

class IrrigationController:
    """The main irrigation controller that manages all the irrigation circuits. Pattern: Singleton"""
    _instance = None
    _lock = threading.Lock()

    # ============================================================================================================
    # Initialization and configuration loading
    # ============================================================================================================

    def __new__(cls, *args, **kwargs):
        """Singleton implementation"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            else:
                cls._instance.logger.warning("IrrigationController instance already exists, returning the existing instance.")
        return cls._instance

    def __init__(self, config_global_path=CONFIG_GLOBAL_PATH, config_zones_path=CONFIG_ZONES_PATH):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.logger = get_logger("IrrigationController")
        self.global_config_path = config_global_path
        self.zones_config_path = config_zones_path

        # Load configurations
        self._load_global_config()
        self._load_zones_config()

        # Initialize components
        self.global_conditions_provider = self._initialize_global_conditions_provider()
        self.state_manager = CircuitStateManager(ZONE_STATE_PATH, IRRIGATION_LOG_PATH)

        # Initialize threading
        self.threads = []
        self.stop_event = threading.Event()
        self.threads_lock = threading.Lock()

        # Initialize automatic irrigation management
        self._timer_thread = None  # Thread for checking irrigation time
        self._timer_stop_event = threading.Event()  # Event to stop the timer thread
        self._timer_pause_event = threading.Event()  # Event to pause the timer thread

        # Consumption tracking
        self.current_consumption = 0.0  # Total consumption of all irrigating circuits in liters per hour

        # Set initial controller state
        self.controller_state = ControllerState.IDLE

        # Register signal handlers for clean shutdown
        self._register_signal_handlers()
        atexit.register(self.cleanup)  # Ensure cleanup is called on exit
        
        self.logger.info("Environment: %s", self.global_config.automation.environment)
        self._initialized = True
        self.logger.info("IrrigationController initialized with %d circuits.", len(self.circuits))
    
    def _register_signal_handlers(self):
        def shutdown_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, performing clean shutdown...")
            sys.exit(0)
        
        # Common termination signals
        signal.signal(signal.SIGTERM, shutdown_handler)  # Termination signal
        signal.signal(signal.SIGINT, shutdown_handler)   # Ctrl+C
        # SIGKILL cannot be caught - when received and the irrigation is running, the valves may remain open until the next startup

    def _load_global_config(self):
        """Loads the globalconfiguration."""
        try:
            self.global_config: GlobalConfig = load_global_config(self.global_config_path, CONFIG_SECRETS_PATH)
            self.logger.debug("Global configuration loaded successfully.")
        except FileNotFoundError as e:
            self.logger.error(f"Global configuration file not found: {e}. Exiting initialization.")
            raise Exception("Global configuration file not found.") from e
        except ValueError as e:
            self.logger.error(f"Error loading global configuration: {e}. Exiting initialization.")
            raise Exception("Error loading global configuration. Check the configuration file format.") from e
        
    def _load_zones_config(self):
        """Loads the zones configuration and initializes circuits."""
        try:
            self.circuits_list = load_zones_config(self.zones_config_path)
            self.circuits: Dict[int, IrrigationCircuit] = {circuit.id: circuit for circuit in self.circuits_list}
            self.logger.debug("Zones configuration loaded successfully with %d circuits.", len(self.circuits))
        except FileNotFoundError as e:
            self.logger.error(f"Zones configuration file not found: {e}. Exiting initialization.")
            raise Exception("Zones configuration file not found.") from e
        except ValueError as e:
            self.logger.error(f"Error loading zones configuration: {e}. Exiting initialization.")
            raise Exception("Error loading zones configuration. Check the configuration file format.") from e

    def _initialize_global_conditions_provider(self) -> WeatherSimulator | RecentWeatherFetcher:
        """Initializes the global conditions provider as WeatherSimulator if API is not available, or RecentWeatherFetcher if it is available."""
        self.logger.debug("Initializing global conditions provider...")
        max_interval_days = max((circuit.interval_days for circuit in self.circuits_list), default=1)
        use_recent_weather_fetcher = self.global_config.automation.environment == "production" or not self.global_config.automation.use_weathersimulator
        if use_recent_weather_fetcher:
            fetcher = RecentWeatherFetcher(global_config=self.global_config, max_interval_days=max_interval_days)
            self.logger.info("Global conditions provider initialized as RecentWeatherFetcher.")
            return fetcher

        self.logger.info("Global conditions provider initialized as WeatherSimulator with seed %d.", WEATHER_SIMULATOR_SEED)
        return WeatherSimulator(seed=WEATHER_SIMULATOR_SEED)

    
    # ===========================================================================================================
    # Configuration management
    # ===========================================================================================================

    def reload_config(self, config_global_path=CONFIG_GLOBAL_PATH, config_zones_path=CONFIG_ZONES_PATH):
        """ Reloads the global configuration and zones configuration in runtime. If any error occurs, it will raise an exception and the controller will not be updated. """
        pass

    # ===========================================================================================================
    # Controller state management
    # ===========================================================================================================

    def _update_controller_state(self, delay: float = 0.0):
        """Updates the controller state based on the current threads and stop event."""
        if delay > 0:
            time.sleep(delay)

        if self.controller_state == ControllerState.ERROR:
            return # Do not change state if in ERROR

        stopping = self.stop_event.is_set()
        with self.threads_lock:
            previous_state = self.controller_state
            if stopping:
                self.controller_state = ControllerState.STOPPING
            # elif any_alive
            elif any(t.is_alive() for t in self.threads):
                self.controller_state = ControllerState.IRRIGATING
            else:
                self.controller_state = ControllerState.IDLE
        
        if previous_state != self.controller_state:
            self.logger.info(f"Controller state changed from {previous_state.name} to {self.controller_state.name}.")
            # Future MQTT publish or other notifications can be added here
    
    def _set_error_state(self):
        """Sets the controller state to ERROR."""
        # if irrigation is running, stop it
        if self.controller_state == ControllerState.IRRIGATING:
            self.stop_irrigation()
        
        self.controller_state = ControllerState.ERROR
        self.logger.error("Controller state set to ERROR.")

    
    # ===========================================================================================================
    # Threading and concurrency management
    # ===========================================================================================================


    # ===========================================================================================================
    # Status and information retrieval
    # ===========================================================================================================

    def get_circuit_snapshot(self, circuit_id: int) -> CircuitSnapshot:
        """Returns the persistent snapshot state of a given circuit."""
        if circuit_id not in self.circuits:
            raise ValueError(f"Circuit ID {circuit_id} does not exist.")
        
        snapshot = self.state_manager.get_circuit_snapshot(circuit_id)
        return snapshot


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

    def get_status(self) -> dict:
        """
        Returns comprehensive snapshot of the irrigation controller's status.:

        """

        # Fetch global conditions
        cached_conditions_str = self.global_conditions_provider.get_conditions_str()

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
            'auto_paused': self._timer_pause_event.is_set(),
            'auto_stopped': self._timer_stop_event.is_set(),
            'scheduled_time': scheduled_time,
            'sequential': self.global_config.automation.sequential,
            'controller_state': self.controller_state.name,
            'cache_update': self.global_conditions_provider.last_cache_update,
            'cached_global_conditions': cached_conditions_str.split(", Timestamp:")[0],
            'zones': zones_status,
            'current_consumption': self.get_current_consumption(),
            'input_flow_capacity': self.global_config.irrigation_limits.main_valve_max_flow,
        }

        return status
    
    def get_circuit_progress(self, circuit_number: int) -> tuple[float, float]:
        """Returns the current progress and target water amount for a given circuit."""
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
        for circuit in self.circuits.values():
            if circuit.is_currently_irrigating:
                total_consumption += circuit.circuit_consumption
        return total_consumption
    
    def get_irrigating_count(self) -> int:
        """Checks how many threads are currently running"""
        with self.threads_lock:
            return len(self.threads)


    # ===========================================================================================================
    # Irrigation management
    # ===========================================================================================================
    
    def start_automatic_irrigation(self):
        """Starts automatic irrigation in a separate thread."""
        if getattr(self, "_auto_irrigation_thread", None) and self._auto_irrigation_thread.is_alive():
            self.logger.info("Automatic irrigation already running.")
            return

        def irrigation_thread_func():
            self.perform_automatic_irrigation()

        self._auto_irrigation_thread = threading.Thread(target=irrigation_thread_func, daemon=True)
        self._auto_irrigation_thread.start()


    def perform_automatic_irrigation(self):
        """Performs automatic irrigation based on the global configuration"""
        if not self.global_config.automation.enabled:
            self.logger.warning("Automatic irrigation is not enabled in the global configuration.")
            return
        
        if self.controller_state not in [ControllerState.IDLE, ControllerState.IRRIGATING]:
            self.logger.warning(f"Cannot start automatic irrigation while the controller is in {self.controller_state.name} state.")
            return

        # Update global conditions before starting irrigation
        self.global_conditions_provider.get_current_conditions()
        current_conditions_str = self.global_conditions_provider.get_conditions_str()
        self.logger.info(f"Global conditions updated: {current_conditions_str}")

        try:
            if self.global_config.automation.sequential:
                self.logger.info("Performing sequential automatic irrigation...")
                self.perform_irrigation_sequential()
            else:
                self.logger.info("Performing concurrent automatic irrigation...")
                self.perform_irrigation_concurrent()
        except Exception as e:
            self.logger.error(f"Error during automatic irrigation: {e}")
            self._set_error_state()
        else:
            self.logger.info("Automatic irrigation process completed.")
            self._update_controller_state()

    def start_irrigation_circuit(self, circuit: IrrigationCircuit) -> threading.Thread:
        """Starts the irrigation process for a specified circuit in a new thread. Returns the thread object."""
        def thread_target():
            # TODO: Handle exceptions within the thread and clean up & update state accordingly
            self.state_manager.irrigation_started(circuit.id)
            self.logger.debug(f"Starting irrigation for circuit {circuit.id}...")
            result = circuit.irrigate_auto(self.global_config, self.global_conditions_provider.get_current_conditions(), self.stop_event)
            self.logger.info(f"Irrigation for circuit {circuit.id} completed with result: {result}.")
            self.state_manager.irrigation_finished(circuit.id, result)
            # after the irrigation is done, OR after interruption, remove the thread from the list
            with self.threads_lock:
                current = threading.current_thread()
                try:
                    self.threads.remove(current)
                except ValueError:
                    self.logger.warning(f"Thread {current.name} not found in the threads list. It might have already been removed.")

        t = threading.Thread(target=thread_target)
        with self.threads_lock:
            self.threads.append(t)

        t.start()
        return t
    
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
                            and self.get_current_consumption() + circuit.circuit_consumption
                            > self.global_config.irrigation_limits.main_valve_max_flow) and \
                            not self.stop_event.is_set():
                        if wait_time >= MAX_WAIT_TIME:
                            result = circuit.flow_overload_timeout_triggered(time_utils.now())
                            self.state_manager.irrigation_finished(circuit.id, result)
                            raise TimeoutError(f"Timeout: Skipping circuit {circuit.id} due to persistent flow overload.")
                        
                        self.logger.debug(f"Waiting for flow capacity for circuit {circuit.id}...")
                        self.logger.info(f"Current consumption: {self.get_current_consumption()} L/h, Circuit consumption: {circuit.circuit_consumption} L/h")
                        time.sleep(WAIT_INTERVAL_SECONDS)  # Wait for 1 second before checking again
                        wait_time += WAIT_INTERVAL_SECONDS

                    if not self.stop_event.is_set():
                        self.start_irrigation_circuit(circuit)
                        self._update_controller_state()
                except TimeoutError as e:
                    self.logger.warning(str(e))
                    continue
        
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
        self._update_controller_state()
        self.logger.debug("All irrigation threads have completed.")

    def perform_irrigation_sequential(self):
        """Performs automatic irrigation for all circuits one by one by their IDs"""
        self.stop_event.clear()

        try:
            for circuit in self.circuits.values():
                # Check if the stop event is set before starting irrigation
                if self.stop_event.is_set():
                    self.logger.info("Stopping irrigation due to stop event.")
                    break

                if not circuit.is_irrigation_allowed(self.state_manager):
                    self.logger.info(f"Circuit {circuit.id} does not need irrigation at the moment.")
                    continue

                # Check the current consumption against the main valve max flow limit
                if self.global_config.automation.max_flow_monitoring and \
                circuit.circuit_consumption > self.global_config.irrigation_limits.main_valve_max_flow:
                    self.logger.warning(f"Circuit {circuit.id} has too high consumption ({circuit.circuit_consumption} L/h) to start irrigation, skipping it.")
                    result = circuit.flow_overload_timeout_triggered(time_utils.now())
                    self.state_manager.irrigation_finished(circuit.id, result)
                    continue

                t = self.start_irrigation_circuit(circuit) # start irrigation in a new thread
                self._update_controller_state()

                # Wait for the thread to finish before starting the next one
                t.join()
                self._update_controller_state()

        except Exception as e:
            self.logger.error(f"Error during sequential irrigation: {e}")
        else:
            self._update_controller_state()
            self.logger.info("Sequential irrigation process completed.")

    def stop_irrigation(self):
        """Stops all irrigation processes"""
        if any(t.is_alive() for t in self.threads) == False:
            self.logger.info("No irrigation processes are running. Nothing to stop.")
            return

        self.stop_event.set()
        self._update_controller_state(delay=0.1)  # Small delay to allow threads to recognize the stop event
        self.logger.info("Stopping all irrigation processes...")

        with self.threads_lock:
            threads_copy = self.threads.copy()
        
        for thread in threads_copy:
            thread.join()  # Wait for all threads to finish
        
        self.threads.clear()  # Clear the thread list after stopping all threads
        self.stop_event.clear()  # Reset the stop event for future irrigation
        self._update_controller_state()
        self.logger.info("Stopping circuits done.")

    def manual_irrigation(self, circuit_number: int, liter_amount: float) -> IrrigationResult:
        """Starts manual irrigation for a specified circuit and liter amount in a separate thread."""
        if circuit_number not in self.circuits:
            self.logger.warning(f"Circuit number {circuit_number} does not exist.")
            raise ValueError(f"Circuit number {circuit_number} does not exist.")
        
        circuit = self.circuits[circuit_number]

        if self.controller_state != ControllerState.IDLE and self.controller_state != ControllerState.IRRIGATING:
            self.logger.warning(f"Cannot start manual irrigation while the controller is not in IDLE state, current state: {self.controller_state.name}.")
            raise RuntimeError("Cannot start manual irrigation while the controller is not in IDLE state.")
    
        if circuit.state != IrrigationState.IDLE:
            self.logger.warning(f"Circuit {circuit.id} is not in IDLE state, current state: {circuit.state.name}. Cannot start manual irrigation.")
            raise RuntimeError(f"Circuit {circuit.id} is not in IDLE state, cannot start manual irrigation.")

        self.logger.debug(f"Starting manual irrigation for circuit {circuit.id} with target {liter_amount} liters...")

        def manual_irrigation_thread_func():
            try:
                self.state_manager.irrigation_started(circuit.id)  # Update the state manager that irrigation has started
                self.logger.info(f"Manual irrigation for circuit {circuit.id} started with target {liter_amount} liters...")
                result = circuit.irrigate_man(liter_amount, self.stop_event)
                self.logger.info(f"Manual irrigation for circuit {circuit.id} completed with result: {result}.")
                self.state_manager.irrigation_finished(circuit.id, result)
            except Exception as e:
                self.logger.error(f"Error during manual irrigation for circuit {circuit.id}: {e}")
            finally:
                with self.threads_lock:
                    current = threading.current_thread()
                    try:
                        self.threads.remove(current)
                    except ValueError:
                        self.logger.warning(f"Thread {current.name} not found in the threads list. It might have already been removed.")
                self._update_controller_state()
                self.logger.info(f"Manual irrigation thread for circuit {circuit.id} has finished.")

        manual_thread = threading.Thread(target=manual_irrigation_thread_func, daemon=True)
        with self.threads_lock:
            self.threads.append(manual_thread)
        manual_thread.start()
        self._update_controller_state()



    # ===========================================================================================================
    # Cleanup and shutdown
    # ===========================================================================================================


    def cleanup(self):
        """Cleans up the resources used by the irrigation controller"""
        self.logger.info("Cleaning up resources...")
        if self.controller_state != ControllerState.IDLE:
            self.stop_irrigation()
        # Check if all valves are closed
        for circuit in self.circuits.values():
            if circuit.state == IrrigationState.IRRIGATING:
                self.logger.warning(f"Circuit {circuit.id} is still irrigating during cleanup, attempting to close valve.")
                circuit.close_valve()
        self.state_manager.handle_clean_shutdown()

    
    # ===========================================================================================================
    # Main loop for automatic irrigation management
    # ===========================================================================================================

    def start_main_loop(self):
        """Starts the main loop for automatic irrigation management. Only one instance of the main loop can run at a time."""
        if self._timer_thread and self._timer_thread.is_alive():
            self.logger.info("Main loop already running.")
            return
        
        self.logger.info("Starting main loop...")
        self._timer_stop_event.clear()
        self._timer_pause_event.clear()
        self._timer_thread = threading.Thread(target=self._main_loop_func, daemon=True)
        self._timer_thread.start()

    def stop_main_loop(self):
        """Stops the main loop for automatic irrigation management"""
        # TODO: blocking call to stop the main loop, should be non-blocking
        self.logger.info("Stopping main loop...")
        self._timer_stop_event.set()
        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join()
    
    def pause_main_loop(self):
        """Pauses the main loop for the next irrigation check"""
        self.logger.info("Pausing main loop...")
        self._timer_pause_event.set()
    
    def resume_main_loop(self):
        """Resumes the main loop after pausing"""
        self.logger.info("Resuming main loop...")
        self._timer_pause_event.clear()
    
    def _main_loop_func(self):
        irrigation_hour = self.global_config.automation.scheduled_hour
        irrigation_minute = self.global_config.automation.scheduled_minute
        skipped_cycle = False   # flag to indicate if the current irrigation cycle was skipped due to pause
        already_checked = False # flag to indicate if the irrigation time has already been checked in the current irrigation window

        try:
            while not self._timer_stop_event.is_set():
                current_time = time.localtime()
                time_diff = (current_time.tm_hour - irrigation_hour) * 60 + (current_time.tm_min - irrigation_minute) # in minutes

                # Check the irrigation window
                if (getattr(self, "_auto_irrigation_thread", None) is None or not self._auto_irrigation_thread.is_alive()) and \
                abs(time_diff) <= TOLERANCE:

                    # If main loop is paused, skip current irrigation and resume
                    if self._timer_pause_event.is_set() and not skipped_cycle:
                        skipped_cycle = True
                        self.logger.info("Main loop is paused, skipping current irrigation check.")
                    
                    elif not already_checked:
                        self.logger.debug(f"Current time {current_time.tm_hour:02}:{current_time.tm_min:02} matches irrigation time {irrigation_hour:02}:{irrigation_minute:02} within tolerance of {TOLERANCE} minutes.")
                        self.start_automatic_irrigation()   # non-blocking call to start irrigation
                        already_checked = True

                # The variable window_passed is used to reset the skipped_cycle and already_checked flags after the irrigation window has passed
                window_passed = abs(time_diff) > TOLERANCE and (skipped_cycle or already_checked)

                # Reset flags after the irrigation window has passed
                if window_passed:
                    skipped_cycle, already_checked = False, False

                time.sleep(CHECK_INTERVAL)  # Wait for the next check
        
        except Exception as e:
            self.logger.error(f"Oh no! Main loop encountered an error: {e}")
        
        finally:
            self.logger.info("Main loop stopped.")