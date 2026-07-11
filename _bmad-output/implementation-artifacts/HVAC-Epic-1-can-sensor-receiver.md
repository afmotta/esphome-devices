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

## Executive Summary

Implement the HVAC-owned CAN sensor receiver so production room-sensor data flows from CAN sensor-kit nodes into the central climate controller, becomes visible in Home Assistant, and drives room climate control through the existing failover abstraction.

The target production failover order is **CAN -> Home Assistant -> Emergency**. The receiver is deliberately sensor-only: it handles `CAT_SENSOR` environmental frames, ignores button and transport-health categories, publishes room-scoped CAN source sensors, and turns stale or degraded CAN measurements into `NaN` so the existing Vesta failover component performs the tier transition without custom PID logic.

This epic turns the frozen spec into implementable slices: generated routing, receiver publish-only behavior, control failover migration, MEV air-quality demand migration, and verification/bench validation.

---

## Problem Statement

### Current State

- HVAC room sensing is still wired around the legacy HA/UDP pattern, and the S1 UDP room sensors were test devices rather than the production architecture.
- The CAN sensor kit already emits SHT45 and SEN66 `CAT_SENSOR` frames, but the HVAC controller has no runtime receiver in `devices/climate-control.yaml` or `hvac/**`.
- At spec time, `registry/nodes.csv` has only placeholder nodes 100 and 101 with `sensors=0` and empty `room_slug`; no production CAN sensor placement is assigned by this epic.
- `registry/map.json` is the frozen HVAC join contract, but the firmware cannot parse it at runtime; ESPHome routing needs compile-time generated artifacts.
- MEV demand currently follows the pre-CAN IAQ shape and does not consume raw CAN VOC, NOx, or particulate measurements.

### Why This Matters

- Production climate control needs room data from the installed CAN sensor-kit network, not the temporary S1 UDP path.
- Home Assistant should remain a fallback, but not the preferred control source when CAN room sensors are available.
- Freshness and degraded sensor status must fail safe by flowing through existing `NaN`-based failover behavior.
- Sensor routing and frame decode are cross-system contracts; they need tests that fail on drift before climate firmware is deployed.

---

## Proposed Solution

### Architecture

1. `canbus/tools/generate_nodes.py` validates sensor-node room joins and generates an idempotent compile-time HVAC routing artifact from the registry.
2. `hvac/packages/can_sensor_receiver.yaml` receives only `CAT_SENSOR` frames on the climate controller, decodes them with the CAN protocol helpers, and routes valid measurements to room-scoped source sensors.
3. CAN source sensors publish decoded values while fresh and `NaN` when missing, degraded, malformed, unknown, or stale for 90 seconds.
4. `hvac/room_sensors.yaml` migrates abstracted temperature and humidity to CAN-primary and HA-secondary inputs; room PID, humidity, dew point, and MEV humidity logic continue to consume abstracted sensors only.
5. MEV demand keeps separate control channels for CO2, Air Quality/Pollutants, and Humidity. Pollutant demand derives from VOC, NOx, PM2.5, and PM10 while PM1.0 and PM4.0 remain diagnostics in v1.

### Data Flow

1. A generated CAN node with `sensors=1` includes `canbus/packages/sensor_kit.yaml`.
2. The node sends `CAT_SENSOR` frames every 30 seconds with `node_id` in the extended CAN ID and `[PROTO_V1, status, meas_lo, meas_hi, value32_le]` in the payload.
3. The HVAC controller receives only `CAT_SENSOR`, validates payload length and protocol version, and decodes `node_id`, status, measurement type, and value using `canbus_protocol.h` helpers.
4. The generated routing artifact maps `(node_id, measurement_type)` to a static room-scoped ESPHome sensor target.
5. The receiver publishes decoded CAN source sensors to Home Assistant and updates freshness state.
6. `hvac/room_sensors.yaml` feeds CAN source sensors into the existing failover component as primary and HA sensors as secondary.
7. Room PID, humidity, dew-point, and MEV humidity logic continue to consume abstracted sensors, not raw source sensors.

### Key Design Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Primary room source | CAN | Production sensor-kit network is the preferred control path. |
| Fallback source | Home Assistant | Preserves the existing safety model and operator visibility. |
| Emergency trigger | Existing `NaN` failover behavior | Avoids bespoke PID or mode logic for CAN availability. |
| Routing | Generated compile-time artifact | ESPHome entity routing cannot depend on runtime `map.json` parsing. |
| Receiver boundary | `CAT_SENSOR` only | HVAC owns environmental interpretation; canbus owns transport health and protocol vocabulary. |
| Control temperature/humidity source | SHT45 | SEN66 temperature/humidity may be diagnostic only. |
| Stale threshold | 90 seconds per room measurement | Sensor kit emits every 30 seconds; three missed OK frames marks the source unavailable. |
| MEV pollutant model | MAX of VOC, NOx, PM2.5, PM10 normalized demands | Keeps CO2 distinct while allowing pollutant families to drive ventilation. |

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
I want to decode valid `CAT_SENSOR` environmental frames and publish fresh room-scoped CAN source sensors,
so that production CAN measurements are observable and can later feed climate failover.

**Primary Files**

- `hvac/packages/can_sensor_receiver.yaml`
- Generated routing artifact from Story HVAC-1.1
- `canbus/protocol/canbus_protocol.h`
- Native receiver/decode tests under `canbus/tests/` or an HVAC-owned native test location agreed during implementation

**Acceptance Criteria**

1. The receiver subscribes to or guards for `CAT_SENSOR` frames only.
2. Button, heartbeat/status, output, arbitration, discovery, health-management, and unknown categories are ignored without publication.
3. Payload validation covers minimum length, `PROTO_V1`, status byte, measurement type, node id, and value width.
4. `SENSOR_STATUS_OK` publishes decoded engineering-unit values and refreshes freshness for the exact room measurement.
5. `SENSOR_STATUS_WARMING_UP`, `SENSOR_STATUS_UNAVAILABLE`, `SENSOR_STATUS_ERROR`, `SENSOR_STATUS_OUT_OF_RANGE`, and any other non-OK status publish `NaN` for the affected CAN source sensor and do not refresh OK freshness.
6. Unknown `node_id` or measurement type logs and does not publish a valid control value.
7. Freshness is tracked per room measurement; 90 seconds without an OK frame publishes `NaN` for that source sensor.
8. Freshness checks may run periodically, but the externally observable stale threshold is 90 seconds.
9. Scaling matches the CAN protocol contract: SHT45 and SEN66 temperature centi-degC to degC; SHT45 and SEN66 humidity x100 to percent RH; SEN66 PM1.0, PM2.5, PM4.0, and PM10 x10 to micrograms per cubic meter; SEN66 CO2 ppm; SEN66 VOC and NOx index unchanged.
10. SHT45 temperature publishes to `<room_slug>_temp_can`; SHT45 humidity publishes to `<room_slug>_humidity_can`.
11. SEN66 temperature and humidity, if published, are diagnostic only and cannot feed abstracted control sensors.
12. Transport-health diagnostics for all mapped CAN nodes are out of scope; freshness diagnostics for sensor-equipped room measurements are in scope because they drive failover.
13. Native tests cover valid decode, malformed payloads, wrong protocol version, non-sensor categories, non-OK statuses, unknown routes, and stale expiry.

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

1. `devices/climate-control.yaml` composes the CAN bus definition required by the receiver on the T-Connect Pro climate controller.
2. The climate controller does not compose gateway-oriented CAN health, lighting button decode, or arbitration packages.
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
8. The S1 UDP room-sensor path is not required for production HVAC room sensing.
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
4. Air Quality/Pollutants demand is derived from the max of normalized VOC, NOx, PM2.5, and PM10 demands.
5. PM1.0 and PM4.0 are diagnostic in v1 and do not drive pollutant demand unless a later tuning pass changes the contract.
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
7. Bench validation proves a `sensors=1` node with a valid `room_slug` updates CAN source sensors and abstracted room control sensors through the HVAC controller.
8. Bench validation proves stopping CAN frames for more than 90 seconds moves the room from CAN to HA.
9. Bench validation proves disabling both CAN and HA drives the abstracted sensor to `NaN` and triggers the existing emergency behavior.
10. Findings from bench validation are recorded in the completion report or a follow-up tuning note.

---

## Functional Requirements Coverage

| Spec Capability | Covered By | Notes |
| --- | --- | --- |
| CAP-1: Sensor-equipped CAN nodes join to HVAC room slugs | HVAC-1.1 | Generated routing artifact and validation. |
| CAP-2: HVAC ingests CAN environmental measurements | HVAC-1.2, HVAC-1.3 | Decode, publish source sensors, compose publish-only receiver. |
| CAP-3: CAN availability participates through source sensor values | HVAC-1.2, HVAC-1.4 | `NaN` on non-OK/stale source data drives failover. |
| CAP-4: Room control uses CAN-primary abstracted sensors and publishes tier | HVAC-1.4, HVAC-1.5 | Temperature/humidity control and MEV humidity consume abstracted values. |
| CAP-5: Receiver changes are covered by drift-breaking tests and compile checks | HVAC-1.1, HVAC-1.2, HVAC-1.6 | Generator, native, ESPHome, idempotence, bench validation. |

---

## Out of Scope

- Defining a new CAN sensor protocol, measurement vocabulary, or wire encoding.
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
- T-Connect Pro climate controller hardware and onboard CAN transceiver configuration.
- Existing Vesta failover component and HVAC `room_sensors.yaml` abstraction pattern.
- Existing MEV Modbus control package and demand aggregation in `hvac/mev_modbus.yaml` and `hvac/mev_demand.yaml`.

## Assumptions

- Existing Home Assistant fallback entity IDs such as `sensor.room_soggiorno_temperature` and `sensor.room_soggiorno_humidity` remain the secondary source for room temperature and humidity.
- Production CAN environmental nodes use the fixed ADR-0006 SHT45 plus SEN66 sensor kit rather than per-node custom measurement inventories.

## Rollout Plan

1. Registry and generator: add the HVAC routing artifact and tests without changing runtime climate behavior.
2. Receiver publish-only: compose the CAN receiver into `devices/climate-control.yaml` and publish raw CAN source sensors to Home Assistant while rooms still use HA fallback sources for control.
3. Control flip: update `hvac/room_sensors.yaml` to CAN-primary and HA-secondary, expose abstracted sensors and tier labels, and validate CAN-to-HA-to-Emergency transitions on the bench.

---

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Generated routing drifts from registry or HVAC room packages | Add generator validation plus byte-identical regeneration tests. |
| ESPHome CAN receiver code becomes too lambda-heavy | Move pure decode/freshness logic into native-testable C++ helpers if needed. |
| `NaN` does not propagate through failover as expected | Test source-sensor stale handling and abstracted sensor tier transitions on bench. |
| MEV pollutant thresholds need real-world tuning | Ship diagnostics and preserve raw measurements; tune thresholds after data collection. |
| Receiver accidentally handles non-sensor CAN traffic | Use category filters where supported and native tests for ignored categories. |
| Climate controller resource pressure | Validate full `devices/locals/climate-control.yaml` compile, not only isolated packages. |

---

## Definition of Done

- All six stories are implemented and marked done in sprint status.
- The promoted epic preserves the original spec and implementation-contract decisions; future contract changes are made directly in the epic or in a successor ADR/spec.
- Generator, native, ESPHome config, ESPHome compile, and idempotence checks pass.
- A bench CAN sensor node proves CAN -> HA -> Emergency transitions through the HVAC controller.
- Home Assistant shows raw CAN source sensors, abstracted control values, and active failover tiers.
- A completion report records delivered files, validation commands, bench results, and any deferred tuning work.
