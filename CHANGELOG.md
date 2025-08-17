# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

### Known Issues
- The `config_global.json` does not contain a `api_enabled` flag, which is required for the `RecentWeatherFetcher` to function correctly. This will be added in the next release.

---

## [0.2.0] - 2025-08-17

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

### Added
- `requirements.txt` file for managing dependencies.

### Changed
- Refactored `IrrigationController` initialization for better structure, readability and error-handling.
- Updated `README.md` with setup instructions and overview of dependencies.

---

## [0.1.0] - 2025-08-06

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


