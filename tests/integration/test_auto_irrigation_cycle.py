import json
import os
from datetime import datetime, timedelta
import time

import pytest

from smart_irrigation_system.node.utils import time_utils


def _set_test_log_dir(tmp_path):
    os.environ["SIS_LOG_DIR"] = str(tmp_path / "logs")


def test_auto_irrigation_triggers_for_due_circuits(tmp_path):
    # Backup existing zones state
    state_path = "runtime/node/data/zones_state.json"
    with open(state_path, "r") as f:
        orig_state = json.load(f)

    try:
        # Modify state: set circuit 11 last_irrigation to yesterday (so it is due)
        mod_state = json.loads(json.dumps(orig_state))
        for c in mod_state.get("circuits", []):
            if c.get("id") == 11:
                yesterday = (datetime.now() - timedelta(days=1)).isoformat()
                c["last_irrigation"] = yesterday
                c["last_decision"] = None
            if c.get("id") == 12:
                # keep circuit 12 recent so it should be skipped
                c["last_irrigation"] = datetime.now().isoformat()

        with open(state_path, "w") as f:
            json.dump(mod_state, f, indent=4)

        # Redirect logs to temp path and ensure writable
        _set_test_log_dir(tmp_path)
        os.makedirs(os.environ["SIS_LOG_DIR"], exist_ok=True)
        log_file = os.path.join(os.environ["SIS_LOG_DIR"], "system_log.log")
        open(log_file, "a").close()

        # Monkeypatch IrrigationCircuit.irrigate_auto to a fast no-op success to keep test fast
        from smart_irrigation_system.node.core.irrigation_circuit import IrrigationCircuit
        import smart_irrigation_system.node.utils.result_factory as result_factory
        from smart_irrigation_system.node.core.enums import IrrigationOutcome

        def _fake_irrigate_auto(self, global_config, global_conditions, stop_event, precomputed_target_volume=None):
            return result_factory.create_general(
                circuit_id=self.zone_config.id,
                start_time=time_utils.now(),
                completed_duration=1,
                target_duration=1,
                actual_water_amount=0.1,
                target_water_amount=0.1,
                success=True,
                outcome=IrrigationOutcome.SUCCESS,
                error=None
            )

        IrrigationCircuit.irrigate_auto = _fake_irrigate_auto

        # Import ControllerCore after setting SIS_LOG_DIR so logger uses test dir
        from smart_irrigation_system.node.core.controller.controller_core import ControllerCore
        from smart_irrigation_system.node.core.controller.thread_manager import TaskType

        # Instantiate controller and run auto cycle
        controller = ControllerCore()

        controller.start_auto_cycle()

        # Wait for executor to finish
        try:
            controller.thread_manager.join_all_workers(task_type=TaskType.EXECUTOR, timeout=30)
        except Exception as e:
            pytest.fail(f"Executor did not finish in time: {e}")

        # Allow a short delay for state save
        time.sleep(0.5)

        # Verify circuit 11 was irrigated (last_irrigation updated)
        snap = controller.state_manager.get_circuit_snapshot(11)
        assert snap.last_irrigation is not None, "Circuit 11 was not irrigated as expected"
        assert snap.last_irrigation.date() == time_utils.now().date()

    finally:
        # Restore original state
        with open(state_path, "w") as f:
            json.dump(orig_state, f, indent=4)
