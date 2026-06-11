---
adr: 0008
title: 'Post-LIVE firmware & protocol evolution: controller as compatibility layer, physical-only node updates, no CAN bootloader'
status: 'Accepted'
date: '2026-06-11'
acceptedDate: '2026-06-11'
deciders: ['Alberto']
author: 'Winston (System Architect)'
dependsOn:
  - 'ADR-0003: Centralized single-controller with on-board fallback'
  - 'ADR-0005: CAN bus topology — segmented multi-bus (radios-off bridges)'
  - 'ADR-0007: Flat node_id identity with central meaning map'
relatedDocuments:
  - _bmad-output/planning-artifacts/adrs/0003-centralized-single-controller-with-onboard-fallback.md
  - _bmad-output/planning-artifacts/adrs/0005-can-bus-topology-segmented-multi-bus.md
  - _bmad-output/planning-artifacts/adrs/0006-sensor-data-transport-over-can.md
  - _bmad-output/planning-artifacts/adrs/0007-flat-node-id-with-central-meaning-map.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/project-context.md
  - firmware/protocol/canbus_protocol.h
---

# ADR-0008: Post-LIVE firmware & protocol evolution doctrine

## Status

**Accepted (2026-06-11).** Ratifies the post-LIVE firmware & protocol evolution doctrine,
drafted from the 2026-06-11 gap analysis: no document answered *what happens when a
node-side firmware or protocol change is needed after LIVE*. This decision carries an
**expiry date** — one of the options it rejects (a CAN bootloader) would have had to be
flashed onto every board *before* it goes into a wall and cannot be retrofitted afterwards.
Accepting this ADR is the deliberate choice, made before the first production node is
installed, to let that option expire — even though it concerns events that may never happen.

## Context

Three facts collide after the project is declared LIVE:

1. **Nodes are unreachable by design.** NFR-5 makes node isolation (no WiFi, no OTA, no
   API) intentional and permanent; nodes are flashed once via USB and mounted in walls.
   ADR-0005 extends this class: **bridges are radios-off as a load-bearing reliability
   decision** (`firmware/bridge/bridge.yaml` — no `wifi:`/`api:`/`ota:`). The
   physically-flashed-only fleet is *nodes + bridges*; only the gateway/controller (and the
   HVAC controller) are OTA-reachable.
2. **The protocol freezes at LIVE.** The versioning policy (project-context.md) keeps
   `PROTO_V1` in place with breaking changes made in lock-step *only because* every board
   can still be reflashed on the bench. Declaring LIVE — Alberto's explicit call — ends
   that: from then on, a breaking payload change means a version bump and some path to
   updating fielded firmware.
3. **A bootloader is the only update path that cannot be added later.** The protocol header
   reserves category values 5–14 with `BOOTLOADER` named in a comment
   (`canbus_protocol.h:62`), but nothing is designed or built. If a CAN-based reflash
   capability is ever wanted, it must ship on every board at install time — this option
   expires the day the first node goes into a wall.

What this ADR is *not*: a prediction that node firmware will need to change. The node's
job (button → frame; sensor → frame) is tiny and stable, and ADR-0007 deliberately made
nodes dumb so that meaning-level change happens centrally. This ADR decides what we do in
the *rare* case where that isn't enough — and, critically, whether we pay an insurance
premium now to keep the remote-update option alive.

## Decision

Five parts. The stance in one line: **change the controller, not the nodes; when a node
must change, touch it physically; do not build a CAN bootloader.**

### 1. The controller is the sole compatibility layer

Post-LIVE protocol evolution is **additive and controller-absorbed first**:

- New behavior ships as new payload versions / new categories emitted by *new* boards;
  the controller (the only always-updatable device) decodes **every historical payload
  version for the life of the deployment**. A fielded node's frames must never stop being
  understood.
- A change is only "node-affecting" if it alters what fielded nodes must *transmit* or
  *receive*. Anything expressible as controller-side translation — new HA event fields,
  re-mapping, new derived semantics — is by definition not a node change. Design reviews
  for post-LIVE changes must exhaust this route before touching node firmware.
- Bridges forward-all (ADR-0005), so new categories and payload versions cross segments
  with **no bridge firmware change** — the forward-all rule is what keeps bridges out of
  the compatibility business, and it is therefore reinforced here: selective filtering
  (ADR-0005 open item 3) would put version knowledge into bridges and must be weighed
  against this doctrine if ever proposed.

### 2. Node and bridge updates are physical: in-place USB reflash, or board swap

When a fielded board genuinely must change:

- **Primary path — in-place USB reflash.** The board stays mounted and wired; a laptop
  reaches its USB port. Identity is preserved (`node_id` is a flash-time substitution —
  recompile from the registry and the board keeps its id and its central-map entry; no
  commissioning needed).
- **Secondary path — board swap.** ADR-0007 already optimised this: flash a spare with a
  *fresh* `node_id` on the bench, swap it in, press-to-identify, re-point the central-map
  entry. Minutes per node, no in-wall flashing. Used when the board is damaged or USB
  access is awkward.
- A fleet-wide breaking change is therefore a **campaign**: ~5–10 min per board including
  ladder time — roughly 2–3 working days for a ~100-node house. That cost is accepted as
  the price of rare events, and is exactly what Decision §1 exists to make rare.

### 3. Service-access install rule (the cheap insurance we *do* buy)

Every node and bridge must be **mounted with its USB port reachable** through the wall-box
opening or enclosure without rewiring — verified at install as part of commissioning.
This converts the worst case from "destructive wall access" to "screwdriver + laptop",
at near-zero install cost. The concrete mechanical spec (connector orientation, pigtail
vs direct, per mount type) belongs to the physical/electrical topology ADR (forthcoming;
ADR-0003 open item 8) — this ADR establishes the *requirement*.

### 4. No CAN bootloader — explicitly forgone

We deliberately do **not** build CAN-based reflashing, and we accept that this option
expires at first install:

- **The bootloader paradox:** the bootloader itself becomes the one piece of frozen,
  unupdatable code on every board — a bug in it is strictly worse than its absence. To
  dodge a hypothetical reflash campaign we would create ~100 permanent installations of
  the most safety-critical custom code in the project.
- **It is not boring technology.** No mainstream, field-proven CAN bootloader exists for
  RP2040 + MCP2515-over-SPI; this would be bespoke firmware (custom SPI driver inside a
  bootloader, A/B flash slots, transfer protocol, brick recovery) plus bench validation
  worthy of its criticality — a project comparable to everything built so far, purchased
  against a low-probability event.
- **The architecture already bought the alternative.** ADR-0007's stateless nodes +
  cheap commissioning (§2 above) and Decision §3's access rule make physical updates
  cheap enough that remote update buys little.
- `BOOTLOADER` stays a *comment-level name reservation* in `canbus_protocol.h` — an
  escape hatch for a hypothetical future board generation, not a commitment. No category
  value is allocated.

### 5. LIVE gate: freeze checklist

Because this doctrine makes post-LIVE node changes expensive, LIVE must not be declared
on the PoC surface alone. Before Alberto declares LIVE, the frozen surface must have
soaked end-to-end:

- Sensor kit (ADR-0006) deployed and reporting on at least one production-form node.
- `ha_ready` arbitration (ADR-0003) tuned with real timeout values, manifest hash real.
- At least one bridge (ADR-0005) soak-tested in line (its open item 5).
- A reflash campaign **runbook** written and timed on the bench (validates the §2 cost
  estimate before we rely on it).
- Compiled firmware artifacts (UF2/bin) archived per release alongside the pinned
  ESPHome version, so a campaign years later does not depend on rebuilding bit-rotted
  toolchains.

## Consequences

### Positive

- **No new frozen code.** The only permanently-fielded firmware is the simple, soaked
  node/bridge firmware itself — no bootloader to get right forever.
- **Evolution pressure lands on the right device** — the controller, which is
  OTA-reachable, centrally tested, and already the meaning-bearing component (ADR-0007).
- **Decision §3 is cheap and compounding** — USB reachability also serves diagnostics
  (serial logs on a misbehaving wall node) and the swap path.
- **The LIVE gate gets teeth** — freeze stops being a date and becomes a checklist.

### Negative / costs

- **The remote-update door closes permanently** at first install. If a fleet-wide
  node-side change is ever needed, it is days of physical work, not an evening of CAN
  traffic. Accepted: probability is low, the campaign is bounded and runbook-validated,
  and the insurance alternative carries its own (worse) risk.
- **Controller accumulates compatibility code** over years (every historical payload
  version). Bounded in practice: versions only proliferate when fielded transmitters
  change, which this doctrine makes rare.
- **USB-reachability constrains mounting** — interacts with wall-box and enclosure
  choices (physical/electrical ADR must honour it).
- **Discipline cost:** "controller-absorbed first" is a review-time rule; it must be
  enforced in design review, not by tooling.

## Alternatives considered

- **A/B-slot CAN bootloader on every board.** A `CAT_BOOTLOADER`-driven transfer
  (~7 KB/s effective at 125 kbps → ~1–2 min per ~500 KB image per node, serialized per
  segment), dual flash slots, controller-orchestrated. Rejected per Decision §4: bespoke
  frozen code, no proven off-the-shelf base for RP2040+MCP2515, validation burden out of
  proportion to event probability, and the brick-recovery story still ends at a wall
  anyway. The natural fallback **if** the fleet were ever rebuilt on boards with a
  vendor-proven CAN bootloader.
- **Bootloader on sensor/bridge boards only** (fewer, more accessible, more complex
  firmware → most likely to need fixes). Rejected: keeps all bootloader costs for a
  subset of the fleet while those same boards are precisely the most physically
  accessible (bridges at segment convergence points, sensor casings ventilated/serviceable)
  — the insurance covers the boards that need it least.
- **WiFi-OTA on nodes "just for updates".** Rejected outright — reverses NFR-5 and
  ADR-0005's radios-off reliability stance; the WiFi stack's failure modes are exactly
  what the wired design exists to avoid.
- **No doctrine (decide when it happens).** Rejected — it silently *is* a decision: it
  forfeits the bootloader option (expires at install) and skips the cheap §3 install rule,
  leaving the worst version of the physical path as the only path.

## Open items

1. **USB-reachability mechanical spec** per mount type (wall box, bridge enclosure,
   sensor casing) — owned by the forthcoming physical/electrical topology ADR. Tracked in
   `deferred-work.md`.
2. **Reflash campaign runbook** — stub now lives at `docs/reflash-campaign-runbook.md`;
   still needs bench-timing of the per-board/fleet numbers to validate the §2 cost estimate
   (feeds the LIVE checklist, §5).
3. **Firmware artifact archival** — where compiled per-release UF2/bin images live
   (repo? release tags?) and what metadata ties them to registry state. Tracked in
   `deferred-work.md`.
4. **Spare-stock policy** — how many pre-flashed spare boards (and at what `node_id`
   allocation discipline) sit on the shelf for the swap path. Tracked in `deferred-work.md`.
5. **LIVE checklist ownership** — done in structure: the freeze gate is now tracked as the
   checklist file `docs/live-freeze-checklist.md` (derived from §5, which stays here as
   rationale), pending Alberto's sign-off and the real values its gates depend on.

## Notes

Builds on ADR-0007 (stateless nodes make board swap cheap — the load-bearing fact of
Decision §2), ADR-0005 (forward-all bridges stay version-agnostic; radios-off makes
bridges part of the physical-update fleet), and ADR-0003 (the controller, as the single
always-updatable authority, is where compatibility lives). The versioning policy in
`project-context.md` ("no bump until LIVE") is unchanged pre-LIVE; this ADR defines what
LIVE *means* for firmware change and what the bump costs after it.
