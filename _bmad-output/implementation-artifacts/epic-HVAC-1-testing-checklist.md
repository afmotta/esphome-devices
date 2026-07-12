# Epic HVAC-1 Testing Checklist: CAN Sensor Receiver Bench Validation

**Date:** July 11, 2026
**Status:** Pending hardware execution (system is pre-live)
**Scope:** Epic HVAC-1 ACs 7-9 (bench proofs) + AC10 (findings recording)
**Bench node:** node 101 (CANBed RP2040 + ADR-0006 SHT45/SEN66 sensor kit), registry-flipped to `sensors=1` / `room_slug=soggiorno`
**Controller:** LilyGO T-Connect Pro flashed with `devices/locals/climate-control.yaml` (receives `CAT_SENSOR` directly on its own CAN interface, ADR-0014)

Epic ACs 1-6 are software gates covered by `scripts/verification-battery.sh`; their
results for this story's run are recorded in
`epic-HVAC-1-completion-report.md`. This checklist is the script for the
**hardware bench session** that the completion report marks as pending.

---

## Bench Prerequisites

- [ ] node 101 board on the bench: CANBed RP2040 with the SHT45 + SEN66 sensor kit wired per `canbus/packages/sensor_kit.yaml`
- [ ] T-Connect Pro climate controller wired to the same CAN bus segment (TWAI TX=IO6 / RX=IO7), 120 Ω termination at both bus ends
- [ ] Controller reachable over Ethernet; laptop with ESPHome 2026.5.3 and this repo checked out
- [ ] Live Home Assistant with the ESPHome integration and the HA fallback source entities present and updating: `sensor.room_soggiorno_temperature`, `sensor.room_soggiorno_humidity` (the failover's Tier 2 — AC8 cannot pass without them)
- [ ] Modbus I/O boards attached (or consciously absent — expect per-switch unavailability noise in logs, not receiver interference)

## Pre-Flash Gates (software, before touching hardware)

1. [ ] Working tree clean, on the commit to be flashed: `git status`
2. [ ] Push-discipline gate (ADR-0009 — registry committed AND pushed; exit 0 = safe to flash):
   ```bash
   python3 canbus/tools/check_registry_pushed.py
   ```
3. [ ] Full verification battery green:
   ```bash
   bash scripts/verification-battery.sh
   ```

## Node 101 Flash Prep (per `canbus/docs/reflash-campaign-runbook.md` Path A)

1. [ ] Confirm the registry row is current: `registry/nodes.csv` line `101,0,8,0,Ground floor living room,1,soggiorno`
2. [ ] Regenerate and confirm a no-op (tree already reconciled by HVAC-1.6):
   ```bash
   python3 canbus/tools/generate_nodes.py && git diff --exit-code canbus hvac registry
   ```
3. [ ] Inspect `canbus/nodes/node101.yaml`: it must include `sensor_kit: !include ../packages/sensor_kit.yaml`
4. [ ] Compile the bench node firmware (RP2040):
   ```bash
   esphome compile canbus/nodes/node101.yaml
   ```
5. [ ] Flash node 101 over USB (nodes have no WiFi/OTA by design):
   ```bash
   esphome upload canbus/nodes/node101.yaml
   ```
6. [ ] Flash/confirm the controller with the current `devices/locals/climate-control.yaml` build and start log capture:
   ```bash
   esphome run devices/locals/climate-control.yaml
   esphome logs devices/locals/climate-control.yaml
   ```

---

## AC7 — CAN Tier Live (node 101 → CAN source sensors → abstracted `CAN` tier)

**Proves:** an existing node flipped to `sensors=1` with a valid `room_slug` updates CAN
source sensors and abstracted room control sensors through the HVAC controller.

1. [ ] Power node 101 on the bus; wait one sensor-kit cadence (frames every 30 s)
2. [ ] Controller logs show `CAT_SENSOR` frames from node 101 decoding and publishing (no unknown-route or malformed-frame warnings for node 101)
3. [ ] `soggiorno_temp_can` and `soggiorno_humidity_can` update every ~30 s with plausible bench values — these two are `internal: true` (declared in `hvac/room_sensors.yaml`), so observe them in the ESPHome log stream, not HA
4. [ ] Raw CAN diagnostic/pollutant entities are visible **in HA** and updating: `soggiorno_sen66_temp_can`, `soggiorno_sen66_humidity_can`, `soggiorno_co2_can`, `soggiorno_voc_index_can`, `soggiorno_nox_index_can`, `soggiorno_pm1_0_can`, `soggiorno_pm2_5_can`, `soggiorno_pm4_0_can`, `soggiorno_pm10_can`
5. [ ] `soggiorno_temp_abstracted_sensor_tier` reads `CAN` (and the humidity tier likewise)
6. [ ] `soggiorno_temp_abstracted` / `soggiorno_humidity_abstracted` track the CAN values (SHT45 source), **not** `sensor.room_soggiorno_temperature` — verify by making the HA source diverge (e.g. breathe on the SHT45; the abstracted value must follow the kit)
7. [ ] SEN66 temp/humidity remain diagnostic-only: abstracted values follow SHT45 even where SEN66 disagrees

**Expected observations:** tier label `CAN` within ~40 s of node power-on; abstracted
values equal the last OK SHT45 measurements; CO2/VOC/NOx/PM entities update at the
30 s cadence; non-OK statuses during SEN66 warm-up publish `NaN` (entity shows
unavailable/unknown in HA) without log spam.

## AC8 — CAN Stale > 90 s → `HA` Tier

**Proves:** stopping CAN frames for more than 90 seconds moves the room from CAN to HA.

1. [ ] Note the current tier (`CAN`) and wall-clock time, then power off node 101 (or disconnect its CAN connector)
2. [ ] For the first ~90 s: tier stays `CAN`, abstracted values hold the last CAN reading
3. [ ] Between ~90 s and ~100 s after the last OK frame (90 s stale threshold + up to one 10 s failover evaluation): controller logs show the stale sweep publishing `NaN` for node 101's routes; `soggiorno_temp_can`/`soggiorno_humidity_can` go `NaN`
4. [ ] `soggiorno_temp_abstracted_sensor_tier` flips to `HA`; abstracted values now track `sensor.room_soggiorno_temperature` / `sensor.room_soggiorno_humidity`
5. [ ] Room control keeps operating on the HA values (PID input stays valid; no emergency behavior)
6. [ ] Recovery: power node 101 back on — within ~40 s the tier returns to `CAN` automatically (no reboot, no manual action)

**Expected observations:** record the measured stale-to-`HA` latency (expected 90-100 s)
and the recovery-to-`CAN` latency (expected ≤ 40 s) in the findings table below.

## AC9 — CAN + HA Both Unavailable → `Emergency` / NaN

**Proves:** disabling both CAN and HA drives the abstracted sensor to `NaN` and triggers
the existing emergency behavior.

1. [ ] With node 101 still off (tier = `HA` from AC8), remove the HA source: stop Home Assistant, or disconnect the controller's Ethernet uplink to HA, or force `sensor.room_soggiorno_temperature`/`_humidity` unavailable in HA
2. [ ] `soggiorno_temp_ha` stops providing values; `soggiorno_temp_abstracted_sensor_tier` flips to `Emergency`
3. [ ] `soggiorno_temp_abstracted` / `soggiorno_humidity_abstracted` read `NaN` (unavailable/unknown in HA, if HA is still attached for observation; otherwise in the local log stream)
4. [ ] Existing NaN emergency behavior engages for the room: the PID loses its input and Soggiorno's zone actuation shuts down safely (radiant `relay_9` off) — record the exact behavior and timing observed (root `CLAUDE.md` documents safe shutdown within ~5 minutes; the bench measurement is the authoritative number)
5. [ ] Recovery ladder: restore HA only → tier returns to `HA` and control resumes; then power node 101 → tier returns to `CAN`

**Expected observations:** tier `Emergency` with both sources dead; no crash/reboot of
the controller; actuation fails safe (off), and recovery is automatic in tier order.

---

## AC10 — Findings Recording

Record every measurement and deviation from this bench session, then carry them into
`epic-HVAC-1-completion-report.md`'s bench-validation section (flip it from "pending
hardware execution" to the dated results) or, for tuning-sized items, into a follow-up
tuning note / `deferred-work.md`.

| # | Proof | Expected | Measured / Observed | Pass? |
|---|-------|----------|---------------------|-------|
| 1 | AC7: node power-on → tier `CAN` | ≤ ~40 s | | |
| 2 | AC7: CAN source cadence in HA | ~30 s | | |
| 3 | AC8: last OK frame → tier `HA` | 90-100 s | | |
| 4 | AC8: node repower → tier `CAN` | ≤ ~40 s | | |
| 5 | AC9: HA loss → tier `Emergency` | ≤ ~10 s after HA source drops | | |
| 6 | AC9: emergency actuation behavior | zone off (safe) | | |
| 7 | AC9: recovery ladder HA → CAN | automatic, in order | | |

- [ ] SEN66 warm-up behavior noted (how long non-OK statuses lasted, what HA showed)
- [ ] Any unknown-route / malformed-frame log lines captured verbatim
- [ ] MEV pollutant demand sanity: with node 101 live, `soggiorno_co2_can` etc. update — note that soggiorno is not an MEV input room (first floor only), so MEV demand should NOT move; confirm
- [ ] Any PID/threshold tuning observations recorded for the deferred/tuning list
- [ ] Bench timings fed back into `canbus/docs/reflash-campaign-runbook.md`'s TBD table (Path A time budget)

## Sign-off

- [ ] AC7 proven (CAN tier live end-to-end)
- [ ] AC8 proven (stale > 90 s → HA tier, automatic recovery)
- [ ] AC9 proven (CAN+HA off → Emergency/NaN + safe shutdown)
- [ ] AC10 satisfied (findings recorded in the completion report / tuning note)
- [ ] `hvac-epic-1` flipped to `done` in `sprint-status.yaml` (manual flip — only after all of the above)

**Tested by:** ________________
**Date:** ________________
