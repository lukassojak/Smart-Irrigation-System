try:
    import threading
    print("Threading module is supported.")
    THREADING_SUPPORTED = True
except ImportError:
    THREADING_SUPPORTED = False
    print("Threading module is not supported. Using dummy threading implementation.")
    class DummyThread:
        def __init__(self, *args, **kwargs): pass
        def start(self): print("Threading not supported.")

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

from smart_irrigation_system.irrigation_circuit import IrrigationCircuit
from smart_irrigation_system.global_conditions import GlobalConditions
from smart_irrigation_system.weather_simulator import WeatherSimulator
from smart_irrigation_system.global_config import GlobalConfig
from smart_irrigation_system.config_loader import load_global_config, load_zones_config
from smart_irrigation_system.enums import IrrigationState
from smart_irrigation_system.circuit_state_manager import CircuitStateManager
from smart_irrigation_system.logger import get_logger


# Paths to configuration files

CONFIG_GLOBAL_PATH = "./config/config_global.json"
CONFIG_ZONES_PATH =  "./config/zones_config.json"
ZONE_STATE_PATH = "./data/zones_state.json"

MAX_WAIT_TIME = 60  # seconds, should be time long enough for most of circuits to finish irrigation, in future maybe make it configurable, or automatically adjust it based on the circuit's average irrigation time
WAIT_INTERVAL_SECONDS = 1  # seconds, how often to check the flow capacity when waiting for it to become available


class IrrigationController:
    """The main irrigation controller that manages all the irrigation circuits. Pattern: Singleton"""

    def __init__(self, config_global_path=CONFIG_GLOBAL_PATH, config_zones_path=CONFIG_ZONES_PATH):
        self.logger = get_logger("IrrigationController")
        self.global_config_path = config_global_path
        self.zones_config_path = config_zones_path
        self.global_conditions: GlobalConditions = WeatherSimulator().get_current_conditions()                 # Initialize with current weather conditions
        self.circuits_list = load_zones_config(config_zones_path)
        self.circuits: Dict[int, IrrigationCircuit] = {circuit.id: circuit for circuit in self.circuits_list}  # Create a dictionary of circuits by their ID
        self.global_config: GlobalConfig = load_global_config(config_global_path)
        self.state_manager = CircuitStateManager(ZONE_STATE_PATH)  # Load the circuit state manager with the state file

        if THREADING_SUPPORTED:
            self.threads = []
            self.stop_event = threading.Event()
            self.threads_lock = threading.Lock()
        
        self.logger.info("IrrigationController initialized with %d circuits.", len(self.circuits))

    
    def reload_config(self, config_global_path=CONFIG_GLOBAL_PATH, config_zones_path=CONFIG_ZONES_PATH):
        """ Reloads the global configuration and zones configuration in runtime. If any error occurs, it will raise an exception and the controller will not be updated. """
        pass

    def get_status_summary(self) -> Dict[str, Any]:
        """Returns a summary of the current status of the irrigation controller for DisplayManager"""
        summary = {
            "global_conditions": self.global_conditions.to_dict(),
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
        
    def get_current_consumption(self) -> float:
        """Returns the total consumption of all irrigating circuits in liters per hour"""
        total_consumption = 0.0
        with self.threads_lock:
            for circuit in self.circuits.values():
                if circuit.is_currently_irrigating:
                    total_consumption += circuit.get_circuit_consumption()
        
        return total_consumption
    
    def update_global_conditions(self) -> GlobalConditions:
        """Updates the global conditions with the latest data from the weather server"""
        self.global_conditions = WeatherSimulator().get_current_conditions()
        self.logger.info("Global conditions updated: %s.", self.global_conditions)
        return self.global_conditions

    
    def start_irrigation_circuit(self, circuit: IrrigationCircuit):
        """Starts the irrigation process for a specified circuit in a new thread"""
        def thread_target():

            try:
                self.state_manager.irrigation_started(circuit)  # Update the state manager that irrigation has started
                self.logger.info(f"Starting irrigation for circuit {circuit.id}...")
                duration = circuit.irrigate_automatic(self.global_config, self.update_global_conditions(), self.stop_event)
                self.state_manager.update_irrigation_result(circuit, "success", duration)
            except Exception as e:
                self.logger.error(f"Error during irrigation of circuit {circuit.id}: {e}")
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
                    circuit.state = IrrigationState.IDLE

        t = threading.Thread(target=thread_target)
        with self.threads_lock:
            self.threads.append(t)

        t.start()

    
    def perform_irrigation_concurrent(self):
        """Performs automatic irrigation for all circuits at once"""
        self.stop_event.clear()
        for circuit in self.circuits.values():
            # Check if the stop event is set before starting irrigation
            print("### Current consumption:", self.get_current_consumption())
            if self.stop_event.is_set():
                self.logger.info("Stopping irrigation due to stop event.")
                break

            if circuit.is_irrigation_allowed(self.state_manager):
                # Check the current consumption against the main valve max flow limit

                # POTENTIAL IMPROVEMENT: Separate scheduler for flow monitoring would be better,
                # so that it can monitor the flow independently of the irrigation process.
                # Also, it would be better to monitor the flow in a separate thread, so that it can run concurrently with the irrigation process.
                # ! The scheduler would prevent a highly demanding circuit from blocking the irrigation of less demanding circuits.
                try:
                    wait_time = 0
                    # NOTE: This is a blocking call, it will wait until the flow capacity is available
                    # if the circuit's consumption is high, it will block the irrigation of other circuits until the flow capacity is available
                    while (self.global_config.automation.max_flow_monitoring
                            and self.get_current_consumption() + circuit.get_circuit_consumption()
                            > self.global_config.irrigation_limits.main_valve_max_flow):
                        if wait_time >= MAX_WAIT_TIME:
                            self.state_manager.update_irrigation_result(circuit, "skipped", 0)
                            raise TimeoutError(f"Timeout: Skipping circuit {circuit.id} due to persistent flow overload.")

                        print(f"I-Controller: Waiting for more flow capacity for circuit {circuit.id} ...")
                        print(f"Current consumption: {self.get_current_consumption()} L/h, Circuit consumption: {circuit.get_circuit_consumption()} L/h")
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
        # Using the threads_lock will lead to a deadlock (Why?)


    def perform_irrigation_sequential(self):
        """Performs automatic irrigation for all circuits one by one by their IDs"""
        self.stop_event.clear()
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
                duration = circuit.irrigate_automatic(self.global_config, self.update_global_conditions(), self.stop_event)
                self.state_manager.update_irrigation_result(circuit, "success", duration)
            except Exception as e:
                self.logger.error(f"Error during irrigation of circuit {circuit.id}: {e}")
                self.state_manager.update_irrigation_result(circuit, "error", 0)
            finally:
                # Update the circuit state after irrigation
                circuit.state = IrrigationState.IDLE
            


    def stop_irrigation(self):
        """Stops all irrigation processes"""
        self.logger.info("Stopping all irrigation processes...")
        self.stop_event.set()

        with self.threads_lock:
            threads_copy = self.threads.copy()
        
        for thread in threads_copy:
            thread.join()  # Wait for all threads to finish
        
        self.logger.info("All irrigation processes stopped.")
        self.threads.clear()  # Clear the thread list after stopping all threads

    
    def irrigating_count(self) -> int:
        """Checks how many threads are currently running"""
        with self.threads_lock:
            return len(self.threads)