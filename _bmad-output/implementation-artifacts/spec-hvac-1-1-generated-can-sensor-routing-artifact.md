---
title: 'HVAC-1.1 Generated CAN Sensor Routing Artifact'
type: 'feature'
created: '2026-07-11'
status: 'done'
baseline_revision: '6fcdc7368caea90bad6491329af99be6d3821d0d'
review_loop_iteration: 0
followup_review_recommended: false
final_revision: 'edff9d433828a027ea4f43b8f2356e683eebf2e2'
context:
  - '{project-root}/hvac/CLAUDE.md'
  - '{project-root}/canbus/CLAUDE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-HVAC-1-context.md'
warnings: []
---

<intent-contract>

## Intent

**Problem:** The HVAC controller cannot parse `registry/map.json` at runtime, so later CAN sensor receiver work needs a deterministic compile-time artifact that joins sensor-node `node_id` values to HVAC room-scoped CAN source sensor targets. Today the generator validates `room_slug` and exports `map.json`, but it does not emit a receiver-ready HVAC routing package.

**Approach:** Extend `canbus/tools/generate_nodes.py` to render `hvac/packages/generated/can_sensor_routes.yaml` from validated `sensors=1` registry rows, then cover the route renderer and generator failure modes in `canbus/tests/test_generate_exports.py`. The artifact should be generated only, deterministic, empty-but-valid for the current placeholder registry, and ready for later receiver composition without changing runtime HVAC behavior in this story.

## Boundaries & Constraints

**Always:** Reuse `load_climate_zones()` and `validate_room_slug()` for room joins; include only rows with `sensors=1` and a valid `room_slug`; preserve the frozen `registry/map.json` contract; mark generated artifacts as generated/do-not-edit; use the CAN protocol measurement names from `canbus/protocol/canbus_protocol.h`; keep regeneration byte-identical for unchanged inputs.

**Block If:** A registry state requires more than one sensor node to publish to the same room-scoped CAN target and no deterministic conflict policy can be implemented safely. Block rather than inventing averaging, priority, or redundancy semantics.

**Never:** Do not assign production node inventory or final room placements; do not implement the CAN receiver, frame decode, freshness expiry, failover migration, MEV demand, or climate-controller composition; do not hand-edit `canbus/nodes/`; do not change the CAN wire protocol or sensor-kit producer behavior.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Current registry | Only `sensors=0` placeholder nodes | `hvac/packages/generated/can_sensor_routes.yaml` exists with generated header and no route targets | No error expected |
| Valid sensor node | A `sensors=1` row with `room_slug: anticamera` on floor 0 | Artifact declares `anticamera_*_can` template targets and routes `(node_id, measurement_type)` to those targets | No error expected |
| Empty sensor room | A `sensors=1` row with blank `room_slug` | Generator exits before writing generated artifacts | Print a clear `sensors=1 requires a room_slug` error |
| Invalid join | A `sensors=1` row with unknown slug or mismatched floor | Generator exits before writing generated artifacts | Print the existing room-slug validation error with node/row context |
| Node moved | Same sensor node changes from one valid `room_slug` to another | Regenerated route artifact changes target room IDs and names deterministically | No stale route remains |

</intent-contract>

## Code Map

- `canbus/tools/generate_nodes.py` -- Owns registry parsing, climate-zone validation, generated node files, `registry/map.json`, and should render/write the new HVAC route package.
- `canbus/tests/test_generate_exports.py` -- Existing stdlib-only generator tests; add pure renderer and temp-generator coverage here.
- `hvac/packages/generated/can_sensor_routes.yaml` -- New generated ESPHome YAML package; current committed registry should generate an empty route package.
- `registry/nodes.csv` -- Source registry; current rows remain placeholders with `sensors=0`.
- `registry/map.json` -- Frozen HVAC consumer export; should remain deterministic and unchanged except for normal generator output if inputs change.
- `canbus/protocol/canbus_protocol.h` -- Source of sensor measurement constants used by the generated route conditions.
- `canbus/packages/sensor_kit.yaml` -- Producer contract for the measurement set and scale comments; read-only for this story.
- `hvac/rooms/**` -- Real room slug source via `load_climate_zones()`; do not infer slugs from filenames.

## Tasks & Acceptance

**Execution:**
- [x] `canbus/tools/generate_nodes.py` -- Add deterministic CAN measurement route metadata for SHT45 temp/RH and SEN66 temp/RH, PM1.0, PM2.5, PM4.0, PM10, VOC index, NOx index, and CO2 -- Ensures the generated artifact maps every producer measurement to the epic's room-scoped CAN source IDs.
- [x] `canbus/tools/generate_nodes.py` -- Add a renderer/writer for `hvac/packages/generated/can_sensor_routes.yaml` and call it only after registry/bindings validation succeeds -- Produces the compile-time HVAC artifact without weakening validate-before-persist behavior.
- [x] `canbus/tests/test_generate_exports.py` -- Add renderer tests for empty registries, mixed sensor/non-sensor rows, route target IDs, deterministic output, and room moves -- Covers the story's routing and idempotence requirements without mutating real registry data.
- [x] `canbus/tests/test_generate_exports.py` -- Add temp-generator tests for `sensors=1` with blank, unknown, and floor-mismatched `room_slug` values, plus no partial route-file write on abort -- Proves invalid joins fail before generated artifacts are persisted.
- [x] `hvac/packages/generated/can_sensor_routes.yaml` -- Regenerate via `python3 canbus/tools/generate_nodes.py` -- Commits the generated empty route artifact for the current placeholder registry.

**Acceptance Criteria:**
- Given a `sensors=1` registry row with blank `room_slug`, when `generate_nodes.py` runs, then it exits non-zero with a clear room-slug-required error and does not leave a new route artifact in the temp output tree.
- Given a `sensors=1` registry row whose `room_slug` is unknown or on the wrong climate floor, when `generate_nodes.py` runs, then it exits non-zero with the existing validation error and writes no generated node or route artifacts.
- Given mixed valid rows where only one node has `sensors=1`, when the route renderer runs, then the artifact includes only that node's room and maps each supported measurement type to the expected `<room_slug>_*_can` target ID.
- Given identical route inputs, when the renderer or generator is run twice, then `can_sensor_routes.yaml` is byte-identical.
- Given a valid sensor node is moved from one valid room slug to another, when routes are regenerated, then the artifact changes from the old room-scoped targets to the new ones and contains no stale old-room targets.
- Given the committed placeholder registry, when `python3 canbus/tools/generate_nodes.py` runs, then `hvac/packages/generated/can_sensor_routes.yaml` is generated as an empty route package and no climate runtime package is composed.

## Spec Change Log

## Review Triage Log

### 2026-07-11 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 3: (high 0, medium 2, low 1)
- defer: 0
- reject: 1: (high 0, medium 0, low 1)
- addressed_findings:
  - `[medium]` `[patch]` Non-empty route packages used protocol constants without providing `canbus_protocol.h`; added a generated `esphome.includes` entry and renderer coverage.
  - `[medium]` `[patch]` Measurement route metadata was only tested against itself; added a test comparing generated route constants to `canbus/protocol/canbus_protocol.h` sensor constants.
  - `[low]` `[patch]` A known climate `room_slug` that cannot form a valid ESPHome ID prefix could generate invalid route IDs; added route validation and a temp-generator failure test.

## Design Notes

The generated YAML should be useful to Story HVAC-1.2 without taking over that story. A practical shape is a package that declares the target template sensors plus generated scripts such as `can_sensor_route_publish` and `can_sensor_route_publish_nan`, parameterized by `node_id`, `measurement_type`, and value. Each generated branch should use named protocol constants like `SENSOR_SHT45_TEMP`, publishing to IDs such as `anticamera_temp_can`, `anticamera_humidity_can`, `anticamera_co2_can`, and `anticamera_pm2_5_can`. With no `sensors=1` rows, the file should still carry its generated header and an explicit empty-routes comment.

Reject duplicate `sensors=1` rows for the same `room_slug` unless the implementation can make the conflict impossible by construction. The receiver-facing API is room-scoped, so duplicate producers for one room would otherwise race on the same template sensor IDs.

## Verification

**Commands:**
- `python3 canbus/tests/test_generate_exports.py` -- expected: all generator/export tests pass.
- `python3 canbus/tools/generate_nodes.py` -- expected: succeeds from repo root and writes/refreshes the generated HVAC route artifact.
- `git diff --check` -- expected: no whitespace errors in generated or hand-authored changes.

## Auto Run Result

Status: done

Summary: Implemented the generated HVAC CAN sensor routing artifact for story HVAC-1.1. The CAN node generator now renders an idempotent `hvac/packages/generated/can_sensor_routes.yaml` package from validated `sensors=1` registry rows, rejects ambiguous or invalid room routes before persisting generated outputs, and keeps the current placeholder registry output empty-but-valid.

Files changed:
- `canbus/tools/generate_nodes.py` -- Added CAN sensor route metadata, generated YAML rendering, route validation, and artifact writing.
- `canbus/tests/test_generate_exports.py` -- Added route renderer, validation, idempotence, room-move, protocol-drift, and invalid ID-prefix coverage.
- `hvac/packages/generated/can_sensor_routes.yaml` -- Added generated empty route package for the current `sensors=0` registry.
- `_bmad-output/implementation-artifacts/epic-HVAC-1-context.md` -- Cached compiled HVAC Epic 1 context required by dev-auto.
- `_bmad-output/implementation-artifacts/spec-hvac-1-1-generated-can-sensor-routing-artifact.md` -- Captured spec, review triage, and run result.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- Marked HVAC Epic 1 in progress and HVAC-1.1 done.

Review findings breakdown: patched 3 findings (2 medium, 1 low), deferred 0, rejected 1. Patched items made non-empty route packages self-sufficient for protocol constants, added protocol-header drift coverage, and rejected room slugs that cannot form ESPHome IDs.

Follow-up review recommendation: false. Review-driven changes were localized, covered by focused tests, and reverified with the full generator test suite.

Verification performed:
- `python3 canbus/tests/test_generate_exports.py` -- passed, 26 export-pipeline tests.
- `python3 canbus/tools/generate_nodes.py` -- passed, regenerated bindings/map/HA package/node map/node YAMLs and `can_sensor_routes.yaml`.
- `git diff --check` -- passed.
- Temporary `esphome config` check for a non-empty generated route package -- passed.
- VS Code diagnostics for modified generator/test files -- no errors. The generated package is valid as a package; standalone validation may require a consumer config with `esphome:`.

Residual risks: The committed registry has no `sensors=1` production rows yet, so the non-empty route artifact is covered by renderer tests and a temporary ESPHome config fixture rather than a committed climate-controller composition. Story HVAC-1.2/HVAC-1.3 will exercise the generated scripts in the real receiver package.