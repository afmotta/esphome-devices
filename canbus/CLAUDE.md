# CAN Bus Wall-Button Subsystem — AI Assistant Guide

This subtree is the CAN bus wall-button system (merged from `afmotta/canbus`,
full history preserved). It is **pre-live**: nodes are not yet walled in.
Everything below is scoped to `canbus/`; the rest of the repo is the climate
control system (see root `CLAUDE.md`).

## Design principle: dumb nodes, smart gateway

- **Nodes are frozen firmware** (CANBed RP2040, no WiFi/OTA, flashed via USB
  before wall installation). They detect button gestures locally and send
  self-describing CAN frames. They do not know what any button "does".
- **The gateway is updatable** (Waveshare ESP32-S3-POE, TWAI CAN → HA via
  ESPHome API over PoE Ethernet). It decodes frames and fires HA events.
- **Home Assistant owns all logic** — bindings are HA automations, changeable
  anytime.

Full protocol and architecture: `docs/canbus-smart-home-reference.md`.
Operational detail (pins, arbitration, health, manifest): `firmware/README.md`.
ADR specs live in `_bmad-output/implementation-artifacts/` (historical record —
new BMAD artifacts go to the root `_bmad-output/`, prefixed **CAN-Epic N**).

## Hard rules

- **Never hand-edit `firmware/nodes/`** — node YAMLs are generated. Edit
  `firmware/registry/nodes.csv` / `registry/bindings.yaml`, then run
  `python3 canbus/firmware/tools/generate_nodes.py`.
- **Git is the system of record for the registry** (ADR-0009). Bindings are
  unrebuildable; before reflashing the gateway run
  `python3 canbus/firmware/tools/check_registry_pushed.py` (exit 0 = safe).
- **Momentary buttons have no state** — never add button-state/bitmask fields
  to frames or HA payloads; buttons emit events only.
- **No PROTO version bump until live** — pre-live breaking changes are made in
  place (no PROTO_V2, no shims).
- **ESPHome globals can't hold custom structs** (storage is emitted before user
  includes) — own struct state via a header accessor (see `pending_acks_store`
  in `gateway.yaml`).
- **`on_frame` guards**: validate payloads with `if:`/`condition:` blocks so
  action lambdas stay clean — no redundant re-checks inside lambdas.

## Test & verify (from repo root)

```bash
# Python (stdlib-only, no deps)
python3 canbus/firmware/tests/test_bindings.py
python3 canbus/firmware/tests/test_generate_exports.py
python3 canbus/firmware/tests/test_push_gate.py

# Native C++ protocol logic (no ESPHome deps)
g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_protocol.cpp -o /tmp/proto && /tmp/proto
g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_ha_arbitration.cpp -o /tmp/arb && /tmp/arb
g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_node_health.cpp -o /tmp/health && /tmp/health
g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_bridge_forwarding.cpp -o /tmp/bridge && /tmp/bridge

# ESPHome compile check without touching generated nodes
esphome compile canbus/firmware/tests/compile_sensor_node.yaml
```

Generator idempotence: an unchanged registry regenerates byte-for-byte
(`generate_nodes.py` then `git diff --exit-code canbus/firmware`).

## Integration with the climate system

`firmware/registry/map.json` is the read-only export consumed by the HVAC
controller (this repo) and dashboards; its field shape is provisional until
confirmed against the consumer (ADR-0009 open item 5). Sensor-kit CAN frames
(ADR-0006) feed the same controller. HA-side YAML (`firmware/gateway/
ha_*_automations.yaml`, generated `ha_manifest_package.yaml`) is imported into
Home Assistant.
