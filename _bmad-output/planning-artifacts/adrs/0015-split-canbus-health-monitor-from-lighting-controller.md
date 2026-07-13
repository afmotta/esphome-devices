---
adr: 0015
title: 'Split canbus health monitoring onto its own device: dedicated Waveshare ESP32-S3 health monitor; the T-Connect Pro becomes the lighting controller'
status: 'Accepted'
date: '2026-07-13'
deciders: ['Alberto']
author: 'Claude (Opus 4.8)'
dependsOn:
  - 'ADR-0014: Standardized controller & Modbus I/O hardware (amends its §3 "no further split" resolution; the one-device-family relay/analog decisions and the hvac physical separation stand)'
  - 'ADR-0011: Health monitoring & degraded-mode visibility (this is the role being relocated to its own device)'
  - 'ADR-0005: CAN bus topology — segmented multi-bus (adds a second backbone tap near the gateway location)'
  - 'ADR-0013: Gateway-local relays, single-click fallback (its deferred physical-split question, closed by ADR-0014 as "no further split", is partially reopened here)'
  - 'AD-7 amendment (2026-07-06): CAN consumers split by domain into per-system packages with per-system gate instances — the logical split that makes this physical split cheap'
amends:
  - 'ADR-0014 §3 (Device composition): the resolution "no further split — lighting + canbus continue sharing the gateway" is replaced by a lighting ↔ canbus-health physical split. Everything else in ADR-0014 (one device family, the Modbus relay/analog banks, mirrored addressing, the hvac controller as a separate device) stands unchanged.'
relatedDocuments:
  - _bmad-output/planning-artifacts/adrs/0014-standardized-controller-modbus-io-hardware.md
  - _bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md
  - devices/light-controller.yaml
  - devices/health-monitor.yaml
  - canbus/packages/health.yaml
  - lighting/packages/buttons.yaml
  - lighting/packages/relay_bank.yaml
  - boards/waveshare-s3-rs485-can.yaml
  - boards/t-connect-pro.yaml
---

# ADR-0015: Split the canbus health monitor from the lighting controller

## Status

**Accepted** (2026-07-13). Amends ADR-0014 §3 only. Root-tree ADR (spans `canbus/`
infrastructure and `lighting/` application; the frozen `canbus/_bmad-output/` tree is never
edited, per AD-1). Implemented P1–P4 the same day: `can0` lifted into each entry point;
`devices/health-monitor.yaml` created on the new `boards/waveshare-s3-rs485-can.yaml`;
`devices/gateway.yaml` reduced and renamed `devices/light-controller.yaml`; docs/CLAUDE.md swept.
Open items 1–3 remain as hardware bring-up checks.

## Context

ADR-0014 §3 resolved the architecture spine's deferred "physical gateway split" as **"no
further split — hvac is already a separate physical device; lighting + canbus continue sharing
the gateway."** That put two systems' packages on one physical device,
`devices/gateway.yaml` (a LilyGO T-Connect Pro):

- `canbus/packages/health.yaml` — **infrastructure**: the bus definition (`can0`), heartbeat
  decode, per-node aliveness (ADR-0011), the fleet aggregates, the drift-visibility diagnostics
  (ADR-0009 §6), and the `node_lost`/`node_recovered`/`node_error`/`node_unknown` HA events.
- `lighting/packages/buttons.yaml` + `lighting/packages/relay_bank.yaml` — **application**:
  CAT_INPUT button decode, the `esphome.canbus_button` events, this system's `ha_ready` gate
  instance, and the single-click fallback actuation against the Modbus relay bank (ADR-0013 §1–2).

Three facts reopen that resolution:

1. **The two halves are already cleanly separable in code.** The AD-7 amendment (2026-07-06)
   split the CAN consumers into per-system packages with per-system `ha_ready` gate instances.
   The *only* remaining coupling between `health.yaml` and `buttons.yaml` is the `can0` bus
   object: `health.yaml` declares it, `buttons.yaml` `!extend`s it. Nothing else is shared.

2. **Combining them was a convenience, and it costs blast radius.** ADR-0014 §3's "no further
   split" was an economy-of-devices call, not a principled coupling. Its practical effect is
   that every lighting OTA reflashes the bus-health monitor, and every health-logic change
   reflashes the lighting actuator — a bus-observability outage on each lighting change and
   vice versa. That contradicts the single-purpose-firmware doctrine `devices/bridge.yaml`
   already follows for exactly this reason (infra observability wants its own failure domain).

3. **The health role has purpose-built hardware already on hand.** `canbus/packages/health.yaml`
   documented its native CAN pins (`GPIO15 / GPIO16`, since lifted to the entry point per §2) as
   suiting "the Waveshare ESP32-S3-RS485-CAN gateway board" — the pre-ADR-0014 gateway, already
   owned. Health
   monitoring needs **only** a CAN transceiver: no RS485, no relay bank, no Ethernet. It is a
   perfect fit for that board, and moving it there frees the boundary without buying anything.

The layered monorepo already believes `canbus/` is infrastructure and `lighting/` is an
application. This ADR draws that boundary at the **hardware** layer too.

## Decision

**Split `devices/gateway.yaml` into two single-purpose physical devices: a dedicated canbus
health monitor on the already-owned Waveshare ESP32-S3 (WiFi, CAN-only), and the lighting
controller on the T-Connect Pro (keeps the relay bank + fallback). Each entry point declares its
own `can0`.**

### 1. Two devices, one role each

| Device (entry point) | Board | Network | CAN pins | Composes | Modbus |
|---|---|---|---|---|---|
| **canbus health monitor** (`devices/health-monitor.yaml`, new) | Waveshare ESP32-S3-RS485-CAN (`boards/waveshare-s3-rs485-can.yaml`, new) | WiFi | GPIO15 / GPIO16 (declared in the entry point) | `canbus/packages/health.yaml` only | none |
| **lighting controller** (`devices/light-controller.yaml`, `devices/gateway.yaml` reduced + renamed) | LilyGO T-Connect Pro (`boards/t-connect-pro.yaml`, Ethernet) | Ethernet | GPIO6 / GPIO7 | `lighting/packages/buttons.yaml` + `lighting/packages/relay_bank.yaml` | relay bank @ `0x2` on `rs485_bus` |

The relay bank and fallback actuation stay on the T-Connect Pro — they need RS485 and the
ADR-0013 §1–2 single-click path. Health needs none of that.

### 2. `can0` moves into each entry point

Today the `canbus:` platform block (`id: can0`, pins, `bit_rate: 125KBPS`, the heartbeat
`on_frame` handlers) lives in `canbus/packages/health.yaml`, and `buttons.yaml` `!extend`s it.
After the split, **the bus definition moves out of the packages and into each entry point** (per
Alberto's call — a bus per entry point, not a shared bus package):

- `devices/health-monitor.yaml` declares `can0` with `tx_pin: GPIO15 / rx_pin: GPIO16`;
  `health.yaml` becomes a pure bus **consumer** — its heartbeat `on_frame` handler moves to an
  `!extend can0` in the entry point (or the entry point declares the full `canbus:` block and
  `health.yaml` keeps only the globals/sensors/logic). *(Which of the two shapes — see
  Implementation P1 — is a mechanical choice made when the block is lifted.)*
- `devices/light-controller.yaml` (lighting) declares its own `can0` with `tx_pin: GPIO6 / rx_pin: GPIO7`;
  `buttons.yaml` keeps `!extend`ing it exactly as today.

Consequences of the lift: the "compose `health.yaml` before any package extending `can0`"
ordering convention disappears (each device has a single CAN package over a bus the entry point
owns), and each device becomes self-contained — no package silently owns a bus another package
depends on.

### 3. The health monitor runs on WiFi

Accepted (Alberto, 2026-07-13): the health monitor is **observability, not actuation**. If WiFi
drops, it keeps observing the bus locally (aliveness sweeps, drift diagnostics) and simply cannot
report `node_lost`/etc. to HA until it reconnects — no bus function is lost, only its telemetry.
The lighting controller stays on **Ethernet**, because its arbitration heartbeats (ADR-0003) and
fallback actuation want a wired link.

### 4. A second CAN tap on the backbone

Both devices sit near the existing gateway location and each drives its own CAN transceiver onto
the same backbone segment (ADR-0005). CAN is multi-drop; two taps a short distance apart is
electrically routine. Termination is unchanged in intent (verify at bring-up, Open item 3).

## Implementation plan

AD-9 slices — in-place edits, no shims, each slice lands green with its consumers. `esphome
config`/`compile` on the affected entry points plus the native test battery
(`scripts/verification-battery.sh`) gate each phase.

| Phase | Scope | Depends on |
|---|---|---|
| P1 | **`can0` lift** — move the `canbus:` block out of `canbus/packages/health.yaml` into `devices/gateway.yaml` while still one combined device. Pure refactor: the gateway compiles identically and the split isn't visible yet, so this slice is independently verifiable against today's behaviour. Update `health.yaml`'s header (drops "the bus lives here so others can `!extend`") and `buttons.yaml`'s header (drops the "`health.yaml` defines `can0`" requirement). | — |
| P2 | **Health monitor device** — `devices/health-monitor.yaml` on `boards/waveshare-s3-rs485-can.yaml` (the new board file), its own `can0` @ GPIO15/16, composing `health.yaml` only; identity/network/OTA substitutions; `esphome config` green. | P1 |
| P3 | **Reduce the lighting controller (in place)** — drop `health.yaml` + the health-only `node_health.h` include + the `node_lost_timeout_ms` sub from `devices/gateway.yaml`; keep `buttons.yaml` + `relay_bank.yaml` + its own `can0` @ GPIO6/7; rewrite the file header for lighting-only. The **file rename** is deferred to P4 (it dangles ~15 CLAUDE.md/README/docs references, so it lands atomically with the doc sweep). | P1, P2 |
| P4 | **Rename + naming & docs sweep** — `git mv devices/gateway.yaml devices/light-controller.yaml`; set its `device_name`/`friendly_name` (and the health monitor's) per the naming proposal (`canbus-health-monitor`, `light-controller`); update every `devices/gateway.yaml` reference in root/`canbus/`/`lighting/` `CLAUDE.md`, `canbus/README.md`, `docs/rs485-wiring-guide.md`, `canbus/docs/*` (paths + the "composes `health.yaml` with `buttons.yaml`" / composition-order rules); annotate ADR-0014 §3 as amended-by-0015; flip the spine's resolved-Deferred "physical gateway split" annotation. | P2, P3 |

## Consequences

### Positive

- **Infra and application get separate failure domains at the hardware layer.** A lighting OTA
  can no longer black out bus-health observability, and health-logic changes can't take down the
  lighting actuator — the single-purpose-firmware doctrine `bridge.yaml` follows, extended to
  the gateway roles.
- **Zero purchase.** The health role returns to its purpose-built, already-owned Waveshare board;
  the design is the one `health.yaml` was written for.
- **Each entry point is self-contained** — it owns its `can0`; no package silently owns a bus a
  different package depends on, and the cross-package composition-order convention goes away.
- **The health monitor sheds RS485/relay dependencies entirely** — the infra observer's failure
  surface shrinks to CAN + WiFi.
- **Device naming disambiguates.** The gateway's awkward dual identity (both `canbus` and
  `lighting`, so it fit no single-system prefix) resolves into `canbus-health-monitor` and
  `light-controller` — this ADR and the pending device-naming proposal reinforce each other.

### Negative / costs

- **Reintroduces a second gateway-class board type**, partially walking back ADR-0014's
  single-spares-shelf thesis. Mitigations: it is *one* already-owned device, not proliferation;
  health is the least-critical bus role (pure observability); and the package stays pin-portable
  back onto a spare T-Connect Pro via two substitutions (`can_tx_pin`/`can_rx_pin`) if the
  Waveshare ever dies.
- **Health telemetry now traverses WiFi** — reporting is missed during WiFi outages (accepted:
  observability, not actuation; the bus is still observed locally).
- **One more device** to power, mount, network, and OTA in the locale tecnico.
- **Two CAN transceivers tap the backbone** instead of one (electrically trivial).
- **`can0` is declared in two entry points** — the pins/id/bitrate block appears twice.
  Deliberate, per the "bus per entry point" decision (§2); the shared-bus-package alternative was
  considered and rejected for locality (Alternatives). The two declarations differ anyway (pins
  GPIO15/16 vs GPIO6/7).

## Alternatives considered

- **Keep them combined (ADR-0014 §3 status quo)** — rejected: couples infrastructure
  observability to application churn for a device-count saving that the already-owned Waveshare
  erases.
- **Shared `can0` package included by both entry points** — rejected per Alberto's call: keep the
  bus local to each entry point for self-containedness; the two devices' pin sets differ, so a
  shared package would be a thin substitution wrapper with little payoff.
- **Health monitor on Ethernet (a second T-Connect Pro)** — rejected: there is no spare
  T-Connect Pro to dedicate, observability does not need a wired link (§3), and the Waveshare is
  already owned and purpose-built for this exact role.
- **Fold health monitoring onto the climate controller** (also on CAN) — rejected: the climate
  controller is a separate, actuation-critical device; loading bus-wide observability onto it
  recreates the very blast-radius coupling this ADR removes, and worse (actuation + observability
  in one failure domain).

## Open items

1. **Confirm the on-hand Waveshare ESP32-S3 is the RS485-CAN variant** with a CAN transceiver
   wired to GPIO15/16 (the pins `devices/health-monitor.yaml` declares for `can0`) — bench check
   at bring-up.
2. **Verify the CAN pin values** (GPIO15/16) against the physical board; ADR-0014's context
   records the old gateway using GPIO15/16 for CAN, so this should hold, but confirm.
3. **CAN termination with two taps** (ADR-0005): both taps sit near the existing gateway
   location, so no change is expected, but confirm termination/stub length at the CAN bring-up.
4. **Device-naming ratification**: this ADR assumes `canbus-health-monitor` / `light-controller`
   from the pending device-naming proposal; if those names change, the entry-point filenames and
   §1 follow.

## Notes

This amends **ADR-0014 §3 only**. The one-device-family decision (T-Connect Pro + Waveshare
Relay 32CH + Analog 8CH (B)), the Modbus relay/analog banks and mirrored addressing, and the
hvac controller as its own physical device all stand. ADR-0013's deferred physical-split
question — closed by ADR-0014 as "no further split" — is partially reopened: the split now falls
between **lighting and canbus-health**, not between lighting and hvac. Hardware quantities (buying
a Waveshare spare) are a purchasing note, not architecture.
