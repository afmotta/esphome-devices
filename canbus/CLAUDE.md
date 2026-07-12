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
  transport, heartbeats, `node_lost` detection, discovery, and the bus
  definition on the gateway (LilyGO T-Connect Pro, TWAI CAN over Ethernet).
  It does not decode button frames or fire HA events — that's
  `lighting/`'s gate instance (see `lighting/CLAUDE.md`). `climate/` consumes
  sensor CAN frames directly, with no gate in between.
- **Home Assistant owns all logic** — bindings are HA automations, changeable
  anytime.

Full protocol and architecture: `docs/canbus-smart-home-reference.md`.
Operational detail (pins, arbitration, health, manifest): `README.md`.
ADR specs live in `_bmad-output/implementation-artifacts/` (historical record —
new BMAD artifacts go to the root `_bmad-output/`, prefixed **CAN-Epic N**).

## Hard rules

- **Never hand-edit `canbus/nodes/`** — node YAMLs are generated. Edit
  `registry/nodes.csv` / `registry/bindings.yaml`, then run
  `python3 canbus/tools/generate_nodes.py`.
- **Git is the system of record for the registry** (ADR-0009). Bindings are
  unrebuildable; before reflashing the gateway run
  `python3 canbus/tools/check_registry_pushed.py` (exit 0 = safe).
- **Momentary buttons have no state** — never add button-state/bitmask fields
  to frames or HA payloads; buttons emit events only.
- **No PROTO version bump until live** — pre-live breaking changes are made in
  place (no PROTO_V2, no shims).
- **ESPHome globals can't hold custom structs** (storage is emitted before user
  includes) — own struct state via a header accessor (see `pending_acks_store`
  in `lighting/packages/buttons.yaml`, `node_health_store` in
  `canbus/packages/health.yaml`).
- **CAN node composition is generic board through base node.** Generated node configs
  in `canbus/nodes/` compose `base_node.yaml` plus optional `sensor_kit.yaml` only;
  `base_node.yaml` pulls in `boards/canbed-rp2040.yaml` (RP2040, logger, SPI,
  MCP2515 `can0`) and owns protocol include, boot logging, standard buttons,
  globals, and heartbeat.
- **`canbus/packages/`** holds both node-side (`base_node.yaml`, `button.yaml`,
  `sensor_kit.yaml`) and gateway-side (`health.yaml` — transport health + the
  bus definition) packages since Phase 6a merged them. `devices/gateway.yaml`
  composes `health.yaml` with `lighting/packages/buttons.yaml` — canbus
  package first (it defines `can0`; lighting `!extend`s it).
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

# ESPHome compile check without touching generated nodes
esphome compile canbus/tests/compile_sensor_node.yaml
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
explicitly outside the freeze. `room_slug` is the climate-zone join key
(validated against `climate/rooms/**`; required when `sensors=1`), and
numeric `floor` converts to a climate floor slug via `FLOOR_SLUGS`
(0→`ground_floor`, 1→`first_floor`, 2→`second_floor`) in
`canbus/tools/generate_nodes.py`. Sensor-kit CAN frames (ADR-0006) feed the
same controller. HA-side YAML (`canbus/home-assistant/
ha_arbitration_automations.yaml`, generated `ha_manifest_package.yaml`) is imported into
Home Assistant.
