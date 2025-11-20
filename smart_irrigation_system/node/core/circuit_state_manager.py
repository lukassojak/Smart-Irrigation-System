import json
from typing import Optional, Any, Dict
from datetime import datetime
import threading

from smart_irrigation_system.node.utils.logger import get_logger
from smart_irrigation_system.node.core.irrigation_result import IrrigationResult
from smart_irrigation_system.node.core.enums import IrrigationOutcome, SnapshotCircuitState
import smart_irrigation_system.node.utils.result_factory as result_factory
import smart_irrigation_system.node.utils.time_utils as time_utils

# Dict vs dict mixing

class CircuitStateManager():
    """A class to manage the state of a circuit. Pattern: Singleton."""
    _instance = None
    _lock = threading.Lock()
    
    # =========================================================================
    # Initialization
    # =========================================================================

    def __new__(cls, state_file: str, irrigation_log_file: str) -> "CircuitStateManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CircuitStateManager, cls).__new__(cls)
        return cls._instance


    def __init__(self, state_file: str, irrigation_log_file: str) -> None:
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.logger = get_logger("CircuitStateManager")
        self.state_file: str = state_file                            # The state file is regulary updated 
        self.state: dict[str, Any] = self._load_state()              # The internal state is loaded, then used to update the file
        self.irrigation_log_file: str = irrigation_log_file          # The irrigation log file is append-only, used for historical data. Contains dicts (key is date) of lists of IrrigationResult

        # File locks
        self.state_file_lock = threading.Lock()
        self.irrigation_log_file_lock = threading.Lock()

        # For optimization, quick access to circuits by their ID
        self.circuit_index: dict[int, int] = {}          # Maps circuit ID to index in self.state["circuits"]
        self._rebuild_circuit_index()                    # Build the index from the loaded state
        self._init_circuit_states()                              

        self.logger.info(f"CircuitStateManager initialized.")


    # =========================================================================
    # Internal: Circuit entry management
    # =========================================================================
    
    def _get_entry_by_id(self, circuit_id: int) -> dict | None:
        if circuit_id in self.circuit_index:
            idx = self.circuit_index[circuit_id]
            return self.state["circuits"][idx]
        return None


    def _create_entry(self, circuit_id: int) -> dict:
        entry = {
            "id": circuit_id,
            "circuit_state": SnapshotCircuitState.IDLE.value,
            "last_outcome": None,
            "last_irrigation": None,
            "last_duration": None,
            "last_volume": None,
        }
        self.state["circuits"].append(entry)
        self._rebuild_circuit_index()
        return entry


    def _get_or_create_entry(self, circuit_id: int) -> dict:
        entry = self._get_entry_by_id(circuit_id)
        if entry is None:
            self.logger.warning(f"Circuit with ID {circuit_id} not found in state. Creating a new entry.")
            entry = self._create_entry(circuit_id)
        return entry
    

    # =========================================================================
    # Internal: State loading/saving & validation
    # =========================================================================

    def _save_state(self) -> None:
        """Saves the current state to the state file and updates the last_updated timestamp."""
        if not isinstance(self.state, dict):
            self.logger.error("State is not a dictionary. Empty state will be saved.")
            self.state = {}
        
        self.state.setdefault("circuits", [])
        self.state["last_updated"] = time_utils.now_iso()

        with self.state_file_lock:
            try:
                with open(self.state_file, "w") as f:
                    json.dump(self.state, f, indent=4)
            except Exception as e:
                self.logger.error(f"Failed to save state to {self.state_file}: {e}")


    def _load_state(self) -> dict:
        try:
            with open(self.state_file, "r") as f:
                state = json.load(f)
        except FileNotFoundError:
            self.logger.error(f"State file {self.state_file} not found. Returning new empty state.")
            return {"last_updated": time_utils.now_iso(), "circuits": []}
        except json.JSONDecodeError:
            self.logger.error(f"State file {self.state_file} is corrupted. Returning new empty state.")
            return {"last_updated": time_utils.now_iso(), "circuits": []}
        try:
            self._validate_state(state)
        except Exception as e:
            self.logger.error(f"Invalid state structure in {self.state_file}: {e}. Returning new empty state.")
            return {"last_updated": time_utils.now_iso(), "circuits": []}
        
        return state    
    

    def _validate_state(self, state: dict) -> None:
        """Validates the state structure. See zones_state_explained.md for details."""
        if not isinstance(state, dict):
            raise ValueError("State must be a dictionary")

        # Validate last_updated
        if "last_updated" not in state:
            raise ValueError("State must contain 'last_updated' key")
        try:
            datetime.fromisoformat(state["last_updated"])
        except Exception:
            raise ValueError("Invalid 'last_updated' timestamp format")

        # Validate circuits
        circuits = state.get("circuits")
        if not isinstance(circuits, list) or circuits is None:
            raise ValueError("'circuits' must be a list")

        for circuit in circuits:
            if not isinstance(circuit, dict):
                raise ValueError("Each circuit must be a dictionary")
            
            # Validate id key
            if "id" not in circuit:
                raise ValueError("Each circuit must contain 'id' key")
            if not isinstance(circuit["id"], int):
                raise ValueError("Circuit 'id' must be an integer")
            
            # Validate circuit_state key
            if "circuit_state" not in circuit:
                raise ValueError("Each circuit must contain 'circuit_state' key")
            if circuit["circuit_state"] not in [state.value for state in SnapshotCircuitState]:
                raise ValueError(f"Invalid 'circuit_state' value: {circuit['circuit_state']}")

            # Validate last_irrigation key 
            if "last_irrigation" not in circuit:
                raise ValueError("Each circuit must contain 'last_irrigation' key")
            if "last_irrigation" in circuit and circuit["last_irrigation"] is not None:
                try:
                    datetime.fromisoformat(circuit["last_irrigation"])
                except Exception:
                    raise ValueError("Invalid 'last_irrigation' timestamp format")
            
            # Validate last_outcome, last_duration, last_volume keys
            if "last_outcome" not in circuit:
                raise ValueError("Each circuit must contain 'last_outcome' key")
            if circuit["last_outcome"] is not None and circuit["last_outcome"] not in [outcome.value for outcome in IrrigationOutcome]:
                raise ValueError(f"Invalid 'last_outcome' value: {circuit['last_outcome']}")
            if "last_duration" not in circuit:
                raise ValueError("Each circuit must contain 'last_duration' key.")
            if circuit["last_duration"] is not None and not isinstance(circuit["last_duration"], int):
                raise ValueError("Circuit 'last_duration' must be an integer or None.")
            if "last_volume" not in circuit:
                raise ValueError("Each circuit must contain 'last_volume' key.")
            if circuit["last_volume"] is not None and not isinstance(circuit["last_volume"], (int, float)):
                raise ValueError("Circuit 'last_volume' must be a number or None.")


    # =========================================================================
    # Internal: Circuit index management and state loading/saving & validation
    # =========================================================================

    def _rebuild_circuit_index(self) -> None:
        """Rebuilds the circuit index from the current state.
    
        Must be called after any structural change to `self.state["circuits"]`,
        such as adding, removing or reordering circuits.
        """
        self.circuit_index = {int(c["id"]): i for i, c in enumerate(self.state.get("circuits", []))}  
    

    # =========================================================================
    # Internal: State file management
    # =========================================================================

    def _init_circuit_states(self) -> None:
        """Initializes the state of all circuits to 'idle'. Checks for unclean shutdown."""
        unclean_shutdown_detected = False
        recovered_circuits = []  # List of circuit IDs that were irrigating during unclean shutdown
        for circuit in self.state.get("circuits", []):
            circuit_id = circuit.get("id")
            if circuit.get("circuit_state") != SnapshotCircuitState.SHUTDOWN.value:
                unclean_shutdown_detected = True
                if circuit.get("circuit_state") == SnapshotCircuitState.IRRIGATING.value:
                    # Interrupted irrigation detected
                    circuit["last_outcome"] = IrrigationOutcome.INTERRUPTED.value
                    circuit["last_duration"] = None
                    circuit["last_volume"] = None
                    # Unknown irrigation time due to unclean shutdown, set to current time
                    circuit["last_irrigation"] = time_utils.now_iso()
                    recovered_circuits.append(circuit_id)
                    self._log_missing_interrupted_result(circuit_id)

            circuit["circuit_state"] = SnapshotCircuitState.IDLE.value

        self._save_state()

        if unclean_shutdown_detected:
            self.logger.warning("Unclean shutdown detected.")
            if recovered_circuits:
                self.logger.warning(f"Circuits: [{', '.join(map(str, recovered_circuits))}] were irrigating during shutdown and have been marked as 'interrupted'.")


    def _update_irrigation_result(self, circuit_id: int, result: IrrigationResult) -> None:
        """Updates the last irrigation result and duration for a given circuit.
        Updates the internal state and saves it to the file."""        
        entry = self._get_or_create_entry(circuit_id)

        # Set circuit state back to IDLE after irrigation
        entry["circuit_state"] = SnapshotCircuitState.IDLE.value
    
        entry["last_outcome"] = result.outcome.value

        # SKIPPED - special case, no real irrigation happened
        if result.outcome.value == IrrigationOutcome.SKIPPED.value:
            self._save_state()
            return

        # All the real-run outcomes
        entry["last_irrigation"] = time_utils.to_iso(result.start_time)
        entry["last_duration"] = result.completed_duration
        entry["last_volume"] = result.actual_water_amount
        self._save_state()

    # =========================================================================
    # Internal: Irrigation log management
    # =========================================================================


    def _log_irrigation_result(self, result: IrrigationResult) -> None:
        """Logs the given IrrigationResult into the irrigation log file, grouped by date."""
        with self.irrigation_log_file_lock:
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
        
                irrigation_full_datetime = datetime.fromisoformat(result.to_dict()["start_time"])
                irrigation_date = irrigation_full_datetime.date().isoformat()
                if irrigation_date not in log_data:
                    log_data[irrigation_date] = []
                log_data[irrigation_date].append(result.to_dict())
        
                # Save the updated log back to the file
                with open(self.irrigation_log_file, "w") as f:
                    json.dump(log_data, f, indent=4)
            except Exception as e:
                self.logger.error(f"Failed to log irrigation result to {self.irrigation_log_file}: {e}")


    def _log_missing_interrupted_result(self, circuit_id: int) -> None:
        """Logs an interrupted irrigation result for a circuit that was irrigating during an unclean shutdown."""

        try:
            interrupted_result = result_factory.create_interrupted(
                circuit_id=circuit_id,
                start_time=time_utils.now(),
                elapsed=0,
                actual_water_amount=0,
                target_duration=0,
                target_water_amount=0,
                reason="Unclean shutdown during irrigation. 'start_time', 'completed_duration', 'target_duration', 'actual_water_amount', and 'target_water_amount' are unknown."
            )
            
            self._log_irrigation_result(interrupted_result)
        except Exception as e:
            self.logger.error(f"Failed to log interrupted irrigation result for circuit {circuit_id}: {e}")


    # =========================================================================
    # Public API
    # =========================================================================

    def get_circuit_snapshot(circuit_id) -> "CircuitSnapshot":
        # TODO: Implement CircuitSnapshot data class and return its instance
        pass

    def get_last_irrigation_time(self, circuit_id: int) -> Optional[datetime]:
        """Returns the last irrigation time for a given circuit."""
        entry = self._get_or_create_entry(circuit_id)
        last_irrigation = entry.get("last_irrigation")
        if last_irrigation is not None:
            return time_utils.from_iso(last_irrigation)
        return None


    def get_last_irrigation_duration(self, circuit_id: int) -> Optional[int]:
        """Returns the last irrigation duration for a given circuit."""
        entry = self._get_or_create_entry(circuit_id)
        duration = entry.get("last_duration")
        if duration is not None:
            return int(duration)
        return None
    

    def get_last_irrigation_outcome(self, circuit_id: int) -> Optional[str]:
        """Returns the last irrigation result for a given circuit."""
        entry = self._get_or_create_entry(circuit_id)
        raw = entry.get("last_outcome")
        if raw is None:
            return None
        try:
            return IrrigationOutcome(raw).value # temporary return .value to ensure backward compatibility
        except ValueError:
            self.logger.error(f"Invalid last_outcome value '{raw}' for circuit ID {circuit_id}.")
    

    def irrigation_started(self, circuit_id: int) -> None:
        """Updates the last irrigation time to the current time for a given circuit.
        This is called when the irrigation starts."""
        entry = self._get_or_create_entry(circuit_id)
        entry["circuit_state"] = SnapshotCircuitState.IRRIGATING.value
        self._save_state()
    

    def irrigation_finished(self, circuit_id: int, result: IrrigationResult) -> None:
        """Updates the circuit state based on the given IrrigationResult and records the result."""
        self._update_irrigation_result(circuit_id, result)
        self._log_irrigation_result(result)

    
    def handle_clean_shutdown(self) -> None:
        """Sets all circuits to 'shutdown' state during a clean exit."""
        for circuit in self.state.get("circuits", []):
            circuit["circuit_state"] = SnapshotCircuitState.SHUTDOWN.value
        self._save_state()
        self.logger.debug("All circuits set to 'shutdown' state during clean exit.")