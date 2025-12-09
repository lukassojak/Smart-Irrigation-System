# smart_irrigation_system/node/core/controller/legacy_controller_api.py

from smart_irrigation_system.node.core.status_models import CircuitStatus
from smart_irrigation_system.node.core.enums import ControllerState


class LegacyControllerAPI:
    """
    A legacy controller API for backward compatibility with older modules.
    """

    # ==================================================================================================================
    # Deprecated public methods from IrrigationController
    # ==================================================================================================================

    # ----------------- MQTT -----------------------

    def get_status_message(self) -> str:
        """Returns a brief status message of the irrigation controller for mqtt publishing."""

        # self.logger.warning("get_status_message is deprecated and may be removed in future versions.")
        status = self.get_status()
        status_msg = f"Controller State: {status['controller_state']}, Auto Enabled: {not status['auto_stopped']}, Auto Paused: {status['auto_paused']}, Currently Irrigating Zones: {self.get_currently_irrigating_zones()}"
        return status_msg


    def get_currently_irrigating_zones(self) -> list[int]:
        """Returns a list of IDs of currently irrigating zones."""

        # self.logger.warning("get_currently_irrigating_zones is deprecated and may be removed in future versions.")
        irrigating_zones = []
        for circuit in self.circuits.values():
            if circuit.is_currently_irrigating:
                irrigating_zones.append(circuit.id)
        return irrigating_zones
    

    # ----------------- CLI -----------------------

    def get_circuit_snapshot(self, circuit_id: int) -> CircuitStatus:
        """Returns the persistent snapshot state of a given circuit."""

        # self.logger.warning("get_circuit_snapshot is deprecated and may be removed in future versions.")
        if circuit_id not in self.circuits.keys():
            raise ValueError(f"Circuit ID {circuit_id} does not exist.")
        
        snapshot = self.state_manager.get_circuit_snapshot(circuit_id)
        return snapshot


    def get_status(self) -> dict:
        """Returns comprehensive snapshot of the irrigation controller's status."""

        # self.logger.warning("get_status is deprecated and may be removed in future versions.")
        # Fetch global conditions
        cached_conditions_str = self.conditions_provider.get_conditions_str()

        # Prepare zones status
        zones_status = []
        for circuit in self.circuits.values():
            zones_status.append({
                'id': circuit.id,
                'name': circuit.name,
                'state': circuit.state.name,
                'pin': circuit.valve.pin,
            })

        scheduled_time = f"{self.global_config.automation.scheduled_hour:02}:{self.global_config.automation.scheduled_minute:02}"
        status = {
            'auto_enabled': self.global_config.automation.enabled,
            'auto_paused': False,                               # Placeholder for not supported functionality
            'auto_stopped': not self.ais.is_runtime_enabled,
            'scheduled_time': scheduled_time,
            'sequential': self.global_config.automation.sequential,
            'controller_state': self._controller_state.name,
            'cache_update': self.conditions_provider.last_cache_update,
            'cached_global_conditions': cached_conditions_str.split(", Timestamp:")[0],
            'zones': zones_status,
            'current_consumption': self.get_current_consumption(),
            'input_flow_capacity': self.global_config.irrigation_limits.main_valve_max_flow,
        }

        return status
    
    def get_circuit_progress(self, circuit_number: int) -> tuple[float, float]:
        """Returns the current progress and target water amount for a given circuit."""
        from smart_irrigation_system.node.core.enums import IrrigationState
        from smart_irrigation_system.node.core.status_models import CircuitRuntimeStatus

        # self.logger.warning("get_circuit_progress is deprecated and may be removed in future versions.")
        if circuit_number not in self.circuits:
            raise ValueError(f"Circuit number {circuit_number} does not exist.")
        
        circuit = self.circuits[circuit_number]
        if circuit.state != IrrigationState.IRRIGATING:
            return 0.0, 0.0
        try:
            runtime_status: CircuitRuntimeStatus = circuit.runtime_status
            target_water_amount = runtime_status.target_volume if runtime_status.target_volume is not None else 0.0
            current_water_amount = runtime_status.current_volume if runtime_status.current_volume is not None else 0.0
        except Exception as e:
            self.logger.error(f"Error getting runtime status for circuit {circuit_number}: {e}")
            return 0.0, 0.0
        return target_water_amount, current_water_amount
        
    
    def get_daily_irrigation_time(self):
        """Returns the daily irrigation time based on the global configuration"""

        import time

        # self.logger.warning("get_daily_irrigation_time is deprecated and may be removed in future versions.")
        return time.struct_time((0, 0, 0, self.global_config.automation.scheduled_hour, self.global_config.automation.scheduled_minute, 0, 0, 0, -1))
    
    def get_circuit(self, circuit_number):
        """Returns the circuit object for a given circuit number"""

        # self.logger.warning("get_circuit is deprecated and may be removed in future versions.")
        if circuit_number in self.circuits.keys():
            return self.circuits[circuit_number]
        else:
            raise ValueError(f"Circuit number {circuit_number} does not exist.")
    
    def get_state(self) -> ControllerState:
        """Returns the current state of the irrigation controller"""

        # self.logger.warning("get_state is deprecated and may be removed in future versions.")
        return self._controller_state
        
    def get_current_consumption(self) -> float:
        """Returns the total consumption of all irrigating circuits in liters per hour"""

        # self.logger.warning("get_current_consumption is deprecated and may be removed in future versions.")
        total_consumption = 0.0
        for circuit in self.circuits.values():
            if circuit.is_currently_irrigating:
                total_consumption += circuit.circuit_consumption
        return total_consumption
    
    def get_irrigating_count(self) -> int:
        """Checks how many threads are currently running"""

        self.logger.warning("get_irrigating_count is deprecated and not supported in ControllerCore.")
        return 0
    
    # ----------------- Deprecated Irrigation Control Methods -----------------------

    def start_automatic_irrigation(self):
        """Starts automatic irrigation based on the configured schedule."""
        
        self.logger.warning("start_automatic_irrigation is deprecated and may be removed in future versions.")
        self.start_auto_cycle()
    
    def stop_irrigation(self):
        """Stops all ongoing irrigation tasks."""
        
        self.logger.warning("stop_irrigation is deprecated and may be removed in future versions.")
        self.stop_all_irrigation()

    def manual_irrigation(self, circuit_number: int, liter_amount: float) -> None:
        """Starts manual irrigation for a specific circuit with the given volume in liters."""
        
        self.logger.warning("manual_irrigation is deprecated and may be removed in future versions.")
        self.start_manual_irrigation(circuit_number, liter_amount)


    # ----------------- Deprecated Main Loop Methods -----------------------

    def start_main_loop(self):
        """Enables automatic irrigation scheduling"""
        
        self.logger.warning("start_main_loop is deprecated and may be removed in future versions.")
        self.enable_auto_irrigation()

    def stop_main_loop(self):
        """Disables automatic irrigation scheduling"""
        
        self.logger.warning("stop_main_loop is deprecated and may be removed in future versions.")
        self.disable_auto_irrigation()
    
    def pause_main_loop(self):
        """Pauses the main loop for the next irrigation check"""
        
        self.logger.warning("pause_main_loop is deprecated and not supported in ControllerCore.")
    
    def resume_main_loop(self):
        """Resumes the main loop after pausing"""
        
        self.logger.warning("resume_main_loop is deprecated and not supported in ControllerCore.")