---
title: 'HVAC-1.2 Sensor-Only CAN Receiver and Freshness Core'
type: 'feature'
created: '2026-07-11'
status: 'done'
baseline_revision: '91f8e7f00df1d90b7991fc3341d268de58eed0cf'
review_loop_iteration: 0
followup_review_recommended: false
final_revision: 'abf876eaf01e212121449660f765f06358872011'
context:
  - '{project-root}/hvac/CLAUDE.md'
  - '{project-root}/canbus/CLAUDE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-HVAC-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-hvac-1-1-generated-can-sensor-routing-artifact.md'
warnings: []
---

<intent-contract>

## Intent

**Problem:** The existing CAN sensor-kit nodes already emit `CAT_SENSOR` frames and HVAC-1.1 generates static room routes, but the HVAC system has no receiver package that decodes those frames, publishes room-scoped CAN source sensors, or expires stale measurements. Without this core, later CAN-primary failover work has no reliable CAN source values to consume.

**Approach:** Add an HVAC-owned, publish-only CAN sensor receiver package plus native-testable decode/freshness helpers. The package defines the climate controller's own CAN bus receive path (the T-Connect Pro has a native CAN transceiver, ADR-0014 — the HVAC controller receives sensor data **directly**, per the epic's 2026-07-11 scope clarifications), handles `CAT_SENSOR` only, delegates valid/invalid routed publications to the generated route scripts, and marks each routed measurement stale after 90 seconds without an OK frame. The **existing** registry nodes are the only frame sources — this story creates no CAN nodes. The lighting/canbus gateway (`devices/gateway.yaml`) is not involved and not modified.

## Boundaries & Constraints

**Always:** Use `canbus/protocol/canbus_protocol.h` constants/helpers for category, protocol, status, measurement, and payload decoding; scale raw values exactly per ADR-0006; keep route target publication delegated to `can_sensor_route_publish` and `can_sensor_route_publish_nan`; track freshness per routed `(node_id, measurement_type)` behind a header accessor (ESPHome globals cannot hold custom structs); treat 90 seconds as the externally observable stale threshold; ignore non-sensor categories by CAN filter/guard (`if:`/`condition:` per the canbus `on_frame` convention); keep the story publish-only, with no climate control failover flip.

**Block If:** The generated route artifact cannot expose enough deterministic route metadata for receiver freshness without weakening HVAC-1.1's no-runtime-registry rule; ESPHome cannot compile a sensor receiver package that both defines the T-Connect Pro CAN bus and includes the generated routes; a route conflict would require choosing between duplicate producers for one room measurement.

**Never:** Do not create new CAN nodes — no new `registry/nodes.csv` rows, no new node firmware configs, no producer-side changes (existing nodes are the sources; flipping one to `sensors=1` is a registry edit outside this story's code scope); do not modify `devices/gateway.yaml` or the gateway-side packages (`canbus/packages/health.yaml`, `lighting/packages/buttons.yaml`) — the lighting/canbus gateway carries no sensor-data role; do not edit generated files by hand except through `canbus/tools/generate_nodes.py`; do not alter the CAN wire protocol, sensor-kit producer cadence, or `PROTO_V1`; do not compose the receiver into `devices/climate-control.yaml` in this story (HVAC-1.3); do not change `hvac/room_sensors.yaml`, Vesta failover order, MEV demand, lighting button handling, gateway transport health, node health, or arbitration behavior.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Valid routed sensor frame | Extended `CAT_SENSOR` frame from an existing node, known `node_id`, known measurement, length >= `SENSOR_PAYLOAD_MIN`, `PROTO_V1`, `SENSOR_STATUS_OK` | Publish scaled engineering-unit value through `can_sensor_route_publish` and refresh that route's last-OK timestamp | No error expected |
| Non-sensor frame | `CAT_INPUT`, `CAT_STATUS`, `CAT_OUTPUT`, `CAT_SYSTEM`, `CAT_EXTENDED`, or unknown category | No route publish, no freshness refresh, no application log noise | Ignored |
| Malformed sensor payload | Short payload or wrong protocol version | No valid-value publish and no freshness refresh | Drop quietly or at debug level only |
| Non-OK sensor status | Warming-up, unavailable, error, out-of-range, or any status other than OK | Publish `NaN` for the affected routed source sensor and do not refresh last-OK freshness | No warning spam |
| Unknown route | Valid sensor frame with unmapped `node_id` or unsupported measurement type | No valid control value is published and no freshness route is created or refreshed | Drop quietly or at debug level only |
| Stale routed measurement | A routed measurement has not received an OK frame for 90 seconds | Publish `NaN` through `can_sensor_route_publish_nan` for that exact route | Repeat publication may occur on sweeps, but threshold must not exceed 90 seconds |

</intent-contract>

## Code Map

- `hvac/packages/can_sensor_receiver.yaml` -- New hand-authored package for the HVAC controller CAN bus receiver: defines the controller's CAN interface (receive-only; T-Connect Pro onboard transceiver pin defaults), the CAT_SENSOR `on_frame` handling, and the periodic freshness sweep.
- `hvac/protocol/can_sensor_receiver.h` -- New native-testable helper for route metadata, frame validation/scaling, and last-OK freshness state via a store accessor (the `node_health_store()`/`pending_acks_store()` pattern).
- `hvac/packages/generated/can_sensor_routes.yaml` -- Generated target sensors and publish scripts from HVAC-1.1; generator may need to add route metadata/freshness hooks but this file must remain generated.
- `canbus/tools/generate_nodes.py` -- Source of CAN sensor route generation; extend only if receiver/freshness needs generated route tables or script hooks.
- `canbus/tests/test_generate_exports.py` -- Existing stdlib generator tests; extend if generated route artifact shape changes.
- `hvac/tests/test_can_sensor_receiver.cpp` -- New native C++ tests for decode, scaling, route lookup, non-OK behavior, ignored categories, unknown routes, and stale expiry.
- `hvac/tests/compile_can_sensor_receiver.yaml` -- New ESPHome compile fixture that composes the generated route package and receiver package without the full climate controller.
- `canbus/packages/sensor_kit.yaml` -- Producer contract: 30-second cadence and raw scaling; read-only for this story.
- `canbus/protocol/canbus_protocol.h` -- Protocol constants and payload helpers; read-only unless tests expose a real contract bug.

## Tasks & Acceptance

**Execution:**
- [x] `hvac/protocol/can_sensor_receiver.h` -- Add pure helper functions/classes for sensor-frame classification, validation, raw-value scaling, generated route lookup, route state refresh, and stale-route detection, with freshness state behind a store accessor -- Keeps ESPHome lambdas thin and makes edge cases testable without hardware.
- [x] `canbus/tools/generate_nodes.py` and `canbus/tests/test_generate_exports.py` -- Extend the generated route artifact with any receiver metadata needed by the helper while preserving empty-registry output, deterministic generation, and HVAC-1.1 validation behavior -- Lets freshness track only real routed measurements.
- [x] `hvac/packages/can_sensor_receiver.yaml` -- Define the T-Connect Pro `esp32_can` receiver package with CAT_SENSOR-only filtering, protocol guards, route publish calls, non-OK `NaN` routing, and a periodic stale sweep using the helper -- Implements publish-only, receive-only receiver behavior on the controller's own CAN interface.
- [x] `hvac/tests/test_can_sensor_receiver.cpp` -- Add native tests for the I/O matrix plus all supported measurement scaling paths -- Proves frame handling and freshness logic independent of ESPHome.
- [x] `hvac/tests/compile_can_sensor_receiver.yaml` -- Add an isolated ESPHome fixture composing generated routes and the receiver package -- Catches YAML/package/include/lambda mistakes before full climate composition.
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- Mark `hvac-1-2-sensor-only-can-receiver-freshness-core` complete only after implementation, verification, and review pass -- Keeps BMAD tracking accurate.

**Acceptance Criteria:**
- Given a valid routed `SENSOR_STATUS_OK` frame for each supported measurement type, when the receiver handles it, then it publishes the expected scaled engineering-unit value and refreshes freshness for only that routed measurement.
- Given any non-`CAT_SENSOR` frame, when receiver logic is evaluated, then no route publish, NaN publish, or freshness refresh occurs.
- Given a short payload or wrong protocol version, when the receiver handles the frame, then it drops the frame without publishing a valid value or refreshing freshness.
- Given a non-OK status for a routed node and measurement, when the receiver handles it, then it publishes `NaN` for that route and does not refresh last-OK freshness.
- Given an unknown node id or unsupported measurement type, when the receiver handles the frame, then no valid-value publish occurs and no freshness state is refreshed.
- Given a routed measurement receives no OK frame for 90 seconds, when the freshness sweep runs, then the receiver publishes `NaN` for exactly that measurement's CAN source sensor.
- Given the story's diff, when inspected, then `registry/nodes.csv`, node firmware configs, `canbus/packages/sensor_kit.yaml`, `devices/gateway.yaml`, and the gateway-side packages are unchanged — existing nodes are the only sources and the lighting/canbus gateway is untouched.
- Given the committed placeholder registry has no `sensors=1` rows, when generator and receiver tests run, then empty route output remains valid and no compile fixture depends on production node inventory.

## Spec Change Log

- **2026-07-11 (a) — First run blocked; interim replan (superseded).** The first dev run was blocked mid-implementation by an architecture correction from Alberto; the interrupted attempt was cleaned up (direct-HVAC receiver package, helper, compile fixture, and native tests removed; `canbus/tools/generate_nodes.py`, `canbus/tests/test_generate_exports.py`, and `hvac/packages/generated/can_sensor_routes.yaml` restored to the HVAC-1.1 shape; generator and export tests re-verified green, 26 tests). An interim replan then moved the receiver onto the lighting/canbus gateway with a UDP rebroadcast to the controller — that replan misread the correction and was rejected by Alberto the same day.
- **2026-07-11 (b) — Final scope clarifications (authoritative).** Alberto clarified: (1) the stories must use the **existing** CAN nodes as the sources of sensor messages — no new CAN nodes are created (the real issue behind the blocked run); (2) the HVAC controller has its own CAN capability (T-Connect Pro, ADR-0014) and receives `CAT_SENSOR` **directly** on its own interface — the lighting system gateway must not receive sensor data. This restores the original controller-side receiver design with the existing-nodes constraint now explicit. See the epic's "Scope Clarifications (2026-07-11)" section.

## Review Triage Log

### 2026-07-11 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 2: (high 0, medium 2, low 0)
- defer: 1: (high 0, medium 1, low 0)
- reject: 4: (high 0, medium 1, low 3)
- addressed_findings:
  - `[medium]` `[patch]` Freshness sweep marked all expired routes stale but only published `NaN` for the first route; changed the sweep to execute `can_sensor_route_publish_nan` for every route returned by the helper and added native coverage for simultaneous stale routes.
  - `[medium]` `[patch]` Routes that had never received an OK frame after boot never became stale; updated stale detection to expire never-seen routes at the 90-second threshold and added native coverage.

## Design Notes

The generated route package should stay the sole source of route targets. If freshness needs a table, generate compact metadata next to the existing scripts instead of deriving routes from IDs or parsing YAML at runtime. The receiver package should be order-composed after generated routes in any fixture so `can_sensor_route_publish` and `can_sensor_route_publish_nan` exist before the receiver calls them.

Receiver YAML should avoid gateway packages. `canbus/packages/health.yaml` is for transport health and lighting gateway composition; HVAC only needs its own bus receive path and environmental interpretation. The T-Connect Pro board notes the onboard CAN transceiver pins as TX `GPIO6` and RX `GPIO7` (the same board wiring the gateway uses), so defaults should match that unless a composing fixture overrides them. The receiver sends nothing on the bus — it is a receive-only member; do not add TX paths, arbitration, or heartbeat behavior.

Freshness state is per-route custom-struct state, so it lives behind a header accessor (`node_health_store()` / `pending_acks_store()` pattern); ESPHome globals cannot carry it. Follow the canbus `on_frame` guard convention: `if:`/`condition:` blocks validate the payload so action lambdas stay clean.

## Verification

**Commands:**
- `python3 canbus/tests/test_generate_exports.py` -- expected: generator/export tests pass, including any route metadata coverage.
- `g++ -std=c++17 -Wall -Wextra -Icanbus/protocol -Ihvac/protocol hvac/tests/test_can_sensor_receiver.cpp -o /tmp/hvac_can_sensor_receiver && /tmp/hvac_can_sensor_receiver` -- expected: native receiver/freshness tests pass.
- `esphome config hvac/tests/compile_can_sensor_receiver.yaml` -- expected: isolated receiver package config validates.
- `git diff --check` -- expected: no whitespace errors.

## Auto Run Result

Status: done

Summary: Implemented the direct HVAC CAT_SENSOR receiver core. The new receiver package defines the controller-side ESP32-S3 CAN receive path, filters/guards `CAT_SENSOR` frames, delegates valid and `NaN` publications to generated route scripts, and sweeps freshness through native helper state. Generated route output now includes no-op publish scripts for empty registries plus a generated route metadata header for receiver freshness.

Files changed:
- `canbus/tools/generate_nodes.py` -- Added generated route metadata header rendering/writing and empty-route no-op scripts.
- `canbus/tests/test_generate_exports.py` -- Added route metadata and no-op-script coverage while preserving empty-registry behavior.
- `hvac/packages/generated/can_sensor_routes.yaml` -- Regenerated empty route package with no-op publish scripts.
- `hvac/protocol/generated_can_sensor_routes.h` -- Added generated empty route metadata for the placeholder registry.
- `hvac/protocol/can_sensor_receiver.h` -- Added decode, validation, scaling, route lookup, freshness state, and stale-route helpers.
- `hvac/packages/can_sensor_receiver.yaml` -- Added receive-only HVAC CAN package with `CAT_SENSOR` guards, route publication, non-OK `NaN`, and stale sweeps.
- `hvac/tests/test_can_sensor_receiver.cpp` -- Added native coverage for scaling, malformed frames, non-sensor categories, non-OK statuses, unknown routes, stale expiry, never-seen expiry, simultaneous stale routes, and millis wraparound.
- `hvac/tests/compile_can_sensor_receiver.yaml` -- Added isolated ESPHome composition fixture.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- Marked HVAC-1.2 done.
- `_bmad-output/implementation-artifacts/deferred-work.md` -- Recorded the pre-existing local registry/generated-route mismatch as deferred work.

Review findings breakdown: patched 2 medium findings, deferred 1 medium pre-existing worktree mismatch, rejected 4 findings. Patched items fixed simultaneous stale-route publication and never-seen route expiry after 90 seconds. Follow-up review recommendation: false; review-driven changes were localized and covered by focused native tests plus ESPHome config validation.

Verification performed:
- `python3 canbus/tests/test_generate_exports.py` -- passed, 29 export-pipeline tests.
- `g++ -std=c++17 -Wall -Wextra -Icanbus/protocol -Ihvac/protocol hvac/tests/test_can_sensor_receiver.cpp -o /tmp/hvac_can_sensor_receiver && /tmp/hvac_can_sensor_receiver` -- passed.
- `esphome config hvac/tests/compile_can_sensor_receiver.yaml` -- passed, configuration valid.
- `git diff --check` -- passed.
- VS Code diagnostics for modified implementation/test files -- no errors.

Residual risks: The committed placeholder registry remains empty (`sensors=0`) by story scope, so non-empty route behavior is covered by generator/native tests rather than the committed compile fixture. A local dirty `registry/nodes.csv` edit enables node 101 for `soggiorno`; generated route artifacts were intentionally kept at the baseline empty-registry shape and the mismatch was deferred. A scoped local commit was created while leaving unrelated dirty files out of the commit.
