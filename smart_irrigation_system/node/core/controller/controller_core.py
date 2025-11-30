# node/core/controller/controller_core.py

import os, atexit, sys, signal

import smart_irrigation_system.node.config.config_loader as config_loader

from smart_irrigation_system.node.utils.logger import get_logger

from smart_irrigation_system.node.config.global_config import GlobalConfig
from smart_irrigation_system.node.core.circuit_state_manager import CircuitStateManager
from smart_irrigation_system.node.core.enums import ControllerState
from smart_irrigation_system.node.core.irrigation_circuit import IrrigationCircuit
from smart_irrigation_system.node.core.status_models import CircuitSnapshot

from smart_irrigation_system.node.core.controller.batch_strategy import BatchStrategy
from smart_irrigation_system.node.core.controller.irrigation_executor import IrrigationExecutor
from smart_irrigation_system.node.core.controller.status_aggregator import StatusAggregator
from smart_irrigation_system.node.core.controller.task_scheduler import TaskScheduler
from smart_irrigation_system.node.core.controller.task_planner import TaskPlanner
from smart_irrigation_system.node.core.controller.thread_manager import ThreadManager

from smart_irrigation_system.node.weather.recent_weather_fetcher import RecentWeatherFetcher
from smart_irrigation_system.node.weather.weather_simulator import WeatherSimulator


# Seed for the weather simulator to ensure reproducibility in tests
WEATHER_SIMULATOR_SEED = 42

# Determine the base directory of the project
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)

# Paths to configuration and data files
CONFIG_SECRETS_PATH = os.path.join(BASE_DIR, "runtime/node/config/config_secrets.json")
CONFIG_GLOBAL_PATH = os.path.join(BASE_DIR, "runtime/node/config/config_global.json")
CONFIG_ZONES_PATH = os.path.join(BASE_DIR, "runtime/node/config/zones_config.json")
ZONE_STATE_PATH = os.path.join(BASE_DIR, "runtime/node/data/zones_state.json")
IRRIGATION_LOG_PATH = os.path.join(BASE_DIR, "runtime/node/data/irrigation_log.json")


class ControllerCore:
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
        self.task_scheduler = TaskScheduler(self.thread_manager)
        self.batch_strategy = BatchStrategy()
        self.task_planner = TaskPlanner(self.batch_strategy)
        self.irrigation_executor = IrrigationExecutor(
            circuits=self.circuits,
            state_manager=self.state_manager,
            thread_manager=self.thread_manager
        )
        self.agg: StatusAggregator = StatusAggregator(
            circuits=self.circuits,
            state_manager=self.state_manager
        )

        self.controller_state = ControllerState.IDLE
        self._register_signal_handlers()
        self.logger.info("ControllerCore initialized successfully.")

    
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
        if self.global_config.use_weathersimulator:
            self.logger.info("Using Weather Simulator as conditions provider.")
            return WeatherSimulator(seed=WEATHER_SIMULATOR_SEED)
        else:
            self.logger.info("Using Recent Weather Fetcher as conditions provider.")
            max_interval_days = max((circuit.interval_days for circuit in self.circuits.values()), default=1)
            return RecentWeatherFetcher(self.global_config, max_interval_days)
        
    def _register_signal_handlers(self):
        def shutdown_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, performing clean shutdown...")
            sys.exit(0)
        
        # Common termination signals
        signal.signal(signal.SIGTERM, shutdown_handler)  # Termination signal
        signal.signal(signal.SIGINT, shutdown_handler)   # Ctrl+C
        # SIGKILL cannot be caught - when received and the irrigation is running, the valves may remain open until the next startup


    # ==================================================================================================================
    # Public API
    # ==================================================================================================================

    # ==================================================================================================================
    # Deprecated methods from IrrigationController
    # ==================================================================================================================

    def get_circuit_snapshot(self, circuit_id: int) -> CircuitSnapshot:
        """Returns the persistent snapshot state of a given circuit."""
        if circuit_id not in self.circuits:
            raise ValueError(f"Circuit ID {circuit_id} does not exist.")
        
        snapshot = self.state_manager.get_circuit_snapshot(circuit_id)
        return snapshot
    
    