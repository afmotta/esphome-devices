# CAN Bus Wall-Button Subsystem — AI Assistant Guide

This subtree is the CAN bus wall-button system (merged from `afmotta/canbus`,
full history preserved). It is **pre-live**: nodes are not yet walled in.
Everything below is scoped to `canbus/`; the rest of the repo is the climate
control system (see root `CLAUDE.md`).

## Design principle: dumb nodes, domain-split gateway

- **Nodes are frozen firmware** (CANBed RP2040, no WiFi/OTA, flashed via USB
  before wall installation). They detect button gestures locally and send
  self-describing CAN frames. They do not know what any button "does".
- **canbus owns transport health only** (amended AD-7, 2026-07-06): frame
  transport, heartbeats, `node_lost` detection, discovery. Since the ADR-0015
  split this runs on its own dedicated device — the health monitor (Waveshare
  ESP32-S3-RS485-CAN, TWAI CAN over WiFi, `devices/health-monitor.yaml`) — not
  on the lighting controller. It does not decode button frames or fire HA button
  events — that's `lighting/`'s gate instance on `devices/light-controller.yaml`
  (see `lighting/CLAUDE.md`). `climate/` consumes sensor CAN frames directly,
  with no gate in between.
- **Home Assistant owns all logic** — bindings are HA automations, changeable
  anytime.

Full protocol and architecture: `docs/canbus-smart-home-reference.md`.
Operational detail (pins, arbitration, health, manifest): `README.md`.
The CAN decisions are recorded as ADR-0001…0013 in `docs/adr/` (the "why"); the CAN
firmware implementation rules are in `docs/design-notes/canbus-implementation-rules.md`.
Record new decisions as ADRs under `docs/adr/`; prefix commits touching this system with `canbus:`.

## Hard rules

- **Never hand-edit `canbus/nodes/`** — node YAMLs are generated. Edit
  `registry/nodes.csv` / `registry/bindings.yaml`, then run
  `python3 canbus/tools/generate_nodes.py`.
- **Git is the system of record for the registry** (ADR-0009). Bindings are
  unrebuildable; before reflashing a gateway-class device (`light-controller`
  or `health-monitor` — both compile registry-derived headers) run
  `python3 canbus/tools/check_registry_pushed.py` (exit 0 = safe).
- **Momentary buttons have no state** — never add button-state/bitmask fields
  to frames or HA payloads; buttons emit events only.
- **No PROTO version bump until live** — pre-live breaking changes are made in
  place (no PROTO_V2, no shims).
- **ESPHome globals can't hold custom structs** (storage is emitted before user
  includes) — own struct state via a header accessor (see `pending_acks_store`
  in `lighting/packages/buttons.yaml`, `node_health_store` in
  `canbus/packages/health.yaml`).
- **CAN node composition is driven by the registry `profile` column** (ADR-0017).
  Generated configs in `canbus/nodes/` compose `node_core.yaml` plus exactly the
  packages **and its board** — `buttons` / `buttons+sensors` / `sensors` /
  `bridge-t2can` / `bridge` / `buttons+bridge`, defined in one place, `PROFILES`
  in `canbus/tools/generate_nodes.py`.
  `node_core.yaml` is **board-agnostic**: it owns protocol include, boot logging,
  globals and heartbeat, and asks only that the board declare `can0`. That is what
  lets bridges run on an ESP32-S3 (`boards/lilygo-t-2can.yaml`) while everything
  else runs on the CANBed RP2040. Never add a board include to `node_core.yaml`.
  The column is **single-valued on purpose**: ADR-0005 requires single-purpose
  bridge firmware, so "bridge AND sensors" is unrepresentable rather than merely
  rejected — `bridge+sensors` is a string the generator refuses, and a test asserts
  no profile ever pairs those two packages. **Buttons are the one sanctioned
  co-tenant of a bridge** (`buttons+bridge`, for the boxes where a segment splits
  at a button box): they add no blocking I/O and no new way to hang the forwarding
  loop, which is precisely what the sensor kit does add. Adding a profile = a new
  `PROFILES` row + its package file; never an `if profile == ...` branch.
- **Two invariants hold across every profile** (ADR-0017 §3), and they are what let
  `node_core.yaml` contain no conditionals: **`can0` is always the controller-facing
  port** (on a bridge that is the backbone side, `can1` the zone side), and
  **`error_flags` is the shared contribution point with `node_core.yaml` as its sole
  transmitter** — a profile package reports by OR-ing its `ERR_*` bit in, and never
  adds a second `CAT_STATUS` interval. One node_id, one heartbeat.
- **Bridges are ordinary registry rows.** A bridge carries a `node_id` from the same
  allocation space, so it lands in `node_map.h`, `map.json`, and the generated HA
  per-node health entities for free.
- **External actuator nodes** (`profile.external`, e.g. `led-penta`, ADR-0020) are also
  ordinary registry rows — they reserve a `node_id` and land in `node_map.h`/`map.json`/health —
  but their firmware is a hand-composed entry point on a non-CANBed board (`devices/an-penta-1.yaml`),
  so the generator emits **no** `canbus/nodes/*.yaml` for them. Such a node RECEIVES `CAT_OUTPUT`
  commands (an actuator) rather than sending button/sensor frames; it still heartbeats. This is the
  one profile with empty `boards`/`packages` — gated by the `external` attribute, not an
  `if profile ==` branch.
- **Two bridge boards** (ADR-0017 §1). `bridge-t2can` on the LilyGO T-2CAN is
  **preferred** — one integrated board, backbone on the interrupt-driven TWAI
  controller. `bridge` / `buttons+bridge` on the CANBed + a 3.3 V add-on MCP2515
  are the second source, and CANBed is the only board that can carry
  `buttons+bridge`. If you touch the add-on board file, `clock:` must match the
  module's actual crystal (ESPHome supports 8/12/16/20 MHz only).
- **`canbus/packages/`** holds both node-side (`node_core.yaml`, `buttons_8.yaml`,
  `button.yaml`, `sensor_kit.yaml`, `bridge.yaml`) and gateway-side (`health.yaml` —
  transport health) packages
  since Phase 6a merged them. Since the ADR-0015 split, `health.yaml` composes
  onto its own device, `devices/health-monitor.yaml` (Waveshare ESP32-S3-RS485-CAN),
  while `lighting/packages/buttons.yaml` composes onto `devices/light-controller.yaml`
  (T-Connect Pro) — two physical devices, not one. `health.yaml` no longer owns the
  bus: each entry point declares its own `can0` (ADR-0015 §2) and `health.yaml` /
  `buttons.yaml` each `!extend can0` to attach their handlers.
- **`on_frame` guards**: validate payloads with `if:`/`condition:` blocks so
  action lambdas stay clean — no redundant re-checks inside lambdas.

## Test & verify (from repo root)

```bash
# Python (stdlib-only, no deps)
python3 canbus/tests/test_bindings.py
python3 canbus/tests/test_generate_exports.py
python3 canbus/tests/test_push_gate.py

# Native C++ protocol logic (no ESPHome deps)
g++ -std=c++17 -Wall -Wextra canbus/tests/test_protocol.cpp -o /tmp/proto && /tmp/proto
g++ -std=c++17 -Wall -Wextra canbus/tests/test_ha_arbitration.cpp -o /tmp/arb && /tmp/arb
g++ -std=c++17 -Wall -Wextra canbus/tests/test_node_health.cpp -o /tmp/health && /tmp/health
g++ -std=c++17 -Wall -Wextra canbus/tests/test_bridge_forwarding.cpp -o /tmp/bridge && /tmp/bridge
g++ -std=c++17 -Wall -Wextra canbus/tests/test_bindings_contract.cpp -o /tmp/bcontract && /tmp/bcontract

# Lighting's fallback-actuation pure logic (needs -I flags: it includes canbus'
# frozen headers by flat filename, the form ESPHome's flattened build needs —
# see lighting/protocol/binding_actuation.h's own header comment)
g++ -std=c++17 -Wall -Wextra -Icanbus/protocol -Ilighting/protocol lighting/tests/test_binding_actuation.cpp -o /tmp/act && /tmp/act

# ESPHome compile checks without touching generated nodes
esphome compile canbus/tests/compile_sensor_node.yaml   # buttons+sensors profile
esphome compile canbus/tests/compile_bridge.yaml        # bridge profile (CANBed, 2x MCP2515)
esphome compile canbus/tests/compile_buttons_bridge.yaml  # buttons+bridge (the pin-budget gate)
esphome compile canbus/tests/compile_bridge_t2can.yaml    # bridge-t2can (ESP32-S3, TWAI+MCP2515)
```

Generator idempotence: an unchanged registry regenerates byte-for-byte
(`python3 canbus/tools/generate_nodes.py` then
`git diff --exit-code canbus climate registry` — the generator has written the
`climate/` routing artifacts too since HVAC-1.1/1.4, so the check spans all
three paths and needs them clean before running). This whole battery, plus
the lighting/Climate/shared-package checks and the ESPHome gates, is codified in
`scripts/verification-battery.sh` (`--native-only` skips the ESPHome steps).

## Integration with the climate system

`registry/map.json` is the read-only export consumed by the Climate
controller (this repo) and dashboards. Its Climate-consumer contract is **frozen**
(ADR-0009 open item 5, closed by `spec-map-json-contract`): `schema_version`,
`map_version`, `nodes[].node_id`, `nodes[].room_slug`, `nodes[].location`,
`nodes[].sensors` are frozen-additive; `manifest_hash` and `board` are
explicitly outside the freeze. ADR-0017 replaced the registry's `sensors` column
with `profile`, but `nodes[].sensors` is inside the freeze — it is still exported,
DERIVED from the profile, and `profile` was added alongside (frozen-additive), so
Climate consumers needed no change. `room_slug` is the climate-zone join key
(validated against `climate/rooms/**`; required for any sensor-bearing profile), and
numeric `floor` converts to a climate floor slug via `FLOOR_SLUGS`
(0→`ground_floor`, 1→`first_floor`, 2→`second_floor`) in
`canbus/tools/generate_nodes.py`. Sensor-kit CAN frames (ADR-0006) feed the
same controller. HA-side YAML (`canbus/home-assistant/
ha_arbitration_automations.yaml`, generated `ha_manifest_package.yaml`) is imported into
Home Assistant.
