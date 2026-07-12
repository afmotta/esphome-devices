---
title: 'HVAC-1.5 CAN Air-Quality MEV Demand Integration'
type: 'feature'
created: '2026-07-11'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 'e6e89632da472de08999190d6842751e66bd8aa3'
final_revision: '6fe1d50776f8c9aa7b980a5f33f7965fec921cc7'
context:
  - '{project-root}/hvac/CLAUDE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-HVAC-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-hvac-1-4-can-primary-room-sensor-failover.md'
warnings: []
---

<intent-contract>

## Intent

**Problem:** First-floor MEV demand still derives CO2/IAQ from the legacy S1 UDP `packet_transport` room sensors (`hvac/rooms/first_floor/first-floor.yaml`), and `hvac/mev_demand.yaml` computes a single generic "IAQ" channel instead of the target CO2 / Air-Quality-Pollutants / Humidity split, so MEV cannot yet use raw CAN VOC/NOx/PM measurements.

**Approach:** Replace the 8 per-room UDP `co2`/`iaq` `packet_transport` sensors in `first-floor.yaml` with statically-declared per-room CAN pollutant source sensors (`_co2_can`, `_voc_index_can`, `_nox_index_can`, `_pm1_0_can`, `_pm2_5_can`, `_pm4_0_can`, `_pm10_can`, following the HVAC-1.4 static-declaration pattern so `hvac/packages/can_sensor_receiver.yaml`'s dispatch scripts always have a valid publish target), re-aggregate each pollutant across the 8 rooms via `combination`/`max`, and rework `hvac/mev_demand.yaml` to add proportional demand channels (VOC, NOx, PM1.0, PM2.5, PM4.0, PM10) collapsed via MAX into one `air_quality_demand`, while keeping CO2 and Humidity as separate top-level channels.

## Boundaries & Constraints

**Always:** Keep `hvac/room_sensors.yaml`, `vesta/packages/components/failover_sensor.yaml`, and the temperature/humidity abstracted-sensor contract untouched — this story only touches air-quality/pollutant plumbing. Expose all per-room CAN pollutant sensors to Home Assistant (not `internal: true`) per the epic's Entity Contract (`<room_slug>_co2_can`, `_voc_index_can`, `_nox_index_can`, `_pm1_0_can`, `_pm2_5_can`, `_pm4_0_can`, `_pm10_can`). Keep CO2 and Humidity as independent top-level MEV demand channels; derive a new `${mev_slug}_air_quality_demand` as the MAX of normalized VOC/NOx/PM1.0/PM2.5/PM4.0/PM10 demand sensors (each built via `vesta/packages/components/proportional_demand_sensor.yaml`, mirroring the existing `iaq_demand` block's HA `input_number` lower/upper-bound wiring convention, e.g. `input_number.mev_voc_lower_bound`/`upper_bound`, etc. for each pollutant). Update the final `${mev_slug}_max_demand` lambda to `max(co2, air_quality, humidity)` and keep `text_sensor.${mev_slug}_dominant_demand` at the control-channel level (`CO2`, `Air Quality`, `Humidity`, `Ventilation`) only — do not surface individual pollutants there. Update `hvac/mev_modbus.yaml`'s `demand:` package `vars` to match the new `hvac/mev_demand.yaml` var contract (drop `iaq_sensor`, add the pollutant sensor vars sourced from new first-floor `combination` aggregates). Update doc comments/headers in `hvac/mev_demand.yaml` and `hvac/rooms/first_floor/first-floor.yaml` to describe the new shape; update `hvac/CLAUDE.md`'s MEV entity list and the "CO2/IAQ still reports over UDP `packet_transport`" lines (both occurrences) to describe the CAN-sourced pollutant path instead.

**Block If:** Any file outside `hvac/rooms/first_floor/first-floor.yaml`, `hvac/mev_demand.yaml`, `hvac/mev_modbus.yaml` is found depending on the current `first_floor_max_co2`/`first_floor_max_iaq` sensor IDs or the room-level `_co2`/`_iaq` UDP sensor IDs — re-verify before renaming/removing them (a mismatch changes this story's Task list). Any second-floor/ground-floor MEV consumer of `iaq_sensor` beyond `hvac/mev_modbus.yaml`'s single first-floor include — this epic scope is first-floor only, so a second consumer needs a decision on whether to migrate it too.

**Never:** Do not touch `hvac/room_sensors.yaml`, temperature/humidity failover wiring, `devices/climate-control.yaml`'s `packet_transport:`/`canbus:` composition, `hvac/packages/can_sensor_receiver.yaml`'s decode/freshness core, `canbus/tools/generate_nodes.py`, `registry/nodes.csv`, or `hvac/packages/generated/can_sensor_routes.yaml` — this story only wires MEV-side demand consumption of already-static/generated CAN pollutant sensors, it does not touch routing or receiver internals. Do not add a per-pollutant top-level MEV demand channel (the deferred alternative in the epic doc) — keep the single collapsed `air_quality_demand`. Do not remove the room-sensor UDP `packet_transport` provider entries from `devices/climate-control.yaml`'s `providers:` list even after this story stops consuming their CO2/IAQ sensors (out of scope; tracked separately if ever needed).

</intent-contract>

## Code Map

- `hvac/rooms/first_floor/first-floor.yaml` -- currently declares 8x `packet_transport` CO2 + 8x IAQ UDP sensors and `first_floor_max_co2`/`first_floor_max_iaq` `combination` aggregates; replace with static per-room CAN pollutant sensors + pollutant-specific `combination` aggregates.
- `hvac/mev_demand.yaml` -- currently takes `co2_sensor`/`iaq_sensor` vars and includes one `iaq_demand` proportional-demand package; rework to 4 pollutant demand packages + `air_quality_demand` MAX + updated `max_demand`/`dominant_demand` lambda.
- `hvac/mev_modbus.yaml` -- passes `co2_sensor`/`iaq_sensor` vars into `mev_demand.yaml`; update to pass CO2 + 4 pollutant sensor vars.
- `vesta/packages/components/proportional_demand_sensor.yaml` -- reused unmodified template for each of the 4 new pollutant demand instances.
- `hvac/CLAUDE.md` -- MEV entity list + "CO2/IAQ still reports over UDP" lines need updating to match the new CAN-sourced shape.

## Tasks & Acceptance

**Execution:**
- [x] `hvac/rooms/first_floor/first-floor.yaml` -- Replace the 8 `packet_transport` CO2 and 8 IAQ sensors with statically-declared `platform: template` CAN sensors per room (`${room}_co2_can`, `${room}_voc_index_can`, `${room}_nox_index_can`, `${room}_pm1_0_can`, `${room}_pm2_5_can`, `${room}_pm4_0_can`, `${room}_pm10_can`), all `internal: false` with appropriate `unit_of_measurement`/`device_class` (mirror `hvac/room_sensors.yaml`'s CAN-static-sensor pattern and the epic's Entity Contract) -- makes them valid always-present CAN dispatch targets and exposes raw pollutants to HA per AC1.
- [x] `hvac/rooms/first_floor/first-floor.yaml` -- Replace `first_floor_max_co2`/`first_floor_max_iaq` `combination` blocks with `first_floor_max_co2`, `first_floor_max_voc_index`, `first_floor_max_nox_index`, `first_floor_max_pm1_0`, `first_floor_max_pm2_5`, `first_floor_max_pm4_0`, `first_floor_max_pm10` (`type: max` across the 8 rooms' new `_can` sensors) -- feeds the new per-pollutant MEV demand channels.
- [x] `hvac/mev_demand.yaml` -- Drop the `iaq_sensor` var/`iaq_demand` package; add `voc_sensor`/`nox_sensor`/`pm2_5_sensor`/`pm10_sensor` vars, each wired through its own `proportional_demand_sensor.yaml` include (new `input_number.mev_{voc,nox,pm2_5,pm10}_{lower,upper}_bound` HA entities, mirroring existing bound-entity naming); add `${mev_slug}_air_quality_demand` template sensor computing `max(voc_demand, nox_demand, pm2_5_demand, pm10_demand)`; update `${mev_slug}_max_demand` lambda to `max(co2, air_quality, humidity)` and `dominant_demand` to report `CO2`/`Air Quality`/`Humidity`/`Ventilation` -- implements the CO2/Air-Quality/Humidity split from the epic's MEV Air-Quality Model.
- [x] `hvac/mev_modbus.yaml` -- Update the `demand:` package's `vars` to pass `voc_sensor: first_floor_max_voc_index`, `nox_sensor: first_floor_max_nox_index`, `pm2_5_sensor: first_floor_max_pm2_5`, `pm10_sensor: first_floor_max_pm10` alongside the existing `co2_sensor`/`humidity_sensor` -- keeps the MEV controller composition consistent with the new `mev_demand.yaml` contract.
- [x] `hvac/CLAUDE.md` -- Update the MEV entity example list (`first_floor_mev_co2_demand` block) to include `air_quality_demand`, and rewrite both "room CO2/IAQ still reports over UDP `packet_transport`" lines to describe the CAN-sourced pollutant path -- keeps documentation aligned with the new architecture.

**Acceptance Criteria:**
- Given a first-floor room's CAN node publishes an `SEN66_CO2`/`VOC_INDEX`/`NOX_INDEX`/`PM2_5`/`PM10` measurement, when `can_sensor_receiver.yaml`'s dispatch script runs, then the corresponding `${room}_..._can` sensor updates and is visible (non-internal) in Home Assistant.
- Given all 8 first-floor rooms' pollutant sensors, when the `combination`/`max` aggregates evaluate, then `first_floor_max_voc_index`/`_nox_index`/`_pm2_5`/`_pm10` reflect the maximum across rooms, matching the existing `first_floor_max_co2` pattern.
- Given VOC/NOx/PM2.5/PM10 demand sensors, when `${mev_slug}_air_quality_demand` evaluates, then it returns the max of the four, and `${mev_slug}_max_demand` returns `max(co2_demand, air_quality_demand, humidity_demand)`.
- Given `air_quality_demand` is the largest of the three channels, when `dominant_demand` publishes, then it reports `"Air Quality"` (not an individual pollutant name).
- Given `esphome config devices/locals/climate-control.yaml`, when run, then it succeeds with no undefined-ID or duplicate-ID errors.

## Verification

**Commands:**
- `esphome config devices/locals/climate-control.yaml` -- expected: validates cleanly, confirming new sensor IDs/vars resolve and no duplicates were introduced.
- `esphome compile devices/locals/climate-control.yaml` -- expected: compiles cleanly (final confidence check; may be skipped if environment lacks toolchain, per repo memory on prior stories).

## Spec Change Log

## Review Triage Log

### 2026-07-11 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 0
- defer: 1 (low)
- reject: 14 (medium 3, low 11)
- addressed_findings:
  - none

## Auto Run Result

**Status:** done

**Summary:** Replaced the 8 rooms' UDP `packet_transport` CO2/IAQ sensors in `hvac/rooms/first_floor/first-floor.yaml` with statically-declared CAN pollutant sensors (CO2, VOC index, NOx index, PM1.0/2.5/4.0/10), matching the HVAC-1.4 static-declaration pattern so they are always-valid dispatch targets. Reworked `hvac/mev_demand.yaml` into three top-level MEV demand channels (CO2, Air Quality, Humidity), with Air Quality computed as the MAX of proportional pollutant-demand sensors (VOC, NOx, PM1.0, PM2.5, PM4.0, PM10). Updated `hvac/mev_modbus.yaml`'s `demand:` package vars and `hvac/CLAUDE.md`'s MEV entity list / CO2-IAQ-over-UDP documentation to match.

**Files changed:**
- `hvac/rooms/first_floor/first-floor.yaml` -- replaced 16 UDP CO2/IAQ sensors + 2 combination aggregates with 56 static CAN pollutant sensors + 5 per-pollutant `combination` max aggregates.
- `hvac/mev_demand.yaml` -- dropped `iaq_sensor`/`iaq_demand`; added `voc_sensor`/`nox_sensor`/`pm2_5_sensor`/`pm10_sensor` vars, 4 new proportional demand packages, an `air_quality_demand` MAX sensor, and updated `max_demand`/`dominant_demand` logic.
- `hvac/mev_modbus.yaml` -- updated `demand:` package vars to the new contract.
- `hvac/CLAUDE.md` -- updated MEV entity example list and both CO2/IAQ-over-UDP description lines.
- `_bmad-output/implementation-artifacts/deferred-work.md` -- appended one deferred finding (missing HA `input_number` helper entities for new pollutant bounds — pre-existing convention gap, mirrors the same gap for CO2/humidity).
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- marked `hvac-1-5-can-air-quality-mev-demand-integration: done`.

**Review findings breakdown:** 0 patches applied, 1 item deferred (low severity — missing HA `input_number` helper entities, pre-existing convention gap not caused by this story), 14 items rejected as noise/out-of-scope/incorrect (e.g. claims about missing lambdas on the static template sensors, which is the intentional HVAC-1.4-established dispatch pattern; claims about entity-ID "breaking changes," which mirror this repo's existing internal-migration convention with no external consumers frozen by contract).

**Follow-up review recommendation:** false — no patch or bad_spec changes were made in this pass; the diff shipped as originally planned.

**Verification performed:**
- `esphome config devices/locals/climate-control.yaml` -- succeeded, "Configuration is valid!".
- `esphome compile devices/locals/climate-control.yaml` -- succeeded, "Successfully compiled program." (77s build, RAM 29.4%, Flash 9.3%).

**Residual risks:**
- New pollutant `input_number` HA helper entities are not created by any committed HA package (deferred; pre-existing pattern for CO2/humidity too) — proportional demand sensors will read from those `homeassistant:` sensors as NaN/unavailable until an operator creates them, falling back to `fallback_value` (20.0) exactly as CO2/humidity already do.
- No first-floor CAN node is yet flipped to `sensors=1` in `registry/nodes.csv` for these rooms, so the new CAN pollutant sensors will read NaN in production until HVAC-1.6 bench rollout enables real nodes — this matches the epic's rollout sequencing and is expected, not a regression.

## Follow-Up Change Log

### 2026-07-12 — PM1.0/PM4.0 join Air Quality demand
- Trigger: User asked to include PM1.0 and PM4.0 when no valid technical reason was found to exclude them.
- Change: `hvac/mev_demand.yaml` now includes `pm1_0_demand` and `pm4_0_demand`; `hvac/mev_modbus.yaml` and the first-floor caller expose/pass the matching aggregate sensor vars.
- Result: Air Quality remains one top-level MEV control family, but its MAX now covers VOC, NOx, PM1.0, PM2.5, PM4.0, and PM10.

