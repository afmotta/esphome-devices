# Epic HVAC-1 Completion Report: HVAC CAN Sensor Receiver

**Date:** July 11, 2026
**Status:** Software delivered — compile gates pending a network-unrestricted battery run; bench validation pending hardware execution
**Epic:** HVAC-Epic 1 (`HVAC-Epic-1-can-sensor-receiver.md`), 6 stories, 18 points
**Verification toolchain:** `esphome==2026.5.3` (vesta/tests/pyproject.toml's deliberate pin, >= repo floor 2026.5.0), Python 3.11, g++ 13

---

## Executive Summary

Epic HVAC-1 gives the climate controller its production room-sensor path: `CAT_SENSOR`
frames from the existing CAN sensor-kit nodes are received directly on the T-Connect
Pro's own CAN interface, decoded and routed to room-scoped source sensors by generated
compile-time artifacts, and fed through the existing Vesta failover abstraction as
CAN-primary / HA-secondary / Emergency. MEV air-quality demand now derives from raw CAN
pollutant measurements. Story HVAC-1.6 (this report) reconciled the last three stale
generated artifacts, codified the whole verification battery as one repeatable runner
(`scripts/verification-battery.sh`), ran everything this story environment's network
policy permits — all python/native tests, the idempotence gate, and every `esphome
config` gate, green — and shipped the bench-session script
(`epic-HVAC-1-testing-checklist.md`) for the epic's remaining hardware proofs
(ACs 7-10). The three `esphome compile` gates and the vesta failover e2e could **not**
execute here: the session's egress policy denies PlatformIO package downloads (GitHub
release assets and the PlatformIO registry both refuse with 403) — see "Environment
limits of this run" below for the one-command local follow-up.

**The epic is NOT done:** its Definition of Done requires bench-proven CAN → HA →
Emergency transitions on real hardware. `hvac-epic-1` stays `in-progress` in
`sprint-status.yaml` until that session completes.

---

## Stories Delivered

| Story | Title | Points | Status |
|-------|-------|-------:|--------|
| HVAC-1.1 | Generated CAN Sensor Routing Artifact | 3 | done |
| HVAC-1.2 | Sensor-Only CAN Receiver and Freshness Core | 5 | done |
| HVAC-1.3 | Climate Controller Publish-Only Composition | 2 | done |
| HVAC-1.4 | CAN-Primary Room Sensor Failover | 3 | done |
| HVAC-1.5 | CAN Air-Quality MEV Demand Integration | 3 | done |
| HVAC-1.6 | Verification Battery and Bench Rollout | 2 | delivered — compile gates (unrestricted-network run) + bench session are the epic's remaining work |

## Delivered Files per Story

Sourced from each story spec's Auto Run Result (`spec-hvac-1-1-*.md` ..
`spec-hvac-1-5-*.md`) and this story's diff. BMAD bookkeeping files
(spec/sprint-status/deferred-work updates) are omitted for brevity.

### HVAC-1.1 — Generated CAN Sensor Routing Artifact
- `canbus/tools/generate_nodes.py` — CAN sensor route metadata, generated-YAML rendering, room-slug/route validation, artifact writing
- `canbus/tests/test_generate_exports.py` — route renderer, validation, idempotence, room-move, protocol-drift, invalid-ID-prefix coverage
- `hvac/packages/generated/can_sensor_routes.yaml` — generated routing artifact (empty for the then-`sensors=0` registry)

### HVAC-1.2 — Sensor-Only CAN Receiver and Freshness Core
- `hvac/packages/can_sensor_receiver.yaml` — receive-only controller CAN package: `CAT_SENSOR` guards, route publication, non-OK `NaN`, stale sweeps
- `hvac/protocol/can_sensor_receiver.h` — native-testable decode, validation, scaling, route lookup, freshness state (header accessor)
- `hvac/protocol/generated_can_sensor_routes.h` — generated route metadata for freshness tracking (new generator output)
- `hvac/tests/test_can_sensor_receiver.cpp` — native coverage: scaling, malformed frames, wrong proto, non-sensor categories, non-OK statuses, unknown routes, stale/never-seen expiry, simultaneous stale routes, millis wraparound
- `hvac/tests/compile_can_sensor_receiver.yaml` — isolated ESPHome composition fixture
- `canbus/tools/generate_nodes.py`, `canbus/tests/test_generate_exports.py` — metadata header rendering + no-op publish scripts for empty registries

### HVAC-1.3 — Climate Controller Publish-Only Composition
- `devices/climate-control.yaml` — `esphome: includes:` for the three receiver headers (at wrapper-relative `../../` depth) + `can_routes`/`can_receiver` packages (routes before receiver), publish-only

### HVAC-1.4 — CAN-Primary Room Sensor Failover
- `hvac/room_sensors.yaml` — CAN-primary / HA-secondary / Emergency wiring for all 13 rooms; static `<room_slug>_temp_can`/`_humidity_can` dispatch targets
- `vesta/packages/components/failover_sensor.yaml` — backward-compatible tier-label vars (`CAN`/`HA`/`Emergency` as caller labels); + `vesta/docs/failover-sensor.md`
- `devices/climate-control.yaml`, `hvac/CLAUDE.md`, root `CLAUDE.md` — failover-order flip documentation
- `canbus/tools/generate_nodes.py` — skip statically-declared temp/humidity targets in generated routes (duplicate-id protection); include-depth bugfix in the non-empty routes branch
- `hvac/packages/generated/can_sensor_routes.yaml`, `hvac/protocol/generated_can_sensor_routes.h` — regenerated from the committed registry (node 101 / soggiorno)
- Residual recorded then: `vesta/tests/e2e/test_failover_sensor.py` not run (pytest unavailable) — **closed by this story's run, see battery results**

### HVAC-1.5 — CAN Air-Quality MEV Demand Integration
- `hvac/rooms/first_floor/first-floor.yaml` — 16 UDP CO2/IAQ sensors replaced with 56 static CAN pollutant sensors + 5 per-pollutant max aggregates
- `hvac/mev_demand.yaml` — three top-level channels (CO2, Air Quality, Humidity); Air Quality = MAX of proportional VOC/NOx/PM2.5/PM10 demands; PM1.0/PM4.0 diagnostic-only
- `hvac/mev_modbus.yaml` — `demand:` package vars updated to the new contract
- `hvac/CLAUDE.md` — MEV entity list and CAN-sourcing description

### HVAC-1.6 — Verification Battery and Bench Rollout (this story)
- `registry/map.json`, `canbus/nodes/node101.yaml`, `canbus/protocol/node_map.h` — reconciled by one sanctioned `generate_nodes.py` run (node 101 → `sensors:1`/`soggiorno` in map.json with new `map_version`; node101.yaml gains the `sensor_kit` include; `NODE_MAP_VERSION` restamped) — completes the bench flip, epic AC6 idempotence now holds
- `scripts/verification-battery.sh` — new fail-fast battery runner (per-step PASS/FAIL + summary table, `--native-only` esphome-free subset, documented clean-tree precondition for the idempotence step)
- `canbus/tests/test_protocol.cpp`, `test_ha_arbitration.cpp`, `test_node_health.cpp`, `test_bridge_forwarding.cpp`, `test_bindings_contract.cpp` — stale pre-Phase-6a `firmware/tests/`-era (and one cwd-relative) build-command header comments corrected to the documented repo-root commands (comments only; `lighting/tests/test_binding_actuation.cpp` audited — already correct)
- `hvac/CLAUDE.md` — new "Test & verify (from repo root)" section
- `canbus/CLAUDE.md` — idempotence check widened to `git diff --exit-code canbus hvac registry`; runner pointer
- `_bmad-output/implementation-artifacts/epic-HVAC-1-testing-checklist.md` — bench-session script for epic ACs 7-10
- `_bmad-output/implementation-artifacts/epic-HVAC-1-completion-report.md` — this report

---

## Verification Battery — This Run's Results

Executed in this story's environment (fresh clone, toolchain installed for the run:
`esphome==2026.5.3`, `pytest`, `pytest-asyncio`, `aioesphomeapi`; Python 3.11, g++ 13).
`bash scripts/verification-battery.sh` runs all of the below; each row records this
run's actual outcome.

| # | Command | Epic AC | Result |
|---|---------|---------|--------|
| 1 | `python3 canbus/tests/test_bindings.py` | — | PASS |
| 2 | `python3 canbus/tests/test_generate_exports.py` | AC1 | PASS — "All 29 export-pipeline tests passed" |
| 3 | `python3 canbus/tests/test_push_gate.py` | — | PASS |
| 4 | `g++ -std=c++17 -Wall -Wextra canbus/tests/test_protocol.cpp -o /tmp/proto && /tmp/proto` | — | PASS |
| 5 | `g++ -std=c++17 -Wall -Wextra canbus/tests/test_ha_arbitration.cpp -o /tmp/arb && /tmp/arb` | — | PASS |
| 6 | `g++ -std=c++17 -Wall -Wextra canbus/tests/test_node_health.cpp -o /tmp/health && /tmp/health` | — | PASS |
| 7 | `g++ -std=c++17 -Wall -Wextra canbus/tests/test_bridge_forwarding.cpp -o /tmp/bridge && /tmp/bridge` | — | PASS |
| 8 | `g++ -std=c++17 -Wall -Wextra canbus/tests/test_bindings_contract.cpp -o /tmp/bcontract && /tmp/bcontract` | — | PASS |
| 9 | `g++ -std=c++17 -Wall -Wextra -Icanbus/protocol -Ilighting/protocol lighting/tests/test_binding_actuation.cpp -o /tmp/act && /tmp/act` | — | PASS |
| 10 | `g++ -std=c++17 -Wall -Wextra -Icanbus/protocol -Ihvac/protocol hvac/tests/test_can_sensor_receiver.cpp -o /tmp/hvac_can_sensor_receiver && /tmp/hvac_can_sensor_receiver` | AC2 | PASS — all 9 receiver/freshness cases |
| 11 | `python3 canbus/tools/generate_nodes.py && git diff --exit-code canbus hvac registry` | AC6 | PASS — byte-identical regeneration after reconciliation |
| 12 | `esphome config hvac/tests/compile_can_sensor_receiver.yaml` | AC2 (fixture) | PASS |
| 13 | `esphome compile canbus/tests/compile_sensor_node.yaml` | AC3 | **BLOCKED (environment)** — egress 403 on the RP2040 toolchain release asset (`github.com/earlephilhower/pico-quick-toolchain/releases/download/…`) |
| 14 | `esphome config devices/locals/climate-control.yaml` | AC4 | PASS — "Configuration is valid!" (full 13-room config) |
| 15 | `esphome compile devices/locals/climate-control.yaml` | AC5 | **BLOCKED (environment)** — egress 403 on `github.com/pioarduino/platform-espressif32/releases/download/55.03.38-1/platform-espressif32.zip` |
| 16 | `python3 -m pytest vesta/tests/e2e/test_failover_sensor.py` | HVAC-1.4 residual | **BLOCKED (environment)** — harness host build needs `platformio/native` from the PlatformIO registry; `api.registry.platformio.org` CONNECT is egress-denied (403). pytest/pytest-asyncio/aioesphomeapi themselves installed fine — the 1.4 "pytest unavailable" residual is half-closed; the run still needs an unrestricted network |
| 17 | `bash scripts/verification-battery.sh` | AC1-6 | `--native-only`: **PASS** (all 11 steps). Full mode: runs green through step 12, then fails at step 13 on the environment block above |
| 18 | `esphome compile canbus/nodes/node101.yaml` (bench node flash-ready) | AC7 prep | **BLOCKED (environment)** — same RP2040 toolchain asset; `esphome config canbus/nodes/node101.yaml` PASS ("Configuration is valid!") as the environment-feasible check |
| 19 | `git diff --check` | — | PASS |

### Coverage cross-check (epic AC1/AC2, asserted not rewritten)

- **AC1** — `canbus/tests/test_generate_exports.py` covers sensor-node `room_slug`
  validation (empty/invalid/unroutable slugs rejected), routing-artifact generation
  (including the room-move drift test), and byte-identical regeneration.
- **AC2** — `hvac/tests/test_can_sensor_receiver.cpp` covers valid decode + scaling,
  malformed payloads, wrong protocol version, non-sensor categories, non-OK statuses,
  unknown routes, and 90 s stale expiry (plus never-seen expiry, simultaneous stale
  routes, and millis wraparound).

### Environment limits of this run

This story ran in a Claude Code remote session whose network egress policy allows
PyPI and git-protocol GitHub operations but **denies GitHub release-asset downloads
and the PlatformIO registry** (both refuse at the proxy with 403; the proxy's own
documentation classifies 403 as organization policy — "do not retry or route around
it"). Every `esphome compile` needs PlatformIO platform packages served from exactly
those hosts (esp32-s3, RP2040, and even the host/`native` platform the vesta e2e
harness uses), so rows 13, 15, 16, and 18 could not execute here. `esphome config`
performs full YAML/substitution/id validation without PlatformIO and ran green.

**Local follow-up (any network-unrestricted machine, from repo root):**

```bash
pip install "esphome==2026.5.3" pytest pytest-asyncio aioesphomeapi
bash scripts/verification-battery.sh        # expected: RESULT: PASS, all 16 steps
esphome compile canbus/nodes/node101.yaml   # bench-node flash readiness (AC7 prep)
```

When that run is green: flip `hvac-1-6-verification-battery-bench-rollout` to `done`
in `sprint-status.yaml`, update rows 13/15/16/17/18 above, and proceed to the bench
session (`epic-HVAC-1-testing-checklist.md`).

**Environment note:** `devices/locals/secrets.yaml` (gitignored) was created in-session
with clearly-labeled dummy values so the `devices/locals/` config gate could resolve
its `!secret` references — never flash a device with those values.

---

## Bench Validation — PENDING HARDWARE EXECUTION

Epic ACs 7-9 (node 101 live → `CAN` tier; frames stopped > 90 s → `HA` tier; CAN+HA
off → `Emergency`/NaN + safe shutdown) and AC10 (findings recording) require the
physical bench: node 101 hardware, the T-Connect Pro controller, a shared CAN segment,
and a live Home Assistant. None of that exists in this environment (the system is
pre-live), so **no bench results are recorded here** — recording them without the
session would be fabrication.

The session script is `epic-HVAC-1-testing-checklist.md` (same directory): pre-flash
push gate, node 101 flash prep per the reflash runbook Path A, the three numbered
proofs with expected observations and exact entity ids, and the AC10 findings table.
When the session completes, its results replace this section (or land in a follow-up
tuning note) and `hvac-epic-1` can be flipped to `done`.

---

## Deferred / Tuning List

Carried forward for the bench session and beyond (fuller context in `deferred-work.md`):

1. **Bench session itself** — epic ACs 7-10; the epic's DoD gate. Script:
   `epic-HVAC-1-testing-checklist.md`.
2. **MEV pollutant thresholds need real-world tuning** (epic risk register) — raw CAN
   measurements and per-pollutant demand diagnostics are shipped precisely so
   thresholds can be tuned from data; the 8 `input_number.mev_*_bound` HA helper
   entities are also still uncreated (pre-existing convention gap, HVAC-1.5 deferral).
3. **First-floor rollout snag (found by this story, not fixed — generator change needs
   its own decision):** `generate_nodes.py`'s `STATIC_CAN_SENSOR_TARGET_SUFFIXES`
   only exempts `temp`/`humidity` from route-target declaration, but HVAC-1.5
   statically declared the pollutant `_can` entities for all 8 first-floor rooms in
   `first-floor.yaml`. Flipping any **first-floor** node to `sensors=1` and
   regenerating would therefore declare duplicate ids (generated routes + static
   declarations) and fail `esphome config`. Harmless today (node 101 is ground-floor
   soggiorno, which has no static pollutant declarations); must be resolved before
   first-floor nodes are registry-flipped.
4. **No committed regression fixture for `devices/climate-control.yaml`'s CAN
   composition** (HVAC-1.3 deferral) — package order/include depth are guarded only by
   the battery's config gate, which is now at least codified in the runner.
5. **Runner is not wired into any hook/CI** — deliberate (this story's contract);
   hook/CI wiring is a separately-tracked decision in `deferred-work.md`'s lineage.
6. **Reflash-campaign runbook time budgets are still TBD** — the bench session should
   feed measured Path A timings back into `canbus/docs/reflash-campaign-runbook.md`.

---

## Sign-off

- [x] HVAC-1.1..1.5 `done` in sprint-status; HVAC-1.6 software delivered (`in-progress` until the compile gates run)
- [x] Battery results recorded (permitted subset green; compile gates environment-blocked — see table)
- [ ] Compile gates green on a network-unrestricted run (`bash scripts/verification-battery.sh`) — **pending**
- [x] Bench checklist created (`epic-HVAC-1-testing-checklist.md`)
- [ ] Bench session executed and findings recorded (AC7-AC10) — **pending hardware**
- [ ] `hvac-epic-1` flipped to `done` — **only after the bench session**
