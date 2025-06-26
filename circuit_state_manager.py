import json
from irrigation_circuit import IrrigationCircuit
from typing import Optional, Any
from datetime import datetime

class CircuitStateManager():
    """A class to manage the state of a circuit. Pattern: Singleton."""
    def __init__(self, state_file: str):
        self.state_file = state_file                            # The state file is regulary updated 
        self.state: dict[str, Any] = self.load_state()          # The internal state is loaded, then used to update the file
        # for optimization, quick access to circuits by their ID
        self.circuit_index = {}                                 # ensures O(1) lookup time
    
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
            # logging.error(f"State file {self.state_file} not found. Returning empty state.")
            return {}
        if not self._is_valid_state(state):
            # add logging here
            # logging.error(f"Invalid state structure in {self.state_file}. Returning empty state.")
            return {}
        
        self._rebuild_circuit_index()
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
    
    def update_irrigation_time(self, circuit: IrrigationCircuit) -> None: 
        """Sets the last irrigation time for a given circuit and updates the last_updated timestamp.
        Updates the internal state and saves it to the file."""
        now = datetime.now()
        iso_timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")
        circuit_index = self.circuit_index.get(circuit.id)
        if circuit_index is None:
            # add logging here
            # logging.error(f"Circuit with ID {circuit.id} not found in state.")
            return
        
        self.state["circuits"][circuit_index]["last_irrigation"] = iso_timestamp
        self.state["last_updated"] = iso_timestamp
        self.save_state()
        # Rebuild is not needed here, as we are only updating the last irrigation time and last_updated timestamp.