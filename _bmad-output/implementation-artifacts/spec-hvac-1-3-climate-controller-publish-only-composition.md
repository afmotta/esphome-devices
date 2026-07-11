---
title: 'HVAC-1.3 Climate Controller Publish-Only Composition'
type: 'feature'
created: '2026-07-11'
status: 'done'
baseline_revision: '59e1a48'
review_loop_iteration: 0
followup_review_recommended: false
final_revision: 'b5c8eab'
context:
  - '{project-root}/hvac/CLAUDE.md'
  - '{project-root}/canbus/CLAUDE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-HVAC-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-hvac-1-2-sensor-only-can-receiver-freshness-core.md'
warnings: []
---

<intent-contract>

## Intent

**Problem:** HVAC-1.2 built a receive-only CAN sensor receiver package and its generated route dependency, but `devices/climate-control.yaml` (the real climate controller entry point) does not compose either one, so no CAN source entities exist on the actual controller for inspection before any control-flip work begins.

**Approach:** Add the generated routes package and the `can_sensor_receiver.yaml` package to `devices/climate-control.yaml`'s `packages:` (routes before receiver, matching the HVAC-1.2 compile fixture order), plus the three headers (`canbus_protocol.h`, `generated_can_sensor_routes.h`, `can_sensor_receiver.h`) to its `esphome: includes:`. Purely additive composition — no control logic changes.

## Boundaries & Constraints

**Always:** Compose `../hvac/packages/generated/can_sensor_routes.yaml` before `../hvac/packages/can_sensor_receiver.yaml` in `devices/climate-control.yaml`'s `packages:` map, mirroring `hvac/tests/compile_can_sensor_receiver.yaml`'s order; add `esphome: includes:` for `../canbus/protocol/canbus_protocol.h`, `../hvac/protocol/generated_can_sensor_routes.h`, and `../hvac/protocol/can_sensor_receiver.h` using the same relative-path convention `devices/gateway.yaml` already uses for its own includes; rely on `can_sensor_receiver.yaml`'s own substitution defaults (`can_tx_pin`, `can_rx_pin`, `can_bit_rate`, `can_sensor_stale_check_interval`) rather than redeclaring them; leave `devices/locals/climate-control.yaml` untouched unless it fails to compile through the unchanged wrapper.

**Block If:** any substitution name already defined in `devices/climate-control.yaml` or `boards/t-connect-pro.yaml` collides with `can_tx_pin`, `can_rx_pin`, `can_bit_rate`, or `can_sensor_stale_check_interval` with a conflicting value (none found during planning, but re-verify before editing).

**Never:** Do not add `canbus/packages/health.yaml`, `lighting/packages/buttons.yaml`, `lighting/packages/relay_bank.yaml`, or any arbitration/discovery package to `devices/climate-control.yaml` — those remain exclusive to `devices/gateway.yaml`; do not modify `hvac/packages/can_sensor_receiver.yaml`, `hvac/packages/generated/can_sensor_routes.yaml`, any file under `canbus/protocol/`, `hvac/protocol/`, or `registry/`; do not touch `hvac/room_sensors.yaml`, room PID/humidity/dew-point/MEV logic, or any CAN-primary failover behavior (that is HVAC-1.4); do not modify `devices/gateway.yaml`.

</intent-contract>

## Code Map

- `devices/climate-control.yaml` -- Add `esphome: includes:` for the three headers and add the `can_routes`/`can_receiver` packages (in that order) to the existing `packages:` map.
- `devices/locals/climate-control.yaml` -- Thin secrets wrapper that `!include`s `../climate-control.yaml`; expected to need no edits since the new packages use their own substitution defaults, but verify it still compiles.
- `hvac/packages/can_sensor_receiver.yaml` -- Read-only (HVAC-1.2 output); defines the receive-only `canbus:` platform, `on_frame` guard, globals, and stale sweep being composed in.
- `hvac/packages/generated/can_sensor_routes.yaml` -- Read-only generated artifact; provides `can_sensor_route_publish`/`can_sensor_route_publish_nan` scripts the receiver calls.
- `hvac/protocol/can_sensor_receiver.h`, `hvac/protocol/generated_can_sensor_routes.h`, `canbus/protocol/canbus_protocol.h` -- Read-only headers required by the receiver's lambdas; must be listed in `esphome: includes:` for the compiled firmware to link.
- `boards/t-connect-pro.yaml` -- Read-only; already provides the `esp32s3`/`esp-idf` framework the `esp32_can` platform requires. Its comment calling the onboard TWAI transceiver "unconsumed by hvac today" becomes stale once this story lands (no edit required by this story).
- `devices/gateway.yaml` -- Read-only reference showing the gateway-only packages/includes that must stay off the climate controller, and the `../canbus/protocol/...` include-path convention to mirror.
- `hvac/tests/compile_can_sensor_receiver.yaml` -- Read-only reference for correct package order and the exact include list.

## Tasks & Acceptance

**Execution:**
- [x] `devices/climate-control.yaml` -- Add an `esphome:` block with `includes: [../canbus/protocol/canbus_protocol.h, ../hvac/protocol/generated_can_sensor_routes.h, ../hvac/protocol/can_sensor_receiver.h]` -- Makes the receiver's decode/scaling/freshness helpers available to the compiled firmware. **Implementation note:** the literal `../...` paths from this task/Design Notes resolve relative to `boards/t-connect-pro.yaml`'s directory correctly when `devices/climate-control.yaml` is compiled directly, but ESPHome resolves `esphome.includes` relative to the top-level file passed on the CLI. Since `climate-control.yaml` is only ever compiled through a one-level-deeper wrapper (`devices/locals/*.yaml`/`devices/remotes/*.yaml`, per its own `defaults:` pattern — see `devices/gateway.yaml`'s comment on that pattern), the paths actually needed one extra `../` (`../../canbus/protocol/canbus_protocol.h`, etc.) to resolve when validated via `esphome config devices/locals/climate-control.yaml`. Used `../../` to satisfy the verification command; see Design Notes below.
- [x] `devices/climate-control.yaml` -- Add `can_routes: !include ../hvac/packages/generated/can_sensor_routes.yaml` and `can_receiver: !include ../hvac/packages/can_sensor_receiver.yaml` to `packages:`, routes entry ordered before receiver entry -- Composes the publish-only CAN sensor path onto the real climate controller.
- [x] `devices/locals/climate-control.yaml` -- Compile-check only, no expected edit -- Confirmed the local wrapper still resolves through the updated entry point (`esphome config devices/locals/climate-control.yaml` exits 0); no edit made to this file.
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- Mark `hvac-1-3-climate-controller-publish-only-composition` done only after verification passes -- Keeps BMAD tracking accurate.

**Acceptance Criteria:**
- Given `devices/climate-control.yaml`, when its `packages:` map is inspected, then it includes the generated CAN sensor routes package and the `can_sensor_receiver.yaml` package, with routes ordered before the receiver.
- Given `devices/climate-control.yaml`, when its `esphome: includes:` list is inspected, then it contains `canbus_protocol.h`, `generated_can_sensor_routes.h`, and `can_sensor_receiver.h`.
- Given `devices/climate-control.yaml`, when its full composition is inspected, then it contains none of `canbus/packages/health.yaml`, `lighting/packages/buttons.yaml`, `lighting/packages/relay_bank.yaml`, or any arbitration package.
- Given `esphome config devices/locals/climate-control.yaml`, when run, then it exits successfully with the CAN bus, Modbus, Ethernet, API, OTA, and logger configuration all present and valid alongside the existing room/coordinator packages.
- Given the story's diff, when inspected, then `hvac/room_sensors.yaml`, room PID/humidity/dew-point/MEV logic, `hvac/packages/can_sensor_receiver.yaml`, `hvac/packages/generated/can_sensor_routes.yaml`, `devices/gateway.yaml`, and every file under `canbus/protocol/`, `hvac/protocol/`, and `registry/` are unchanged.

## Design Notes

Include paths mirror `devices/gateway.yaml`'s existing convention (`../canbus/protocol/...`) since both files live one level below the repo root under `devices/`. Package order matters here for the same reason it did in the HVAC-1.2 compile fixture: `can_sensor_receiver.yaml`'s `on_frame` action calls `can_sensor_route_publish`/`can_sensor_route_publish_nan`, which only exist once the generated routes package has loaded — declare the `can_routes` package entry before `can_receiver` in the YAML map.

**Correction found during implementation (2026-07-11):** `devices/gateway.yaml` is compiled directly, so its top-level file and its `includes:`-declaring file are the same directory (`devices/`), and `../canbus/protocol/...` is correct for it. `devices/climate-control.yaml` is different: it is never compiled directly (its `defaults:` substitutions are a no-op unless loaded via `!include`, exactly as `devices/gateway.yaml`'s own comment describes for that pattern) — it is always compiled through `devices/locals/*.yaml` or `devices/remotes/*.yaml`, one directory level deeper. ESPHome resolves `esphome.includes` paths relative to the top-level CLI-invoked file, not the file where `includes:` is declared. So through the `devices/locals/climate-control.yaml` wrapper used in this story's own Verification command, `../canbus/protocol/canbus_protocol.h` resolves to the wrong (nonexistent) `devices/canbus/protocol/canbus_protocol.h`. The paths actually added are `../../canbus/protocol/canbus_protocol.h`, `../../hvac/protocol/generated_can_sensor_routes.h`, and `../../hvac/protocol/can_sensor_receiver.h`, which validated successfully against `esphome config devices/locals/climate-control.yaml`.

Because the committed registry is still the empty placeholder (`sensors=0`), the generated routes package resolves to no-op scripts. Verification for this story is about composition and successful config validation, not about observing populated CAN source sensors in Home Assistant — that requires a registry change out of this story's scope.

## Review Triage Log

### 2026-07-11 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 2: (high 0, medium 0, low 2)
- defer: 1: (high 0, medium 0, low 1)
- reject: 9: (high 0, medium 0, low 9)
- addressed_findings:
  - `[low]` `[patch]` No inline comment explained why `devices/climate-control.yaml`'s new `esphome.includes` paths use `../../` instead of `devices/gateway.yaml`'s `../` convention, and nothing warned that this file cannot be compiled directly; added a comment above `esphome: includes:` explaining ESPHome resolves `includes:` relative to the top-level CLI-invoked file's directory (verified against ESPHome 2026.5.0 source: `CORE.relative_config_path` / `config_dir`), not this file's own directory, and that direct compilation is unsupported.
  - `[low]` `[patch]` The `can_routes`/`can_receiver` package entries had no comment explaining their position or that this composition is currently no-op wiring (empty registry); added a short comment above the two entries.

Rejected findings (with evidence): a reviewer flagged that `devices/remotes/climate-control.yaml` (the GitHub-package-fetch entry point) was unverified for the same `../../` path depth. Rejected with evidence — inspected ESPHome 2026.5.0 source (`esphome/core/__init__.py`: `relative_config_path`/`config_dir` derive from `self.config_path`, the CLI-invoked file) and confirmed `add_includes` in `esphome/core/config.py` resolves via `CORE.relative_config_path(include)`. Both `devices/locals/climate-control.yaml` and `devices/remotes/climate-control.yaml` are the CLI-invoked file at the same directory depth (`devices/locals/` and `devices/remotes/`), regardless of whether their content is read from disk or fetched via the packages URL mechanism, so `../../` resolves identically for both. A reviewer's claim that a single `esphome config` exit-0 didn't prove the new top-level `esphome:` key merges cleanly with package-contributed `esphome:` keys (name/friendly_name/min_version/comment/on_boot) was also rejected with evidence — the full resolved config was inspected and shows all keys merged correctly alongside the new `includes:` list. Remaining findings (no regression compile fixture for `devices/climate-control.yaml`, no CLAUDE.md update, duplicated path literals across files at different compile depths, no structural lint enforcing the "Never" boundaries, sprint-status flipped to done before this review pass completed, and the receiver/routes composition being untested against a populated registry) were rejected as out of this story's scope or as expected/documented limitations, except the missing regression-fixture suggestion, which was deferred as a real but non-blocking future improvement.

## Verification

**Commands:**
- `esphome config devices/locals/climate-control.yaml` -- expected: exits 0, full config (including the CAN bus, Modbus, room packages, and coordinators) validates without errors.
- `git diff --check` -- expected: no whitespace errors.

## Auto Run Result

Status: done

Summary: Composed the already-implemented (HVAC-1.2) CAN sensor receiver package and its generated route dependency into the real climate controller entry point, `devices/climate-control.yaml`, in publish-only mode. Added the three required headers to `esphome: includes:` and the two packages (`can_routes` before `can_receiver`) to `packages:`. No control logic, room sensor failover, or MEV logic was touched.

Files changed:
- `devices/climate-control.yaml` -- Added `esphome: includes:` for `canbus_protocol.h`, `generated_can_sensor_routes.h`, and `can_sensor_receiver.h` (at `../../` depth, since this file is only ever compiled through the one-level-deeper `devices/locals/*.yaml`/`devices/remotes/*.yaml` wrappers), and added `can_routes`/`can_receiver` package entries ordered before the pre-existing `analog_outputs_1` entry. Added explanatory comments for both, added during the review pass.
- `_bmad-output/implementation-artifacts/spec-hvac-1-3-climate-controller-publish-only-composition.md` -- New spec file for this story.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- Marked `hvac-1-3-climate-controller-publish-only-composition` done.
- `_bmad-output/implementation-artifacts/deferred-work.md` -- Recorded the missing regression-fixture gap for `devices/climate-control.yaml`'s CAN composition as deferred work.

Review findings breakdown: patched 2 low-severity findings (missing explanatory comments for the `../../` path depth / direct-compile restriction, and for the package block's position/no-op status), deferred 1 low-severity finding (no committed regression fixture guarding this composition, beyond the existing isolated HVAC-1.2 test fixture), and rejected 9 findings — including one (`devices/remotes/climate-control.yaml`'s path depth being unverified) that was investigated and disproved by reading the installed ESPHome 2026.5.0 source (`CORE.relative_config_path`/`config_dir` and `add_includes`), confirming both `devices/locals/` and `devices/remotes/` wrappers resolve `includes:` identically since both are the CLI-invoked file at the same directory depth. Follow-up review recommendation: false — patches were two localized, cosmetic comment additions with no behavior change; the rejected/deferred findings required only inspection, not code changes.

Verification performed:
- `esphome config devices/locals/climate-control.yaml` -- passed both before and after the review-pass comment additions; exit 0, "Configuration is valid!", full resolved config confirmed the `canbus:`/`esp32_can` platform, Modbus, Ethernet, API, OTA, logger, and all room/coordinator packages present, and confirmed the three header paths resolve to the correct absolute files (`.../canbus/protocol/canbus_protocol.h`, etc.) and that the new `esphome.includes` key merges cleanly alongside package-contributed `esphome:` keys (name, friendly_name, min_version, comment, on_boot).
- `git diff --check` -- passed, no whitespace errors.
- `git status --short` -- confirmed no forbidden files touched (`devices/gateway.yaml`, `hvac/room_sensors.yaml`, room PID/humidity/MEV logic, `hvac/packages/can_sensor_receiver.yaml`, `hvac/packages/generated/can_sensor_routes.yaml`, and everything under `canbus/protocol/`, `hvac/protocol/`, `registry/` are all unchanged).

Residual risks: The committed registry remains empty (`sensors=0`), so this composition is currently no-op wiring on the real controller; no CAN source entities will be visible in Home Assistant until a registry change (out of this story's scope) enables a real node. `devices/remotes/climate-control.yaml` was verified analytically (via ESPHome source inspection) rather than by an actual network fetch/compile against GitHub, since that requires live credentials and network access unavailable in this environment. Deferred: no committed regression fixture guards this exact composition (package order, include depth) in `devices/climate-control.yaml` itself beyond the existing isolated `hvac/tests/compile_can_sensor_receiver.yaml` fixture and this story's manual verification.
