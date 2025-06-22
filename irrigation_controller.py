import threading
from irrigation_circuit import IrrigationCircuit
from global_conditions import GlobalConditions
import threading
from enums import TEMP_WATERING_TIME


class IrrigationController:
    """The main irrigation controller that manages all the irrigation circuits"""

    def __init__(self):
        self.global_conditions = GlobalConditions()
        self.circuits = {}
        self.threads = []
        self.stop_event = threading.Event()
        self.threads_lock = threading.Lock()


    def get_circuit(self, circuit_number):
        """Returns the circuit object for a given circuit number"""

        if circuit_number in self.circuits:
            return self.circuits[circuit_number]
        else:
            raise ValueError(f"Circuit number {circuit_number} does not exist.")
        

    def add_circuit(self, name, relay_pin, sensor_pins=[]):
        """Adds a new irrigation circuit to the controller"""

        circuit_number = len(self.circuits)
        circuit = IrrigationCircuit(name, circuit_number, relay_pin, sensor_pins)
        self.circuits[circuit_number] = circuit

    
    def print_conditions(self):
        self.global_conditions.update()
        conditions = self.global_conditions.get_conditions()

        print("I-Controller: Current global conditions:")
        print(conditions)

    
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

    
    def perform_irrigation(self):
        """Performs irrigation for all circuits based on the current conditions"""
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
        


    def remove_thread(self, thread):
        self.threads.remove(thread)

    
    def is_irrigating(self) -> int:
        """Checks how many threads are currently running"""
        with self.threads_lock:
            return len(self.threads)