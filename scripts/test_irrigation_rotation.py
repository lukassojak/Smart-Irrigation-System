"""Simple test harness for irrigation log rotation/migration.
Run with: PYTHONPATH=. python3 scripts/test_irrigation_rotation.py
"""
import json
import os
import tempfile
from datetime import datetime, timedelta, date

from smart_irrigation_system.node.core.circuit_state_manager import CircuitStateManager
from smart_irrigation_system.node.core.irrigation_result import IrrigationResult
from smart_irrigation_system.node.core.enums import IrrigationOutcome


def write_legacy_file(path, mapping):
    with open(path, "w") as f:
        json.dump(mapping, f, indent=4)


def list_logs(dirpath):
    return sorted([p for p in os.listdir(dirpath) if p.startswith("irrigation_log")])


def main():
    tmp = tempfile.mkdtemp(prefix="irrigation_test_")
    state_file = os.path.join(tmp, "state.json")
    irrigation_log = os.path.join(tmp, "irrigation_log.json")

    # initial state file
    with open(state_file, "w") as f:
        json.dump({"last_updated": datetime.now().isoformat(), "circuits": []}, f)

    # prepare legacy mapping with multiple dates including an old date
    today = date.today()
    legacy = {}
    for d in [today - timedelta(days=40), today - timedelta(days=5), today]:
        ds = d.isoformat()
        legacy[ds] = [
            {
                "circuit_id": 1,
                "success": True,
                "outcome": "completed",
                "start_time": datetime(d.year, d.month, d.day, 6, 0).isoformat(),
                "completed_duration": 10,
                "target_duration": 10,
                "actual_water_amount": 1.2,
                "target_water_amount": 1.2,
                "error": None,
            }
        ]

    write_legacy_file(irrigation_log, legacy)

    print("Before change — files:", list_logs(tmp))

    # Ensure node logs directory exists and is writable (logger uses project runtime/node/logs)
    project_logs = os.path.join(os.path.dirname(os.path.dirname(__file__)), "runtime/node/logs")
    os.makedirs(project_logs, exist_ok=True)
    try:
        os.chmod(project_logs, 0o777)
    except Exception:
        pass

    manager = CircuitStateManager(state_file, irrigation_log)

    # Create a new result for today and log it via public method
    result = IrrigationResult(
        circuit_id=2,
        success=True,
        outcome=IrrigationOutcome.SUCCESS,
        start_time=datetime.now(),
        completed_duration=5,
        target_duration=5,
        actual_water_amount=0.8,
        target_water_amount=0.8,
        error=None,
    )

    manager.irrigation_finished(2, result)

    print("After logging once — files:", list_logs(tmp))

    # Create many old dated files to test rotation
    for i in range(1, 42):
        d = today - timedelta(days=i)
        fname = os.path.join(tmp, f"irrigation_log-{d.isoformat()}.json")
        with open(fname, "w") as f:
            json.dump([], f)

    # Trigger logging again to run rotation
    manager.irrigation_finished(3, result)

    final_files = list_logs(tmp)
    print("After rotation — files (count):", len(final_files))
    print(final_files)

    # Cleanup
    # shutil.rmtree(tmp)  # leave files for inspection


if __name__ == "__main__":
    main()
