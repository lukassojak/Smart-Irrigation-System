# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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


