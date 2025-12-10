# Smart Irrigation System – Features & Configuration

This document provides a **technical overview** of key features, configuration files, and data management mechanisms of the Smart Irrigation System.  
It complements the main [README.md](../../README.md) by offering an in-depth look into how the system works and how to customize it.

---

## Core Functionalities

### 1. Multi-Zone Irrigation Control
Each **edge node** (typically a Raspberry Pi Zero 2 W) manages one or more irrigation zones — each zone corresponding to a relay output that controls a valve.

**Capabilities:**
- Independent settings and weather sensitivity per zone
    - This allows for tailored irrigation strategies based on plant type and location.
    - **Example 1**: *A vegetable garden zone may require more frequent watering than a lawn zone*
    - **Example 2**: *A shaded flower is less affected by solar radiation changes than a sun-exposed area*
- Sequential or parallel operation (configurable globally)
- Adjustable flow balancing to prevent system low pressure (which would affect irrigation precision)


---

### 2. Weather-Based Irrigation (v0.12+)
Since v0.10 the irrigation volume is computed by a pluggable **Weather Irrigation Model**.
The model receives:
- the circuit configuration,
- the last known weather conditions,
- global irrigation limits and correction factors.

The model returns a `WeatherModelResult` containing:
- final target volume,
- bounds (min/max),
- skip flag,
- computation details.

> All computation is isolated in the model layer and can be replaced or extended.

The system dynamically adjusts watering based on recent weather data (forecast support planned for future releases).

**Recent weather data:**
- Real-time weather data is fetched via a weather API.
- The required water volume is computed by Weather Irrigation Model for each zone using **global correction factors** & **per-zone correction factors**.
- If the node is offline or the weather API is unreachable, the system falls back to default irrigation amounts.
- For testing purposes, a built-in **WeatherSimulator** can generate synthetic weather data.

**Weather forecast:**
- In future releases, forecast data will be integrated to further optimize irrigation scheduling.

**Weather Irrigation Model:**
- The current model calculates the required water volume dynamically based on deviations from *standard weather conditions*. The calculation model uses the following logic:
1. **Base target water amount**:
    - Each irrigation node calculates `base_target_water_amount` from the configured `target_mm` (even-area-mode) or `liters_per_minimum_dripper` (dripper-mode). This represend the default water volume needed under standard weather conditions.
2. **Weather condition deltas**:
    - The system computes the difference (delta) between the current weather conditions and predefined standard conditions (delta solar radiation, delta temperature, delta rainfall).
3. **Correction factors**:
    - The system first applies global correction factors (defined in `config_global.json`) to the base target water amount based on the weather deltas.
    - Next, it applies per-zone correction factors (defined in `zones_config.json`) to further adjust the water amount for each specific zone.
4. **Total adjusted water amount**:
    - The final adjusted water amount for each zone is calculated by combining the base target water amount with the effects of both global and per-zone correction factors.

- This model allows for a nuanced and responsive irrigation strategy that adapts to real-time environmental conditions, ensuring optimal water usage.

> The current weather model can be replaced in future releases with more advanced models, including machine learning-based predictions and self-correcting algorithms if feedback data (e.g., soil moisture sensors) is integrated.


---

### 3. Irrigation Logic & Scheduling
- **Automatic daily irrigation:** runs once per day at configurable time.
- **Manual irrigation:** per-zone manual start with water amount can be triggered remotely in Web UI or locally via CLI.
- **Mixed irrigation:** automatic irrigation can run concurrently with manual tasks if conditions allow.
- **Flow control:** automatically distributes irrigation when simultaneous zones would exceed the max flow rate.

**Irrigation modes:**
- **Sequential mode:** zones irrigate one after another based on order in configuration.
- **Concurrent mode:** multiple zones irrigate concurrently.
- **Hybrid mode:** if *flow control* is enabled, zones irrigate concurrently up to the max flow rate; the zones are batched accordingly by pluggable `BatchStrategy`.

> The flow control feature is not supported since v0.12, as the current batching strategy is single-batch only. Future releases will reintroduce this feature with advanced batching strategies.

> Since v0.12 irrigation is executed using a dedicated modular pipeline:

1. **AutoIrrigationService**
   - periodically checks the scheduled time,
   - requests automatic irrigation when conditions are met.

2. **TaskPlanner + BatchStrategy**
   - selects circuits that need irrigation today,
   - groups them into batches according to strategy (currently single-batch),
   - supports future sequential/concurrent/hybrid batching.

3. **IrrigationExecutor**
   - Starts irrigation based on planned batches,
   - each circuit is executed in its own IRRIGATION worker thread.

*Automatic and manual irrigation run entirely non-blocking, each in separate executor workers.*


**Controller states:**
| State | Description |
|--------|-------------|
| `IDLE` | System ready, no irrigation in progress |
| `IRRIGATING` | One or more zones actively irrigating |
| `STOPPING` | Irrigation stopping in progress |
| `ERROR` | System failure, all valves closed for safety |

**Zone states:**
| State | Description |
|--------|-------------|
| `IDLE` | Zone ready, not irrigating |
| `IRRIGATING` | Zone actively irrigating |
| `WAITING` | Zone queued for irrigation |
| `DISABLED` | Zone disabled via config |
---

### 4. Safety & Reliability
- **Fail-safe valves:** all valves are normally closed (`NC` type). On crash or power loss → system defaults to closed valves.
- **Thread isolation:** each irrigation zone runs inside an IRRIGATION worker thread started by `IrrigationExecutor`.
- **State persistence:** zone states (`zones_state.json`) are saved and restored after restart.
- **Unclean shutdown recovery:** interrupted irrigation sessions are logged and marked as “interrupted”.
- **Error detection:** system monitors for common errors (e.g., weather API failure) and logs them.
- *Watchdog thread and health checks planned for future releases.*
- *Heartbeat mechanism between nodes and server planned for future releases.*

---

### 5. Data Logging & Monitoring
- Local node logs all events in `/runtime/node/logs/` (`system_log.log`).
- Irrigation runs are recorded in `irrigation_log.json` (time, duration, water volume, weather conditions). All irrigation attempts are logged, including interrupted or failed sessions.
- Server aggregates node state and provides summary via `/api/nodes`.
- Web UI displays live node state, last update time.
- *Central log aggregation planned for future releases.*

**Log levels:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (level configurable in `config_global.json`).

---

## Configuration Files

All configuration and runtime data is stored as JSON files, located in the `runtime/` directory.  
Each node and server has its own configuration space.

### Node Configuration Files

> In stable releases, configuration files will be handled by the server and pushed to nodes remotely.

#### `config_global.json`
Defines global system behavior and environmental parameters.

**1. Definition of standard weather conditions:**
Reference values for weather parameters under which base irrigation amounts are considered optimal.

| Parameter | Value | Description |
|-----------|-------|-------------|
| `solar_total` | `6.5` | Total solar radiation (kWh/m²/day) |
| `temperature_celsius` | `17.0` | Average temperature since last irrigation (°C) |
| `rainfall_mm` | `0.0` | Standard daily rainfall (mm) |

**2. Correction factors for weather adjustments:**
Coefficients that determine how deviations from standard conditions affect irrigation amounts.
- Positive values indicate **direct proportionality** (more = more irrigation).
- Negative values indicate **inverse proportionality** (more = less irrigation).

| Parameter | Type | Description |
|-----------|-------|-------------|
| `solar` | `0.05` | % change per kWh/m² deviation |
| `rain` | `-0.15` | % change per mm deviation |
| `temperature` | `0.1` | % change per °C deviation |

*Example:* A `rain` factor of `-0.15` means that for every additional mm of rainfall above the standard, the irrigation amount is reduced by 15%.

**3. Irrigation limits:**
| Parameter | Value | Description |
|-----------|-------|-------------|
| `min_percent` | `20` | Minimum irrigation percentage (e.g., 20% of base amount) |
| `max_percent` | `300` | Maximum irrigation percentage (e.g., 300% of base amount) |
| `main_valve_max_flow` | `1000` | Max total flow rate for the node (liters per hour) |

**4. Automation settings:**
| Key | Type | Description |
|-----|------|-------------|
| `auto_enabled` | `bool` | Enables automatic irrigation on schedule |
| `scheduled_hour` | `int` | Hour of day for automatic irrigation (0-23) |
| `scheduled_minute` | `int` | Minute of hour for automatic irrigation (0-59) |
| `max_flow_monitoring` | `bool` | Enables flow rate monitoring during concurrent irrigation |
| `environment` | `string` | `"development"` or `"production"` |
| `use_weathersimulator` | `bool` | Use simulated weather (for testing) |

**4.1 Automation settings (planned):**
| Key | Type | Description |
|-----|------|-------------|
| `server_offline_fallback` | `string` | Strategy when server is unreachable (`node_weather_fetcher`, `weather_offline_fallback`) |
| `weather_offline_fallback` | `string` | Strategy when weather data is unavailable (`disabled`, `history_based`, `base_volume`, `half_base_volume`) |
| `use_flow_sensor` | `bool` | Enable real-time flow sensor integration |
| `flow_sensor_pin` | `int` | GPIO pin for flow sensor input |
| `water_network_health_monitoring` | `bool` | Enable water network health checks using flow sensor data (leak detection, valve failures, ..) |

**5. Logging settings:**
| Key | Type | Description |
|-----|------|-------------|
| `enabled` | `bool` | Enables or disables logging |
| `log_level` | `string` | Logging verbosity level (e.g., `DEBUG`, `INFO`) |

**6. Weather API settings:**
| Key | Type | Description |
|-----|------|-------------|
| `realtime_url` | `string` | Endpoint for real-time weather data |
| `history_url` | `string` | Endpoint for historical weather data |

> *In future versions, support for multiple weather APIs and forecast data will be added.*
---

#### `zones_config.json`
Contains per-zone configuration (one entry per irrigation circuit).

| Key | Type | Description |
|-----|------|-------------|
| `id` | `int` | Unique ID of the zone |
| `name` | `string` | Zone label |
| `relay_pin` | `int` | GPIO pin controlling valve relay |
| `enabled` | `bool` | Enables or disables zone |
| `even_area_mode` | `bool` | Water calculation model: `true` = even-area-mode, `false` = dripper-mode |
| `zone_area_m2` | `float` | Area of the zone in square meters (only for even-area-mode) |
| `target_mm` | `float` | Target irrigation in mm of water (only for even-area-mode) |
| `liters_per_minimum_dripper` | `float` | Liters per minimum dripper (only for dripper-mode) |
| `interval_days` | `int` | Days between irrigations |
| `drippers_summary` | `dict: string->int` | Summary of dripper types (l/h) and counts in zone (only for dripper-mode) |
| `local_correction_factors` | `dict: string->float` | Per-zone weather correction factors |

> *Planned future additions:*
dynamic `interval_days` based on minimum `irrigation_volume_threshold` and recent weather, not irrigated water volume is carried over to next irrigation cycle. This allows for adaptive irrigation frequency to avoid frequent small irrigations when weather conditions are not optimal.

---

#### `zones_state.json`
Persistent state file, automatically maintained by the system.

| Key | Description |
|-----|--------------|
| `id` | Unique ID of the zone |
| `circuit_state` | Current state of the zone (`IDLE`, `IRRIGATING`, `WAITING`, `DISABLED`) |
| `last_decision` | Timestamp of last irrigation decision |
| `last_outcome` | Outcome of last irrigation (`SUCCESS`, `FAILED`, `STOPPED`, `INTERRUPTED`, `SKIPPED`, `null`) |
| `last_irrigation` | Timestamp of last watering |
| `last_duration` | Duration of last watering (seconds) |
| `last_volume` | Volume of water applied during last watering (liters) |

>*Refactor planned to allow better state management. Renaming to `node_state.json` and including both per-zone and per-node state.*
 *Planned future additions:*
 > - `pending_irrigation_volume`: Volume scheduled for next irrigation based on recent weather but not yet irrigated (dynamic scheduling).
 > - `last_irrigation_start_time`: Timestamp of last completed irrigation start.
 > - `last_irrigation_end_time`: Timestamp of last completed irrigation end.


---

#### `config_secrets.json`
Stores credentials and private keys for third-party APIs (excluded via `.gitignore`).

| Key | Description |
|------|-------------|
| `api_key` | API key for weather provider |
| `application_key` | Application token for weather provider |
| `device_mac` | MAC address of the connected weather station |

>⚠️ *In production, credentials should be loaded from environment variables instead of local files. This will be implemented in future versions.*

---

### Server Configuration Files

*Currently, the server does not have dedicated configuration files. All settings are hardcoded for prototype purposes. In future versions, a `server_config.json` file will be introduced to manage server settings such as MQTT broker details, REST API settings, and node management parameters.*

### 6. Communication & Networking
The system uses:
- **MQTT** for Node ↔ Server communication
- **REST API** for UI ↔ Server integration.

#### MQTT Topics

> *Note: <node_id> is string identifier of the node, e.g., `node1`*

| Direction | Topic | Payload | Notes |
|------------|--------|----------|------|
| Node → Server | `irrigation/<node_id>/status` | JSON with controller state, zones, auto/paused flags | |
| Server → Node | `irrigation/<node_id>/start_irrigation` | JSON with zone_id and volume (liters) | Triggers manual irrigation on specified zone |
| Server → Node | `irrigation/<node_id>/stop_irrigation` | Empty | Stops all irrigation on the node |
| Server → Node | `irrigation/<node_id>/get_status` | Empty | Requests node to send current status |

---