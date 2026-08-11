---
adr: 0019
title: 'Remote HTTP fallback actuators: the gateway drives off-board ESPHome lights over the LAN when HA is down, via the transport-agnostic binding output id'
status: 'Proposed'
date: '2026-08-11'
deciders: ['Alberto']
author: 'Claude'
dependsOn:
  - 'ADR-0013: Gateway-local relays & single-click fallback (this realizes its §1 "transport-agnostic by id" seam with a remote transport)'
  - 'ADR-0003: Centralized single-controller with on-board fallback (HA-drives-up / board-drives-down arbitration, ha_ready gate — unchanged, extended across the LAN)'
  - 'ADR-0009: Central map & binding manifest (the canonical hash is unchanged — this is not a manifest change)'
  - 'ADR-0014: Standardized controller & Modbus I/O hardware (the An-Penta-Plus target is Ethernet/WiFi-only, no CAN transceiver)'
  - 'ADR-0010: Security posture (§5 authenticated OTA — the same "privileged actuator gets authenticated" stance applies to the web_server this calls)'
extends:
  - 'ADR-0013: fixes the *current realization* from "gateway-local outputs only" to "gateway-local relays OR remote HTTP outputs", exactly the extension §1 and its Consequences ("Transport-agnostic by id") left open. No registry schema, canonical-form, manifest-hash, or BindingEntry-contract change.'
relatedDocuments:
  - docs/adr/0013-gateway-local-relays-single-click-fallback.md
  - docs/adr/0003-centralized-single-controller-with-onboard-fallback.md
  - registry/bindings.yaml
  - lighting/protocol/binding_actuation.h
  - lighting/protocol/remote_store.h
  - lighting/protocol/relay_store.h
  - lighting/packages/remote_actuators.yaml
  - devices/light-controller.yaml
  - devices/an-penta-1.yaml
  - canbus/tools/bindings.py
---

# ADR-0019: Remote HTTP fallback actuators

## Status

**Proposed** (2026-08-11). Implemented and config-validated across
`devices/light-controller.yaml` and `devices/an-penta-1.yaml`; the pure dispatch logic is
natively tested (`lighting/tests/test_binding_actuation.cpp`). Not yet hardware-verified and
not yet exercised by real data — `registry/bindings.yaml` is still empty (ADR-0013 open item
4), so like the relay fallback this is live code awaiting authored bindings. Extends ADR-0013;
does not amend its decision, only its realization.

## Context

`devices/an-penta-1.yaml` (a QuinLED-An-Penta-Plus) drives LED strips and exposes an
authenticated `web_server` REST API that stays up when Home Assistant is down
(`api: reboot_timeout: 0s`). But the buttons that should toggle those strips are **CAN
wall-switch nodes**, and their presses are only ever decoded by the **lighting gateway**
(`devices/light-controller.yaml`, `lighting/packages/buttons.yaml`). The An-Penta has **no CAN
transceiver** (ADR-0014), so it cannot see a button. When HA is down, the only actor holding
the button event is the gateway, and the only interface the An-Penta still answers is its REST
API. So the gateway must reach the strip **across the LAN**.

ADR-0013 already routes HA-down single-clicks through a binding manifest keyed
`(node_id, button) → output id(s) + op`, fired only when `ha_ready` is false. Today those
output ids resolve to local Modbus relay `Switch*`es. Crucially, ADR-0013 §1 fixed the id as
**transport-agnostic** — "a later move to remoteable relays needs *no registry change* — only a
`relay_N → coil` map in the gateway config" — and its Consequences list "Transport-agnostic by
id" as a designed extension point. A remote strip reached over HTTP is precisely the remote
output that seam anticipated.

## Decision

**Remote actuators are addressed by the same opaque progressive output id, in a range above
the local relay bank, and realized in the gateway as an authenticated HTTP POST to the target
device's `web_server`. The registry, the manifest schema, the canonical hash, and the compiled
`BindingEntry` contract are all unchanged.**

### 1. Output ids ≥ 32 are remote HTTP actuators

The binding output-id space splits by range (`lighting/protocol/binding_actuation.h`):
`0..31` are the local relay bank (ADR-0014), `REMOTE_ID_BASE (32)..MAX_OUTPUT_ID-1` are remote
HTTP actuators (currently `32 → tunable_white_1`, `33 → tunable_white_2` on `an-penta-1`).
`output_id_kind(id)` classifies `LOCAL | REMOTE | OUT_OF_RANGE`. The registry stays opaque — a
binding is still `relay: 32, op: toggle`; nothing in `registry/` knows it is a light on another
device. Only the gateway config resolves the transport, exactly as ADR-0013 §1 specified for a
`relay_N → coil` map.

### 2. Transport is authenticated HTTP to the target's web_server

The gateway POSTs to `http://<host>/light/<object_id>/<turn_on|turn_off|toggle>`. The
`op → verb` and `id → object_id` maps live in `lighting/protocol/remote_store.h`; the **host**
is a gateway-config substitution (`an_penta_host` in `devices/light-controller.yaml`), not a
protocol constant. The request carries HTTP Basic auth (`an_penta_basic_auth`, a precomputed
`base64("admin:<web password>")`) — same "a privileged actuator gets an authenticated
interface" stance as ADR-0010 §5's OTA. The gateway holds the precomputed token, never the raw
password, and does no runtime base64.

### 3. Non-blocking: fallback enqueues, a drain loop POSTs

`fire_binding_fallback()` runs on the CAN `on_frame` handler and the 250 ms ACK sweep — hot
paths that must not block on the network. For a REMOTE id it only **enqueues** an
`(output_id, op)` command (`remote_cmd_push`, a header-accessor ring like
`pending_acks_store()`); a standalone `interval: 100ms` in
`lighting/packages/remote_actuators.yaml` drains the queue and issues the `http_request.post`
with a short (1 s) timeout. The queue front is always popped — even on a failed or unmapped
POST — so a bad entry can never wedge it, and a failed POST is fire-and-forget (re-issuing a
toggle could double-actuate). The only blocking is the bounded drain-loop stall on an
unreachable target, and only in the already-degraded HA-down path.

### 4. Address the target by static IP, not mDNS

`an_penta_host` MUST be a static / DHCP-reserved IP. mDNS (`*.local`) resolution is slower and
less certain during an outage — the exact moment this path runs — and a fallback should not add
a discovery dependency to reach a device whose address never changes.

### 5. The bounds bump is coordinated, but is not a manifest change

`canbus/tools/bindings.py`'s `MAX_RELAY_ID` widens `31 → 33` so authoring `relay: 32/33`
validates, kept in sync with `binding_actuation.h`'s `MAX_OUTPUT_ID`. This is validation-only:
it touches neither canonicalization nor the hash mechanism (`canonical_hash` is unchanged), so
`BINDINGS_MANIFEST_HASH` is byte-for-byte identical and Home Assistant's readiness heartbeat
still matches with no HA-side change. It is the same "bump the maxima together in one commit"
coordination ADR-0014 open item 2 already describes for a second relay bank.

## Consequences

### Positive

- **Reuses the whole arbitration spine.** The `ha_ready` gate, the manifest-hash agreement, the
  ACK/double-action window, and the `fallback_events` telemetry are unchanged; remote strips
  participate in exactly the same fallback the relays do, rather than a bolted-on side path.
- **No schema / hash / contract churn.** Registry shape, `tools/bindings.py` canonical form,
  the frozen `BindingEntry`, and the HA-side heartbeat are all untouched. The opaque id
  absorbed the new transport, precisely as ADR-0013 predicted.
- **HA-drives-up / gateway-drives-down, extended across the LAN.** When HA is up it still drives
  the strips (HA → An-Penta Native API); when HA is down the gateway drives them (HTTP). One
  set of lights, two drivers, one gate — ADR-0003's stance, now spanning two devices.

### Negative / costs

- **Cross-device secret coupling.** The An-Penta's `web_server` credential now also lives on the
  gateway (as the precomputed Basic token). Rotating the An-Penta web password means updating
  `an_penta_basic_auth` too. Accepted: the alternative (an unauthenticated actuator on the LAN)
  is worse under ADR-0010.
- **A new transport on the gateway.** `http_request` + a command queue + a drain loop is more
  surface than the local-`Switch*` path. Contained to one package and one glue header.
- **Bounded main-loop stall on an unreachable target.** The drain loop blocks up to the 1 s
  timeout when the An-Penta is unreachable. Only in the HA-down path, once per queued click.
- **Operational dependency on a stable IP.** The An-Penta needs a DHCP reservation; a silent IP
  change silently breaks the fallback (the live HA path would still work, masking it).
- **"relay" now spans remote outputs.** The id/field name stays `relay` for zero schema churn,
  so a reader of `registry/bindings.yaml` sees `relay: 32` for a light on another device. The
  opacity is by ADR-0013 design; mitigated by the id-range comment in `bindings.yaml`.
- **Still single-click on/off/toggle only.** No brightness or colour-temperature in fallback —
  consistent with ADR-0013 (continuous control is HA-only). Prefer `op: on`/`off` over `toggle`
  for remote strips: the ADR-0003 double-action window can bounce a toggle.

## Alternatives considered

- **Put the An-Penta on the CAN bus.** Rejected: the board has no CAN transceiver (ADR-0014);
  adding one is a hardware change purely to carry a command the REST API already accepts.
- **MQTT.** Rejected: a broker is normally co-located with HA (Mosquitto add-on), so "HA is
  down" often takes the broker with it. HTTP straight to the device is independent of that.
- **ESPHome native device-to-device call.** Not available: nothing calls another node's entity
  without HA in the middle. `web_server` REST is the supported device-to-device surface, and is
  why it was enabled on `an-penta-1`.
- **An explicit `light:` target field in `bindings.yaml`** (instead of an opaque id). Rejected:
  a canbus-owned contract change — `tools/bindings.py` canonicalization + hash, the
  frozen-additive `BindingEntry`, the contract spec + drift test, and same-commit regen of both
  sides (AD-6). The opaque-id path delivers the same behavior with none of that, and is the
  realization ADR-0013 §1 already sanctioned. If the registry ever needs to *distinguish* a
  light from a relay for humans, that field is the natural future step.
