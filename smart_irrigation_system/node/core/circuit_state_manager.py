# smart_irrigation_system/node/core/circuit_state_manager.py

import json
import threading
from typing import Any, Optional, TYPE_CHECKING
from datetime import datetime, date, timedelta
from pathlib import Path

from smart_irrigation_system.node.core.irrigation_result import IrrigationResult
from smart_irrigation_system.node.core.enums import IrrigationOutcome, SnapshotCircuitState
from smart_irrigation_system.node.core.status_models import CircuitSnapshot

import smart_irrigation_system.node.utils.result_factory as result_factory
import smart_irrigation_system.node.utils.time_utils as time_utils
from smart_irrigation_system.node.utils.logger import get_logger

if TYPE_CHECKING:
    from smart_irrigation_system.node.core.history_sync import HistorySyncManager


class CircuitStateManager():
    """A class to manage the state of a circuit. Pattern: Singleton."""
    _instance = None
    _lock = threading.Lock()
    
    # =========================================================================
    # Initialization
    # =========================================================================

    def __new__(cls, state_file: str, irrigation_log_file: str, history_sync: Optional["HistorySyncManager"] = None) -> "CircuitStateManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CircuitStateManager, cls).__new__(cls)
        return cls._instance


    def __init__(self, state_file: str, irrigation_log_file: str, history_sync: Optional["HistorySyncManager"] = None) -> None:
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.logger = get_logger("CircuitStateManager")

        # File locks
        self.state_file_lock = threading.Lock()
        self.irrigation_log_file_lock = threading.Lock()

        self.state_file: str = state_file
        self.state: dict[str, Any] = self._load_state()     # The internal state is loaded, then used to update the file
        self.irrigation_log_file: str = irrigation_log_file # The irrigation log file is append-only, used for historical data.
        self.history_sync: Optional["HistorySyncManager"] = history_sync  # Optional sync manager for server uploads

        # For optimization, quick access to circuits by their ID
        self.circuit_index: dict[int, int] = {}             # Maps circuit ID to index in self.state["circuits"]
        self._rebuild_circuit_index()                       # Build the index from the loaded state
        self._init_circuit_states()                              

        self._initialized = True
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
            "last_decision": None,
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
        with self.state_file_lock:
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

            # Validate last_decision key
            if "last_decision" not in circuit:
                raise ValueError("Each circuit must contain 'last_decision' key")
            if "last_decision" in circuit and circuit["last_decision"] is not None:
                try:
                    datetime.fromisoformat(circuit["last_decision"])
                except Exception:
                    raise ValueError("Invalid 'last_decision' timestamp format")

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
        # Remove circuit entries that are no longer present in the current configured zones.
        # This prevents stale state from being applied to newly created zones that reuse old IDs.
        try:
            config_path = Path(self.state_file).parent.parent / "config" / "zones_config.json"
            if config_path.exists():
                try:
                    with open(config_path, "r") as cf:
                        cfg = json.load(cf)
                    configured_ids = {int(z.get("id")) for z in cfg.get("zones", []) if isinstance(z.get("id"), int)}
                    orig_len = len(self.state.get("circuits", []))
                    pruned = [c for c in self.state.get("circuits", []) if int(c.get("id")) in configured_ids]
                    if len(pruned) != orig_len:
                        self.state["circuits"] = pruned
                        self._rebuild_circuit_index()
                        self.logger.info(f"Pruned {orig_len - len(pruned)} stale circuit state entries not present in {config_path}")
                except Exception as e:
                    self.logger.debug(f"Failed to read/parse config for pruning: {e}")
        except Exception:
            # non-fatal; proceed with initialization
            pass

        unclean_shutdown_detected = False
        recovered_circuits = []  # List of circuit IDs that were irrigating during unclean shutdown
        for circuit in self.state.get("circuits", []):
            circuit_id = circuit.get("id")
            # The circuit is considered uncleanly shutdown if its state is not 'shutdown'
            if circuit.get("circuit_state") != SnapshotCircuitState.SHUTDOWN.value:
                unclean_shutdown_detected = True
                if circuit.get("circuit_state") == SnapshotCircuitState.IRRIGATING.value:
                    # Interrupted irrigation detected
                    circuit["last_outcome"] = IrrigationOutcome.INTERRUPTED.value
                    circuit["last_duration"] = None
                    circuit["last_volume"] = None
                    # Unknown irrigation time due to unclean shutdown, set to current time
                    circuit["last_irrigation"] = time_utils.now_iso()
                    circuit["last_decision"] = time_utils.now_iso()
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
        self.logger.debug(f"Updating irrigation result for circuit ID {circuit_id} with outcome {result.outcome.value}.")        
        entry = self._get_or_create_entry(circuit_id)

        # Set circuit state back to IDLE, update last outcome and last decision
        entry["circuit_state"] = SnapshotCircuitState.IDLE.value
        entry["last_outcome"] = result.outcome.value
        entry["last_decision"] = time_utils.to_iso(result.start_time)

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
                irrigation_full_datetime = datetime.fromisoformat(result.to_dict()["start_time"])
                irrigation_date = irrigation_full_datetime.date().isoformat()

                log_path = Path(self.irrigation_log_file)
                log_dir = log_path.parent
                log_dir.mkdir(parents=True, exist_ok=True)

                base_name = log_path.stem  # expected 'irrigation_log'

                def dated_filename(d: str) -> Path:
                    return log_dir / f"{base_name}-{d}.json"

                # Helper: rotate old files keeping last 30 days (including today)
                def _rotate_logs(keep_days: int = 30) -> None:
                    files = list(log_dir.glob(f"{base_name}*.json"))
                    date_map: dict[date, Path] = {}
                    for p in files:
                        name = p.stem  # e.g. irrigation_log or irrigation_log-YYYY-MM-DD
                        if name == base_name:
                            # today's file -- treat as today's date
                            try:
                                date_map[date.today()] = p
                            except Exception:
                                continue
                        elif name.startswith(base_name + "-"):
                            suffix = name[len(base_name) + 1 :]
                            try:
                                d = date.fromisoformat(suffix)
                                date_map[d] = p
                            except Exception:
                                continue

                    # Keep only last `keep_days` dates
                    keep_cutoff = date.today() - timedelta(days=keep_days - 1)
                    for d, p in list(date_map.items()):
                        if d < keep_cutoff:
                            try:
                                p.unlink()
                            except Exception:
                                self.logger.debug(f"Failed to remove old irrigation log {p}")

                # Helper: migrate legacy single-file mapping format
                def _migrate_legacy(content: dict) -> None:
                    # Expecting mapping date->list; write each date to its own file
                    for k, v in content.items():
                        if not isinstance(k, str) or not isinstance(v, list):
                            continue
                        try:
                            _ = date.fromisoformat(k)
                        except Exception:
                            continue
                        target = dated_filename(k)
                        try:
                            with open(target, "w") as tf:
                                json.dump(v, tf, indent=4)
                        except Exception:
                            self.logger.debug(f"Failed to migrate irrigation log for date {k} to {target}")

                # Read existing file if present
                today_list: list = []
                if log_path.exists():
                    try:
                        with open(log_path, "r") as f:
                            existing = json.load(f)
                    except json.JSONDecodeError:
                        existing = None

                    # If legacy mapping format detected (dict of date -> list), migrate
                    if isinstance(existing, dict):
                        # Heuristic: keys look like dates
                        date_keys = [k for k in existing.keys() if isinstance(k, str) and len(k) >= 8]
                        if date_keys and any(_ for _ in date_keys):
                            _migrate_legacy(existing)
                            # If today's date present in mapping, use that as today's list
                            today_list = existing.get(irrigation_date, [])
                        else:
                            # Unexpected dict shape, ignore and start fresh
                            today_list = []
                    elif isinstance(existing, list):
                        # New per-day format: today's file contains just a list
                        today_list = existing
                    else:
                        today_list = []
                else:
                    today_list = []

                # Append new entry to today's list
                today_list.append(result.to_dict())

                # Write today's file as the canonical `irrigation_log.json`
                try:
                    with open(log_path, "w") as f:
                        json.dump(today_list, f, indent=4)
                except Exception as e:
                    self.logger.error(f"Failed to write today's irrigation log to {self.irrigation_log_file}: {e}")

                # Also ensure there is a dated file for today (mirror)
                try:
                    with open(dated_filename(irrigation_date), "w") as df:
                        json.dump(today_list, df, indent=4)
                except Exception:
                    self.logger.debug(f"Failed to write dated irrigation log for {irrigation_date}")

                # Rotate older files
                _rotate_logs(keep_days=30)

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

    def get_circuit_snapshot(self, circuit_id: int) -> CircuitSnapshot:
        """
        Returns the persistent snapshot (last known metadata) of a circuit
        as a `CircuitSnapshot` dataclass.
        """
        entry = self._get_or_create_entry(circuit_id)
        
        circuit_state = SnapshotCircuitState(entry.get("circuit_state"))
        last_decision_raw = entry.get("last_decision")
        last_outcome_raw = entry.get("last_outcome")
        last_irrigation_raw = entry.get("last_irrigation")
        last_duration_raw = entry.get("last_duration")
        last_volume_raw = entry.get("last_volume")
        last_updated_raw = self.state.get("last_updated")

        # Enum mapping
        last_outcome = None
        if isinstance(last_outcome_raw, str):
            try:
                last_outcome = IrrigationOutcome(last_outcome_raw)
            except ValueError:
                self.logger.error(f"Invalid last_outcome value '{last_outcome_raw}' for circuit ID {circuit_id}.")
                last_outcome = None
        
        # Timestamp mapping
        last_irrigation = time_utils.from_iso(last_irrigation_raw) if last_irrigation_raw is not None else None
        last_decision = time_utils.from_iso(last_decision_raw) if last_decision_raw is not None else None
        timestamp = time_utils.from_iso(last_updated_raw) if last_updated_raw is not None else None

        return CircuitSnapshot(
            id=circuit_id,
            circuit_state=circuit_state,
            last_decision=last_decision,
            last_outcome=last_outcome,
            last_irrigation=last_irrigation,
            last_duration=int(last_duration_raw) if last_duration_raw is not None else None,
            last_volume=float(last_volume_raw) if last_volume_raw is not None else None,
            timestamp=timestamp
        )
    

    def irrigation_started(self, circuit_id: int) -> None:
        """Updates the last irrigation time to the current time for a given circuit.
        This is called when the irrigation starts."""
        entry = self._get_or_create_entry(circuit_id)
        self.logger.debug(f"Setting circuit ID {circuit_id} state to 'irrigating'.")
        entry["circuit_state"] = SnapshotCircuitState.IRRIGATING.value
        self._save_state()
    

    def irrigation_finished(self, circuit_id: int, result: IrrigationResult) -> None:
        """Updates the circuit state based on the given IrrigationResult and records the result."""
        self._update_irrigation_result(circuit_id, result)
        self._log_irrigation_result(result)
        
        # Sync record to server if sync manager is available
        if self.history_sync:
            try:
                record = result.to_dict()
                self.history_sync.add_record_to_queue(record)
                # Try to sync immediately (non-blocking)
                self.history_sync.sync_to_server(blocking=False)
            except Exception as e:
                self.logger.error(f"Failed to queue irrigation result for sync: {e}")
        # if circuit_id == 2:
            # raise RuntimeError("TEST CRASH - SIMULATED THREAD FAILURE (should be caught and logged)")

    
    def handle_clean_shutdown(self) -> None:
        """Sets all circuits to 'shutdown' state during a clean exit."""
        for circuit in self.state.get("circuits", []):
            circuit["circuit_state"] = SnapshotCircuitState.SHUTDOWN.value
        self._save_state()
        self.logger.debug("All circuits set to 'shutdown' state during clean exit.")