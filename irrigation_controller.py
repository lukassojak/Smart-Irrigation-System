import threading
import time
import json
from typing import List, Dict
from irrigation_circuit import IrrigationCircuit
from global_conditions import GlobalConditions
from global_config import GlobalConfig
from config_loader import load_global_config, load_zones_config


CONFIG_GLOBAL_PATH = "./config/config_global.json"
CONFIG_ZONES_PATH =  "./config/zones_config.json"


class IrrigationController:
    """The main irrigation controller that manages all the irrigation circuits. Pattern: Singleton"""

    def __init__(self, config_global_path=CONFIG_GLOBAL_PATH, config_zones_path=CONFIG_ZONES_PATH):
        self.global_conditions: GlobalConditions = GlobalConditions()                                          # Initialize global conditions
        self.circuits_list = load_zones_config(config_zones_path)
        self.circuits: Dict[int, IrrigationCircuit] = {circuit.id: circuit for circuit in self.circuits_list}  # Create a dictionary of circuits by their ID
        self.global_config: GlobalConfig = load_global_config(config_global_path)

        self.threads = []
        self.stop_event = threading.Event()
        self.threads_lock = threading.Lock()


    def get_circuit(self, circuit_number):
        """Returns the circuit object for a given circuit number"""

        if circuit_number in self.circuits:
            return self.circuits[circuit_number]
        else:
            raise ValueError(f"Circuit number {circuit_number} does not exist.")

    
    def start_irrigation_circuit(self, circuit):
        """Starts the irrigation process for a specified circuit in a new thread"""
        def thread_target():
            circuit.irrigate(duration, self.stop_event)

            # after the irrigation is done, OR after interruption, remove the thread from the list
            with self.threads_lock:
                current = threading.current_thread()
                try:
                    self.threads.remove(current)
                except ValueError:
                    print(f"I-Controller: Thread {current.name} not found in the thread list.")


        # calculate irrigation time
        duration = TEMP_WATERING_TIME

        t = threading.Thread(target=thread_target)
        with self.threads_lock:
            self.threads.append(t)

        t.start()

    
    def perform_irrigation(self, sequential: bool = False):
        """Performs automatic irrigation for all circuits"""
        
        self.stop_event.clear()

        global_conditions = self.global_conditions.get_conditions()

        for circuit in self.circuits.values():
            # irrigate according to global conditions
            self.start_irrigation_circuit(circuit)


    def stop_irrigation(self):
        """Stops all irrigation processes"""
        print("I-Controller: Stopping all irrigation processes ...")
        self.stop_event.set()

        with self.threads_lock:
            threads_copy = self.threads.copy()
        
        for thread in threads_copy:
            thread.join()  # Wait for all threads to finish
        
        self.threads.clear()  # Clear the thread list after stopping all threads

    
    def is_irrigating(self) -> int:
        """Checks how many threads are currently running"""
        with self.threads_lock:
            return len(self.threads)