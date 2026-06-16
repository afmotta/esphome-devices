---
adr: 0010
title: 'Security posture: physical envelope as trust boundary, no bus cryptography, consequence-limiting invariants (accepted-risk record)'
status: 'Accepted'
date: '2026-06-11'
acceptedDate: '2026-06-16'
deciders: ['Alberto']
author: 'Winston (System Architect)'
dependsOn:
  - 'ADR-0005: CAN bus topology (forward-all bridges extend any tap house-wide)'
  - 'ADR-0007: Flat node_id identity (stateless flash-once nodes preclude key distribution)'
  - 'ADR-0008: No CAN bootloader (injection can never become persistent code)'
  - 'ADR-0009: Git as system of record (meaning is never writable over CAN)'
relatedDocuments:
  - _bmad-output/planning-artifacts/adrs/0003-centralized-single-controller-with-onboard-fallback.md
  - _bmad-output/planning-artifacts/adrs/0005-can-bus-topology-segmented-multi-bus.md
  - _bmad-output/planning-artifacts/adrs/0006-sensor-data-transport-over-can.md
  - _bmad-output/planning-artifacts/adrs/0008-post-live-firmware-evolution-no-can-bootloader.md
  - _bmad-output/planning-artifacts/adrs/0009-central-map-binding-manifest-system-of-record.md
  - firmware/gateway/gateway.yaml
  - firmware/gateway/secrets.yaml.example
---

# ADR-0010: Security posture — accepted-risk record

## Status

**Accepted (2026-06-16) — implemented.** From the 2026-06-11 gap analysis: no document
recorded the system's threat model or why the bus carries no authentication. For home
infrastructure the right answer is "physical access is the boundary" — but an
accepted-risk ADR is exactly the artifact that distinguishes a considered decision from an
oversight, and writing it surfaced one concrete defect (unauthenticated OTA) and one rule
that must hold at install time (the envelope rule, §2). Accepted and implemented in one
pass: open item 1 — the OTA password, the only mandated code change — is closed on the
gateway, and open item 5 — the no-security-critical-actuation constraint — is registered in
project-context.md. The remaining open items (2 envelope audit, 3 HVAC sanity bounds, 4
security-signal alerting) are deferred to their named owners. Named revisit triggers: an
exterior device need (§2), an RP2350-class platform change (§3), or nodes gaining RX
behavior (§4.1).

## Context

Classic CAN has no authentication, authorization, or encryption: any device electrically
on the bus can emit any frame with any ID. In this architecture that fact has reach:

- **Every wall plate is a bus tap**, and ADR-0005's forward-all bridges deliberately carry
  every frame across segments — so one tap anywhere reaches the whole house. Segmentation
  isolates electrical faults, not adversaries.
- **What injection can do today:** spoof `CAT_INPUT` (trigger any binding/automation —
  lights, future relays), spoof `CAT_SENSOR` (mislead the HVAC controller), spoof
  `CAT_STATUS` (fake or mask node health), or babble (degrade a segment; bounded bridge
  FIFOs shed load but storms still cross by design).
- **What injection cannot do** — and this is the architecture's quiet strength: it cannot
  install code (no CAN bootloader, ADR-0008), cannot rewrite meaning (map and bindings
  live in git, edited by CLI, compiled in — ADR-0009; nothing is writable over CAN), and
  cannot reconfigure nodes (ADR-0007 nodes are receive-inert: identity baked at flash, no
  CAN-driven code paths). The worst bus-borne outcome is *behavioral and transient*, never
  persistent.
- **The LAN surface** is separate: the gateway/controller speaks ESPHome native API
  (Noise-encrypted, key in gitignored secrets — already in place) and OTA — **currently
  unauthenticated** (`ota: platform: esphome`, no password): anyone on the LAN could push
  firmware to the most privileged device in the system. The PoC gateway is on WiFi;
  production moves to Ethernet (architecture.md). Home Assistant's own exposure (remote
  access, users) is its own domain, out of scope here.
- **Cryptographic bus security would fight the architecture:** per-frame MACs would eat
  the 8-byte payload budget (ADR-0004/0006 layouts have no spare bytes), and key
  provisioning/rotation across ~100 flash-once, stateless, no-OTA nodes contradicts the
  entire ADR-0007/0008 doctrine. RP2040 also lacks secure-boot fuses (RP2350 has them) —
  node-side key storage would be plaintext flash regardless.

The threat actors that matter at house scale: guests, children, tradespeople, and a
burglar already inside. Anyone with sustained physical bus access can also flip a relay
by hand, rewire a switch, or unplug the controller — the marginal power CAN injection
adds is covertness and whole-house reach from a single point. That marginal power is what
this ADR consciously accepts.

## Decision

Six parts. The stance in one line: **trust the walls, harden the LAN, keep the bus
consequence-limited, and detect what we don't prevent.**

### 1. The trust boundary is the house's physical envelope plus the LAN

Bus access is treated as residency: no authentication on CAN, by decision. The system's
security reduces to (a) the physical security of the dwelling and (b) the security of the
home LAN. This is the same posture as classic KNX installations and the household's
existing infrastructure (mains wiring, thermostats, the HA server itself).

### 2. The envelope rule (the one rule installation must honour)

**No bus segment, stub, or node may exist outside the physically secured envelope.** No
gate intercoms, garage-door buttons on exterior walls, doorbell nodes, or runs through
spaces accessible without entering the house. A future exterior need is the **named
revisit trigger** for this ADR: it requires at minimum an isolated segment behind a
*filtering* (not forward-all) bridge — a deliberate exception to ADR-0005's forwarding
doctrine — designed at that time. The forthcoming physical-topology ADR (queue #2) must
carry this rule as a constraint on cable routing.

### 3. No cryptographic bus security — explicitly forgone

No per-frame MACs, no encryption, no signed frames, no node key material. Rationale as in
Context: payload budget, key-management contradiction with stateless flash-once nodes, no
hardware root of trust on RP2040, and a threat model whose bus-borne worst case is
behavioral, bounded, and reversible. Revisit only alongside a platform generation change
(RP2350-class parts with secure boot — the same trigger as ADR-0008's bootloader
alternative).

### 4. Consequence-limiting invariants (the mitigations we already own, now load-bearing)

These four properties exist for other reasons; this ADR promotes them to **security
invariants** — changing any of them now requires revisiting this threat model:

1. **Nodes stay receive-inert.** No CAN-driven code path on nodes; `CAT_OUTPUT` remains
   management-only and node-ignored. Any future feature that makes nodes *act* on frames
   must pass review against this ADR.
2. **No CAN bootloader** (ADR-0008) — injection never becomes persistent code.
3. **Meaning is never writable over the bus or from HA** (ADR-0009) — map and bindings
   change only via git + CLI + reflash.
4. **Bridges hold no security state** (ADR-0005 forward-all) — nothing per-bridge to
   subvert; a compromised segment gains reach but no authority.

### 5. LAN-surface mandates (the cheap, concrete hardening)

- **Close the OTA hole:** add `ota: password:` (secret) on every OTA-capable device —
  gateway/controller now, HVAC controller and bridges' build configs as they gain OTA.
  This is the one immediate code change this ADR mandates.
- API encryption key stays mandatory on every API-bearing device (already shipped on the
  gateway; carry the pattern forward).
- `secrets.yaml` stays gitignored with a committed `.example` (already shipped).
- Production controller on **Ethernet**; WiFi is PoC-temporary (already the architecture).

### 6. Detection over prevention

The bus is observable even though it is not authenticated, and the monitoring layer
(queue #5, next ADR) doubles as the security layer:

- `esphome.canbus_node_unknown` (already shipped) — an un-mapped `node_id` appearing on
  the bus is surfaced to HA: the tamper/foreign-device alarm primitive.
- Heartbeat monitoring — a node *disappearing* (unplugged, tampered) becomes visible.
- Storm/fault surfacing (Epic 5) — bus-level DoS becomes a notification, not a mystery.
- The health/monitoring ADR must treat these three as security signals, not just
  maintenance signals (alerting policy accordingly).

## Consequences

### Positive

- **The posture is now a decision, not a default** — reviewable, with named revisit
  triggers (exterior need; platform generation change; nodes gaining RX behavior).
- **Zero new mechanism** — the entire posture is one YAML key (OTA password), one
  installation rule, and four invariants the architecture already enforces for free.
- **The expensive path was evaluated, not ignored** — bus crypto rejected with reasons
  that trace to existing ADRs, so the next "shouldn't this be encrypted?" question has a
  written answer.

### Negative / costs

- **A hostile insider with a screwdriver owns the house's behavior** — covertly, from any
  wall plate, house-wide. Accepted: the same person owns it overtly today (breakers,
  relays, the HA server's power cable), and the assets at risk are lights and climate,
  not locks or safety systems. **Corollary: this bus must never carry security-critical
  actuation (door locks, alarm arming) without revisiting this ADR — that is a standing
  constraint on future features.**
- **Spoofed sensor data can drive HVAC decisions.** Accepted at house scale; cheap sanity
  bounds on the HVAC side (plausibility clamps, rate-of-change limits) are good
  engineering anyway and noted as an open item, not a mandate.
- **The envelope rule constrains future convenience** (no quick exterior button node) —
  deliberate friction; the revisit path is defined.
- **LAN compromise remains potent** (HA and the controller legitimately command the
  house). Out of scope: securing the LAN/HA is the household's general IT posture, not
  this system's.

## Alternatives considered

- **Per-frame authentication (truncated CMAC in payload, CANcrypt-style, KNX Data Secure
  analog).** Rejected: 4–8 MAC bytes don't fit the frozen 8-byte layouts (ADR-0004/0006);
  key distribution to stateless flash-once nodes contradicts ADR-0007/0008; replay
  protection needs per-node counters/nonces — state the nodes deliberately don't have;
  and the defended-against adversary is already inside the house.
- **Gateway-side anomaly filtering (rate-limit/quarantine suspicious node_ids).**
  Rejected as *prevention* — Epic 5 explicitly chose observability over throttling
  (momentary buttons: every legitimate event must fire; a false-positive filter is a
  broken light switch). Lives on as *detection* (§6).
- **Isolated security segment now (filtering bridge, pre-built for exterior devices).**
  Rejected: no exterior device exists or is planned; building the exception before the
  need violates Rule of Three and complicates the one bridge firmware that must stay
  trivially fail-safe.
- **Do nothing (no ADR).** Rejected — indistinguishable from never having thought about
  it, and it would have left the OTA hole unfound.

## Open items

1. **Add `ota: password:`** — **done (2026-06-16):** `password: !secret ota_password` wired
   into the gateway (the secret was already provisioned in `secrets.yaml`). Thread the same
   pattern into controller/HVAC/bridge configs as they gain OTA.
2. **Envelope audit at install time** — when the physical-topology ADR (queue #2) is
   drafted post-tubes, verify no planned wall box or cable run breaches §2; add the check
   to the commissioning runbook.
3. **HVAC sensor sanity bounds** — plausibility/rate-of-change clamps on the HVAC
   controller (external firmware); recommended, not mandated here.
4. **Security signals in the monitoring ADR** (queue #5) — unknown-node, node-vanished,
   and storm events get alerting treatment as security signals.
5. **Standing constraint registration** — **done (2026-06-16):** "no security-critical
   actuation on this bus without revisiting this ADR" recorded in project-context.md critical
   rules. Re-record wherever future feature intake also happens.

## Notes

This ADR spends its budget naming what is *not* defended and why, because the
architecture's real security work was already done elsewhere: ADR-0007 made nodes
meaningless, ADR-0008 made them unwritable, ADR-0009 made meaning unreachable from the
bus, and ADR-0005 kept bridges stateless. What remained was one missing password, one
installation rule, and the honesty of writing the acceptance down.
