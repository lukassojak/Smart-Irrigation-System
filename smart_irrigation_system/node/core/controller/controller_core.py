# smart_irrigation_system/node/core/controller/controller_core.py

import os, atexit, sys, signal, threading, time

import smart_irrigation_system.node.config.config_loader as config_loader

from typing import Optional

from smart_irrigation_system.node.utils.logger import get_logger

from smart_irrigation_system.node.config.global_config import GlobalConfig
from smart_irrigation_system.node.core.circuit_state_manager import CircuitStateManager
from smart_irrigation_system.node.core.enums import ControllerState, IrrigationState
from smart_irrigation_system.node.core.irrigation_circuit import IrrigationCircuit
from smart_irrigation_system.node.core.status_models import CircuitStatus, CircuitRuntimeStatus, ControllerStatusSummary, ControllerFullStatus

from smart_irrigation_system.node.core.controller.batch_strategy import SimpleBatchStrategy
from smart_irrigation_system.node.core.controller.irrigation_executor import IrrigationExecutor
from smart_irrigation_system.node.core.controller.status_aggregator import StatusAggregator
from smart_irrigation_system.node.core.controller.task_scheduler import TaskScheduler
from smart_irrigation_system.node.core.controller.task_planner import TaskPlanner
from smart_irrigation_system.node.core.controller.thread_manager import ThreadManager, TaskType
from smart_irrigation_system.node.core.controller.auto_irrigation_service import AutoIrrigationService

from smart_irrigation_system.node.weather.recent_weather_fetcher import RecentWeatherFetcher
from smart_irrigation_system.node.weather.weather_simulator import WeatherSimulator

from smart_irrigation_system.node.exceptions import WorkerThreadError, WorkerThreadAlreadyExistsError

from smart_irrigation_system.node.core.controller.legacy_controller_api import LegacyControllerAPI


# Seed for the weather simulator to ensure reproducibility in tests
WEATHER_SIMULATOR_SEED = 42

# Determine the base directory of the project
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../..")
)

# Paths to configuration and data files
CONFIG_SECRETS_PATH = os.path.join(BASE_DIR, "runtime/node/config/config_secrets.json")
CONFIG_GLOBAL_PATH = os.path.join(BASE_DIR, "runtime/node/config/config_global.json")
CONFIG_ZONES_PATH = os.path.join(BASE_DIR, "runtime/node/config/zones_config.json")
ZONE_STATE_PATH = os.path.join(BASE_DIR, "runtime/node/data/zones_state.json")
IRRIGATION_LOG_PATH = os.path.join(BASE_DIR, "runtime/node/data/irrigation_log.json")


class ControllerCore(LegacyControllerAPI):
    """
    Full replacement for (old) IrrigationController class.
    Combines components responsible for configuration, weather featching, scheduling, planning, and execution.
    """

    def __init__(self, global_config_path: str = CONFIG_GLOBAL_PATH,
                    config_zones_path: str = CONFIG_ZONES_PATH):
        self.logger = get_logger(self.__class__.__name__)

        # Load configurations
        self.global_config: GlobalConfig = self._load_global_config(global_config_path)
        self.circuits: dict[int, IrrigationCircuit] = self._load_zones_config(config_zones_path)

        # Initialize components
        self.conditions_provider: RecentWeatherFetcher | WeatherSimulator = \
            self._init_global_conditions_provider()
        self.state_manager = CircuitStateManager(ZONE_STATE_PATH,
                                                 IRRIGATION_LOG_PATH)
        self.thread_manager = ThreadManager()
        self.batch_strategy = SimpleBatchStrategy()
        self.task_planner = TaskPlanner(self.batch_strategy)
        self.irrigation_executor = self._init_irrigation_executor()
        self.agg: StatusAggregator = StatusAggregator(
            circuits=self.circuits,
            state_manager=self.state_manager
        )
        self.ais = AutoIrrigationService(
            global_config=self.global_config,
            on_auto_irrigation_demand=self._on_auto_irrigation_demand
        )

        # Init task scheduler last to ensure all components are ready
        self.task_scheduler = self._init_task_scheduler(
            thread_manager=self.thread_manager,
            delay_seconds=1.0  # Delay to allow other components to initialize first
        )

        self._state_lock = threading.Lock()
        self._controller_state = ControllerState.IDLE
        self._register_signal_handlers()
        atexit.register(self._cleanup)

        # ---- Deprecated attributes for backward compatibility ----
        self.global_conditions_provider = self.conditions_provider

        self.logger.info("ControllerCore initialized successfully.")


    # ==================================================================================================================
    # Public API - Status and State retrieval
    # ==================================================================================================================

    @property
    def controller_state(self) -> ControllerState:
        """Get the current state of the irrigation controller."""
        with self._state_lock:
            return self._controller_state
        
    
    def get_circuit_full_status(self, circuit_id: int) -> CircuitStatus:
        """
        Get the full status (runtime + snapshot) of a specific circuit.
        
        :param circuit_id: ID of the circuit to get status for.
        :return: CircuitStatus object combining runtime and snapshot data.
        :raises ValueError: if the circuit_id is not found.
        """

        return self.agg.get_circuit_status(circuit_id)
    

    def get_circuit_runtime_status(self, circuit_id: int) -> CircuitRuntimeStatus:
        """
        Get the runtime status of a specific circuit.
        
        :param circuit_id: ID of the circuit to get status for.
        :return: CircuitRuntimeStatus object.
        :raises ValueError: if the circuit_id is not found.
        """

        try:
            circuit = self.circuits[circuit_id]
        except KeyError:
            raise ValueError(f"Circuit ID {circuit_id} not found in circuits.")
        
        return circuit.runtime_status
    

    def get_controller_status_summary(self) -> ControllerStatusSummary:
        """
        Get a summary of the controller's overall status.
        
        :return: ControllerStatusSummary object.
        """

        return ControllerStatusSummary(
            circuit_ids=list(self.circuits.keys()),
            controller_state=self.controller_state
        )
    
    def get_controller_full_status(self) -> ControllerFullStatus:
        """
        Get the full status of the controller including all circuit statuses.
        
        :return: ControllerFullStatus object.
        """

        css = self.get_controller_status_summary()
        return self.agg.get_controller_full_status(css)


    # ==================================================================================================================
    # Public API - Irrigation control
    # ==================================================================================================================
    
    def start_auto_cycle(self) -> None:
        """Start the automatic irrigation cycle immediately."""
        def auto_cycle_wrapper():
            try:
                self.irrigation_executor.execute_plan(
                    planner=self.task_planner,
                    global_config=self.global_config,
                    conditions_provider=self.conditions_provider
                )
                self.logger.info("Automatic irrigation cycle completed successfully.")
            except Exception as e:
                self.logger.error(f"Error during automatic irrigation cycle: {e}")
                self._on_executor_error(circuit_id=-1, exception=e)

        # Check controller state
        if self.controller_state == ControllerState.ERROR:
            self.logger.error("Cannot start automatic irrigation cycle while controller is in ERROR state.")
            return
        if self.controller_state == ControllerState.STOPPING:
            self.logger.warning("Cannot start automatic irrigation cycle while controller is STOPPING.")
            return

        self.logger.info("Starting automatic irrigation cycle...")
        self.task_planner.plan(circuits=self.circuits,
                               state_manager=self.state_manager)
        
        # The auto_irrigation_cycle worker name is fixed to ensure only one instance runs at a time
        # However, multiple manual_irrigation_circuit_{id} workers can run concurrently even during auto cycles
        try:
            self.thread_manager.start_worker(
                worker_name="auto_irrigation_cycle",
                task_type=TaskType.EXECUTOR,
                target_fn=auto_cycle_wrapper
            )
        except WorkerThreadAlreadyExistsError:
            self.logger.warning("IrrigationExecutor is already running. Cannot start another automatic irrigation cycle.")
        except Exception as e:
            self.logger.error(f"Error starting automatic irrigation cycle: {e}")
            self._on_executor_error(circuit_id=-1, exception=e)
        

    def start_manual_irrigation(self, circuit_id: int, volume_liters: float) -> None:
        """Start manual irrigation for a specific circuit with the given volume in liters."""
        def manual_irrigation_wrapper():
            try:
                self.irrigation_executor.execute_manual(circuit_id, volume_liters)
            except Exception as e:
                self.logger.error(f"Error during manual irrigation for circuit {circuit_id}: {e}")
                self._on_executor_error(circuit_id=circuit_id, exception=e)

        # Check controller state
        if self.controller_state == ControllerState.ERROR:
            self.logger.error("Cannot start manual irrigation while controller is in ERROR state.")
            return
        if self.controller_state == ControllerState.STOPPING:
            self.logger.warning("Cannot start manual irrigation while controller is STOPPING.")
            return

        try:
            self.thread_manager.start_worker(
                worker_name=f"manual_irrigation_circuit_{circuit_id}",
                task_type=TaskType.EXECUTOR,
                target_fn=manual_irrigation_wrapper
            )
        except WorkerThreadAlreadyExistsError:
            self.logger.warning(f"Manual irrigation for circuit {circuit_id} is already running.")
        except Exception as e:
            self.logger.error(f"Error during manual irrigation for circuit {circuit_id}: {e}")
            self._on_executor_error(circuit_id=circuit_id, exception=e)
        

    def stop_all_irrigation(self, timeout: float = 10.0) -> None:
        """Stop all ongoing irrigation tasks."""

        self.logger.info("Stopping all ongoing irrigation tasks...")
        try:
            self.irrigation_executor.stop_all_irrigation(timeout=timeout)
            self.logger.info("All irrigation tasks stopped.")
        except TimeoutError as e:
            self.logger.error(f"Timeout while stopping all irrigation tasks: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error while stopping all irrigation tasks: {e}")


    def stop_circuit_irrigation(self, circuit_id: int, timeout: float = 10.0) -> None:
        """Stop irrigation for a specific circuit."""
        raise NotImplementedError("stop_circuit_irrigation is not yet implemented in ControllerCore.")


    # ==================================================================================================================
    # Public API - Configuration management
    # ==================================================================================================================

    def enable_auto_irrigation(self) -> None:
        """
        Enables automatic irrigation scheduling.
        This is run-time enabling and will not persist after restart.
        """

        self.ais.enable_runtime()
    

    def disable_auto_irrigation(self) -> None:
        """
        Disables automatic irrigation scheduling.
        This is run-time disabling and will not persist after restart.
        """

        self.ais.disable_runtime()


    def reload_config(self, global_config_path: str = CONFIG_GLOBAL_PATH) -> None:
        """
        Reload global and zones configuration from the specified paths.
        Modifies the current configuration in place.
        """
        raise NotImplementedError("reload_config is not yet implemented in ControllerCore.")

    # ==================================================================================================================
    # Public API - Shutdown & Restart
    # ==================================================================================================================

    def shutdown(self) -> None:
        """Perform clean shutdown of the controller."""
        pass

    def restart(self) -> None:
        """Restart the controller."""
        raise NotImplementedError("restart is not yet implemented in ControllerCore.")
    

    # ==================================================================================================================
    # Private initialization helpers
    # ==================================================================================================================

    def _load_global_config(self, path: str) -> GlobalConfig:
        """Load global configuration from the specified path."""
        # TODO: Handle exceptions and validation
        return config_loader.load_global_config(path, CONFIG_SECRETS_PATH)

    def _load_zones_config(self, path: str) -> dict[int, IrrigationCircuit]:
        """Load zones configuration and initialize circuits."""
        # TODO: Handle exceptions and validation
        circuit_list: list[IrrigationCircuit] = config_loader.load_zones_config(path)
        return {circuit.id: circuit for circuit in circuit_list}
    
    def _init_global_conditions_provider(self) -> RecentWeatherFetcher | WeatherSimulator:
        """Initialize the global weather conditions provider based on configuration."""
        if self.global_config.automation.use_weathersimulator:
            self.logger.info("Using Weather Simulator as conditions provider.")
            return WeatherSimulator(seed=WEATHER_SIMULATOR_SEED)
        else:
            self.logger.info("Using Recent Weather Fetcher as conditions provider.")
            max_interval_days = max((circuit.interval_days for circuit in self.circuits.values()), default=1)
            return RecentWeatherFetcher(self.global_config, max_interval_days)
        
    def _init_irrigation_executor(self) -> IrrigationExecutor:
        """Initialize the IrrigationExecutor with necessary components and register callbacks."""
        executor = IrrigationExecutor(
            circuits=self.circuits,
            state_manager=self.state_manager,
            thread_manager=self.thread_manager
        )
        executor.register_callbacks(
            on_irrigation_start=self._on_irrigation_start,
            on_auto_irrigation_finish=self._on_auto_irrigation_finish,
            on_man_irrigation_finish=self._on_man_irrigation_finish,
            on_irrigation_stopped=self._on_irrigation_stopped,
            on_executor_error=self._on_executor_error,
            on_irrigation_waiting=self._on_irrigation_waiting,
            on_irrigation_failed=self._on_irrigation_failure,
            on_irrigation_stop_requested=self._on_irrigation_stop_requested
        )
        return executor
    
    def _init_task_scheduler(self, thread_manager: ThreadManager, delay_seconds: float = 0.0) -> TaskScheduler:
        """Initialize the TaskScheduler with necessary periodic tasks."""
        scheduler = TaskScheduler(thread_manager)

        # Register a periodic task to refresh state
        scheduler.register_task(
            name="refresh_state",
            fn=self._refresh_state,
            interval=5,  # every 5 seconds
            async_mode=False,
            initial_delay=delay_seconds
        )

        # Register a periodic task to tick the AutoIrrigationService
        scheduler.register_task(
            name="auto_irrigation_service_tick",
            fn=self.ais.tick,
            interval=60,  # every 60 seconds
            async_mode=False,
            initial_delay=delay_seconds
        )

        scheduler.start()

        return scheduler
        
    def _register_signal_handlers(self):
        def shutdown_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, performing clean shutdown...")
            sys.exit(0)
        
        # Common termination signals
        signal.signal(signal.SIGTERM, shutdown_handler)  # Termination signal
        signal.signal(signal.SIGINT, shutdown_handler)   # Ctrl+C
        # SIGKILL cannot be caught - when received and the irrigation is running, the valves may remain open until the next startup

    
    # ==================================================================================================================
    # Private methods - State management
    # ==================================================================================================================

    def _refresh_state(self):
        """Set the controller to the specified state"""

        with self._state_lock:
            if self._controller_state == ControllerState.ERROR:
                self.logger.warning(f"Attempted to change state from ERROR state, ignoring.")
                return

            prev_name = self._controller_state.name
            if self.thread_manager.get_running_workers(TaskType.IRRIGATION) and self.irrigation_executor.stop_event.is_set():
                self._controller_state = ControllerState.STOPPING
            elif self.thread_manager.get_running_workers(TaskType.IRRIGATION):
                self._controller_state = ControllerState.IRRIGATING
            else:
                self._controller_state = ControllerState.IDLE
            
            if prev_name != self._controller_state.name:
                self.logger.debug(f"Controller state changed: {prev_name} → {self._controller_state.name}")

    def _set_error_state(self, reason: str):
        """Set the controller to ERROR state"""

        with self._state_lock:
            self._controller_state = ControllerState.ERROR

        self.logger.error(f"Controller entered ERROR state: {reason}")
        # Additional error handling can be added here (e.g., notifications, alerts)

    def _on_irrigation_start(self):
        """Callback for when irrigation starts."""

        self._refresh_state()
        # Additional actions on irrigation start can be added here e.g., MQTT notifications
    
    def _on_irrigation_waiting(self, circuit_id: int, msg: str):
        # Callback for when irrigation is waiting to start on a circuit (eg. due to flow limits)
        # MQTT notifications can be added here
        pass

    def _on_irrigation_failure(self, circuit_id: int, reason: str):
        # Callback for when irrigation fails on a circuit
        # MQTT notifications can be added here
        pass

    def _on_irrigation_stop_requested(self):
        self._refresh_state()

    def _on_auto_irrigation_finish(self):
        self._refresh_state()

    def _on_man_irrigation_finish(self, circuit_id: int):
        # update state only if no other irrigation is ongoing
        # MQTT notifications can be added here
        self._refresh_state()

    def _on_irrigation_stopped(self):
        self._refresh_state()

    def _on_executor_error(self, circuit_id: int, exception: Exception):
        self._set_error_state(f"IrrigationExecutor error on circuit {circuit_id}: {exception}")


    # ==================================================================================================================
    # Private methods - AutoIrrigationService callback
    # ==================================================================================================================
    
    def _on_auto_irrigation_demand(self):
        """Callback when automatic irrigation is demanded by the AutoIrrigationService."""

        self.logger.info("Automatic irrigation demand received.")
        self.start_auto_cycle()


    # ==================================================================================================================
    # Private methods - Cleanup
    # ==================================================================================================================


    def _cleanup(self):
        """Cleans up the resources used by the irrigation controller"""
        self.logger.info("Cleaning up resources...")
        if self.controller_state != ControllerState.IDLE:
            try:
                self.logger.info("Stopping all ongoing irrigation tasks before shutdown...")
                self.irrigation_executor.stop_all_irrigation(timeout=60.0)
            except TimeoutError:
                self.logger.critical("Timeout while stopping irrigation tasks during cleanup.")
            except Exception as e:
                self.logger.critical(f"Unexpected error while stopping irrigation tasks during cleanup: {e}")

        self.task_scheduler.stop(timeout=10.0)
        self.thread_manager.join_all_workers(timeout=10.0)

        # Double check if all valves are closed
        for circuit in self.circuits.values():
            if circuit.state == IrrigationState.IRRIGATING:
                self.logger.warning(f"Circuit {circuit.id} is still irrigating during cleanup, attempting to force-close valve.")	
                circuit.close_valve()

        self.state_manager.handle_clean_shutdown()