import json
from typing import Optional, Any
from datetime import datetime

from smart_irrigation_system.logger import get_logger
from smart_irrigation_system.irrigation_result import IrrigationResult
from smart_irrigation_system.enums import IrrigationOutcome



# 1. Possible problem with key being a string
# 2. Add last_decision_time to track the last decision and reason of watering / not watering
# In case the decision is to water manually by user (selected volume), the volume should not be
# used in case of offline mode - in this case, it should use the last automatically calculated volume instead


class CircuitStateManager():
    """A class to manage the state of a circuit. Pattern: Singleton."""
    # 2025-08-30 22:52:46,025 | smart_irrigation_system.main | ERROR | Failed to initialize IrrigationController: CircuitStateManager.__init__() missing 1 required positional argument: 'irrigation_log_file'
    def __init__(self, state_file: str, irrigation_log_file: str) -> None:
        self.logger = get_logger("CircuitStateManager")
        self.state_file = state_file                            # The state file is regulary updated 
        self.state: dict[str, Any] = self.load_state()          # The internal state is loaded, then used to update the file

        self.irrigation_log_file = irrigation_log_file          # The irrigation log file is append-only, used for historical data. Contains dicts (key is date) of lists of IrrigationResult

        # for optimization, quick access to circuits by their ID
        self.circuit_index = {}                                 # ensures O(1) lookup time, key is circuit ID, value is index in the circuits list
        self._rebuild_circuit_index()
        self.init_circuit_states()                              

        self.logger.info(f"CircuitStateManager initialized.")
    

    def log_irrigation_result(self, result: IrrigationResult) -> None:
        """Logs the given IrrigationResult into the irrigation log file, grouped by date."""
        try:
            # Load the existing log file or initialize an empty dictionary
            try:
                with open(self.irrigation_log_file, "r") as f:
                    try:
                        log_data = json.load(f)
                    except json.JSONDecodeError:
                        log_data = {}
            except FileNotFoundError:
                log_data = {}
    
            # Extract the date from the result's start_time
            irrigation_date = datetime.fromisoformat(result.to_dict()["start_time"]).date().isoformat()
    
            # Ensure the date key exists in the log
            if irrigation_date not in log_data:
                log_data[irrigation_date] = []
    
            # Append the new result to the list for the date
            log_data[irrigation_date].append(result.to_dict())
    
            # Save the updated log back to the file
            with open(self.irrigation_log_file, "w") as f:
                json.dump(log_data, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to log irrigation result to {self.irrigation_log_file}: {e}")

    
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
            self.logger.error(f"State file {self.state_file} not found. Returning new empty state.")
            return {"last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "circuits": []}
        except json.JSONDecodeError:
            self.logger.error(f"State file {self.state_file} is corrupted. Returning new empty state.")
            return {"last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "circuits": []}
        try:
            self._valid_state(state)
        except Exception as e:
            # single invalid circuit entry cause the whole state to be invalid, so we return a new empty state
            self.logger.error(f"Invalid state structure in {self.state_file}: {e}. Returning new empty state.")
            return {"last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "circuits": []}
        
        return state
    
    def save_state(self) -> None:
        """Saves the current state to the state file and updates the last_updated timestamp."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save state to {self.state_file}: {e}")

    
    def _valid_state(self, state: dict) -> None:
        """Validates the state structure. See zones_state_explained.md for details."""
        if not isinstance(state, dict):
            raise ValueError("State must be a dictionary")

        # Check last_updated
        if "last_updated" not in state:
            raise ValueError("State must contain 'last_updated' key")
        # None is not allowed for last_updated for now, if needed, wrap the try-except in a condition
        try:
            datetime.fromisoformat(state["last_updated"])
        except Exception:
            raise ValueError("Invalid 'last_updated' timestamp format")

        # Check circuits
        circuits = state.get("circuits")
        if not isinstance(circuits, list) or circuits is None:
            raise ValueError("'circuits' must be a list")

        for circuit in circuits:
            if not isinstance(circuit, dict):
                raise ValueError("Each circuit must be a dictionary")
            if "id" not in circuit:
                raise ValueError("Each circuit must contain 'id' key")
            if "irrigation_state" not in circuit:
                raise ValueError("Each circuit must contain 'irrigation_state' key")
            if "last_irrigation" in circuit and circuit["last_irrigation"] is not None:
                try:
                    datetime.fromisoformat(circuit["last_irrigation"])
                except Exception:
                    raise ValueError("Invalid 'last_irrigation' timestamp format")
            if "last_result" not in circuit:
                raise ValueError("Each circuit must contain 'last_result' key")
            if circuit["last_result"] not in ["success", "failed", "skipped", "interrupted", "error", None]:
                raise ValueError(f"Invalid 'last_result' value: {circuit['last_result']}")
            if "last_duration" not in circuit:
                raise ValueError("Each circuit must contain 'last_duration' key.")

        return True
    

    def get_last_irrigation_time(self, circuit: "IrrigationCircuit") -> Optional[datetime]:
        """Returns the last irrigation time for a given circuit."""
        circuit_index = self.circuit_index.get(circuit.id)
        if circuit_index is None:
            self.logger.warning(f"Circuit with ID {circuit.id} not found in state.")
            return None
        result = self.state.get("circuits", {})[circuit_index].get("last_irrigation")
        if result:
            return datetime.fromisoformat(result)
        return None

    def get_last_irrigation_duration(self, circuit: "IrrigationCircuit") -> Optional[int]:
        """Returns the last irrigation duration for a given circuit."""
        circuit_index = self.circuit_index.get(circuit.id)
        if circuit_index is None:
            self.logger.warning(f"Circuit with ID {circuit.id} not found in state.")
            return None
        result = self.state.get("circuits", {})[circuit_index].get("last_duration")
        if result is not None:
            return int(result)
        return None
    
    def get_last_irrigation_result(self, circuit: "IrrigationCircuit") -> Optional[str]:
        """Returns the last irrigation result for a given circuit."""
        circuit_index = self.circuit_index.get(circuit.id)
        if circuit_index is None:
            self.logger.warning(f"Circuit with ID {circuit.id} not found in state.")
            return None
        result = self.state.get("circuits", {})[circuit_index].get("last_result")
        if result is not None:
            return str(result)
        return None
    
    def irrigation_started(self, circuit: "IrrigationCircuit") -> None:
        """Updates the last irrigation time to the current time for a given circuit.
        This is called when the irrigation starts."""
        circuit_index = self.circuit_index.get(circuit.id)
        if circuit_index is None:
            self.logger.warning(f"Circuit with ID {circuit.id} not found in state. Creating a new entry.")
            self.create_circuit_entry(circuit)
            circuit_index = self.circuit_index.get(circuit.id)
        
        self.state["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.state["circuits"][circuit_index]["irrigation_state"] = "irrigating"  # Set irrigation state to running
        self.save_state()
    
    def irrigation_finished(self, circuit: "IrrigationCircuit", result: IrrigationResult) -> None:
        """Updates the circuit state based on the given IrrigationResult and records the result."""
        self.update_irrigation_result(circuit, result.outcome.value, result.completed_duration)
        self.log_irrigation_result(result)

    def update_irrigation_result(self, circuit: "IrrigationCircuit", result: str, duration: int) -> None:
        """Updates the last irrigation result and duration for a given circuit.
        Updates the internal state and saves it to the file."""
        
        circuit_index = self.circuit_index.get(circuit.id)
        if circuit_index is None:
            self.logger.warning(f"Circuit with ID {circuit.id} not found in state. Creating a new entry.")
            # create a new circuit entry if it does not exist
            self.create_circuit_entry(circuit)
            circuit_index = self.circuit_index.get(circuit.id)
        
        self.state["circuits"][circuit_index]["irrigation_state"] = "idle"  # Set irrigation state to idle after irrigation is done
        

    
        # .get() would be safer here, but we assume the structure is valid since we validated it in load_state()
        self.state["circuits"][circuit_index]["last_result"] = result
        self.state["circuits"][circuit_index]["last_duration"] = duration                       # if "failed" or "error", duration is 0
        if result == IrrigationOutcome.SUCCESS.value:
            self.state["circuits"][circuit_index]["last_irrigation"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.state["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.save_state()
        # Rebuild is not needed here, as we are only updating the last irrigation time and last_updated timestamp.


    def create_circuit_entry(self, circuit: "IrrigationCircuit") -> None:
        """Creates a new circuit entry in the state if it does not exist."""
        if circuit.id in self.circuit_index:
            self.logger.warning(f"Circuit with ID {circuit.id} already exists in state. Skipping creation.")
            return
        
        new_entry = {
            "id": str(circuit.id),
            "irrigation_state": "idle",
            "last_irrigation": None,
            "last_result": None,
            "last_duration": 0
        }
        self.state["circuits"].append(new_entry)
        self._rebuild_circuit_index()

    
    def init_circuit_states(self) -> None:
        """Initializes the state of all circuits to 'idle'. Checks for unclean shutdown."""
        for circuit in self.state.get("circuits", []):
            if circuit.get("irrigation_state") != "shutdown":
                self.logger.warning(f"Unclean shutdown detected on circuit {circuit.get('id')}.")
            circuit["irrigation_state"] = "idle"
        self.save_state()

    
    def handle_clean_shutdown(self) -> None:
        """Sets all circuits to 'shutdown' state during a clean exit."""
        for circuit in self.state.get("circuits", []):
            circuit["irrigation_state"] = "shutdown"
        self.save_state()
        self.logger.debug("All circuits set to 'shutdown' state during clean exit.")