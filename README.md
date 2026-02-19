# Smart Irrigation System

**A distributed IoT system for automated irrigation**, designed for Raspberry Pi–based edge nodes coordinated by a central server and web dashboard.  
The project demonstrates a fully functional **prototype** of a irrigation network with weather-based logic, MQTT communication, and modular architecture.

<table width="100%">
  <tr>
    <td align="center">
      <p>
        <img src="./other/dashboard_v0.9.0_screenshot.png" width="40%" />
        <img src="./other/wizard-1.png" width="40%" />
      </p>
    </td>
  </tr>
</table>

> Project is currently in *Phase 3 (v0.12)* - fundamental node and server functionality is complete, web UI prototype is implemented. Demo is available for local testing.

---

## Overview 

**Architecture Layers**

1. **User Layer** – Web Dashboard for monitoring and manual control of the system. Communicates with the central server via REST API.
2. **Central Server** – Main coordinator handling multiple irrigation nodes via MQTT, configuration & data hub, REST API provider. Runs on Raspberry Pi 4/5 or PC.
3. **Irrigation Nodes** – autonomous controllers managing valves and sensors, fail-safe operation. Runs on Raspberry Pi Zero 2 W.

The Smart Irrigation System uses **edge computing** to manage watering zones autonomously. In case of network failure, each node continues to operate based on local data, schedules, weather conditions and configuration. 
Each **node** controls multiple irrigation circuits, while a **central server** coordinates and monitors the network through MQTT and a REST API.

<div style="display: flex; justify-content: space-between; align-items: center; gap: 20px">
  <div>
    <img src="./other/architecture_0.9.0.svg" alt="0.9 version architecture" title="v0.9 architecture" style="height: 300px";/>
    <p>Fig. 1: Current v0.12 architecture</p>
  </div>
  <div>
    <img src="./other/architecture_target.svg" alt="target architecture" title="target architecture" style="height: 300px";/>
    <p>Fig. 2: Target architecture (v1.0+)</p>
  </div>
</div>

---

## Feature Highlights

### Intelligent Irrigation Control (v0.12+)
- **Pluggable irrigation computation models**:
- **Weather-adaptive watering** using live or simulated weather data.
  - for intelligent per-zone watering volume decision logic based on multiple factors
  - supported factors include: local weather, intervals, correction factors, min/max boundaries, ....
  - Models with custom algorithms can be easily added.
  - *More factors for decision logic planned for future versions (forecast data, soil moisture, evapotranspiration, machine learning, ...).*
- Automatic irrigation scheduling via **AutoIrrigationService**.
- **Multi-zone management** using a modular execution pipeline:
  - **TaskPlanner** for deciding which circuits need irrigation based on configuration and weather data.
  - **Pluggable BatchStrategy** for grouping circuits into execution batches (flow control, sequential/parallel modes, custom strategies).
  - **IrrigationExecutor** running each circuit in isolated worker threads.
- **Zone-specific configuration**: weather conditions sensivity, dripper/soaker hose/sprinkler modes, custom schedules, ...
- **Manual start/stop**.
- **Flow control** to prevent pressure drops & automatic staggering of zones.

### Reliability and Safety
- **Fail-safe design:** Valves are *normally closed* and always close on crash or power loss
- **Local fallback:** Nodes continue operating without server connectivity
- **Thread-safe control:** Each circuit runs in an isolated thread with monitored state
- **Deterministic controller state:** Controller state is derived exclusively from active `IRRIGATION` workers.
- **State recovery:** Nodes store states and logs them in data file to recover after unclean shutdowns
- **Verbose logging:** Detailed local logging at multiple levels for debugging and audit trails + cental collection (planned)

### Security and Robustness
- MQTT communication prepared for TLS support (planned v1.1+)
- Clear separation of configuration, runtime data, and credentials
- Validation and filtering of weather anomalies
- Modular, testable Python codebase with separation of concerns

---

## Configuration & Planning
Configuration of irrigation nodes is managed via the central server and web UI, which store settings in a central database and distribute them to nodes via MQTT.
Node Manager allows users to:
- visually configure irrigation nodes and zones via an intuitive UI,
- define irrigation strategies, limits, and fallback behavior,
- validate domain rules.


## Quick Start (Local Demo)

You can test the full **Node ↔ Server ↔ Web UI** chain on a single computer using a local Mosquitto MQTT broker.

Full instructions are in the [SETUP_AND_RUN_DEMO.md](docs/user_guide/SETUP_AND_RUN_DEMO.md) file.

*Dockerization and deployment setup is planned for the next iterations.*

---

## Roadmap

| Phase | Version | Status | Focus |
|-------|---------|--------|-------|
| 1     | v0.6    | Completed | **Node MVP**: autonomous irrigation logic, MQTT communication, configuration & logging |
| 2     | v0.8    | Completed | **Server prototype**: MQTT communication with single demo node, REST API |
| 3     | v0.9    | Completed | Web UI prototype: basic dashboard for manual control and monitoring (React), REST integration |
| **4**     | **v0.12**    | **Completed** | **Node core redesign**: substantially refactored node controller architecture, stability improvements |
| 5     | v1.0    | *Planned* | **Full architecture MVP**: multi-node support, server-side configuration, log collection, Web UI enhancements |
| 6     | v1.1+   | *Planned* | Stability improvements, refactoring node codebase, security enhancements (TLS, OAuth, credential management) |

---

## Documentation

Full documentation is available in the [docs/](docs/) folder, including:
- [User Guide](docs/user_guide/) – Installation and setup (local all-in-one demo, server, node)
- [Developer Reference](docs/developer_reference/) – Architecture, code structure
- [Architecture Overview](docs/overview/ARCHITECTURE_OVERVIEW.md)
- [Features & Configuration](docs/overview/FEATURES_AND_CONFIG.md)
- [Roadmap](docs/overview/ROADMAP.md)

---

## License

This project is licensed under the [MIT License](./LICENSE) © 2025 Lukáš Soják.

