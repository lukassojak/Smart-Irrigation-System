import json
from smart_irrigation_system.irrigation_circuit import IrrigationCircuit
from typing import Optional, Any
from datetime import datetime


# 1. Possible problem with key being a string
# 2. Add last_decision_time to track the last decision and reason of watering / not watering
# In case the decision is to water manually by user (selected volume), the volume should not be
# used in case of offline mode - in this case, it should use the last automatically calculated volume instead


class CircuitStateManager():
    """A class to manage the state of a circuit. Pattern: Singleton."""
    def __init__(self, state_file: str):
        self.state_file = state_file                            # The state file is regulary updated 
        self.state: dict[str, Any] = self.load_state()          # The internal state is loaded, then used to update the file
        self._rebuild_circuit_index()
        # for optimization, quick access to circuits by their ID
        self.circuit_index = {}                                 # ensures O(1) lookup time, key is circuit ID, value is index in the circuits list
    
    def _rebuild_circuit_index(self):
        """Rebuilds the circuit index from the current state.
    
        ! Must be called manually after any structural change to `self.state["circuits"]`,
        such as adding, removing or reordering circuits.
        """
        self.circuit_index = {int(c["id"]): i for i, c in enumerate(self.state.get("circuits", []))}

    def load_state(self) -> dict:
        try:
            with open(self.state_file, "r") as f:
                state = json.load(f)
        except FileNotFoundError:
            # add logging here
            # logging.error(f"State file {self.state_file} not found. Returning new empty state.")
            return {"last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "circuits": []}
        if not self._is_valid_state(state):
            # single invalid circuit entry cause the whole state to be invalid, so we return a new empty state
            # add logging here
            # logging.error(f"Invalid state structure in {self.state_file}. Returning new empty state.")
            return {"last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "circuits": []}
        
        return state
    
    def save_state(self) -> None:
        """Saves the current state to the state file and updates the last_updated timestamp."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            # add logging here
            # logging.error(f"Error saving state to {self.state_file}: {e}")
            pass
    
    def _is_valid_state(self, state: dict) -> bool:
        """Validates the state structure. See zones_state_explained.md for details."""
        if not isinstance(state, dict):
            return False

        # Check last_updated
        if "last_updated" not in state:
            return False
        # None is not allowed for last_updated for now, if needed, wrap the try-except in a condition
        try:
            datetime.fromisoformat(state["last_updated"])
        except Exception:
            return False

        # Check circuits
        circuits = state.get("circuits")
        if not isinstance(circuits, list) or circuits is None:
            return False

        for circuit in circuits:
            if not isinstance(circuit, dict):
                return False
            if "id" not in circuit:
                return False
            if "last_irrigation" in circuit and circuit["last_irrigation"] is not None:
                try:
                    datetime.fromisoformat(circuit["last_irrigation"])
                except Exception:
                    return False
            if "last_result" not in circuit:
                return False
            if circuit["last_result"] not in ["success", "failure", "skipped", "error", None]:
                return False
            if "last_duration" not in circuit:
                return False

        return True
    

    def get_last_irrigation_time(self, circuit: IrrigationCircuit) -> Optional[datetime]:
        """Returns the last irrigation time for a given circuit."""
        circuit_index = self.circuit_index.get(circuit.id)
        if circuit_index is None:
            # add logging here
            return None
        result = self.state.get("circuits", {})[circuit_index].get("last_irrigation")
        if result:
            return datetime.fromisoformat(result)
        return None


    def update_irrigation_result(self, circuit: IrrigationCircuit, result: str, duration: int) -> None:
        """Updates the last irrigation result and duration for a given circuit.
        Updates the internal state and saves it to the file."""
        if result not in ["success", "failure", "skipped", "error"]:
            # add logging here
            # logging.error(f"Invalid irrigation result: {result}")
            return
        
        circuit_index = self.circuit_index.get(circuit.id)
        if circuit_index is None:
            # add logging here
            # logging.error(f"Circuit with ID {circuit.id} not found in state.")
            # create a new circuit entry if it does not exist
            self.create_circuit_entry(circuit)
        
        if result == "skipped":
            # If the result is "skipped", we do not update last_irrigation or last_duration
            # Because we need to keep the last irrigation time and duration intact to calculate the next irrigation time correctly.
            self.state["circuits"][circuit_index]["last_result"] = result
            self.state["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            self.save_state()
            return
        
        # If the result is "failure" or "error", we update the last_irrigation time and last_duration (to None)
        # This leads to loss of the last irrigation time and duration, which is acceptable in this case.
    
        # .get() would be safer here, but we assume the structure is valid since we validated it in load_state()
        self.state["circuits"][circuit_index]["last_result"] = result
        self.state["circuits"][circuit_index]["last_duration"] = duration                       # if "failure" or "error", duration is 0
        self.state["circuits"][circuit_index]["last_irrigation"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.state["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.save_state()
        # Rebuild is not needed here, as we are only updating the last irrigation time and last_updated timestamp.


    def create_circuit_entry(self, circuit: IrrigationCircuit) -> None:
        """Creates a new circuit entry in the state if it does not exist."""
        if circuit.id in self.circuit_index:
            # add logging here
            # logging.warning(f"Circuit with ID {circuit.id} already exists in state.")
            return
        
        new_entry = {
            "id": str(circuit.id),
            "last_irrigation": None,
            "last_result": None,
            "last_duration": 0
        }
        self.state["circuits"].append(new_entry)
        self._rebuild_circuit_index()