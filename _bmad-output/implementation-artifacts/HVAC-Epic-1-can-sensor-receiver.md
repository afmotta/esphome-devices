# HVAC-Epic 1: HVAC CAN Sensor Receiver

**Date:** July 11, 2026
**Status:** Draft
**Priority:** High
**Estimated Story Points:** 18
**Owning System:** HVAC
**Affected Systems:** HVAC, CAN bus generator/protocol tests, `devices/climate-control.yaml`, Vesta failover component if tier-label support needs a backward-compatible extension
**Promoted From:** `SPEC-hvac-can-sensor-receiver` and its implementation contract
**Related Contract:** [`spec-map-json-contract`](../specs/spec-map-json-contract/SPEC.md)

---

## Scope Clarifications (2026-07-11)

Recorded here per this epic's Definition of Done (contract changes land in the epic).
Two clarifications from Alberto after the first HVAC-1.2 implementation run was blocked:

1. **Sensor sources are the existing CAN nodes.** The stories must not create new CAN
   nodes — no new registry rows, no new node firmware configs, no new bus hardware. A
   room becomes CAN-sensed by flipping an *existing* node's registry row to `sensors=1`
   with a valid `room_slug` (e.g. node 101 → `soggiorno` for the bench) and
   regenerating; the node then includes the already-implemented
   `canbus/packages/sensor_kit.yaml` producer. Final production placement remains out
   of scope for this epic.
2. **The HVAC controller receives CAN sensor data directly, on its own CAN
   interface.** The climate controller (`devices/climate-control.yaml`, LilyGO
   T-Connect Pro) has a native CAN transceiver (ADR-0014) and is the HVAC system's own
   gateway onto the bus: `hvac/packages/can_sensor_receiver.yaml` defines its CAN
   interface and handles `CAT_SENSOR` locally. The lighting/canbus gateway
   (`devices/gateway.yaml`) plays **no role** in sensor data — its duties remain
   transport health, button decode, and the relay bank. This matches AD-7 as amended
   ("the hvac controller consumes sensor frames directly") and `canbus/CLAUDE.md`.
   *(An interim same-day replan routed sensor receive through the lighting gateway
   with a UDP rebroadcast; Alberto rejected it. This section is authoritative.)*

---

## Executive Summary

Implement the HVAC-owned CAN sensor receiver so production room-sensor data flows from
the existing CAN sensor-kit nodes into the central climate controller, becomes visible
in Home Assistant, and drives room climate control through the existing failover
abstraction.

The target production failover order is **CAN -> Home Assistant -> Emergency**. The
receiver is deliberately sensor-only: it handles `CAT_SENSOR` environmental frames
received directly on the climate controller's onboard CAN interface (ADR-0014), ignores
button and transport-health categories, publishes room-scoped CAN source sensors, and
turns stale or degraded CAN measurements into `NaN` so the existing Vesta failover
component performs the tier transition without custom PID logic.

This epic turns the frozen spec into implementable slices: generated routing, receiver
publish-only behavior, control failover migration, MEV air-quality demand migration,
and verification/bench validation.

---

## Problem Statement

### Current State

- HVAC room sensing is still wired around the legacy HA/UDP pattern, and the S1 UDP
  room sensors were test devices rather than the production architecture.
- The CAN sensor kit already emits SHT45 and SEN66 `CAT_SENSOR` frames, but the HVAC
  controller has no runtime receiver in `devices/climate-control.yaml` or `hvac/**` —
  the climate controller is not yet on the CAN bus at all.
- At spec time, `registry/nodes.csv` had only placeholder nodes 100 and 101 with
  `sensors=0` and empty `room_slug`. Making an existing node a sensor source is a
  registry edit (`sensors=1` + a valid `room_slug`) plus regeneration — not new
  hardware and not a new node. No final production placement is assigned by this epic.
- `registry/map.json` is the frozen HVAC join contract, but the firmware cannot parse
  it at runtime; ESPHome routing needs compile-time generated artifacts (HVAC-1.1,
  done).
- MEV demand currently follows the pre-CAN IAQ shape and does not consume raw CAN VOC,
  NOx, or particulate measurements.

### Why This Matters

- Production climate control needs room data from the installed CAN sensor-kit
  network, not the temporary S1 UDP path.
- Home Assistant should remain a fallback, but not the preferred control source when
  CAN room sensors are available.
- Freshness and degraded sensor status must fail safe by flowing through existing
  `NaN`-based failover behavior.
- Sensor routing and frame decode are cross-system contracts; they need tests that
  fail on drift before climate firmware is deployed.

---

## Proposed Solution

### Architecture

1. `canbus/tools/generate_nodes.py` validates sensor-node room joins and generates an
   idempotent compile-time HVAC routing artifact from the registry (HVAC-1.1, done;
   extended only if the receiver needs route/freshness metadata).
2. `hvac/packages/can_sensor_receiver.yaml` defines the climate controller's own CAN
   bus interface (T-Connect Pro onboard transceiver — TX `GPIO6` / RX `GPIO7` per the
   board notes, matching the gateway's wiring of the same board), receives only
   `CAT_SENSOR` frames, decodes them with the CAN protocol helpers, and routes valid
   measurements to room-scoped source sensors via the generated publish scripts.
3. CAN source sensors publish decoded values while fresh and `NaN` when missing,
   degraded, malformed, unknown, or stale for 90 seconds.
4. `hvac/room_sensors.yaml` migrates abstracted temperature and humidity to
   CAN-primary and HA-secondary inputs; room PID, humidity, dew point, and MEV
   humidity logic continue to consume abstracted sensors only.
5. MEV demand keeps separate control channels for CO2, Air Quality/Pollutants, and
   Humidity. Pollutant demand derives from VOC, NOx, PM1.0, PM2.5, PM4.0, and PM10.

### Data Flow

1. An existing generated CAN node with `sensors=1` includes
   `canbus/packages/sensor_kit.yaml` (already-implemented producer behavior; enabling
   a node is a registry edit, not new hardware).
2. The node sends `CAT_SENSOR` frames every 30 seconds with `node_id` in the extended
   CAN ID and `[PROTO_V1, status, meas_lo, meas_hi, value32_le]` in the payload.
3. The HVAC controller receives only `CAT_SENSOR` on its own CAN interface, validates
   payload length and protocol version, and decodes `node_id`, status, measurement
   type, and value using `canbus_protocol.h` helpers.
4. The generated routing artifact maps `(node_id, measurement_type)` to a static
   room-scoped ESPHome sensor target.
5. The receiver publishes decoded CAN source sensors to Home Assistant and updates
   freshness state.
6. `hvac/room_sensors.yaml` feeds CAN source sensors into the existing failover
   component as primary and HA sensors as secondary.
7. Room PID, humidity, dew-point, and MEV humidity logic continue to consume
   abstracted sensors, not raw source sensors.

### Failure Modes

| Failure | Detection | Result |
| --- | --- | --- |
| Sensor degraded (warm-up, error, out-of-range) | Node sends non-OK status; receiver publishes `NaN` for that route | Failover moves that room measurement to HA |
| Sensor node dead or unreachable | Receiver freshness: 90 s without an OK frame → `NaN` | Failover moves that room measurement to HA |
| Controller CAN interface or bus segment fault | All routed measurements stop refreshing → stale → `NaN` (same freshness mechanism) | Failover moves affected rooms to HA |
| CAN and HA both unavailable | Abstracted sensor `NaN` | Existing emergency shutdown behavior |

### Key Design Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Primary room source | CAN | Production sensor-kit network is the preferred control path. |
| Fallback source | Home Assistant | Preserves the existing safety model and operator visibility. |
| Emergency trigger | Existing `NaN` failover behavior | Avoids bespoke PID or mode logic for CAN availability. |
| Routing | Generated compile-time artifact | ESPHome entity routing cannot depend on runtime `map.json` parsing. |
| Receiver boundary | `CAT_SENSOR` only | HVAC owns environmental interpretation; canbus owns transport health and protocol vocabulary. |
| Receiver location | Climate controller's onboard CAN interface — direct receive | The T-Connect Pro has a native CAN transceiver (ADR-0014); the lighting/canbus gateway carries no sensor-data role (2026-07-11 clarification, matching AD-7 as amended). |
| Sensor sources | Existing registry nodes flipped to `sensors=1` | No new CAN nodes are created by this epic; enabling a room is a registry edit plus regeneration. |
| Control temperature/humidity source | SHT45 | SEN66 temperature/humidity may be diagnostic only. |
| Stale threshold | 90 seconds per room measurement | Sensor kit emits every 30 seconds; three missed OK frames marks the source unavailable. |
| MEV pollutant model | MAX of VOC, NOx, PM1.0, PM2.5, PM4.0, PM10 normalized demands | Keeps CO2 distinct while allowing pollutant families to drive ventilation. |

### Entity Contract

For each CAN-equipped room, publish raw CAN source sensors to Home Assistant using the existing room slug convention:

- `<room_slug>_temp_can`
- `<room_slug>_humidity_can`
- `<room_slug>_sen66_temp_can` or an equivalent diagnostic name, if SEN66 temperature is published
- `<room_slug>_sen66_humidity_can` or an equivalent diagnostic name, if SEN66 humidity is published
- `<room_slug>_co2_can`
- `<room_slug>_voc_index_can`
- `<room_slug>_nox_index_can`
- `<room_slug>_pm1_0_can`
- `<room_slug>_pm2_5_can`
- `<room_slug>_pm4_0_can`
- `<room_slug>_pm10_can`

Temperature and humidity abstracted sensors remain the control-facing API:

- `<room_slug>_temp_abstracted`
- `<room_slug>_humidity_abstracted`
- `<room_slug>_temp_abstracted_sensor_tier`
- `<room_slug>_humidity_abstracted_sensor_tier`

The abstracted values and active tier must be visible to Home Assistant. HA fallback source sensors may remain internal unless needed for diagnostics.

---

## User Stories

| Story | Title | Points | Priority | Rollout Slice |
| --- | --- | ---: | --- | --- |
| HVAC-1.1 | Generated CAN Sensor Routing Artifact | 3 | High | Registry and generator |
| HVAC-1.2 | Sensor-Only CAN Receiver and Freshness Core | 5 | High | Receiver publish-only |
| HVAC-1.3 | Climate Controller Publish-Only Composition | 2 | High | Receiver publish-only |
| HVAC-1.4 | CAN-Primary Room Sensor Failover | 3 | High | Control flip |
| HVAC-1.5 | CAN Air-Quality MEV Demand Integration | 3 | Medium | Control flip |
| HVAC-1.6 | Verification Battery and Bench Rollout | 2 | High | Release gate |

**Total: 18 Story Points**

---

## Story Specifications

### Story HVAC-1.1: Generated CAN Sensor Routing Artifact

*(Done — commit `91f8e7f`.)*

**As an HVAC implementer,**
I want sensor-equipped CAN nodes routed to valid HVAC room slugs by generated compile-time artifacts,
so that the climate controller can map CAN measurements to room entities without runtime registry parsing or free-text matching.

**Primary Files**

- `registry/nodes.csv`
- `registry/map.json`
- `canbus/tools/generate_nodes.py`
- Generated HVAC routing artifact, expected location: `hvac/packages/generated/can_sensor_routes.yaml`
- Generator tests under `canbus/tests/`

**Acceptance Criteria**

1. `generate_nodes.py` rejects any `sensors=1` node with an empty `room_slug`.
2. `generate_nodes.py` rejects any `sensors=1` node whose `room_slug` does not join to a real HVAC room package.
3. The generated routing artifact includes only sensor-equipped nodes with valid HVAC room joins.
4. The routing artifact maps `node_id` plus CAN measurement type to static room-scoped ESPHome targets.
5. Regeneration is byte-identical when registry inputs are unchanged.
6. A generator test proves the routing artifact changes when a sensor node is moved to another room.
7. Generated artifacts are clearly marked as generated and are never hand edited.

**Notes**

- This story does not assign final production node inventory or room placements.
- `canbus/` owns the generator mechanics; `hvac/` owns how routed measurements are interpreted.

---

### Story HVAC-1.2: Sensor-Only CAN Receiver and Freshness Core

**As the HVAC controller,**
I want to decode valid `CAT_SENSOR` environmental frames from the existing sensor-kit nodes, received directly on my own CAN interface, and publish fresh room-scoped CAN source sensors,
so that production CAN measurements are observable and can later feed climate failover.

**Primary Files**

- `hvac/packages/can_sensor_receiver.yaml`
- `hvac/protocol/can_sensor_receiver.h` (native-testable decode/route/freshness helpers)
- Generated routing artifact from Story HVAC-1.1
- `canbus/protocol/canbus_protocol.h` (read-only)
- Native receiver/decode tests under `hvac/tests/` (mirroring `lighting/tests/`' pattern) or an agreed location

**Acceptance Criteria**

1. The receiver package defines the climate controller's CAN bus interface (T-Connect Pro onboard transceiver pins as defaults) and subscribes to or guards for `CAT_SENSOR` frames only. It is receive-only: it sends no frames.
2. The existing nodes are the only frame sources: no new registry rows, node firmware, or producer changes are made, and `devices/gateway.yaml` and the gateway-side packages (`canbus/packages/health.yaml`, `lighting/packages/buttons.yaml`) are untouched.
3. Button, heartbeat/status, output, arbitration, discovery, health-management, and unknown categories are ignored without publication.
4. Payload validation covers minimum length, `PROTO_V1`, status byte, measurement type, node id, and value width, using `if:`/`condition:` guards per the canbus `on_frame` convention.
5. `SENSOR_STATUS_OK` publishes decoded engineering-unit values and refreshes freshness for the exact room measurement.
6. `SENSOR_STATUS_WARMING_UP`, `SENSOR_STATUS_UNAVAILABLE`, `SENSOR_STATUS_ERROR`, `SENSOR_STATUS_OUT_OF_RANGE`, and any other non-OK status publish `NaN` for the affected CAN source sensor and do not refresh OK freshness.
7. Unknown `node_id` or measurement type logs and does not publish a valid control value.
8. Freshness is tracked per room measurement; 90 seconds without an OK frame publishes `NaN` for that source sensor. Freshness state lives behind a header accessor (ESPHome globals cannot hold custom structs).
9. Freshness checks may run periodically, but the externally observable stale threshold is 90 seconds.
10. Scaling matches the CAN protocol contract: SHT45 and SEN66 temperature centi-degC to degC; SHT45 and SEN66 humidity x100 to percent RH; SEN66 PM1.0, PM2.5, PM4.0, and PM10 x10 to micrograms per cubic meter; SEN66 CO2 ppm; SEN66 VOC and NOx index unchanged.
11. SHT45 temperature publishes to `<room_slug>_temp_can`; SHT45 humidity publishes to `<room_slug>_humidity_can`.
12. SEN66 temperature and humidity, if published, are diagnostic only and cannot feed abstracted control sensors.
13. Transport-health diagnostics for all mapped CAN nodes are out of scope (canbus owns them, on the lighting/canbus gateway); freshness diagnostics for sensor-equipped room measurements are in scope because they drive failover.
14. Native tests cover valid decode, malformed payloads, wrong protocol version, non-sensor categories, non-OK statuses, unknown routes, and stale expiry.
15. An isolated ESPHome compile fixture composes the generated routes and the receiver package without the full climate controller — proving bus definition, composition order, and script wiring in isolation.

---

### Story HVAC-1.3: Climate Controller Publish-Only Composition

**As an integrator,**
I want the climate controller to compose the CAN bus receiver in publish-only mode,
so that CAN source entities can be inspected in Home Assistant before control logic is flipped to CAN-primary.

**Primary Files**

- `devices/climate-control.yaml`
- `devices/locals/climate-control.yaml`
- `boards/t-connect-pro.yaml` and T-Connect CAN pin substitutions if needed
- `hvac/packages/can_sensor_receiver.yaml`

**Acceptance Criteria**

1. `devices/climate-control.yaml` composes the CAN bus definition required by the receiver on the T-Connect Pro climate controller, plus the generated routes and the receiver package.
2. The climate controller does not compose gateway-oriented CAN health, lighting button decode, or arbitration packages — those stay on `devices/gateway.yaml`, which this epic does not modify.
3. Raw CAN source entities are visible in Home Assistant with room-scoped names such as `<room_slug>_co2_can` and `<room_slug>_pm2_5_can`.
4. Existing room control still uses the current non-CAN abstracted sensor path during this publish-only stage.
5. CAN reception coexists with Modbus, Ethernet, API, OTA, logger, and existing board configuration.
6. `esphome config devices/locals/climate-control.yaml` succeeds after composition.

---

### Story HVAC-1.4: CAN-Primary Room Sensor Failover

**As a homeowner,**
I want room climate control to prefer CAN sensor-kit temperature and humidity but fall back to Home Assistant when CAN is unavailable,
so that control remains autonomous while retaining the existing emergency safety behavior.

**Primary Files**

- `hvac/room_sensors.yaml`
- `vesta/packages/components/failover_sensor.yaml` only if a backward-compatible tier-label or exposure extension is required
- Room packages under `hvac/rooms/**` that consume abstracted sensors

**Acceptance Criteria**

1. Temperature failover uses `<room_slug>_temp_can` as primary and `<room_slug>_temp_ha` as secondary.
2. Humidity failover uses `<room_slug>_humidity_can` as primary and `<room_slug>_humidity_ha` as secondary.
3. Abstracted control sensors remain `<room_slug>_temp_abstracted` and `<room_slug>_humidity_abstracted`.
4. Active tier entities are visible in Home Assistant and label states as `CAN`, `HA`, and `Emergency`.
5. PID, humidity, dew-point, and MEV humidity logic consume abstracted sensors, not raw CAN or HA source sensors directly.
6. When CAN source data becomes stale or degraded, failover moves to HA through existing `NaN` behavior.
7. When both CAN and HA are unavailable, the abstracted value becomes `NaN` and existing emergency behavior engages.
8. The S1 UDP room-sensor path is not required for production HVAC room sensing; the S1 `packet_transport` providers and `_udp` tier sensors may be dropped as rooms flip to CAN.
9. The Vesta failover component remains backward-compatible for existing callers.

**Failover Wiring Shape**

Temperature after migration uses the existing failover component with CAN as primary and HA as secondary:

```yaml
packages:
  temperature_failover: !include
    file: ../vesta/packages/components/failover_sensor.yaml
    vars:
      sensor_id: ${room_slug}_temp_abstracted
      sensor_name: "${room_name} Temperature"
      unit_of_measurement: "degC"
      device_class: temperature
      primary_sensor: ${room_slug}_temp_can
      secondary_sensor: ${room_slug}_temp_ha
```

Humidity follows the same pattern with `${room_slug}_humidity_can` and `${room_slug}_humidity_ha`. The tier labels should be user-facing as `CAN`, `HA`, and `Emergency`; if the Vesta component remains generic internally, the room package may adapt labels without changing failover semantics.

---

### Story HVAC-1.5: CAN Air-Quality MEV Demand Integration

**As the MEV controller,**
I want CAN air-quality measurements to feed the existing demand model without collapsing distinct signals,
so that ventilation responds to occupancy, pollutants, and humidity with clear diagnostics.

**Primary Files**

- `hvac/mev_demand.yaml`
- `hvac/packages/can_sensor_receiver.yaml`
- First-floor room/floor packages that aggregate MEV inputs
- Home Assistant dashboard/docs only where needed for entity visibility

**Acceptance Criteria**

1. Raw CAN CO2, VOC index, NOx index, PM1.0, PM2.5, PM4.0, and PM10 are published to Home Assistant per routed room.
2. CO2 demand remains a separate top-level MEV demand channel.
3. Humidity demand remains a separate top-level MEV demand channel and continues to use abstracted humidity.
4. Air Quality/Pollutants demand is derived from the max of normalized VOC, NOx, PM1.0, PM2.5, PM4.0, and PM10 demands.
5. PM1.0 and PM4.0 participate in pollutant demand alongside the other SEN66 particulate channels.
6. Final fan-speed demand remains the max of CO2, Air Quality/Pollutants, Humidity, and baseline ventilation demand.
7. `text_sensor.${mev_slug}_dominant_demand` stays at the control-channel level: `CO2`, `Air Quality`, `Humidity`, or `Ventilation`.
8. Optional pollutant-level diagnostics may identify which pollutant is dominant inside the Air Quality channel.
9. Existing MEV Modbus control entities are not regressed.

**MEV Rationale and Deferred Alternative**

This first implementation keeps CO2 and pollutants diagnostically distinct: CO2 tracks occupancy and ventilation adequacy, while VOC, NOx, and PM track contamination that may spike independently of occupancy. It lets the main pollutant families influence MEV without adding a top-level MEV demand channel for every raw sensor, keeps the existing `hvac/mev_demand.yaml` mental model and dashboard shape close to what is already implemented, and preserves room-by-room raw observability in Home Assistant for threshold tuning.

Deferred alternative: expose one independent demand channel per pollutant. That is more transparent at the control layer, but expands `mev_demand.yaml`, dominant-demand diagnostics, HA threshold helpers, and dashboard surface area.

---

### Story HVAC-1.6: Verification Battery and Bench Rollout

**As the project owner,**
I want a repeatable verification battery and bench rollout for the CAN sensor receiver,
so that routing drift, decode mistakes, stale handling regressions, and climate compile failures are caught before deployment.

**Acceptance Criteria**

1. Generator tests cover sensor-node `room_slug` validation, routing artifact generation, and idempotence.
2. Native decode/freshness tests cover valid frames, malformed frames, wrong protocol version, non-sensor categories, non-OK statuses, unknown routes, and 90-second stale expiry.
3. Existing CAN sensor node compile remains green: `esphome compile canbus/tests/compile_sensor_node.yaml`.
4. Local climate configuration check succeeds: `esphome config devices/locals/climate-control.yaml`.
5. Local climate compile succeeds before rollout: `esphome compile devices/locals/climate-control.yaml`.
6. Regeneration idempotence leaves `canbus/`, `hvac/`, and `registry/` clean after an unchanged generation run.
7. Bench validation proves an existing node flipped to `sensors=1` with a valid `room_slug` (e.g. node 101 / `soggiorno`) updates CAN source sensors and abstracted room control sensors through the HVAC controller.
8. Bench validation proves stopping CAN frames for more than 90 seconds moves the room from CAN to HA.
9. Bench validation proves disabling both CAN and HA drives the abstracted sensor to `NaN` and triggers the existing emergency behavior.
10. Findings from bench validation are recorded in the completion report or a follow-up tuning note.

---

## Functional Requirements Coverage

| Spec Capability | Covered By | Notes |
| --- | --- | --- |
| CAP-1: Sensor-equipped CAN nodes join to HVAC room slugs | HVAC-1.1 | Generated routing artifact and validation. |
| CAP-2: HVAC ingests CAN environmental measurements | HVAC-1.2, HVAC-1.3 | Direct decode on the controller's CAN interface, publish source sensors, compose publish-only receiver. |
| CAP-3: CAN availability participates through source sensor values | HVAC-1.2, HVAC-1.4 | `NaN` on non-OK/stale source data drives failover. |
| CAP-4: Room control uses CAN-primary abstracted sensors and publishes tier | HVAC-1.4, HVAC-1.5 | Temperature/humidity control and MEV humidity consume abstracted values. |
| CAP-5: Receiver changes are covered by drift-breaking tests and compile checks | HVAC-1.1, HVAC-1.2, HVAC-1.6 | Generator, native, ESPHome, idempotence, bench validation. |

---

## Out of Scope

- Defining a new CAN sensor protocol, measurement vocabulary, or wire encoding.
- Creating new CAN nodes — registry rows, node firmware configs, or bus hardware; the existing nodes are the sensor sources.
- Modifying the lighting/canbus gateway (`devices/gateway.yaml`) or its packages — it carries no sensor-data role.
- Removing Home Assistant as the fallback source.
- Moving lighting button handling, gateway behavior, arbitration, or transport-health management into HVAC.
- Assigning final production node inventory or final physical room placements.
- Building new dashboards beyond the entities needed for observability.
- Preserving the S1 UDP room-sensor path as production architecture.

---

## Dependencies

- Frozen `registry/map.json` HVAC consumer contract from `spec-map-json-contract`.
- Existing CAN sensor-kit producer behavior in `canbus/packages/sensor_kit.yaml`.
- Protocol constants and status semantics in `canbus/protocol/canbus_protocol.h`.
- T-Connect Pro climate controller hardware and onboard CAN transceiver configuration (ADR-0014).
- Existing Vesta failover component and HVAC `room_sensors.yaml` abstraction pattern.
- Existing MEV Modbus control package and demand aggregation in `hvac/mev_modbus.yaml` and `hvac/mev_demand.yaml`.

## Assumptions

- Existing Home Assistant fallback entity IDs such as `sensor.room_soggiorno_temperature` and `sensor.room_soggiorno_humidity` remain the secondary source for room temperature and humidity.
- Production CAN environmental nodes use the fixed ADR-0006 SHT45 plus SEN66 sensor kit rather than per-node custom measurement inventories.

## Rollout Plan

1. Registry and generator: add the HVAC routing artifact and tests without changing runtime climate behavior (done, HVAC-1.1).
2. Receiver publish-only: compose the CAN receiver into `devices/climate-control.yaml` and publish raw CAN source sensors to Home Assistant while rooms still use the existing sensor path for control.
3. Control flip: update `hvac/room_sensors.yaml` to CAN-primary and HA-secondary, expose abstracted sensors and tier labels, and validate CAN-to-HA-to-Emergency transitions on the bench.

---

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Generated routing drifts from registry or HVAC room packages | Add generator validation plus byte-identical regeneration tests. |
| ESPHome CAN receiver code becomes too lambda-heavy | Move pure decode/freshness logic into native-testable C++ helpers (`hvac/protocol/can_sensor_receiver.h`). |
| `NaN` does not propagate through failover as expected | Test source-sensor stale handling and abstracted sensor tier transitions on bench. |
| MEV pollutant thresholds need real-world tuning | Ship diagnostics and preserve raw measurements; tune thresholds after data collection. |
| Receiver accidentally handles non-sensor CAN traffic | Use category filters where supported and native tests for ignored categories. |
| Climate controller resource pressure — CAN RX joins Modbus, 13 rooms of PID, and MEV on one device | Validate full `devices/locals/climate-control.yaml` compile, not only isolated packages. |

---

## Definition of Done

- All six stories are implemented and marked done in sprint status.
- The promoted epic preserves the original spec and implementation-contract decisions as amended by the 2026-07-11 scope clarifications recorded above; future contract changes are made directly in the epic or in a successor ADR/spec.
- Generator, native, ESPHome config, ESPHome compile, and idempotence checks pass.
- A bench CAN sensor node (an existing node, registry-flipped) proves CAN -> HA -> Emergency transitions through the HVAC controller.
- Home Assistant shows raw CAN source sensors, abstracted control values, and active failover tiers.
- A completion report records delivered files, validation commands, bench results, and any deferred tuning work.
