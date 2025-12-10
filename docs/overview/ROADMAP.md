# Smart Irrigation System – Roadmap

This document outlines the development roadmap of the **Smart Irrigation System**, including historical milestones and future goals.  
The project follows a modular **Hub & Spoke architecture** with **edge computing** nodes (Raspberry Pi Zero W / Zero 2 W) and a central server (Raspberry Pi 4/5).

---

## Phase 4 – Full architecture MVP (v1.0.0, in progress)

**Goal:**  
Complete the full stable architecture of the Smart Irrigation System, integrating multiple autonomous nodes with a central server and web-based dashboard.

**Planned features:**
- [ ] Optimize MQTT communication for advanced dashboard features
- [ ] Enhance web UI with real-time updates (periodic polling, later WebSockets or Server-Sent Events), full zones vizualization with live progress, extended irrigation controls and settings
- [ ] Implement multi-node support in the server and web UI
- [ ] Move configuration management (JSON) to the server side and implement remote configuration updates to nodes

---

## Phase 3.5 – Node Architecture Refactor (v0.12.0, December 2025)

**Goal:**  
Replace the legacy monolithic `IrrigationController` with a fully modular, testable, and reliable
edge-node architecture designed for multi-node scalability and real-time control.

**Highlights:**
- Introduced new modular controller subsystem (`ControllerCore`) composed of:
  - **ThreadManager** – unified and safe worker lifecycle manager  
  - **IrrigationExecutor** – dedicated execution layer for manual & automatic irrigation  
  - **TaskPlanner + BatchStrategy** – irrigation planning and pluggable batching strategies
  - **TaskScheduler** – cron-like scheduling of periodic background tasks
  - **StatusAggregator** – unified runtime + snapshot status model  
  - **AutoIrrigationService** – scheduled automatic irrigation orchestration  
- Controller state machine redesigned:
  - State now derived exclusively from active irrigation workers  
  - Deterministic transitions (`IDLE → IRRIGATING → STOPPING → IDLE` or `ERROR`)  
- Fully non-blocking irrigation execution (each circuit in its own IRRIGATION worker)
- Improved safe shutdown (executor stop, worker joining, final valve checks)
- Backward compatibility preserved via `LegacyControllerAPI`

**Outcome:**  
A robust, scalable, and testable node architecture that forms the basis for the upcoming
multi-node system and full dashboard integration in Phase 4.

---

## Phase 3 – Web UI prototype (v0.9.0, October 2025)

**Goal:**  
Develop a minimal web-based dashboard for system control and monitoring. This will complete the first full iteration of the Smart Irrigation System.

**Highlights:**
- React frontend prototype (basic layout and REST API integration)
- Implemented live node status table (`GET /nodes`)
- Implemented manual irrigation control (`POST /start_irrigation`, `POST /stop_irrigation`)
- Implemented dashboard refresh button (manual polling)
- Connected frontend to backend REST API.

---

## Phase 2 – Server prototype (v0.8.0, October 2025)

**Goal:**  
Build the central coordination layer between irrigation nodes and a unified control interface.

**Highlights:**
- Implemented central server (`IrrigationServer`) to manage multiple nodes.
- Bidirectional MQTT communication with nodes.
- Introduced `NodeRegistry` for tracking and storing node runtime information.
- Added REST API (FastAPI) for external integration:
  - `GET /nodes` – list all nodes and their statuses  
  - `POST /update_status` – trigger MQTT status refresh  
  - `POST /start_irrigation` – start manual irrigation  
  - `POST /stop_irrigation` – stop all irrigation  
  - `GET /ping` – health check

**Outcome:**  
The server can monitor, control, and update nodes (prototype supports only one hardcoded node).
It acts as the foundation for Web UI integration and future analytics.

---

## Phase 1 – Node MVP (v0.6.0, October 2025)

**Goal:**  
Create a fully autonomous irrigation node capable of controlling multiple irrigation zones independently, with weather-based logic, persistent state tracking and fail-safe design.

**Highlights:**
- Implemented `IrrigationController` as a central manager for multi-zone control and scheduling.
- Added weather-based irrigation logic (`RecentWeatherFetcher`, `WeatherSimulator`).
- Introduced runtime state tracking (`CircuitStateManager`, JSON persistence).
- Added multi-threaded irrigation with per-zone state isolation.
- Implemented manual and automatic irrigation modes.
- Added command-line interface (`IrrigationCLI`) for local debugging.
- Introduced verbose logging system for debugging and diagnostics.

**Outcome:**  
A standalone, Raspberry-Pi-ready irrigation node that can automatically water zones based on weather and schedule.  
The node runs autonomously and can recover from unclean shutdowns.

*MVP of the edge-computing node completed.*

---

