# Lighting Subsystem — AI Assistant Guide

This is the lighting application system (layered-restructure spine,
`docs/architecture/ARCHITECTURE-SPINE.md`).
Relay actuation is real (ADR-0014 P4/P5): the lighting controller drives a
Waveshare Modbus RTU Relay 32CH bank (`relay_0..relay_31`, HA-switchable), and
the ADR-0013 fallback branches actuate bindings when HA is down. ADR-0014 first
resolved the physical split as "no further split", but **ADR-0015 (2026-07-13)
split after all**: canbus transport health moved to its own device
(`devices/health-monitor.yaml`), and this system's packages now compose alone on
`devices/light-controller.yaml` (T-Connect Pro). The system stays **pre-live** in one specific
sense: `registry/bindings.yaml` is still empty — no real bindings are
authored yet (ADR-0013 open item 4, pending the lighting circuit inventory).

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

- `packages/buttons.yaml` — the lighting-controller package: CAT_INPUT
  decode → HA events + the ha_ready gate instance, including the ADR-0013
  fallback actuation calls. Composed by `devices/light-controller.yaml`, which
  defines `can0` itself (ADR-0015 §2); this package `!extend`s that bus.
- `packages/relay_bank.yaml` — lighting's 32-channel relay bank (ADR-0014):
  one modbus_controller + 32 self-registering channels, 0-based
  `relay_0..relay_31` natively (no id_offset arithmetic).
- `packages/relay_channel.yaml` — one bank channel: wraps the shared top-level
  `packages/devices/modbus-io/modbus_relay_switch.yaml` hardware driver and registers the created
  switch into `relay_store()` — the registration lives next to the switch it
  registers, so adding a channel registers it automatically.
- `packages/ui/` — the opt-in on-device LVGL panel (composed only by
  `devices/light-controller-touch.yaml`; the screen-less build never sees it).
  `light_touch_ui.yaml` is the panel; `relay_cell.yaml`/`relay_refresh.yaml`
  and `button_row.yaml`/`button_refresh.yaml` are the per-item fragments;
  `touch_ui_format.h` holds the column formatters and the button-event log.
  **It deliberately mirrors `climate/packages/ui/`** — same shared dark theme
  (`packages/ui/dark_theme.yaml`), same read-only glance tab, same
  aligned-column rows, same pinned status strip with a liveness pulse. Two
  panels on identical hardware read by the same person; keep changes to one
  side in step with the other rather than letting the idioms diverge.
- `protocol/binding_actuation.h` — fallback pure logic (click-only gesture
  gate; output-id classification `output_id_kind()` and bounds
  `binding_outputs_in_bounds()` spanning local relays 0–31 and remote HTTP ids
  32+, ADR-0019); natively tested, no ESPHome includes.
- `protocol/relay_store.h` — ESPHome glue: relay-id → `Switch*` store and
  `fire_binding_fallback()`, the single actuation entry point both fallback
  branches call. Dispatches each bound output id by transport — LOCAL drives the
  `Switch*`; REMOTE enqueues onto `remote_store.h` (ADR-0019).
- `protocol/remote_store.h` — ESPHome glue for the remote (HTTP) transport
  (ADR-0019): the remote-command queue (header-accessor ring), the id→object_id
  table, the op→REST-verb map, and the URL builder. Drained by
  `packages/remote_actuators.yaml`. Not natively tested (same split as
  `relay_store.h`).
- `packages/remote_actuators.yaml` — gateway-side HTTP fallback transport
  (ADR-0019): the `http_request` client + a 100 ms drain loop that POSTs queued
  remote commands to a target device's `web_server` (an-penta-1's strips) when
  HA is down. Composed by `devices/light-controller.yaml`, which supplies the
  `an_penta_host`/`an_penta_basic_auth` substitutions. Enqueue-only on the hot
  paths keeps the CAN handler / ACK sweep non-blocking.
- `tests/test_binding_actuation.cpp` — native test for the pure logic, incl. the
  ADR-0019 output-id classification/bounds (see Test & verify below for the
  required `-I` flags).
- `home-assistant/ha_hold_automations.yaml` — hand-maintained HA reference
  automations for hold/hold_release gestures (ADR-0012). Copy or `!include`
  into Home Assistant; replace the EXAMPLE node_id/button/entity_id values
  with real ones.

## Conventions

- Prefix commits touching this system with `lighting:`. Record significant decisions as new ADRs under `docs/adr/`.
- Entity-ID/automation-naming conventions are lighting's own to set — still
  undecided now that the fallback code exists (ADR-0014 P5); expected to firm
  up with binding authoring (see Deferred in the architecture spine).

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
follows. It's exercised by `esphome compile devices/light-controller.yaml` and,
eventually, hardware bring-up.
