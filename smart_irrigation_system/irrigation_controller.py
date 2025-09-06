
import time, threading, atexit
from typing import Dict, Any
from datetime import datetime

from smart_irrigation_system.irrigation_circuit import IrrigationCircuit
from smart_irrigation_system.global_conditions import GlobalConditions
from smart_irrigation_system.weather_simulator import WeatherSimulator
from smart_irrigation_system.recent_weather_fetcher import RecentWeatherFetcher
from smart_irrigation_system.global_config import GlobalConfig
from smart_irrigation_system.config_loader import load_global_config, load_zones_config
from smart_irrigation_system.enums import IrrigationState, ControllerState, IrrigationOutcome
from smart_irrigation_system.circuit_state_manager import CircuitStateManager
from smart_irrigation_system.logger import get_logger
from smart_irrigation_system.irrigation_result import IrrigationResult

# Seed for the weather simulator to ensure reproducibility in tests
WEATHER_SIMULATOR_SEED = 42

# Paths to configuration and data files
CONFIG_GLOBAL_PATH = "./config/config_global.json"
CONFIG_ZONES_PATH =  "./config/zones_config.json"
ZONE_STATE_PATH = "./data/zones_state.json"
IRRIGATION_LOG_PATH = "./data/irrigation_log.json"

# Constants for irrigation process
MAX_WAIT_TIME = 10    # seconds, should be time long enough for most of circuits to finish irrigation, in future maybe make it configurable, or automatically adjust it based on the circuit's average irrigation time
WAIT_INTERVAL_SECONDS = 1  # seconds, how often to check the flow capacity when waiting for it to become available

# Constants for automatic irrigation main loop
CHECK_INTERVAL = 5  # seconds, how often to check the time for irrigation
TOLERANCE = 1  # minutes, tolerance for irrigation time, if the current time is within this tolerance of the scheduled time, irrigation will be started


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
        self.state_manager = CircuitStateManager(ZONE_STATE_PATH, IRRIGATION_LOG_PATH)
        atexit.register(self.state_manager.handle_clean_shutdown)
        for circuit in self.circuits_list:
            circuit.init_last_irrigation_data(self.state_manager)  # Initialize last irrigation data for each circuit

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
        
        self.logger.info("Environment: %s", self.global_config.automation.environment)
        self.logger.info("IrrigationController initialized with %d circuits.", len(self.circuits))

    def _load_global_config(self):
        """Loads the globalconfiguration."""
        try:
            self.global_config: GlobalConfig = load_global_config(self.global_config_path)
            self.logger.debug("Global configuration loaded successfully.")
        except FileNotFoundError as e:
            self.logger.error(f"Global configuration file not found: {e}. Exiting initialization.")
            raise Exception("Global configuration file not found.") from e
        except ValueError as e:
            self.logger.error(f"Error loading global configuration: {e}. Exiting initialization.")
            raise Exception("Error loading global configuration. Check the configuration file format.") from es
        
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
        use_recent_weather_fetcher = self.global_config.automation.environment == "production" or self.global_config.weather_api.api_enabled
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
    # Status and information retrieval
    # ===========================================================================================================

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
        
        _, _, _, target_water_amount, current_water_amount = circuit.get_progress
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
                total_consumption += circuit.get_circuit_consumption()
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
        
        if self.controller_state != ControllerState.IDLE:
            self.logger.warning("Cannot start automatic irrigation while the controller is not in IDLE state.")
            return


        # Update global conditions before starting irrigation
        self.global_conditions_provider.get_current_conditions()
        current_conditions_str = self.global_conditions_provider.get_conditions_str()
        self.logger.info(f"Global conditions updated: {current_conditions_str}")

        self.controller_state = ControllerState.IRRIGATING

        try:
            if self.global_config.automation.sequential:
                self.logger.info("Performing sequential automatic irrigation...")
                self.perform_irrigation_sequential()
            else:
                self.logger.info("Performing concurrent automatic irrigation...")
                self.perform_irrigation_concurrent()
        except Exception as e:
            self.logger.error(f"Error during automatic irrigation: {e}")
            self.controller_state = ControllerState.ERROR
        else:
            self.logger.info("Automatic irrigation process completed.")
            self.controller_state = ControllerState.IDLE

    def start_irrigation_circuit(self, circuit: IrrigationCircuit):
        """Starts the irrigation process for a specified circuit in a new thread"""
        def thread_target():
            self.state_manager.irrigation_started(circuit)  # Update the state manager that irrigation has started
            self.logger.debug(f"Starting irrigation for circuit {circuit.id}...")
            result = circuit.irrigate_automatic(self.global_config, self.global_conditions_provider.get_current_conditions(), self.stop_event)
            self.logger.info(f"Irrigation for circuit {circuit.id} completed with result: {result}.")
            self.state_manager.irrigation_finished(circuit, result)
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
                            > self.global_config.irrigation_limits.main_valve_max_flow) and \
                            not self.stop_event.is_set():
                        if wait_time >= MAX_WAIT_TIME:
                            result = circuit.flow_overload_timeout_trigerred(datetime.now())
                            self.state_manager.irrigation_finished(circuit, result)
                            raise TimeoutError(f"Timeout: Skipping circuit {circuit.id} due to persistent flow overload.")
                        
                        self.logger.debug(f"Waiting for flow capacity for circuit {circuit.id}...")
                        self.logger.info(f"Current consumption: {self.get_current_consumption()} L/h, Circuit consumption: {circuit.get_circuit_consumption()} L/h")
                        time.sleep(WAIT_INTERVAL_SECONDS)  # Wait for 1 second before checking again
                        wait_time += WAIT_INTERVAL_SECONDS

                    if not self.stop_event.is_set():
                        self.start_irrigation_circuit(circuit)
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
                    continue

                # Check the current consumption against the main valve max flow limit
                if self.global_config.automation.max_flow_monitoring and \
                circuit.get_circuit_consumption() > self.global_config.irrigation_limits.main_valve_max_flow:
                    self.logger.warning(f"Circuit {circuit.id} has too high consumption ({circuit.get_circuit_consumption()} L/h) to start irrigation, skipping it.")
                    result = circuit.flow_overload_timeout_trigerred(datetime.now())
                    self.state_manager.irrigation_finished(circuit, result)
                    continue

                self.state_manager.irrigation_started(circuit)  # Update the state manager that irrigation has started
                self.logger.info(f"Starting irrigation for circuit {circuit.id}...")
                result = circuit.irrigate_automatic(self.global_config, self.global_conditions_provider.get_current_conditions(), self.stop_event)
                self.logger.info(f"Irrigation for circuit {circuit.id} completed with result: {result}.")
                self.state_manager.irrigation_finished(circuit, result)

        except Exception as e:
            self.logger.error(f"Error during sequential irrigation: {e}")
            self.controller_state = ControllerState.ERROR
        else:
            self.logger.info("Sequential irrigation process completed.")
            self.controller_state = ControllerState.IDLE

    def stop_irrigation(self):
        """Stops all irrigation processes"""
        if self.controller_state == ControllerState.IDLE:
            self.logger.info("No irrigation processes are running. Nothing to stop.")
            return

        self.controller_state = ControllerState.STOPPING
        self.logger.info("Stopping all irrigation processes...")

        self.stop_event.set()

        with self.threads_lock:
            threads_copy = self.threads.copy()
        
        for thread in threads_copy:
            thread.join()  # Wait for all threads to finish
        
        self.threads.clear()  # Clear the thread list after stopping all threads

        self.controller_state = ControllerState.IDLE
        self.logger.info("Stopping circuits done.")


    # ===========================================================================================================
    # Cleanup and shutdown
    # ===========================================================================================================

    def cleanup(self):
        """Cleans up the resources used by the irrigation controller"""
        self.logger.info("Cleaning up resources...")
        self.stop_irrigation()

    
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
        skipped_cycle = False

        while not self._timer_stop_event.is_set():
            current_time = time.localtime()
            time_diff = (current_time.tm_hour - irrigation_hour) * 60 + (current_time.tm_min - irrigation_minute) # in minutes
            if (self.get_state() == ControllerState.IDLE and abs(time_diff) <= TOLERANCE):
                # If main loop is paused, skip current irrigation and resume
                if self._timer_pause_event.is_set():
                    if not skipped_cycle:
                        skipped_cycle = True
                        self.logger.info("Main loop is paused, skipping current irrigation check.")
                    time.sleep(CHECK_INTERVAL)
                    continue  # Skip the current iteration

                self.logger.debug(f"Current time {current_time.tm_hour:02}:{current_time.tm_min:02} matches irrigation time {irrigation_hour:02}:{irrigation_minute:02} within tolerance of {TOLERANCE} minutes.")
                self.start_automatic_irrigation()   # non-blocking call to start irrigation
            elif (self.get_state() == ControllerState.IDLE and skipped_cycle):
                skipped_cycle = False
                self._timer_pause_event.clear()
                self.logger.info("Main loop resumed from pause, next irrigation will be at the scheduled time.")

            time.sleep(CHECK_INTERVAL)  # Wait for the next check
        
        self.logger.info("Main loop stopped.")


    # ===========================================================================================================
    # Debugging and testing methods
    # ===========================================================================================================

    def open_valves(self):
        """Opens all valves for debugging purposes"""
        self.logger.debug("Opening all valves for debugging purposes.")
        for circuit in self.circuits.values():
            circuit.open_valve()
    
    def close_valves(self):
        """Closes all valves for debugging purposes"""
        self.logger.debug("Closing all valves for debugging purposes.")
        for circuit in self.circuits.values():
            circuit.close_valve()
    
