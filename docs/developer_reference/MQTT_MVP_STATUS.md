# MQTT MVP Status

## Scope

This document summarizes the current MVP state of MQTT communication in Smart Irrigation System, including what is implemented, what is still pending, and recommended next steps.

Related contract specification:
- See `docs/developer_reference/MQTT_REFERENCE.md` for full message and topic definitions.

## Current MVP State

### Implemented

1. Versioned MQTT contract namespace (`sis/v1`) is implemented on both server and node side.
2. Common envelope and message type definitions are centralized in shared module (`smart_irrigation_system/common/mqtt_contract.py`).
3. Server MQTT manager was replaced with v1 contract-aware implementation.
4. Node MQTT client was replaced with v1 contract-aware implementation.
5. Runtime live projection is fed from MQTT telemetry through `RuntimeLiveStore`.
6. Configuration push command (`CMD_APPLY_CONFIG`) is available via configuration API endpoint:
   - `POST /api/v1/nodes/{node_id}/push-config`
7. Node can write received legacy runtime config payload into:
   - `runtime/node/config/config_global.json`
   - `runtime/node/config/zones_config.json`
8. Legacy compatibility bridge remains available (temporary):
   - old `irrigation/...` topics
   - old action-based command adapter

### Message flows currently working

1. Server -> Node command flow:
   - `CMD_GET_STATUS`
   - `CMD_START_IRRIGATION`
   - `CMD_STOP_IRRIGATION`
   - `CMD_APPLY_CONFIG`
2. Node -> Server telemetry flow:
   - `NODE_STATUS_SNAPSHOT`
3. Node -> Server response flow:
   - `NODE_ACK`
   - `NODE_ERROR`

ACK policy (MVP):

1. ACK is sent only for mutating commands:
   - `CMD_START_IRRIGATION`
   - `CMD_STOP_IRRIGATION`
   - `CMD_APPLY_CONFIG`
2. `CMD_GET_STATUS` does not emit ACK (status snapshot only).

### Runtime integration state

1. Server updates in-memory runtime state from MQTT messages:
   - node liveness derived from status snapshot timestamps
   - zone live states
   - current tasks
   - alerts
2. Live API (`/api/v1/runtime/live`) is based on runtime projection with:
   - online/offline evaluation
   - stale evaluation
   - connecting bootstrap state

## Known Gaps and Limitations

1. `ControllerCore` runtime config reload is not implemented yet.
   - `CMD_APPLY_CONFIG` currently writes files but does not fully apply config in-process.
2. ACK and ERROR handling is currently logged but not persisted into dedicated tracking storage.
3. Task removal semantics are basic (upsert-only approach in MVP).
4. Legacy compatibility code still exists and should be removed later.
5. End-to-end retry policy for failed config apply is not yet formalized.
6. Auth/TLS/security for MQTT transport is not part of MVP.

## Recommended Next Steps

### Phase 1: Stabilize command lifecycle

1. Implement config apply lifecycle states on server side:
   - accepted
   - applying
   - applied
   - failed
2. Store command outcomes by `message_id` and `correlation_id`.
3. Add API endpoint to query command delivery/apply status.

### Phase 2: Runtime reload support on node

1. Implement `ControllerCore.reload_config(...)` with safe validation and rollback.
2. For `CMD_APPLY_CONFIG` with `apply_now`:
   - write files
   - validate
   - apply in runtime
   - send `NODE_ACK` (`applied`) only after successful reload
3. Return structured `NODE_ERROR` details on failure.

### Phase 3: Hardening and cleanup

1. Add reconnect backoff strategy and optional jitter.
2. Add deduplication strategy for repeated command processing.
3. Improve task cleanup semantics in runtime store.
4. Remove legacy `irrigation/...` compatibility once all components use `sis/v1`.

### Phase 4: Security and operations

1. Add broker authentication and topic ACL strategy.
2. Add TLS for production transport.
3. Add message signing or integrity checks if required by deployment model.
4. Add MQTT observability metrics (publish errors, latency, reconnect counts, ACK timing).

## Operational Notes (MVP)

1. Recommended intervals:
   - status snapshot: 5 seconds
   - server fallback status request: on-demand by default
2. Optional periodic server fallback polling can be enabled with:
   - `MQTT_ENABLE_STATUS_POLLING=true`
   - `MQTT_STATUS_POLL_INTERVAL_SECONDS=10`
3. Runtime live defaults:
   - connecting timeout: 30 seconds
   - stale timeout: 20 seconds
   - offline timeout: 60 seconds
4. During migration period, keep legacy and v1 flows running in parallel.
5. Before disabling legacy topics, verify all deployments publish and subscribe only to `sis/v1` topics.

## Migration Exit Criteria

Legacy MQTT compatibility can be removed when all criteria below are true:

1. No active publisher/subscriber uses `irrigation/{node_id}/...` topics.
2. Server command API uses v1 envelope-only path.
3. Node responds with `NODE_ACK`/`NODE_ERROR` for all v1 command types.
4. `CMD_APPLY_CONFIG` has full runtime apply support and rollback path.
5. Integration tests validate reconnect and command correlation behavior.

## Quick Verification Checklist

1. Node connects and subscribes to v1 command/config topics.
2. Server receives heartbeat and status snapshots.
3. Live dashboard updates from runtime store.
4. Manual irrigation command triggers and returns ACK.
5. Config push writes node config files and returns ACK or ERROR.
6. No envelope validation errors in logs under normal traffic.
