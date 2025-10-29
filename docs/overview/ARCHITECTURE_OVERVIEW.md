# Smart Irrigation System – Architecture Overview

This document provides an overview of the **system architecture**, component responsibilities, and data flow in the *Smart Irrigation System*.  
The architecture is designed around **edge computing** principles — distributing logic across lightweight Raspberry Pi nodes coordinated by a central server.

---

## System Overview

The system consists of three main layers:

1. **User Layer (UI / Integration)**  
   – Web Dashboard (React), Home Assistant integration, REST API clients.

2. **Central Server Layer (Coordinator)**  
   – Runs on Raspberry Pi 4/5.  
   – Provides MQTT-based coordination, REST API, and system state aggregation.

3. **Edge Node Layer (Autonomous Controllers)**  
   – Runs on Raspberry Pi Zero 2 W.  
   – Controls local irrigation zones independently, with weather-based adjustments and local fallback.

---

## High-Level Architecture Diagram

```text
                    ┌────────────────────────────────────────┐
                    │            User Layer                  │
                    │ ────────────────────────────────────── │
                    │  • Web Dashboard (React + REST)        │
                    │  • Home Assistant Integration (planned)│
                    │  • CLI Interface                       │
                    └────────────────────────────────────────┘
                                   │       ▲
                                   │REST   │JSON
                                   ▼       │
                    ┌────────────────────────────────────────┐
                    │         Central Server Layer           │
                    │ ────────────────────────────────────── │
                    │  • MQTT Manager (Server ↔ Nodes)       │
                    │  • Node Registry (state tracking)      │
                    │  • Zone–Node Mapper                    │
                    │  • REST API                            │
                    └────────────────────────────────────────┘
                                   │       ▲
                            MQTT   │       │  MQTT
                                   ▼       │
                    ┌────────────────────────────────────────┐
                    │           Edge Node Layer              │
                    │ ────────────────────────────────────── │
                    │  • IrrigationController                │
                    │  • IrrigationCircuits (per-zone)       │
                    │  • WeatherFetcher / WeatherSimulator   │
                    │  • CircuitStateManager (JSON state)    │
                    │  • MQTT Client (status + commands)     │
                    └────────────────────────────────────────┘
```

## Component Responsibilities

### User Layer (Web UI)
Provides a simple, user-friendly interface for monitoring and controlling the irrigation system. Communicates with the Central Server via REST API.

**Features (prototype):**
- Display all the nodes with their statuses:
    - node online/offline
    - node state last update
    - controller state
    - auto mode enabled/disabled
    - currently irrigating zones
- Manual control panel:
    - Start irrigation on selected zones
    - Stop all irrigation
- Refresh button to update the dashboard data (manual polling)
- Periodic polling for live status
- REST API integration using Axios

**Planned extensions:**
- Real-time updates (Server-Sent Events or WebSockets)
- Zone visualization panel with live progress
- Weather overview panel
- Node and zone configuration management
- Log viewing and export

### Central Server Layer
Acts as the central coordinator for multiple irrigation nodes. Manages MQTT communication, aggregates node states, and exposes a REST API for external clients.

**Main responsibilities:**
- Manage communication with multiple nodes via MQTT
- Expose REST API endpoints for the frontend and other clients
- Store and aggregate node runtime information in `NodeRegistry`
- Broadcast commands to nodes (e.g., start/stop irrigation)
- Provide configuration management (planned)
- Monitor node activity and health

**Key modules:**
- `IrrigationServer`: Orchestrates server lifecycle, integrates all subsystems
- `MQTTManager`: Manages MQTT connection and subscribes to node status topics
- `NodeRegistry`: Tracks registered nodes and their runtime states
- `ZoneNodeMapper`: Maps zones to their respective nodes to abstract multi-node control (planned)
- `FastAPI routes`: Implements REST API endpoints for node management and control

**REST API endpoints**
REST API reference will be continuously documented in file [docs/developer_reference/API_REFERENCE.md](../developer_reference/API_REFERENCE.md). Below is a summary of the main endpoints available in the current prototype:

| Method | Endpoint | Description |
|--------|-----------|-------------|
| `GET` | `/api/` | Root endpoint |
| `GET` | `/api/nodes` | Returns all registered node states cached on server |
| `POST` | `/api/update_status` | Requests all nodes to send current status |
| `POST` | `/api/start_irrigation` | Starts manual irrigation for selected zone |
| `POST` | `/api/stop_irrigation` | Stops irrigation on all nodes |
| `GET` | `/api/ping` | Health check endpoint |

### Edge Node Layer
Each node is a self-contained irrigation controller with:
- **Independent decision-making**: Runs local schedules and applies weather-based adjustments.
- **Autonomy**: Continues operating even if disconnected from the server or internet connectivity is lost.
- **MQTT communication**:
    - Publishes its current status to the server
    - Subscribes to commands from the server
- **Data persistence**:
    - Zone and controller state states stored in `runtime/node/data/`
    - Irrigation records stored in `runtime/node/data/`
    - Logs stored in `runtime/node/logs/`

**MQTT Topics**
| Topic | Direction | Description |
|-------|-----------|-------------|
| `/irrigation/{node_id}/status` | Node → Server | Node publishes its current status |
| `/irrigation/{node_id}/command` | Server → Node | Server issues control commands to node. Commands include: `start_irrigation`, `stop_irrigation`, `get_status` |

## Safety & reliability principles

**1. Fail-safe design:**
- Normally closed valves that close on power loss or crash
- Thread-safe operation with isolated zone threads
- State recovery on restart
- Wifi watchdog to auto-restart wifi module on connectivity loss and auto-reboot on repeated failures
- *Watchdog thread to monitor main thread health and auto-restart on unresponsiveness (planned)*
- *Heartbeat messages to server to indicate node health (planned)*
- *Running as a systemd service to ensure automatic startup on crash/reboot (planned)*

**2. Autonomous edge logic:**
- Each node operates using local schedules and last known configuration.
- On server disconnection or internet loss, nodes continue irrigation based on configuration.

**3. Data persistence & recovery:**
- State file `zones_state.json` enables the system to resume with consistent data after unclead shutdowns.

**5. Validation:**
- *Weather data and sensor readings are checked for anomalies or extreme values (planned)*

---

## Data Flow

| Direction | Transport | Description |
|-----------|-----------|-------------|
| Node → Server | MQTT `/status` | Node publishes its current status |
| Server → Node | MQTT `/command` | Server issues control commands to nodes |
| Server ↔ Web UI | REST API | Web UI polls or receives updates |
| Node ↔ Weather API | HTTPS | Node fetches weather data |

> **Note:** In current prototype, the Weather API calls are performed by each node independently. In the full architecture MVP, weather fetching will be centralized on the server to reduce API calls and ensure consistency.