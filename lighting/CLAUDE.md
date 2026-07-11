# Lighting Subsystem — AI Assistant Guide

This is the lighting application system (layered-restructure spine,
`_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md`).
It is **pre-live**: no relay actuation exists yet (ADR-0013 open item 2 —
fallback is log-only). The gateway-side button/gate package lives here since
migration Phase 5b-2; relay outputs land with ADR-0013's hardware decision,
which also triggers the intended physical split onto a dedicated lighting
gateway device (until then, `devices/gateway.yaml` composes this system's
package alongside canbus's).

## What lighting owns

- **`registry/bindings.yaml` schema** — the binding manifest's shape (fields,
  ops, fan-out) is lighting's to define and change (ADR-0013 lineage). A
  schema change to `bindings.yaml` is a lighting-owned edit.
- **The `ha_ready` gate INSTANCE** (AD-7 as amended 2026-07-06) — the YAML
  wiring in `packages/buttons.yaml`: readiness/ACK api services, the
  manifest-hash agreement with HA over `bindings.yaml`, the pending-ACK sweep,
  and the fallback actions. The arbitration *pure logic* stays the shared
  canbus header `ha_arbitration.h` — lighting instantiates it, never forks it.
- **Button events** — decoding CAT_INPUT frames and firing
  `esphome.canbus_button`, plus fallback semantics: what a binding *means*
  (which relay(s), which op) when Home Assistant is down.
- **The compiled `bindings.h` consumer contract** — frozen per
  `spec-bindings-arbitration-contract` (drift test:
  `test_bindings_contract.cpp`); changes are lighting-led, **LIGHT-** acked.
- **HA-side automations under `lighting/home-assistant/`** — hold/hold_release
  dimmer and cover gestures (ADR-0012), and eventually any lighting-specific
  automation that isn't arbitration.

## What lighting never touches (AD-7)

- **Canonicalization or the manifest hash mechanism** — `tools/bindings.py`'s
  `canonical_hash` and the `bindings.h` *emission* are canbus-owned. A
  lighting schema change that alters canonical form is still an AD-6 contract
  change: canbus regenerates both sides in the same commit.
- **Transport health** — heartbeats, node_lost/discovery, the bus definition
  (`canbus/packages/health.yaml`) are canbus infra.

## Files here today

- `packages/buttons.yaml` — the gateway-side lighting package: CAT_INPUT
  decode → HA events + the ha_ready gate instance, including the ADR-0013
  fallback actuation calls. Composed by `devices/gateway.yaml` AFTER
  `canbus/packages/health.yaml` (it `!extend`s the bus that package defines).
- `packages/relay_bank.yaml` — lighting's 32-channel relay bank (ADR-0014):
  one modbus_controller + 32 self-registering channels, 0-based
  `relay_0..relay_31` natively (no id_offset arithmetic).
- `packages/relay_channel.yaml` — one bank channel: wraps vesta's shared
  `modbus_relay_switch.yaml` hardware driver and registers the created
  switch into `relay_store()` — the registration lives next to the switch it
  registers, so adding a channel registers it automatically.
- `protocol/binding_actuation.h` — fallback pure logic (click-only gesture
  gate, relay-bounds check); natively tested, no ESPHome includes.
- `protocol/relay_store.h` — ESPHome glue: relay-id → `Switch*` store and
  `fire_binding_fallback()`, the single actuation entry point both fallback
  branches call.
- `tests/test_binding_actuation.cpp` — native test for the pure logic (see
  Test & verify below for the required `-I` flags).
- `home-assistant/ha_hold_automations.yaml` — hand-maintained HA reference
  automations for hold/hold_release gestures (ADR-0012). Copy or `!include`
  into Home Assistant; replace the EXAMPLE node_id/button/entity_id values
  with real ones.

## Conventions

- Epic prefix: **LIGHT-**. New BMAD artifacts go to the root `_bmad-output/`.
- Entity-ID/automation-naming conventions are lighting's own to set once real
  fallback code lands — not yet decided (see Deferred in the architecture
  spine).

## Test & verify (from repo root)

```bash
# Fallback gesture-gate/bounds-check pure logic (no ESPHome deps). -I flags
# required: binding_actuation.h includes canbus's frozen headers by flat
# filename — the form ESPHome's flattened esphome.includes: build needs, which
# a bare g++ compile of a nested file can't resolve without them.
g++ -std=c++17 -Wall -Wextra -Icanbus/protocol -Ilighting/protocol \
  lighting/tests/test_binding_actuation.cpp -o /tmp/act && /tmp/act
```

`relay_store.h` (the relay-id -> `Switch*` glue and `fire_binding_fallback()`)
is deliberately not natively tested — it needs real `esphome::switch_::Switch`
objects that only exist inside a compiled ESPHome binary, the same split
`ha_arbitration.h`'s pure logic vs. `buttons.yaml`'s lambda glue already
follows. It's exercised by `esphome compile devices/gateway.yaml` and,
eventually, hardware bring-up.
