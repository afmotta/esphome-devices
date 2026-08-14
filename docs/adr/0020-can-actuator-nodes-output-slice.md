---
adr: 0020
title: 'CAN actuator nodes and the CAT_OUTPUT command slice: the gateway drives off-board ESPHome actuators (An-Penta LED strips) over CAN when HA is down'
status: 'Proposed'
date: '2026-08-11'
deciders: ['Alberto']
author: 'Claude'
dependsOn:
  - 'ADR-0007: Flat node_id with central meaning map (the OUTPUT frame addresses a node by its flat id; the actuator is an ordinary registry node)'
  - 'ADR-0009: Central map & binding manifest (the CAN-output target is a new binding-manifest target; the empty-manifest hash is unchanged)'
  - 'ADR-0014: Standardized controller & Modbus I/O hardware (the An-Penta-Plus is the actuator board; the T-Connect Pro gateway already has onboard CAN)'
  - 'ADR-0017: Node deployment profiles (the external-actuator profile extends the profile system to non-CANBed, externally-firmwared nodes)'
amends:
  - 'ADR-0005: nodes were "dumb button/sensor sources → controller"; a node may now also be an ACTUATOR that applies controller→node CAT_OUTPUT commands. It stays dumb — the gateway/HA decides what to send; the node only applies it. The topology, bit rate, and single-purpose-forwarder rules are unchanged.'
  - 'ADR-0013: the HA-down fallback may target a CAN OUTPUT (a remote actuator node), not only a gateway-local relay. Single-click-only semantics and the ha_ready gate are unchanged.'
relatedDocuments:
  - docs/adr/0013-gateway-local-relays-single-click-fallback.md
  - docs/adr/0005-can-bus-topology-segmented-multi-bus.md
  - docs/contracts/spec-bindings-arbitration-contract/SPEC.md
  - canbus/protocol/canbus_protocol.h
  - canbus/tools/generate_nodes.py
  - canbus/tools/bindings.py
  - registry/nodes.csv
  - lighting/packages/led_can_actuator.yaml
  - lighting/protocol/binding_actuation.h
  - lighting/protocol/relay_store.h
  - devices/an-penta-1.yaml
  - devices/light-controller.yaml
---

# ADR-0020: CAN actuator nodes and the CAT_OUTPUT command slice

## Status

**Proposed** (2026-08-11). Implemented and config-validated; the protocol slice, binding
validation/canonicalization, and fallback dispatch are natively tested, and both the An-Penta
(`devices/an-penta-1.yaml`) and gateway (`devices/light-controller.yaml`) firmware compile. Not
yet hardware-verified (the CAN bench test — a gateway + An-Penta on a terminated pair — is the
outstanding proof) and not yet exercised by data: `registry/bindings.yaml` stays empty until the
lighting circuit inventory (ADR-0013 open item 4). Extends ADR-0013 and amends ADR-0005's node
role; does not touch their load-bearing decisions.

A withdrawn predecessor actuated the strips over HTTP (`web_server` REST), modeling each as a
"relay id 32+" in the binding manifest. It was rejected in review as too hacky (an HTTP endpoint
masquerading as a relay) and too dependent on the WiFi/HA/HTTP software stack. This ADR is the
dedicated-hardware-channel replacement.

## Context

`devices/an-penta-1.yaml` (a QuinLED-An-Penta-Plus) drives LED strips. Its buttons are **CAN
wall-switch nodes**, decoded only by the lighting **gateway** (`devices/light-controller.yaml`).
When HA is down, only the gateway holds the button event, and the strips must still respond — over
a channel independent of WiFi/router/HA.

The CAN protocol already cut the seam: `canbus_protocol.h` reserved **`CAT_OUTPUT`
("commands / management, controller → node")**, the node RX filter `CAN_MASK_ADDR` (category +
node_id), and noted the OUTPUT command set was a deferred "later slice." The gateway already owns
`can0` and defaults its TX id to the CAT_OUTPUT base. So a controller→node actuator command is not
a bolt-on — it is that deferred slice, and the An-Penta is its first consumer.

**Hardware feasibility (verified):** the An-Penta-Plus QWIIC/I²C header (GPIO15 SDA, GPIO16 SCL,
+3.3 V, GND) hosts an external **SN65HVD230** 3.3 V CAN transceiver — 2 GPIOs for TWAI TX/RX plus
power — independent of the board's Ethernet/WiFi (it repurposes the unused I²C bus). Wiring:
`GPIO16 (tx) → CTX`, `GPIO15 (rx) → CRX` (GPIO15 as rx is favorable — CRX idles high = its
strapping level), `CANH/CANL` to the nearest segment. The board's fixed onboard 120 Ω terminator
means a mid-bus An-Penta needs that resistor removed (only bus ends terminate) — the same
discipline the existing CANBed/T-2CAN bus follows.

## Decision

**Scope: CAN carries only the HA-down fallback.** HA drives the strips normally over the WiFi
native API; when HA is down the gateway commands them over CAN. Five parts:

### 1. The CAT_OUTPUT command slice (protocol)

`canbus_protocol.h` gains `MSG_OUT_SET_CHANNEL` and numeric op codes `OUT_OP_OFF/ON/TOGGLE`
(mirroring the relay `on|off|toggle` vocabulary — single-click semantics, ADR-0013). Frame:
ID = `can_id(CAT_OUTPUT, target_node_id)`, payload `[PROTO_V1, MSG_OUT_SET_CHANNEL, channel, op]`.
`output_payload()` + decoders are pure/native-tested. This is the general actuator-command layer;
any future CAN actuator reuses it.

### 2. The An-Penta as a CAN actuator node

`lighting/packages/led_can_actuator.yaml` (named `an_penta_can.yaml` at the time of this ADR;
generalized to serve both boards in ADR-0021) declares `can0` (esp32_can on the QWIIC pins, 125 kbps) with
an `on_frame` that decodes CAT_OUTPUT commands addressed to its node_id (channel → `tw1`/`tw2`,
op → turn_on/off/toggle), plus a CAT_STATUS heartbeat so the health monitor tracks it like any
node. Composed by `devices/an-penta-1.yaml`, which keeps its WiFi + HA API (the normal path).

### 3. A first-class registry node (external-actuator profile)

`generate_nodes.py` gains a `profile.external` attribute and a `led-penta` profile: it reserves a
node_id, emits the `node_map.h` / `map.json` / HA-health entries, but generates **no**
`canbus/nodes/*.yaml` (the firmware is the hand-composed entry point). `registry/nodes.csv` gets
node 102. This generalizes ADR-0017's profile system to non-CANBed, externally-firmwared nodes; a
bridge and an An-Penta are both "ordinary registry rows," addressable and health-tracked.

### 4. A first-class CAN-output binding target

The binding manifest gains an `output: <node>/<channel>` target as a sibling to `relay:` (a
binding carries exactly one). `bindings.py` validates it (destination exists, is an external
actuator, channel in range) and canonicalizes it by meaning. `BindingEntry` gains, **frozen-
additive** (spec + drift test updated in the same lighting-led commit, per the
`spec-bindings-arbitration-contract` ownership rule), `target_kind` / `target_node_id` / `channel`.
The empty-manifest hash is unchanged, so HA's readiness heartbeat still matches. This is the clean
replacement for the withdrawn relay-id-32 overload.

### 5. The gateway sends CAT_OUTPUT on fallback

`fire_binding_fallback()` (`relay_store.h`) dispatches by `target_kind`: `relay` drives the local
`Switch*` as before; `output` sends `output_payload(channel, op)` on `can0` to
`can_id(CAT_OUTPUT, target_node_id)`. `can0` is registered in `can_output_sender()` in the
gateway's `on_boot` (mirroring the relay `Switch*` registration). CAN TX is non-blocking, so it
fires inline — simpler than the queue the withdrawn HTTP path needed.

## Consequences

### Positive

- **Native to the protocol.** Implements the pre-reserved CAT_OUTPUT slice rather than overloading
  relays; a light is addressed as a node/channel, not a fake relay.
- **Infra-independent + multi-drop.** One CAN pair reaches every An-Penta, each a first-class node,
  with no dependence on WiFi/router/HA/HTTP.
- **Reuses the arbitration spine.** The `ha_ready` gate, ACK/double-action window, and
  `fallback_events` telemetry are unchanged; CAN outputs participate exactly as relays do.
- **HA-drives-up / gateway-drives-down, over the bus.** HA still drives the strips over WiFi; only
  the fallback is CAN. One actuator, two drivers, one gate — ADR-0003's stance across two devices.

### Negative / costs

- **A transceiver per An-Penta.** The board has no CAN transceiver; each unit needs an external
  SN65HVD230 on the QWIIC header (and its onboard 120 Ω removed unless it sits at a bus end).
- **CAN wiring reach.** A drop must reach each An-Penta location — the real-world constraint (the
  user confirmed it is satisfiable). Repurposes the An-Penta's I²C header (unused in this project).
- **Coarse channel validation.** `bindings.py` bounds the output channel by a constant, not a
  per-actuator count (not in the registry yet), so a binding to a channel the target lacks is
  caught at the actuator, not at validation.
- **Single-click on/off/toggle only.** No brightness/CCT in fallback — consistent with ADR-0013.
  Prefer `op: on`/`off` over `toggle` for the ADR-0003 double-action window.
- **A non-CANBed node role.** An actuator node runs hand-composed firmware, so it is exempt from
  the generated-node path — a deliberate `profile.external` seam, not an `if profile ==` branch.

## Alternatives considered

- **HTTP to `web_server`** (the withdrawn predecessor). Rejected: it leans on the WiFi/HA/HTTP
  stack the fallback is meant to survive, and modeled a light as a relay id. The An-Penta's
  `web_server` may remain as an optional manual/diagnostic local control, but is not the gateway
  integration path.
- **Direct GPIO / UART point-to-point.** Uses the same two QWIIC pins but is point-to-point — it
  does not scale to several An-Pentas without a link (and gateway pins) per unit. CAN gives a
  multi-drop bus on the same pins + a transceiver, so it dominates for multiple units.
- **RS485 / Modbus (An-Penta as a Modbus slave).** ESPHome's Modbus-*server* support is immature,
  and it conflates the lighting actuator with the climate/relay RS485 bus. CAN is already the
  lighting-domain transport (buttons) and has priority arbitration.
- **ESP-NOW.** Wireless and infra-light, but uses the WiFi radio and is not a dedicated wired
  channel. Retained as the fallback if CAN wiring ever proves unreachable.
