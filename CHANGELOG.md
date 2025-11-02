# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.2] - 2025-11-02
*Documentation and usability patch release focusing on simplified installation, local demo, and system demonstration.*

### Added
- **Automated installation script:** `demo/install_demo.sh` for simplified setup of Python/Node dependencies and environment creation.
- **Automated demo runner:** `demo/run_demo.sh` supporting both GUI (multi-terminal) and headless (WSL/SSH) modes.
  - Detects `gnome-terminal` and automatically launches Server, Node, and Web UI in separate windows if available.
  - Fallback to background mode with live Node CLI in the foreground when GUI is not present.
- **Demo documentation:**  
  - `docs/user_guide/SETUP_AND_RUN_DEMO.md` – step-by-step guide for local demo on a single machine.  
  - Clarified quick start instructions in `README.md` and linked demo guide.
- **Combined dependency file:** `requirements_demo.txt` for all-in-one demo environment.
- **Improved developer experience:** Added `.gitattributes` to enforce LF line endings for shell scripts.

### Changed
- Updated `README.md` with simplified and concise structure.
- Updated `/docs/` structure for better separation between *user guides* and *developer references*.

### Fixed
- Links to developer reference in `README.md` fixed.
- Environment activation and path issues in non-GUI environments.

### Removed

### Known Issues
- Parser currently supports only the default Node MQTT format; additional metrics will require format extension.
- Backend still returns `last_status` as a raw text string; parsing of irrigation zones and states is done client-side. This is planned to be addressed in the next patch. Server will provide structured data in future - planned for `v0.9.1`.
- When multiple zones are irrigating concurrently, only the first zone may appear in the UI (due to backend message format).
- Web UI currently includes only monitoring (`NodeList`) — no irrigation control or real-time updates.
- Build serving via FastAPI (`/web_ui/dist`) not yet finalized for production deployment.
- `ZoneNodeMapper` currently uses a static mapping returning `"node1"`.
- Configuration management not yet implemented.
- Authentication and access control for REST API endpoints are not yet included.
- Node ID is currently hardcoded in `/start_irrigation` (`"node1"`). Dynamic assignment from NodeRegistry will be implemented in the next iteration.
- Server documentation and REST API usage examples are not yet included in the main documentation.

---

## [0.9.1] - 2025-10-29
*Enhanced node status parsing and frontend updates for improved monitoring.*

### Added
- New structured status parsing for node states:
  - Introduced function `parse_node_status(raw_status)` in `NodeRegistry` to convert
    raw MQTT status strings into structured JSON objects.
  - Handles invalid or missing data gracefully (returns `None` if parsing fails).
- Extended `/nodes` endpoint:
  - Now returns an additional field `"status"` for each node, containing the parsed structure.
  - Original `"last_status"` string is preserved for backward compatibility with older frontends.
- Added frontend node state refresh on first load.
- Added frontend periodic polling every 5 seconds.

### Changed

### Fixed

### Removed
- (Node side) Removed periodic weather cache updates in the main loop; weather data is now fetched only on demand.

### Known Issues
- Parser currently supports only the default Node MQTT format; additional metrics will require format extension.
- Backend still returns `last_status` as a raw text string; parsing of irrigation zones and states is done client-side. This is planned to be addressed in the next patch. Server will provide structured data in future - planned for `v0.9.1`.
- When multiple zones are irrigating concurrently, only the first zone may appear in the UI (due to backend message format).
- Web UI currently includes only monitoring (`NodeList`) — no irrigation control or real-time updates.
- Build serving via FastAPI (`/web_ui/dist`) not yet finalized for production deployment.
- `ZoneNodeMapper` currently uses a static mapping returning `"node1"`.
- Configuration management not yet implemented.
- Authentication and access control for REST API endpoints are not yet included.
- Node ID is currently hardcoded in `/start_irrigation` (`"node1"`). Dynamic assignment from NodeRegistry will be implemented in the next iteration.
- Server documentation and REST API usage examples are not yet included in the main documentation.

---

## [0.9.0] - 2025-10-27
*First functional prototype of the Web UI layer (React + Vite) integrated with FastAPI backend.*

### Added
- Introduced new `web_ui/` module containing the first functional React + Vite dashboard.
- Added API communication layer `src/lib/api.js` using Axios with support for:
  - `GET /api/nodes`
  - `POST /api/update_status`
  - `POST /api/start_irrigation`
  - `POST /api/stop_irrigation`
  - `GET /api/ping`
- Implemented `NodeList.jsx` component:
  - Fetches and visualizes node statuses from the backend.
  - Displays each node as a modern card layout with:
    - Controller state, Auto mode (enabled/paused), currently irrigating zones.
    - Last update timestamp (formatted as `HH:MM:SS DD.MM.YYYY`).
    - Online/offline indicator with icon.
  - Supports manual refresh via `/update_status` endpoint.
- Integrated Tailwind CSS and Lucide icons for clean and responsive UI styling.
- Added development proxy configuration in `vite.config.js` for seamless connection with FastAPI.
- Added base documentation file `docs/SETUP_SERVER_AND_WEB_UI.md` for server and frontend deployment.
- Prepared build integration with FastAPI for future production serving (`app.mount("/", StaticFiles(...))`).

### Changed
- Refactored FastAPI endpoints to be prefixed with `/api` for better separation of API and static content.

### Fixed

### Removed

### Known Issues

---

## [0.8.0] - 2025-10-25
*Initial prototype of the central server component – ready for Web UI integration.*

### Added
- **FastAPI REST API** for the central server component:
  - Implemented base endpoints for node monitoring and irrigation control.
    - `GET /nodes` - returns current state of all registered nodes.
    - `POST /update_status` - requests status update of all nodes via MQTT.
    - `POST /start_irrigation` - sends command to start manual irrigation for a specified zone and amount.
    - `POST /stop_irrigation` - sends command to stop irrigation of all irrigation (all zones, all nodes).
    - `GET /ping` - simple health check endpoint.
  - All endpoints are fully integrated with the `MQTTManager` for backend communication with nodes.
- FastAPI server lifecycle now manages `IrrigationServer` startup and shutdown.
- Added initial API documentation via auto-generated Swagger UI at `/docs` endpoint.
- `ZoneNodeMapper` module introduced for dynamic mapping of zones to irrigation nodes.
  - Current implementation returns `"node1"` (single-node setup).
  - Future versions will load mappings from configuration or database.

### Changed
- Refactored server entry point (`server/main.py`) for clean FastAPI integration.
- Server logger (`server/utils/logger.py`) now configured for simplified console output during API operation.
- Verified functional communication chain: REST API -> MQTTManager -> Irrigation Node -> NodeRegistry update.

### Fixed
- `NodeRegistry` now correctly updates the `last_update` timestamp with real-time values upon receiving status updates from nodes.

### Removed

### Known Issues
- `ZoneNodeMapper` currently uses a static mapping returning `"node1"`.
- Configuration management not yet implemented.
- Authentication and access control for REST API endpoints are not yet included.
- Node ID is currently hardcoded in `/start_irrigation` (`"node1"`). Dynamic assignment from NodeRegistry will be implemented in the next iteration.
- Server documentation and REST API usage examples are not yet included in the main documentation.

---

## [0.7.0] - 2025-10-24
*First functional version of the central server component*

### Added
- **Server prototype**: Initial implementation of the central server architecture.
  - `IrrigationServer` orchestrator introduced for managing server lifecycle.
  - `MQTTManager` added for MQTT-based communication with irrigation nodes.
  - `NodeRegistry` introduced for storing runtime states of all nodes in `runtime/server/data/nodes_state.json`.
  - Logging integrated for all server components.
- Added standalone entry point for the server (`server/main.py`).
- Verified successful MQTT communication between Server and Node (v0.6.0).

### Changed
- Major project refactor: introduced new modular architecture separating `node/` and `server/` components under `smart_irrigation_system/`.
- Updated internal imports and folder structure for better scalability.
- Added dedicated directories for `core`, `interface`, `network`, `weather`, `utils`, `config`  modules in the Node implementation.
- Added placeholder structure for the upcoming Server prototype (`server/` folder, `config`, `data`, `api` placeholders, requirements file).
- Adjusted file path handling in `irrigation_controller.py` to dynamically resolve project root.

### Fixed

### Removed

### Known Issues
- `NodeRegistry` currently stores placeholder timestamp (`"now"`) for `last_update`. Real-time timestamps to be implemented.¨
- Documentation for server setup, usage and architecture is pending.

---

## [0.6.0] - 2025-10-23
*Completed the MVP of the edge node component*

### Added
- Implemented `MQTTClient` module for bidirectional communication between irrigation node and central server via MQTT.
- Added `ServerCommandHandler` class to interpret incoming MQTT messages and translate them into controller actions.
- Added new `get_status_message()` method in `IrrigationController` for simplified status publishing via MQTT.
- Added MQTT initialization and startup integration in `main.py` to launch the MQTT client alongside the irrigation controller.
- Added `network/` directory containing communication modules for MQTT and server commands.

### Changed
- `IrrigationController` can now operate as an MQTT-enabled node, publishing live status updates and responding to remote commands.
- Internal project structure updated to separate core logic (`irrigation_controller`) from communication layer (`network`).
- Simplified message format for node status reporting to support future unification of MQTT and CLI status outputs.

### Fixed

### Removed

### Known Issues
- Node currently publishes status in a simplified format; CLI and MQTT use different formatting — unification planned in future.
- No authentication or TLS implemented yet for MQTT communication (planned for future stable version).
- `IrrigationCLI` throws an exception during irrigation (no more details known yet) - investigation ongoing. Exception in the CLI does not affect the main irrigation process.

---

## [0.5.0] - 2025-10-21

### Added
- `use_weathersimulator` attribute in `config_global.json` to allow switching between `RecentWeatherFetcher` and `WeatherSimulator` for global conditions. If `environment` is set to `production`, this setting is ignored and `RecentWeatherFetcher` is always used.
- Automatic logging of interrupted irrigation results during system startup after unclean shutdowns.
  - If a circuit was irrigating during an unexpected shutdown, it is now automatically marked as `interrupted` in `zones_state.json`.
  - An `IrrigationResult` entry is now appended to `irrigation_log.json` for full historical consistency.

### Changed
- Automatic irrigation now does not require `ControllerState` to be `IDLE`. This allows automatic irrigation to run even if manual irrigation is in progress.
- Improved unclean shutdown detection in `CircuitStateManager.init_circuit_states()` to recover interrupted irrigation sessions and maintain data consistency between state and log files.
- Main loop in `IrrigationController` enhanced and made more robust.

### Fixed
- `CircuitStateManager` now updates `last_update` timestamp when state is changed to `shutdown`.
- Fixed inconsistency in `zones_state.json` and `irrigation_log.json` when system was terminated unexpectedly during irrigation.
- `WeatherSimulator` now provides same interface as `RecentWeatherFetcher` for better compatibility.
- Fixed `IrrigationController` state management when both automatic and manual irrigation run concurrently.
- `CircuitStateManager` now correctly updates `last_update` timestamp when irrigation is stopped.
- `IrrigationController` now correctly handles attempts to manually irrigate a zone which is already irrigating.
- `ControllerState` management significantly improved to accurately reflect ongoing irrigation activities, even when both automatic and manual irrigation processes are running concurrently. The controller state now correctly indicates active irrigation, preventing premature transitions to `IDLE` and ensuring that `stop_irrigation()` functions as intended for all ongoing processes.

### Removed

### Known Issues
- `IrrigationCLI` throws an exception during irrigation (no more details known yet) - investigation ongoing. Exception in the CLI does not affect the main irrigation process.

---

## [0.4.2] - 2025-10-19

### Added
- Weather data cache is now refreshed periodically in main loop based on a interval defined in `IrrigationController`.
- Log rotation added for `system_log.log` to prevent excessive file size growth. Default settings: daily rotation, keep 30 backup files. The logs are located in the `/logs/` directory
- Example data files: `data/zones_state.example.json` and `data/irrigation_log.example.json` added

### Changed
- `RecentWeatherFetcher` now does not save all fetched data to a file (was implemented for debugging purposes only).

### Fixed
- `IrrigationCLI` now handles errors gracefully and continues running instead of crashing on exceptions.
- Fixed duplicated cleanups in `IrrigationController`.

### Removed

### Known Issues
- Type error is occurring when trying to manually irrigate a zone which is already irrigating.
- When irrigation is stopped, `CircuitStateManager` does not update the `last_update` timestamp, leading to inaccurate state tracking.
- If `global_conditions_provider` in `IrrigationController` is set to `WeatherSimulator`, some methods are not available in the simulator, leading to potential crashes.
- `CircuitStateManager` does not update `last_update` timestamp when state is changed to `shutdown`.
- Main loop allows multiple irrigation attempts in irrigation time window if the previous attempt was skipped due to weather conditions. 
- `irrigation_log.json` is not updated correctly.
- `IrrigationCLI` throws an exception during irrigation (no more details known yet) - investigation ongoing. Exception in the CLI does not affect the main irrigation process.

---

## [0.4.1] - 2025-09-08

### Added

### Changed
- Help information in CLI updated and redesigned.

### Fixed
- `IrrigationController` now handles keyboard interrupts (CTRL+C) gracefully, ensuring ongoing irrigation processes are stopped before exiting.
- Manual irrigation is now non-blocking, allowing the CLI to remain responsive during irrigation.

### Removed

### Known Issues

---

## [0.4.0] - 2025-09-08

### Added
- Refactored `IrrigationCircuit` to include runtime attributes for irrigation history tracking.
- Refactored `IrrigationCircuit` to return detailed status after irrigation completion for better state management and irrigation history tracking.
- CLI and `IrrigationController` now support manual irrigation of individual circuits with specified water amount.

### Changed

### Fixed
- Auto pause fixed to work correctly.
- `CircuitStateManager` now correctly handles empty data files, preventing potential crashes.
- `CircuitStateManager` now correctly validates and handles corrupted data files, preventing potential crashes and data loss.
- `RecentWeatherFetcher` now dynamically adjusts the date range for fetching weather data based on the circuits configuration, allowing for retrieval of weather data for the relevant period.
- `RecentWeatherFetcher` now handles no internet connectivity gracefully, preventing unhandled exceptions.
- `IrrigationCircuit` correctly updates its runtime state attribute after skipping irrigation due to weather conditions.

### Removed
- `ConsoleLogHandler` removed as it is no longer needed with the CLI.

### Known Issues
- The `CircuitStateManager` does not handle race conditions when multiple threads access the state file simultaneously. This may lead to data corruption or loss of state information. A locking mechanism will be implemented in a future release to address this issue.
- Manual irrigation from the CLI does not support stopping an ongoing irrigation process. This will be added in a future release.

---

## [0.3.2] - 2025-08-28

### Added
- Enhanced CLI with new features for better user experience and system monitoring.
- Circuit 'DISABLED' state support in CLI and core logic.

### Changed
- The IrrigationCircuit now initializes state as 'DISABLED' if the zone is not enabled in the configuration, otherwise 'IDLE'.

### Fixed
- WeatherSimulator initialization fixed.
- Resolved potential endless loop in `IrrigationController` occuring after first automatic irrigation run.
- Updated logic to skip next irrigation check (AUTO paused)

### Removed

### Known Issues
- On CTRL+C, the CLI does not exit gracefully and when irrigation is running, it may not stop.
- The `config_global.json` does not contain a `api_enabled` flag, which is required for the `RecentWeatherFetcher` to function correctly. This will be added in the future release.
- `max_flow_monitoring` feature does not work correctly at the moment. This will be addressed in a future release.
- Auto pause does not work correctly.
- No internet connectivity leads to unhandled exceptions in `RecentWeatherFetcher`.
- The `CircuitStateManager` does not handle empty data files correctly, leading to potential crashes. 
- The `RecentWeatherFetcher` is hardcoded to fetch weather data for the last 1 day only.

---

## [0.3.1] - 2025-08-22
*Performance and stability improvements for the interactive CLI*

### Added
- Sleep mode for the CLI to reduce CPU usage when not used.
- Adaptive refresh rate for the CLI dashboard based on system activity, reducing CPU usage when the system is idle.

### Changed

### Fixed
- CLI dashboard now correctly displays recent logs.

### Removed

### Known Issues
- On CTRL+C, the CLI does not exit gracefully and when irrigation is running, it may not stop.
- The `config_global.json` does not contain a `api_enabled` flag, which is required for the `RecentWeatherFetcher` to function correctly. This will be added in the next release.
- `max_flow_monitoring` feature does not work correctly at the moment. This will be addressed in a future release.

---

## [0.3.0] - 2025-08-21
*First interactive CLI release with live monitoring and full hardware setup support for irrigation nodes, including utilities and documentation.*

### Added
- [docs/](docs/) directory with detailed documentation on the hardware setup and usage instructions.
- [tools/](tools/) directory with utility scripts for managing the irrigation node (e.g., WiFi monitoring and auto-restart).
- Updated CLI with live dashboard for monitoring the irrigation system status, including:
    - System status and configuration
    - Current cached weather data
    - Current consumption
    - Zone statuses
    - Running irrigation circuits with live progress
    - Log viewer for real-time log output
- Updated `IrrigationCircuit` class to support live progress tracking of irrigation circuits, including:
    - Current and target water amount
    - Elapsed and target watering time
    - Percentage of completion
- Updated `_irrigate()` method in IrrigationCircuit to handle timed irrigation and progress updates using RelayValve.state setter.
- Added inner function in `_irrigate()` for irrigation loop and progress update.

### Changed
- Main loop for automatic irrigation logic is now moved to `IrrigationController` class, allowing for better control and testing and responsibility separation. The loop is now non-blocking, allowing for other tasks to run concurrently.
- The main loop can be turned off, paused, or resumed via the CLI.
- Refactored RelayValve to use `_state` private attribute with a `state` property (getter/setter).
- Introduced private method `_set_gpio_state()` in RelayValve to encapsulate GPIO handling and retries.
- Removed `.open()` method from RelayValve; moved timed irrigation logic to IrrigationCircuit.

### Fixed
- Ensured RelayValve state changes go through property setter for consistent logging and control.

### Removed

### Known Issues
- The `config_global.json` does not contain a `api_enabled` flag, which is required for the `RecentWeatherFetcher` to function correctly. This will be added in the next release.
- `max_flow_monitoring` feature does not work correctly at the moment. This will be addressed in a future release.
- The log viewer in the CLI does not currently show system logs.

---

## [0.2.0] - 2025-08-17
*First hardware-ready release. Added GPIO support and first deployment on Raspberry Pi Zero W for real-world testing.*

### Added
- Command-line interface (CLI) for interactive control of the irrigation system.
    - Non-blocking execution for long-running irrigation processes
    - Provides an interface for testing and monitoring the system over SSH
- Example log outputs for different scenarios in /examples/log_samples/ directory.
- Updated `README.md` with logging examples.
- GPIO support for `RelayValve` class to control irrigation circuits using GPIO pins with fallback to simulated GPIO for testing.

### Changed
- `WeatherSimulator` is now not used in production, nor as a fallback for `RecentWeatherFetcher` in development mode. It is only used when explicitly invoked by disabling use of API in development mode.
- `RecentWeatherFetcher` now uses dictionary for caching weather data, improving performance and simplifying data retrieval.
- Updated `config_global.json` and `zones_config.json` to include `solar_total` and `solar` fields for better solar radiation tracking for irrigation decisions.
- Updated relevant documentation to reflect changes in configuration files and their usage.
- Solar radiation data is now used in the `IrrigationCircuit` for more accurate irrigation decisions based on solar exposure (instead of sunlight hours placeholder).

### Fixed
- RecentWeatherFetcher now handles invalid API secrets gracefully, uses default values (standard weather conditions) when secrets are invalid as a fallback.

### Removed
- Threading support validation in `IrrigationController` as the threading is crucial for the system's operation and should not be disabled.

### Known Issues
- The `config_global.json` does not contain a `api_enabled` flag, which is required for the `RecentWeatherFetcher` to function correctly. This will be added in the next release.

---

## [0.1.1] - 2025-08-07
*Cleanup release improving installation and readability of the prototype.*

### Added
- `requirements.txt` file for managing dependencies.

### Changed
- Refactored `IrrigationController` initialization for better structure, readability and error-handling.
- Updated `README.md` with setup instructions and overview of dependencies.

---

## [0.1.0] - 2025-08-06
*Initial prototype with multi-zone irrigation logic, weather API integration, and configuration files.*


### Added
- Basic runtime entry script `main.py` to start the irrigation system.
- Core logic for multi-zone irrigation based on local and global conditions.
- Main control class `IrrigationController` responsible for managing irrigation circuits and watering schedules
- Configurable global settings stored in `config_global.json` and individual zone configurations in `zones_config.json`.
- Persistent zone state saved in `zones_state.json` to retain circuit statuses across restarts.
- API secrets stored separately in `config_secrets.json` (for development use only).
- Global weather-based irrigation adjustments fetched via `RecentWeatherFetcher` API integration.
- Simulated global weather data generator `WeatherSimulator` for testing and development without live API.
- Multi-level logging system implemented for improved debugging and monitoring.
- Unit test structure with initial test coverage.


