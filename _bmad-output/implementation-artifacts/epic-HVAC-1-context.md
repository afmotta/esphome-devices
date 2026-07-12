# Epic HVAC-1 Context: HVAC CAN Sensor Receiver

<!-- Generated from planning artifacts. Regenerate with compile-epic-context if planning docs change. -->
<!-- Updated 2026-07-11 for the scope clarifications recorded in HVAC-Epic-1-can-sensor-receiver.md:
     existing CAN nodes are the sensor sources (no new nodes created); the climate controller
     receives CAT_SENSOR directly on its own CAN interface (ADR-0014); the lighting/canbus
     gateway carries no sensor-data role. -->

## Goal

Implement the HVAC-owned CAN sensor receiver so production room-sensor data flows from the existing CAN sensor-kit nodes into the central climate controller, becomes visible in Home Assistant, and drives room climate control through the existing failover abstraction. The target production failover order is CAN (primary) -> Home Assistant (secondary) -> Emergency shutdown. The climate controller (T-Connect Pro) receives `CAT_SENSOR` frames **directly on its own native CAN interface** (ADR-0014); the existing registry nodes are the only frame sources (enabling a room is a registry edit — `sensors=1` + valid `room_slug` — plus regeneration, never new hardware); the lighting/canbus gateway (`devices/gateway.yaml`) is not involved and not modified. This epic turns the frozen spec, as amended by the 2026-07-11 scope clarifications, into six implementable slices: generated routing, receiver publish-only behavior, control failover migration, MEV air-quality demand migration, and verification/bench validation.

## Stories

- HVAC-1.1: Generated CAN Sensor Routing Artifact (done)
- HVAC-1.2: Sensor-Only CAN Receiver and Freshness Core
- HVAC-1.3: Climate Controller Publish-Only Composition
- HVAC-1.4: CAN-Primary Room Sensor Failover
- HVAC-1.5: CAN Air-Quality MEV Demand Integration
- HVAC-1.6: Verification Battery and Bench Rollout

## Requirements & Constraints

**Sensor Routing and Validation**: Sensor-equipped CAN nodes must be routed to valid HVAC room slugs by compile-time generated artifacts. The generator rejects any node with an empty room slug or an invalid join to a real room package. Regeneration must be byte-identical when inputs are unchanged.

**Receiver Scope and Behavior**: The receiver package defines the climate controller's own CAN bus interface (receive-only — it sends no frames) and handles `CAT_SENSOR` environmental frames only; it ignores button events, heartbeats, and transport-health categories, which remain the lighting/canbus gateway's handlers. No new CAN nodes are created: existing registry nodes are the only frame sources, and `devices/gateway.yaml` plus the gateway-side packages are untouched. Payload validation covers minimum length, protocol version, status byte, measurement type, and node ID. Valid measurements with `SENSOR_STATUS_OK` are published as room-scoped CAN source sensors; non-OK statuses and unknown routes publish `NaN` without logging noise.

**Freshness and Failover**: Freshness is tracked per room measurement on the controller (state behind a header accessor — ESPHome globals cannot hold custom structs); 90 seconds without an OK frame publishes `NaN` for that source sensor. This threshold drives the existing Vesta failover component to transition from CAN to Home Assistant automatically — and because a controller-side CAN interface or bus fault stops all routes refreshing, the same mechanism covers bus loss. When both CAN and HA are unavailable, the abstracted sensor becomes `NaN` and existing emergency behavior engages.

**Entity Contract**: Raw CAN source sensors are published to Home Assistant using room-slug naming (e.g., `<room_slug>_temp_can`, `<room_slug>_co2_can`, `<room_slug>_voc_index_can`, `<room_slug>_pm2_5_can`). Abstracted control sensors (`<room_slug>_temp_abstracted`, `<room_slug>_humidity_abstracted`) remain the control-facing API, with tier labels (`CAN`, `HA`, `Emergency`) visible to operators.

**Home Assistant Remains Optional**: The climate controller must operate autonomously when HA is unavailable — the CAN path (node -> bus -> controller's own interface) does not involve HA. Room control does not regress to non-CAN logic during publish-only rollout; climate control remains functional using either CAN or HA as the source.

**MEV Air-Quality Model**: Air Quality/Pollutants demand derives from the max of normalized VOC, NOx, PM1.0, PM2.5, PM4.0, and PM10 demands. CO2 and Humidity remain separate demand channels.

## Technical Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Primary room source | CAN | Production sensor-kit network is the preferred control path. |
| Fallback source | Home Assistant | Preserves the existing safety model and operator visibility. |
| Emergency trigger | Existing `NaN` failover behavior | Avoids bespoke PID or mode logic for CAN availability. |
| Routing | Generated compile-time artifact | ESPHome entity routing cannot depend on runtime registry parsing. |
| Receiver boundary | `CAT_SENSOR` only | HVAC owns environmental interpretation; canbus owns transport health. |
| Receiver location | Climate controller's onboard CAN interface — direct receive | T-Connect Pro has a native CAN transceiver (ADR-0014); the lighting gateway carries no sensor-data role (2026-07-11 clarification, matching AD-7 as amended). |
| Sensor sources | Existing registry nodes flipped to `sensors=1` | No new CAN nodes are created by this epic. |
| Control temperature/humidity source | SHT45 | SEN66 temperature/humidity may be diagnostic only. |
| Stale threshold | 90 seconds per room measurement | Sensor kit emits every 30 seconds; three missed OK frames marks unavailability. |

## Cross-Story Dependencies

All six stories are tightly coupled within this epic. Story HVAC-1.1 (routing, done) must be complete before HVAC-1.2 (receiver core) can publish to routed targets. Stories HVAC-1.2 and HVAC-1.3 (receiver composition on the climate controller) proceed in sequence and must both complete before HVAC-1.4 (control flip). Story HVAC-1.5 (MEV integration) depends on HVAC-1.4 completing so that abstracted sensors exist for MEV logic to consume. Story HVAC-1.6 (verification) exercises all prior stories and must run before the epic is marked done. The epic depends on the frozen `registry/map.json` HVAC consumer contract, the T-Connect Pro's onboard CAN transceiver, and existing Vesta failover and MEV components. No external epics block this work.
