# MQTT Reference (v1 Contract)

This document defines the MQTT contract used by the Smart Irrigation System for server-node communication.

## Goals

- Provide stable and versioned message exchange for MVP.
- Support live runtime projection for UI (`/api/v1/runtime/live`).
- Support command dispatch from server to node.
- Support configuration push from server to node.
- Keep temporary compatibility with legacy topics during migration.

## Version

- Contract version: `1`
- Namespace prefix: `sis/v1`

## Topics

### Node -> Server

- `sis/v1/nodes/{node_id}/status`
	- `NODE_STATUS_SNAPSHOT`
- `sis/v1/nodes/{node_id}/event`
	- reserved for future event stream
- `sis/v1/nodes/{node_id}/ack`
	- `NODE_ACK`
- `sis/v1/nodes/{node_id}/error`
	- `NODE_ERROR`

### Server -> Node

- `sis/v1/nodes/{node_id}/command`
	- `CMD_GET_STATUS`
	- `CMD_START_IRRIGATION`
	- `CMD_STOP_IRRIGATION`
- `sis/v1/nodes/{node_id}/config`
	- `CMD_APPLY_CONFIG`

### Legacy migration topics (temporary)

- `irrigation/{node_id}/command`
- `irrigation/{node_id}/status`

## Envelope

All v1 messages use a common envelope.

```json
{
	"version": 1,
	"message_id": "uuid-v4",
	"message_type": "CMD_GET_STATUS",
	"node_id": "node1",
	"sent_at": "2026-03-30T10:10:10Z",
	"correlation_id": null,
	"payload": {}
}
```

### Envelope fields

- `version` (int): must be `1`.
- `message_id` (string): unique UUID v4 for tracing.
- `message_type` (string): see message types below.
- `node_id` (string): target/source node identifier.
- `sent_at` (ISO 8601 UTC string).
- `correlation_id` (string|null): links response to request.
- `payload` (object): type-specific content.

## Message types

### Commands (server -> node)

#### `CMD_GET_STATUS`

Topic: `.../command`

Payload:

```json
{
	"include_alerts": true,
	"include_tasks": true
}
```

Expected behavior:

1. Node publishes `NODE_STATUS_SNAPSHOT`

Note: `CMD_GET_STATUS` does not emit `NODE_ACK` in MVP to reduce message noise.

#### `CMD_START_IRRIGATION`

Topic: `.../command`

Payload:

```json
{
	"zone_id": 3,
	"liter_amount": 12.5
}
```

Expected behavior:

1. Node publishes `NODE_ACK` (`accepted`)
2. Node starts manual irrigation for specified zone and amount
3. Node publishes `NODE_ACK` (`completed`)

#### `CMD_STOP_IRRIGATION`

Topic: `.../command`

Payload:

```json
{}
```

Expected behavior:

1. Node publishes `NODE_ACK` (`accepted`)
2. Node stops all irrigation tasks
3. Node publishes `NODE_ACK` (`completed`)

#### `CMD_APPLY_CONFIG`

Topic: `.../config`

Payload:

```json
{
	"config_revision": "2026-03-30T10:10:10Z",
	"apply_mode": "apply_now",
	"legacy_runtime_config": {
		"config_global": {},
		"zones_config": { "zones": [] }
	},
	"requested_by": "configuration-api"
}
```

`apply_mode` values:

- `validate_only`
- `apply_now`

Expected behavior:

1. Node publishes `NODE_ACK` (`accepted`)
2. Node validates/writes `config_global.json` + `zones_config.json`
3. Node publishes `NODE_ACK` (`applied`) or `NODE_ERROR`

Note: runtime in-place reload is currently not implemented in `ControllerCore`; this command writes files only.

### Telemetry (node -> server)

#### `NODE_STATUS_SNAPSHOT`

Topic: `.../status`

Payload:

```json
{
	"controller_state": "irrigating",
	"auto_enabled": true,
	"auto_paused": false,
	"zones": [
		{
			"zone_id": 1,
			"zone_name": "Zone 1",
			"status": "irrigating",
			"enabled": true,
			"progress_percent": 42.5,
			"last_run": null,
			"updated_at": "2026-03-30T10:10:10Z"
		}
	],
	"current_tasks": [
		{
			"task_id": 1,
			"zone_id": 1,
			"zone_name": "Zone 1",
			"progress_percent": 42.5,
			"current_volume": 10.2,
			"target_volume": 24.0,
			"remaining_minutes": 7,
			"updated_at": "2026-03-30T10:10:10Z"
		}
	],
	"alerts": []
}
```

`zones[].status` values (v1):

- `idle`
- `irrigating`
- `waiting`
- `error`
- `stopping`
- `offline`

### Responses (node -> server)

#### `NODE_ACK`

Topic: `.../ack`

Payload:

```json
{
	"ack_type": "accepted",
	"for_message_type": "CMD_GET_STATUS",
	"details": {}
}
```

`ack_type` values:

- `accepted`
- `applied`
- `completed`

MVP ACK policy:

- ACK is emitted only for mutating commands:
	- `CMD_START_IRRIGATION`
	- `CMD_STOP_IRRIGATION`
	- `CMD_APPLY_CONFIG`
- `CMD_GET_STATUS` does not emit ACK.

#### `NODE_ERROR`

Topic: `.../error`

Payload:

```json
{
	"code": "INVALID_PAYLOAD",
	"message": "zone_id and liter_amount are required",
	"retryable": false,
	"details": {}
}
```

## Correlation rules

- For `NODE_ACK` and `NODE_ERROR`, `correlation_id` must equal request `message_id`.
- Telemetry messages (`NODE_HEARTBEAT`, `NODE_STATUS_SNAPSHOT`) use `correlation_id = null`.

## QoS recommendations (MVP)

- `CMD_*`: QoS 1
- `NODE_ACK` / `NODE_ERROR`: QoS 1
- `NODE_STATUS_SNAPSHOT`: QoS 1
- `NODE_HEARTBEAT`: QoS 0
- Retain: `false` for all current v1 messages

## Timing recommendations (MVP)

- Status snapshot interval: 5 s
- Server fallback `CMD_GET_STATUS`: on-demand by default (periodic polling disabled)
- Optional periodic fallback polling can be enabled with:
  - `MQTT_ENABLE_STATUS_POLLING=true`
  - `MQTT_STATUS_POLL_INTERVAL_SECONDS=10`
- Runtime service defaults:
	- `connecting_timeout`: 30 s
	- `stale_timeout`: 20 s
	- `offline_timeout`: 60 s

## Live store integration (server)

Server MQTT manager updates `RuntimeLiveStore` as follows:

- `NODE_STATUS_SNAPSHOT.zones[]` -> `upsert_zone_state(...)`
- `NODE_STATUS_SNAPSHOT.current_tasks[]` -> `upsert_current_task(...)`
- `NODE_STATUS_SNAPSHOT.alerts[]` -> `add_alert(...)` (deduplicated by level/title/message/timestamp)

Note: In MVP snapshot-only mode, node liveness is derived from `NODE_STATUS_SNAPSHOT.sent_at`.

This enables `/api/v1/runtime/live` to return system-wide live projection using stale/offline/connecting logic.

## Backward compatibility notes

- Existing legacy command API (`action` style) is still supported by adapter methods.
- Existing legacy topics are subscribed/handled during transition.
- Legacy compatibility should be removed in a future minor release after all clients migrate to `sis/v1`.
