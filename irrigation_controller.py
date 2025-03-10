import threading
from irrigation_circuit import IrrigationCircuit
from global_conditions import GlobalConditions

class IrrigationController:
    """The main irrigation controller that manages all the irrigation circuits"""

    def __init__(self):
        self.global_conditions = GlobalConditions()
        self.circuits = {}
        self.threads = []
        self.stop_event = threading.Event()


    def add_circuit(self, name, relay_pin, sensor_pins=[]):
        """Adds a new irrigation circuit to the controller"""

        circuit_number = len(self.circuits)
        circuit = IrrigationCircuit(name, circuit_number, relay_pin, sensor_pins)
        self.circuits[circuit_number] = circuit

    
    def print_conditions(self):
        self.global_conditions.update()
        conditions = self.global_conditions.get_conditions()

        print("Current global conditions:")
        print(conditions)

    
    def start_irrigation(self, circuit, duration):
        """Starts the irrigation process for a specified circuit in a new thread"""

        t = threading.Thread(target=self._run_irrigation, args=(circuit, duration))
        t.start()

        with self.threads_lock:
            self.threads.append(t)
    

    def _run_irrigation(self, circuit, duration):
        """Controls irrigation and updates the thread list"""

        circuit.irrigate(duration, self.stop_event)

        # after the irrigation is done, remove the thread from the list
        with self.threads_lock:
            self.threads = [t for t in self.threads if t.is_alive()]        # not too efficient, but works

    
    def perform_irrigation(self):
        """Performs irrigation for all circuits based on the current conditions"""
        self.stop_event.clear()

        global_conditions = self.global_conditions.get_conditions()

        for circuit in self.circuits.values():
            moisture_readings = circuit.read_moisture()

            if SoilMoisture.TOO_WET in moisture_readings:
                print(f"Soil too wet in the circuit number {circuit.number}: {circuit.name}, skipping irrigation cycle for the circuit ...")
                continue

            # move this to the circuit class
            if SoilMoisture.TOO_DRY in moisture_readings:
                print(f"Soil too dry in the circuit number {circuit.number}: {circuit.name}, performing irrigation cycle for dry conditions ...")
                t = threading.Thread(target=circuit.irrigate_too_dry, args=(self.stop_event,))
                self.threads.append(t)
                t.start()
                continue

            if moisture_readings == []:
                print(f"No soil moisture sensors in the circuit number {circuit.number}: {circuit.name}, irrigation cycle depends only on global conditions ...")

            # optimal soil moisture here, irrigate according to global conditions
            t = threading.Thread(target=circuit.irrigate_automatic, args=(self.stop_event,))
            self.threads.append(t)
            t.start()


    def stop_irrigation(self):
        """Stops all irrigation processes"""
        print("Stopping all irrigation processes ...")
        self.stop_event.set()

        with self.threads_lock:
            for t in self.threads:
                t.join()
            self.threads.clear()


    def remove_thread(self, thread):
        self.threads.remove(thread)